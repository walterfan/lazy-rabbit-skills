#!/usr/bin/env python3
"""harvest.py — turn a pile of real errors/tickets into FAQ + gotcha entries.

The closing loop of the living-tutorial family. Learners hit real failures;
those failures are the highest-signal source of what a tutorial is missing.
This script:

  1. reads a corpus of incidents (JSONL, or plain text separated by blank
     lines / `---`);
  2. extracts the most salient error line from each and NORMALIZES it into a
     signature (numbers, ids, paths, urls, quotes → placeholders; HTTP status
     kept as a strong signal) so the same failure clusters even when the
     surface text differs;
  3. ranks clusters by frequency — the gotcha that bites most gets fixed first;
  4. checks each cluster against the gotchas already documented in existing
     tutorials/notebooks (the family's `症状/原因/修复` marker format) and flags
     the ones NOT yet covered — that gap list is the feedback the loop exists to
     produce;
  5. emits FAQ entries and gotcha-marker SKELETONS in the exact family format so
     they paste straight back into notebooks / the code-tutor playbook / tours.

Honest by construction: it fills `症状` (the real, observed symptom) from the
data, but leaves `原因/修复` as TODO — the mechanical step surfaces the gap; a
human/AI enriches it. Same two-phase discipline as tutorial-to-notebook.

Stdlib only. Never phones home.

Usage:
    python harvest.py incidents.jsonl --out ./faq
    python harvest.py tickets.txt --out ./faq --against ../../notebook.ipynb ../tutorial.md
    python harvest.py incidents.jsonl --out ./faq --min-count 2
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

# --- normalization: strip the noise, keep the shape --------------------------
_URL_RE = re.compile(r"https?://\S+")
_UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                      r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_HEX_RE = re.compile(r"\b[0-9a-fA-F]{12,}\b")
_PATH_RE = re.compile(r"(?:[A-Za-z]:\\[^\s]+|/(?:[\w.\-]+/)*[\w.\-]+)")
_QUOTED_RE = re.compile(r"\"[^\"]*\"|'[^']*'")
_NUM_RE = re.compile(r"\b\d+\b")
_HTTP_RE = re.compile(r"\b([45]\d\d)\b")
_WS_RE = re.compile(r"\s+")

# lines that smell like the actual error
_ERR_HINT_RE = re.compile(r"(Error|Exception|Warning|Traceback|failed|denied|"
                          r"timeout|refused|invalid|unauthorized|forbidden)", re.I)
_PY_EXC_RE = re.compile(r"^[A-Za-z_][\w.]*(Error|Exception|Warning):")
# a named exception class anywhere in the line, e.g. AttributeError, ConnectionError
_EXC_CLASS_RE = re.compile(r"\b([A-Za-z_]\w*(?:Error|Exception|Warning))\b")
# similarity threshold for the keyword-overlap fallback
_KW_THRESHOLD = 0.4

_STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "your", "you", "from", "have",
    "was", "were", "when", "will", "not", "but", "are", "get", "got", "please",
    "error", "exception", "failed", "while", "http", "https", "code", "status",
    "request", "response", "call", "api", "return", "returned", "null", "none",
}


class HarvestError(Exception):
    pass


def load_incidents(path):
    """Return list of {'text': str, 'source': str}. JSONL or text blocks."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    if not raw.strip():
        raise HarvestError("input is empty.")

    # try JSONL first
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if lines and all(ln.lstrip().startswith("{") for ln in lines):
        incidents = []
        for i, ln in enumerate(lines, 1):
            try:
                obj = json.loads(ln)
            except json.JSONDecodeError as e:
                raise HarvestError(f"line {i}: invalid JSON ({e}).")
            text = obj.get("text") or obj.get("message") or obj.get("body") or ""
            src = obj.get("source") or obj.get("id") or f"line-{i}"
            if text.strip():
                incidents.append({"text": text, "source": str(src)})
        if incidents:
            return incidents

    # else: plain-text blocks separated by `---` or blank lines
    blocks = re.split(r"(?m)^\s*---\s*$", raw) if re.search(r"(?m)^\s*---\s*$", raw) \
        else re.split(r"\n\s*\n", raw)
    incidents = []
    for i, b in enumerate(blocks, 1):
        if b.strip():
            incidents.append({"text": b.strip(), "source": f"block-{i}"})
    if not incidents:
        raise HarvestError("no incidents found in input.")
    return incidents


def pick_error_line(text):
    """The most salient single line: a Python exception > an HTTP 4xx/5xx line >
    any error-ish line > the first non-empty line."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""
    for ln in reversed(lines):          # exception is usually last in a traceback
        if _PY_EXC_RE.search(ln):
            return ln
    for ln in lines:
        if _HTTP_RE.search(ln):
            return ln
    for ln in lines:
        if _ERR_HINT_RE.search(ln):
            return ln
    return lines[0]


def normalize(line):
    """Collapse a raw error line into a stable signature."""
    http = _HTTP_RE.search(line)
    s = line
    s = _URL_RE.sub("<URL>", s)
    s = _UUID_RE.sub("<ID>", s)
    s = _PATH_RE.sub("<PATH>", s)
    s = _HEX_RE.sub("<ID>", s)
    s = _QUOTED_RE.sub("<STR>", s)
    s = _NUM_RE.sub("<N>", s)
    s = _WS_RE.sub(" ", s).strip().lower()
    # keep HTTP status as an explicit prefix so 401 and 429 never merge
    if http:
        s = f"[http {http.group(1)}] {s}"
    return s


def _keywords(text):
    toks = re.findall(r"[a-zA-Z][a-zA-Z]{3,}", text.lower())
    kws = {t for t in toks if t not in _STOPWORDS}
    kws.update(re.findall(r"\b[45]\d\d\b", text))   # http statuses are keywords
    return kws


def _cluster_key(line, http):
    """The strong grouping signal, in priority order:
      1. HTTP status  (401 tickets belong together however they're worded)
      2. named exception class (AttributeError, ConnectionError, …)
      3. None → fall back to keyword-overlap agglomeration
    """
    if http:
        return ("http", http)
    m = _EXC_CLASS_RE.search(line)
    if m:
        return ("exc", m.group(1))
    return None


def _add(bucket, line, source, http, kws):
    bucket["count"] += 1
    if len(bucket["examples"]) < 3 and line not in bucket["examples"]:
        bucket["examples"].append(line)
    bucket["sources"].append(source)
    bucket["keywords"] |= kws
    if http and not bucket["http"]:
        bucket["http"] = http


def _new_bucket(line, http, key):
    return {"signature": normalize(line), "count": 0, "examples": [],
            "sources": [], "http": http, "keywords": set(), "key": key}


def cluster(incidents, min_count=1):
    """Group incidents by HTTP status / exception class, else by keyword overlap.

    Exact-signature matching under-clusters free-text tickets ("got a 401" vs
    "401 Unauthorized rejected"), so we key on the status/exception first and use
    keyword agglomeration only for everything else.
    """
    keyed = {}          # ("http",401) / ("exc","AttributeError") -> bucket
    kw_buckets = []     # keyword-overlap buckets (no strong key)

    for inc in incidents:
        line = pick_error_line(inc["text"])
        if not line:
            continue
        m = _HTTP_RE.search(line)
        http = m.group(1) if m else None
        kws = _keywords(line)
        key = _cluster_key(line, http)

        if key is not None:
            b = keyed.get(key)
            if b is None:
                b = _new_bucket(line, http, key)
                keyed[key] = b
            _add(b, line, inc["source"], http, kws)
        else:
            # greedy: join the most-similar existing keyword bucket over threshold
            best, best_sim = None, 0.0
            for b in kw_buckets:
                union = kws | b["keywords"]
                sim = len(kws & b["keywords"]) / len(union) if union else 0.0
                if sim > best_sim:
                    best, best_sim = b, sim
            if best is not None and best_sim >= _KW_THRESHOLD:
                _add(best, line, inc["source"], http, kws)
            else:
                b = _new_bucket(line, http, None)
                _add(b, line, inc["source"], http, kws)
                kw_buckets.append(b)

    clusters = [c for c in list(keyed.values()) + kw_buckets if c["count"] >= min_count]
    # stable sort: count desc, then signature asc for determinism
    clusters.sort(key=lambda c: (-c["count"], c["signature"]))
    return clusters


# --- coverage: what do existing tutorials already document? -------------------
_GOTCHA_HEAD_RE = re.compile(r"(⚠️|常见坑|gotcha|pitfall)", re.I)
_SYMPTOM_RE = re.compile(r"(症状|symptom)\s*[:：]\s*(.+)", re.I)


def parse_existing_gotchas(paths):
    """Extract already-documented gotchas (symptom text) from tutorials/notebooks.

    Understands the family's marker format and, for .ipynb, scans markdown cells.
    """
    gotchas = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        texts = []
        if p.endswith(".ipynb"):
            try:
                nb = json.loads(content)
                for cell in nb.get("cells", []):
                    if cell.get("cell_type") == "markdown":
                        texts.append("".join(cell.get("source", [])))
            except json.JSONDecodeError:
                texts.append(content)
        else:
            texts.append(content)
        for text in texts:
            in_gotcha = False
            symptom = None
            for ln in text.splitlines():
                if _GOTCHA_HEAD_RE.search(ln):
                    in_gotcha = True
                    symptom = None
                    continue
                if in_gotcha:
                    m = _SYMPTOM_RE.search(ln)
                    if m:
                        symptom = m.group(2).strip()
                        gotchas.append({"symptom": symptom, "source": p,
                                        "keywords": _keywords(symptom)})
                        in_gotcha = False
    return gotchas


def annotate_coverage(clusters, gotchas):
    """Mark each cluster covered/new by matching against existing gotchas."""
    for c in clusters:
        c["covered_by"] = None
        for g in gotchas:
            # strong match: same HTTP status shared as a keyword
            if c["http"] and c["http"] in g["keywords"]:
                c["covered_by"] = g["source"]
                break
            inter = c["keywords"] & g["keywords"]
            union = c["keywords"] | g["keywords"]
            if union and len(inter) / len(union) >= 0.34:
                c["covered_by"] = g["source"]
                break
    return clusters


# --- rendering ---------------------------------------------------------------
def render_faq(clusters):
    out = ["# FAQ (harvested from real incidents)", "",
           "Ranked by how often it actually happened. `原因/修复` are TODO — fill",
           "them from your own knowledge; the symptom and frequency are real data.",
           ""]
    for i, c in enumerate(clusters, 1):
        ex = c["examples"][0] if c["examples"] else c["signature"]
        cov = f" _(already in {os.path.basename(c['covered_by'])})_" if c.get("covered_by") else ""
        out += [
            f"## Q{i}. 遇到：`{ex}`{cov}",
            f"- **出现次数**: {c['count']}",
            f"- **来源**: {', '.join(c['sources'][:5])}" + (" …" if len(c["sources"]) > 5 else ""),
            "- **原因**: <!-- TODO: 填真正的原因 -->",
            "- **解决办法**: <!-- TODO: 填可复制的修复步骤 -->",
            "",
        ]
    return "\n".join(out)


def render_gotchas(clusters):
    """Family-format markers, ready to paste into a notebook/tutorial."""
    out = ["# Gotcha markers (paste into tutorials / code-tutor playbook)", "",
           "These use the family's shared format so `code-tutor` and",
           "`tutorial-to-notebook` recognize them. Enrich 原因/修复 before shipping.",
           ""]
    for c in clusters:
        ex = c["examples"][0] if c["examples"] else c["signature"]
        title = c["http"] and f"HTTP {c['http']}" or ex[:40]
        out += [
            f"> ⚠️ **常见坑 · {title}**（出现 {c['count']} 次）",
            f"> 症状: {ex}",
            "> 原因: <!-- TODO -->",
            "> 修复: <!-- TODO -->",
            "",
        ]
    return "\n".join(out)


def render_coverage(clusters):
    covered = [c for c in clusters if c.get("covered_by")]
    new = [c for c in clusters if not c.get("covered_by")]
    out = ["# Coverage report", "",
           f"- clusters found: **{len(clusters)}**",
           f"- already covered by existing tutorials: **{len(covered)}**",
           f"- **NOT yet covered (add these): {len(new)}**", ""]
    if new:
        out += ["## New — the tutorial is missing these", "",
                "| # | count | symptom | http |", "|---|---|---|---|"]
        for i, c in enumerate(new, 1):
            ex = (c["examples"][0] if c["examples"] else c["signature"]).replace("|", "\\|")
            out.append(f"| {i} | {c['count']} | {ex[:70]} | {c['http'] or '—'} |")
        out.append("")
    if covered:
        out += ["## Already covered (verify the fix still works)", ""]
        for c in covered:
            ex = c["examples"][0] if c["examples"] else c["signature"]
            out.append(f"- ({c['count']}×) {ex[:70]} → {os.path.basename(c['covered_by'])}")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Harvest FAQ + gotchas from real incidents.")
    ap.add_argument("input", help="incidents file (JSONL or text blocks)")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--against", nargs="*", default=[],
                    help="existing tutorial/notebook files to check coverage against")
    ap.add_argument("--min-count", type=int, default=1,
                    help="ignore clusters seen fewer than N times")
    args = ap.parse_args(argv)

    try:
        incidents = load_incidents(args.input)
    except (OSError, HarvestError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    clusters = cluster(incidents, min_count=args.min_count)
    if not clusters:
        print(f"error: no clusters at --min-count {args.min_count} "
              f"({len(incidents)} incidents read).", file=sys.stderr)
        return 1

    gotchas = parse_existing_gotchas(args.against) if args.against else []
    annotate_coverage(clusters, gotchas)

    os.makedirs(args.out, exist_ok=True)
    files = {
        "faq.md": render_faq(clusters),
        "gotchas.md": render_gotchas(clusters),
        "coverage.md": render_coverage(clusters),
    }
    for name, body in files.items():
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
            f.write(body)
            if not body.endswith("\n"):
                f.write("\n")

    new = [c for c in clusters if not c.get("covered_by")]
    print(f"ok: {len(incidents)} incidents → {len(clusters)} clusters")
    print(f"  top: {clusters[0]['count']}× {clusters[0]['examples'][0][:60]!r}")
    if args.against:
        print(f"  coverage: {len(clusters) - len(new)} covered, {len(new)} NEW to add")
    for name in files:
        print(f"  wrote {os.path.join(args.out, name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
