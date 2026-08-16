---
name: faq-harvester
description: >-
  Use when you have a pile of real user errors / support tickets / Q&A and want
  to turn them into FAQ entries and tutorial gotchas — and to find what the
  tutorial is still missing. Reads incidents (JSONL or text blocks), extracts
  and normalizes the salient error line, clusters by HTTP status / exception
  class / keyword overlap, ranks by frequency, and checks each cluster against
  the gotchas already documented in your tutorials/notebooks — flagging the ones
  NOT yet covered. Emits FAQ entries plus gotcha markers in the family's shared
  症状/原因/修复 format, ready to paste back into notebooks, the code-tutor
  playbook, or a tour. The feedback loop of the living-tutorial skill family.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - faq
  - support
  - error-clustering
  - documentation
  - developer-experience
category: dev-tools
use_cases:
  - "Cluster real support tickets/errors into ranked FAQ entries"
  - "Find which failures a tutorial does NOT yet document (coverage gap)"
  - "Generate gotcha markers in the family format to paste back into tutorials"
  - "Prioritize doc work by how often each failure actually happens"
platforms:
  - claude-code
visibility: public
---

# faq-harvester

The best source of truth about what a tutorial is missing is the list of ways
real people failed with it. This skill closes the living-tutorial loop: it takes
a heap of messy incidents — support tickets, error logs, Slack questions — and
turns them into ranked FAQ entries and paste-ready gotcha markers, while telling
you **which failures your tutorial still doesn't cover.**

This is the **feedback half** of the family. `tutorial-to-notebook`,
`api-to-sandbox`, and `tour-builder` push a tutorial out; `code-tutor` helps at
the moment of failure; `faq-harvester` collects those failures back up and feeds
them into the next revision. The output speaks the family's shared dialect —
`症状 / 原因 / 修复` markers and `# → expected` — so it drops straight back in.

> Honest by construction: the script fills **症状** (the real, observed symptom)
> and the **frequency** from your data, but leaves **原因 / 修复** as `TODO`. It
> surfaces the gap mechanically; a human or AI enriches it. Same two-phase
> discipline as `tutorial-to-notebook` — never fabricate a root cause you didn't
> verify.

## What it does

1. **Reads** incidents from JSONL (`{"text": "...", "source": "ticket-123"}`) or
   plain text separated by blank lines / `---`.
2. **Extracts** the most salient error line per incident (Python exception >
   HTTP 4xx/5xx line > error-ish line > first line).
3. **Normalizes** it (numbers/ids/paths/urls/quotes → placeholders; HTTP status
   kept) so the same failure clusters despite surface differences.
4. **Clusters** by HTTP status → exception class → keyword overlap, and **ranks**
   by frequency (fix the gotcha that bites most, first).
5. **Checks coverage** against existing tutorials/notebooks — parses their
   `症状/原因/修复` gotcha markers and flags clusters **not yet covered**.

## What it generates

Into an output directory:

| File | Purpose |
|---|---|
| `coverage.md` | The payoff: clusters **NEW** (tutorial is missing them) vs already covered |
| `faq.md` | Ranked Q&A entries, with real frequency + sources, `原因/修复` as TODO |
| `gotchas.md` | Gotcha markers in the family format, ready to paste into a notebook/playbook/tour |

## Ask First (only if it changes the output)

- **What to compare against** — which existing tutorial/notebook files define the
  gotchas already covered (`--against`). Without it, everything reads as "new".
- **Noise floor** — should one-off incidents be ignored (`--min-count 2` keeps
  only recurring failures)?

If you just have a ticket dump and want everything, run it as-is.

## Workflow

### 1. Gather the corpus

Export tickets/errors to JSONL (one per line, `text` + `source`) or paste them
into a `.txt` with `---` between incidents. More is better; duplicates are the
point (frequency is signal).

### 2. Harvest

```bash
python scripts/harvest.py incidents.jsonl --out ./faq
# check against what the tutorial already documents:
python scripts/harvest.py incidents.jsonl --out ./faq \
    --against ../my-tutorial.ipynb ../getting-started.md
# only recurring failures:
python scripts/harvest.py incidents.jsonl --out ./faq --min-count 2
```

### 3. Read `coverage.md` first

The **New** table is your work list, ranked by frequency. Each row is a failure
real users hit that your tutorial doesn't yet address.

### 4. Enrich, then feed back

For each new cluster, fill `原因 / 修复` from real knowledge (verify, don't
guess), then:

- paste the marker into the relevant notebook cell (picked up by `code-tutor`);
- add it to the `code-tutor` diagnosis playbook if it's a general pattern;
- if it's a UI stumble, add/clarify a `tour-builder` step.

That is the loop closing.

## Security

- **Incidents often contain secrets.** Real tickets paste tokens, keys, and PII.
  Treat the corpus as sensitive: store it access-controlled, and **scrub before
  publishing** any generated FAQ. The generator normalizes long hex/ids/quoted
  strings out of *signatures*, but example lines may still carry a pasted secret
  — review `faq.md`/`gotchas.md` before shipping and redact.
- **No fabricated fixes.** `原因/修复` ship as `TODO`; do not auto-fill a root
  cause you haven't confirmed. A wrong fix in an FAQ is worse than a gap.
- **Local only.** The script never uploads the corpus anywhere.

## Verification

Block delivery until:

- The three files are written and `coverage.md` lists a New/covered split.
- Generated `gotchas.md` markers use the family format (`> ⚠️ **常见坑 · …**` +
  `症状/原因/修复`) so `code-tutor` can parse them.
- Every example line in `faq.md`/`gotchas.md` has been eyeballed for a leaked
  secret/PII and redacted.
- `原因/修复` are either enriched with verified content or clearly left as TODO
  (never guessed).

Warn, but still deliver:

- No `--against` given → everything shows as "new"; say so.
- Free-text tickets cluster loosely (see Limitations) → note that counts are a
  floor, not exact.

## Limitations (say these out loud)

- **Log-like input clusters tightly; free prose clusters loosely.** Two tickets
  describing the same bug in very different words may stay separate. Frequencies
  are a lower bound.
- **HTTP clusters are status-level.** Two different `500` causes group together;
  the up-to-3 example lines per cluster show the variety — split during
  enrichment if needed.
- **No semantics.** It matches by tokens and status, not meaning. It finds the
  obvious, high-frequency gaps; a human still reads the long tail.

## Delivery Summary

- Incident count → cluster count; the top cluster and its frequency.
- Coverage split (New vs covered) when `--against` was used.
- The New work list, ranked.
- A reminder to scrub secrets and enrich `原因/修复`.

## Skill Family

- **`code-tutor`** consumes the gotcha markers this produces; keep the
  `症状/原因/修复` format identical so its parser reads them.
- **`tutorial-to-notebook`** is where enriched gotchas land as cell markers.
- **`tour-builder`** takes the UI-stumble clusters as new/clearer steps.
- **`api-to-sandbox`** benefits indirectly: recurring auth/rate-limit clusters
  often mean the sandbox's golden path or guardrails need adjusting.

## Resources

- Harvester: `scripts/harvest.py`
- Method + clustering notes: `references/harvesting-guide.md`
- Sample corpus: `templates/sample_incidents.jsonl`

<!-- last_updated: 2026-08-01 -->
<!-- maintained-by: walter.fan -->
