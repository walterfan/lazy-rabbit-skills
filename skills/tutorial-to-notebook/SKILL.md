---
name: tutorial-to-notebook
description: >-
  Use when asked to turn a static API/SDK tutorial (Markdown with code
  examples) into an executable, "read-and-run" notebook where explanation and
  runnable code sit together, users run each step in place, tweak parameters,
  and hit the real gotchas. Handles Pelican/Jekyll/plain Markdown, splits prose
  from code, and enriches the notebook with a setup cell, expected outputs,
  editable-parameter markers, gotcha markers, and verification cells. The first
  of a "living tutorial" skill family (sandbox, tour-builder, code-tutor).
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - tutorial
  - notebook
  - jupyter
  - developer-experience
  - api-docs
category: dev-tools
use_cases:
  - "Convert a Getting Started API tutorial into a runnable .ipynb"
  - "Turn SDK docs + example code into a read-and-run notebook"
  - "Rebuild a static integration guide as an executable golden path"
  - "Prepare a notebook for a sandbox / JupyterLite / Colab environment"
platforms:
  - claude-code
  - jupyter
  - colab
  - jupyterlite
visibility: public
---

# tutorial-to-notebook

Turn a static tutorial into a **living tutorial**: explanation and runnable code
in one document, where the reader runs each step, sees the result immediately,
tweaks a parameter and re-runs, and meets the real-world gotchas with guidance
right next to them.

A static tutorial makes the reader build a bridge between "reading" and "doing"
themselves — and many fall off that bridge. This skill removes the bridge by
welding the two together in a notebook.

> The goal is **not** a prettier dump of the same prose. It is: *a stranger opens
> the notebook, and within a few clicks runs a real call successfully — and when
> they slip, the notebook already anticipated it.*

## Two-Phase Method

**Phase 1 — Mechanical split (deterministic script).** Run the converter to split
prose into Markdown cells and runnable code into code cells. This is boring and
reliable; do not do it by hand.

**Phase 2 — Enrichment (the real value).** A raw split is not yet a living
tutorial. You add the setup cell, annotate expected outputs, mark editable
params, insert gotcha markers and verification cells, and prune to the golden
path. This is where the skill earns its keep — follow
`references/notebook-authoring-guide.md`.

## Ask First (only when it changes the output)

Ask at most one or two of these when the answer is not already given:

- **Language/runtime** of the code cells (Python? a specific SDK?). Default:
  Python.
- **Target environment**: a backend sandbox with a real SDK, or a pure-browser
  runtime (JupyterLite/Colab)? This decides whether network calls are allowed and
  how auth is injected.
- **The one golden path** to teach if the tutorial sprawls (e.g. "auth → first
  call → one integration"). Keep it to 3–7 steps.

If the tutorial already names the language and a single clear flow, infer it and
proceed.

## Workflow

### 1. Read the source, pick the golden path

Read the tutorial. Identify the single highest-value flow a newcomer must get
working (usually: authenticate → first successful call → one realistic
integration). Everything off that path is a candidate to cut or move to the end.
A living tutorial that nails one path beats a complete one nobody finishes.

### 2. Mechanical split

From the skill root:

```bash
python scripts/md_to_notebook.py <tutorial.md> -o <tutorial.ipynb>
# multiple runnable languages:
python scripts/md_to_notebook.py <tutorial.md> --lang python,bash -o out.ipynb
```

The script:

- turns runnable fenced blocks (```python by default) into **code cells**;
- leaves illustrative blocks (```console, ```json, ```text, output samples)
  inside **Markdown cells** — they are results to read, not code to run;
- strips a leading Pelican/YAML metadata block unless `--keep-frontmatter`;
- never executes or fetches anything.

### 3. Enrich into a living tutorial

Apply `references/notebook-authoring-guide.md`. The non-negotiable moves:

1. **Insert a setup cell first** — imports + config + auth. Auth uses an env var
   or OAuth2-injected token. **Never hardcode a real key or secret**; use
   `os.environ[...]` with a comment that the sandbox/OAuth injects it.
2. **Make each code cell one runnable step**, in order, with state flowing
   forward (the token from step 1 is used in step 2). No cell should depend on
   something the reader has not run yet.
3. **Annotate expected output** in a trailing comment (`# → 'job_7c3e1a'`) or a
   short Markdown line, so the reader knows what success looks like.
4. **Mark editable parameters** the reader should tweak (`target="en"  # 改成
   ja/fr 再跑一次`). Learning happens by fiddling.
5. **Insert a gotcha marker** at each place the reader predictably slips —
   async/polling, auth ordering, pagination, rate limits. State the symptom
   ("returns processing / empty, no error") so a downstream `code-tutor` skill
   (or the reader's AI helper) can catch it. See the family note below.
6. **Add a verification cell** at the end of the golden path (an assert or a
   printed check) that proves the whole chain worked.
7. **Prune**: move edge cases and reference material below a `## 进阶 / Beyond
   the golden path` divider so the main flow stays short.

### 4. Validate

Run the checks in Verification. Confirm the notebook is valid JSON, opens, and —
if a runtime is available and the user approves — the golden path actually runs
top-to-bottom without manual fixes.

## Cell-Ordering Rules

- Setup cell is always first and self-contained.
- Cells run **top to bottom with no gaps**: never reference a variable a prior
  cell did not define.
- Prefer many small cells over one giant cell — each teachable step is its own
  run button.
- Keep a cell's output small and legible; truncate large responses in the code
  itself.
- Put every secret behind `os.environ` / OAuth injection, never inline.

## Security (hard rules)

- No hardcoded API keys, tokens, passwords, or private URLs in any cell.
- Auth = env var or OAuth2-injected short-lived token, with a comment saying so.
- If the source tutorial contains a real-looking secret, replace it with a
  placeholder and note it in the delivery summary.
- The converter neither executes nor downloads anything; keep it that way.

## Verification

Block delivery until these pass:

- Output is valid nbformat v4 JSON and opens without error
  (`python -c "import json,sys; json.load(open(sys.argv[1]))" out.ipynb`).
- At least one code cell exists (else the `--lang` was wrong for this tutorial).
- A setup/auth cell is present and first.
- No hardcoded secret remains in any cell.
- Cells run top-to-bottom with no forward references (state flows in order).
- A final verification cell proves the golden path.
- If a runtime was available and approved, the golden path ran end-to-end.

Warn, but still deliver:

- No runtime available to actually execute the notebook (say so; it is unproven).
- The tutorial had no clear single golden path and you had to choose one.
- Illustrative blocks were left in Markdown by design (not a bug).

## Delivery Summary

Return a short summary:

- Notebook path and cell counts (markdown / code).
- The golden path chosen (the ordered steps).
- Gotcha markers inserted and where.
- Any secrets replaced with placeholders.
- Whether the notebook was actually executed, or only structurally validated.

## Skill Family

This is step 1 of a "living tutorial" toolkit. It pairs naturally with:

- **`api-to-sandbox`** — generate the runtime (deps, OAuth2, container guardrails:
  timeout, resource caps, network allowlist) the notebook runs inside.
- **`tour-builder`** — the same idea for UI/console pages: interactive product
  tours instead of runnable cells.
- **`code-tutor`** — the runtime AI helper that reads the reader's current cell +
  real error + tutorial context and explains/fixes. The gotcha markers this skill
  inserts are what `code-tutor` keys off.

Keep the interface between them simple: this skill's gotcha markers and expected
outputs are the shared contract.

## Resources

- Converter: `scripts/md_to_notebook.py`
- Authoring guide (Phase 2): `references/notebook-authoring-guide.md`
- Example input: `templates/sample_tutorial.md`

<!-- last_updated: 2026-07-31 -->
<!-- maintained-by: walter.fan -->
