#!/usr/bin/env python3
"""gen_tour.py — turn a plain-markdown tour script into a runnable UI tour.

The UI-page counterpart to api-to-sandbox: instead of a code sandbox, it
produces a step-by-step interactive guide that overlays a real web page
(console / backend UI), plus the *contract* the page must satisfy.

Design opinions baked in:
  1. Steps anchor to STABLE `data-tour-id` attributes, never to brittle CSS
     selectors (`.btn-primary`, `div > span:nth-child(3)`). A tour that breaks
     every time the CSS changes is worse than no tour. The generator warns on
     raw selectors and emits an anchor contract for the frontend.
  2. Tour text is HTML-escaped at generation time, so author content can never
     turn into DOM injection when the tour library renders it as HTML.
  3. Destructive steps (revoke / delete / rotate) are flagged, and any
     secret-looking text in a step body is caught before it ships.

Outputs (into --out):
  tour.js       driver.js ES module: `steps` + `startTour()`
  tour.json     framework-agnostic step list (for tests / other runtimes)
  anchors.md    the contract: which `data-tour-id` each element needs

Stdlib only. Never fetches anything, never runs a browser.

Input format (markdown), one step per `##` heading:

    # Tour: Console onboarding

    ## Open the API Keys page
    target: nav-api-keys
    side: right
    Click here to manage your credentials.

    ## Revoke a leaked key
    target: btn-revoke
    side: left
    action: click
    destructive: true
    Revoking is instant and irreversible. Confirm the key id first.

Usage:
    python gen_tour.py TOUR.md --out ./tour
    python gen_tour.py TOUR.md --out ./tour --name "Onboarding"
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys

# --- what a stable anchor id looks like: a plain token, not a CSS selector ---
_ID_RE = re.compile(r"^[A-Za-z][\w-]*$")
_SELECTOR_HINT_RE = re.compile(r"[.#>\[\]:\s]")

# fields we understand on a step; everything else is body text
_KNOWN_FIELDS = {"target", "side", "placement", "action", "destructive"}
_VALID_SIDES = {"top", "right", "bottom", "left", "over"}

# cheap secret sniffers so a credential never ends up narrated in a tooltip
_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}"
    r"|-----BEGIN|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    r"|(?i:password|secret|api[_-]?key|token)\s*[:=]\s*\S{6,})"
)
_DESTRUCTIVE_WORDS = ("revoke", "delete", "remove", "rotate", "reset",
                      "destroy", "wipe", "disable", "terminate")


class TourError(Exception):
    pass


def parse_tour(markdown):
    """Parse the markdown tour into (name, steps, warnings).

    A step is a dict: title, target, side, action, destructive(bool), body.
    Parsing is forgiving on content but strict on the anchor contract.
    """
    name = None
    steps = []
    warnings = []
    cur = None
    body_lines = []

    def flush():
        if cur is None:
            return
        cur["body"] = "\n".join(body_lines).strip()
        steps.append(cur)

    for raw in markdown.splitlines():
        line = raw.rstrip("\n")
        stripped = line.strip()

        # top-level title: "# Tour: X" or the first "# X"
        if stripped.startswith("# ") and not stripped.startswith("## "):
            if name is None:
                heading = stripped[2:].strip()
                name = re.sub(r"^tour\s*:\s*", "", heading, flags=re.I).strip()
            continue

        # new step
        if stripped.startswith("## "):
            flush()
            title = stripped[3:].strip()
            # allow "## step: Foo" sugar
            title = re.sub(r"^step\s*:\s*", "", title, flags=re.I).strip()
            cur = {
                "title": title,
                "target": None,
                "side": "bottom",
                "action": None,
                "destructive": False,
                "body": "",
            }
            body_lines = []
            continue

        if cur is None:
            continue  # preamble before the first step

        # field line?  key: value  (only for keys we know)
        m = re.match(r"^([A-Za-z_]+)\s*:\s*(.*)$", stripped)
        if m and m.group(1).lower() in _KNOWN_FIELDS:
            key = m.group(1).lower()
            val = m.group(2).strip()
            if key in ("side", "placement"):
                if val not in _VALID_SIDES:
                    warnings.append(
                        f"step '{cur['title']}': side '{val}' is not one of "
                        f"{sorted(_VALID_SIDES)}; defaulting to 'bottom'."
                    )
                    val = "bottom"
                cur["side"] = val
            elif key == "destructive":
                cur["destructive"] = val.lower() in ("true", "yes", "1", "y")
            else:
                cur[key] = val
            continue

        body_lines.append(line)

    flush()

    if name is None:
        name = "Guided tour"
    if not steps:
        raise TourError("no steps found — each step is a '## ' heading.")
    return name, steps, warnings


def validate(steps):
    """Return (errors, warnings). Errors block delivery; warnings do not."""
    errors = []
    warnings = []
    seen = {}

    for i, s in enumerate(steps, 1):
        tag = f"step {i} ('{s['title']}')"
        target = s["target"]

        if not target:
            errors.append(f"{tag}: missing `target:` — every step needs an anchor.")
        else:
            if _SELECTOR_HINT_RE.search(target) or not _ID_RE.match(target):
                warnings.append(
                    f"{tag}: target '{target}' looks like a raw CSS selector. "
                    f"Prefer a stable id used as data-tour-id (e.g. 'nav-api-keys'); "
                    f"CSS selectors break when styling changes."
                )
            if target in seen:
                warnings.append(
                    f"{tag}: target '{target}' already used in step {seen[target]} — "
                    f"anchors are usually unique per step."
                )
            else:
                seen[target] = i

        if not s["body"]:
            warnings.append(f"{tag}: empty body — the tooltip will have no guidance text.")

        blob = f"{s['title']}\n{s['body']}"
        if _SECRET_RE.search(blob):
            errors.append(
                f"{tag}: the step text looks like it contains a secret/credential. "
                f"Tours are shown in the browser — never narrate real keys."
            )

        # auto-flag likely-destructive steps the author didn't mark
        low = blob.lower()
        if not s["destructive"] and any(w in low for w in _DESTRUCTIVE_WORDS):
            warnings.append(
                f"{tag}: mentions a destructive action but isn't marked "
                f"`destructive: true` — consider adding a confirm before this step."
            )
    return errors, warnings


def _selector(target):
    return f'[data-tour-id="{target}"]'


def to_step_objects(steps):
    """Framework-agnostic, HTML-escaped step objects (the safe core)."""
    out = []
    for s in steps:
        out.append({
            "target": s["target"],
            "selector": _selector(s["target"]) if s["target"] else None,
            "title": html.escape(s["title"]),
            "description": html.escape(s["body"]),
            "side": s["side"],
            "action": s["action"],
            "destructive": bool(s["destructive"]),
        })
    return out


def render_driver_js(name, objs):
    """driver.js v1 ES module. Content is pre-escaped in `objs`."""
    driver_steps = []
    for o in objs:
        popover = {"title": o["title"], "description": o["description"], "side": o["side"]}
        driver_steps.append({"element": o["selector"], "popover": popover})
    steps_json = json.dumps(driver_steps, indent=2, ensure_ascii=False)
    safe_name = json.dumps(name, ensure_ascii=False)
    return f'''// Auto-generated by tour-builder — do not hand-edit; regenerate from the .md.
// Tour: {name}
// Requires driver.js v1:  npm i driver.js
// Anchors this tour needs on the page: see anchors.md
//
// Step text is HTML-escaped at generation time, so author content cannot
// inject markup when driver.js renders the popover description as HTML.
import {{ driver }} from "driver.js";
import "driver.js/dist/driver.css";

export const tourName = {safe_name};

export const steps = {steps_json};

export function startTour(overrides = {{}}) {{
  const d = driver({{
    showProgress: true,
    allowClose: true,
    nextBtnText: "下一步",
    prevBtnText: "上一步",
    doneBtnText: "完成",
    ...overrides,
    steps,
  }});
  d.drive();
  return d;
}}
'''


def render_anchors_md(name, objs):
    lines = [
        f"# Anchor contract — {name}",
        "",
        "The tour targets these elements by `data-tour-id`. Add each attribute to",
        "the matching element in the page. Do **not** switch the tour to CSS/XPath",
        "selectors — `data-tour-id` is the stable contract that survives restyles.",
        "",
        "```html",
        '<button data-tour-id="btn-create-key">Create key</button>',
        "```",
        "",
        "| # | data-tour-id | Step | Action | Destructive |",
        "|---|---|---|---|---|",
    ]
    for i, o in enumerate(objs, 1):
        tid = o["target"] or "⚠️ MISSING"
        action = o["action"] or "—"
        dz = "⚠️ yes" if o["destructive"] else "no"
        lines.append(f"| {i} | `{tid}` | {o['title']} | {action} | {dz} |")
    lines.append("")
    lines.append("> Tip: keep these ids in a shared list so frontend and tour stay in sync.")
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate a UI tour from a markdown script.")
    ap.add_argument("input", help="tour markdown file")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--name", help="override the tour name")
    args = ap.parse_args(argv)

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            md = f.read()
    except OSError as e:
        print(f"error: cannot read input: {e}", file=sys.stderr)
        return 2

    try:
        name, steps, parse_warnings = parse_tour(md)
    except TourError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.name:
        name = args.name

    errors, warnings = validate(steps)
    warnings = parse_warnings + warnings

    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print("refusing to generate: fix the errors above.", file=sys.stderr)
        return 1

    objs = to_step_objects(steps)
    os.makedirs(args.out, exist_ok=True)

    out_js = os.path.join(args.out, "tour.js")
    out_json = os.path.join(args.out, "tour.json")
    out_anchors = os.path.join(args.out, "anchors.md")

    with open(out_js, "w", encoding="utf-8") as f:
        f.write(render_driver_js(name, objs))
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"name": name, "steps": objs}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(out_anchors, "w", encoding="utf-8") as f:
        f.write(render_anchors_md(name, objs))

    destructive = [o["target"] for o in objs if o["destructive"]]
    print(f"ok: '{name}' — {len(objs)} steps")
    print(f"  wrote {out_js}")
    print(f"  wrote {out_json}")
    print(f"  wrote {out_anchors}")
    print(f"  anchors: {', '.join(o['target'] for o in objs if o['target'])}")
    if destructive:
        print(f"  destructive steps (add a confirm): {', '.join(destructive)}")
    if warnings:
        print(f"  {len(warnings)} warning(s) — see above")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
