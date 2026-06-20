# Markdown Mindmap Render — Detailed Guide

## What this skill does

This skill turns Markdown structure into a PlantUML mindmap and can render the mindmap to PNG.

It is intentionally narrow:

- It focuses on headings and bullet lists.
- It prefers deterministic output over clever summarization.
- It doubles as a local Promptfoo example.

## Supported input

- `.md`
- `.markdown`
- `.txt`
- pasted Markdown content via stdin or Promptfoo prompt variables

## Markdown mapping rules

### Root node

- Use the first H1 heading as the root if present.
- Otherwise use the fallback title from CLI or file stem.

### Section nodes

- H2, H3, and deeper headings become child branches.
- Repeated identical adjacent nodes are deduplicated.

### List nodes

- Bullet lists and numbered lists become deeper child nodes.
- Indentation controls nesting depth.

### Ignored content

- fenced code blocks
- blank lines
- most free-form paragraph text

## Manual commands

### Generate `.puml`

```bash
python scripts/markdown_to_mindmap.py \
  -i evals/fixtures/sample_note.md \
  -o output/sample_note.puml
```

### Render `.png`

```bash
PLANTUML_MODE=server python scripts/render_markdown_mindmap.py \
  -i evals/fixtures/sample_note.md \
  -o output/sample_note.png
```

If you have the `plantuml` CLI installed locally, you can omit `PLANTUML_MODE=server`.

## Promptfoo layout

### `evals/promptfooconfig.generation.yaml`

Purpose:

- validate Markdown -> PlantUML generation

Checks include:

- `@startmindmap`
- expected root title
- expected child nodes
- one golden deterministic fixture

### `evals/promptfooconfig.e2e.yaml`

Purpose:

- validate Markdown -> PlantUML -> PNG

Checks include:

- JSON output exists
- `.puml` file exists
- `.png` file exists
- rendered PNG size is non-zero

## Running Promptfoo

From the skill directory:

```bash
npx promptfoo@latest eval -c evals/promptfooconfig.generation.yaml
PLANTUML_MODE=server npx promptfoo@latest eval -c evals/promptfooconfig.e2e.yaml
```

If your environment routes npm through a slow private registry, force the public registry for the demo:

```bash
npm_config_registry=https://registry.npmjs.org npx -y promptfoo@0.121.5 eval -c evals/promptfooconfig.generation.yaml
npm_config_registry=https://registry.npmjs.org PLANTUML_MODE=server npx -y promptfoo@0.121.5 eval -c evals/promptfooconfig.e2e.yaml
```

## Why this Promptfoo demo is useful

This example shows two useful Promptfoo patterns:

1. **Generation eval**
   Check whether structured output is right.

2. **End-to-end eval**
   Check whether a workflow produces a real artifact, not just a plausible answer.

That second point matters for AI skills. A model can claim it generated a diagram. The file on disk is a more honest witness.

## Troubleshooting

### `requests` missing

```bash
pip install -r scripts/requirements.txt
```

### `plantuml` local binary missing

Use server mode:

```bash
export PLANTUML_MODE=server
```

### PNG file not produced

Check:

- the generated `.puml` file is valid
- PlantUML server is reachable
- output path is writable

### Promptfoo provider path errors

Run Promptfoo from the skill directory so relative `file://` paths resolve correctly.
