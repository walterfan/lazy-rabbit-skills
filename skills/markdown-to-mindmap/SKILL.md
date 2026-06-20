---
name: markdown-to-mindmap
description: >-
  Read a Markdown file or Markdown content, generate a PlantUML mindmap script,
  and render it to a PNG image. Use when the user wants to turn Markdown notes,
  docs, outlines, or architecture writeups into a mind map, especially when
  they mention PlantUML, mindmap, Markdown-to-diagram, or want both source and
  rendered image output.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - markdown
  - plantuml
  - mindmap
  - diagram
  - image
category: dev-tools
repository: https://github.com/walterfan/lazy-rabbit-skills/tree/main/skills/markdown-to-mindmap
use_cases:
  - "Read a Markdown file and generate a PlantUML mindmap"
  - "Render Markdown notes into a PNG mind map"
  - "Turn section headings and bullet lists into diagram source"
  - "Demonstrate Promptfoo evaluation with a deterministic skill-like workflow"
platforms:
  - claude-code
  - cursor
visibility: public
---

# markdown-to-mindmap

Read Markdown, generate PlantUML mindmap source, and render it to PNG.

All `scripts/` paths below are relative to the skill directory.

## Contract

- **scope_in**: local Markdown files (`.md`, `.markdown`, `.txt`) or pasted Markdown content; PlantUML mindmap generation; PNG rendering for the generated mindmap; notes, outlines, architecture docs, and structured Markdown with headings and bullet lists
- **scope_out**: Mermaid or Graphviz generation; arbitrary diagram types beyond PlantUML mindmap; remote URL fetching; free-form semantic summarization of long prose without structure; writing images outside the requested local workspace
- **Preconditions**:
  - Python 3.9+ is available
  - For server rendering mode: `requests` is installed via `pip install -r scripts/requirements.txt`
  - For local PlantUML rendering mode: `plantuml` CLI is available on `$PATH`
  - Input Markdown exists locally if file path mode is used
- **Postconditions**:
  - Generated source is valid PlantUML mindmap text with `@startmindmap` and `@endmindmap`
  - Output PNG exists and is non-empty when render mode is requested
  - Output paths are explicit and predictable

## Trigger Scenarios

- User asks to read a Markdown file and turn it into a mind map
- User wants both PlantUML source and a rendered PNG image
- A document has clear headings and bullet lists that should become a diagram
- User wants a small, reproducible Promptfoo demo based on a skill-like workflow

## Quick Start

### 1. Generate PlantUML source only

```bash
python scripts/markdown_to_mindmap.py \
  -i examples/note.md \
  -o output/note_mindmap.puml
```

### 2. Generate source and render PNG

```bash
PLANTUML_MODE=server python scripts/render_markdown_mindmap.py \
  -i examples/note.md \
  -o output/note_mindmap.png
```

If local `plantuml` is installed, you can omit `PLANTUML_MODE=server`.

## Script Overview

### `scripts/markdown_to_mindmap.py`

Purpose:

- Parse Markdown headings and bullet lists
- Generate deterministic PlantUML mindmap source
- Act as a Promptfoo Python provider for generation evals

### `scripts/render_diagram.py`

Purpose:

- Render PlantUML, Mermaid, or Graphviz diagrams to PNG or SVG
- Reused locally so this skill stays self-contained

### `scripts/render_markdown_mindmap.py`

Purpose:

- Wrap generation + rendering into one end-to-end command
- Act as a Promptfoo Python provider for e2e evals

## Recommended Workflow

1. Read the Markdown file or pasted Markdown content.
2. Prefer the first H1 heading as the root title.
3. Map headings to mindmap branches.
4. Map nested bullet lists to deeper child nodes.
5. Generate PlantUML source first.
6. Render PNG only after source generation succeeds.
7. Return both file paths when render mode is used.

## Execution

### Phase 1: Gather input and validate

- Entry: user provides a local Markdown path or pasted Markdown content within `scope_in`
- Steps:
  1. Confirm the input is Markdown text or a supported local file
  2. Check prerequisites for generation and, if requested, rendering
  3. Resolve explicit output paths before generating artifacts
- Exit: validated input, chosen render mode, and deterministic output paths
- On fail: stop immediately with a clear setup or input error instead of guessing

### Phase 2: Generate PlantUML mindmap

- Entry: Phase 1 completed
- Steps:
  1. Parse headings and bullet structure
  2. Choose the root title from the first H1 or a safe fallback
  3. Emit PlantUML wrapped by `@startmindmap` and `@endmindmap`
- Exit: `.puml` output exists and reflects the Markdown hierarchy
- On fail: return the parse or generation error and do not attempt rendering

### Phase 3: Render PNG when requested

- Entry: Phase 2 completed and render mode requested
- Steps:
  1. Use local `plantuml` when available, otherwise server mode when configured
  2. Render the generated source to PNG
  3. Return both source and image paths
- Exit: PNG exists and is non-empty
- On fail: fall back to returning the generated `.puml` path with actionable render guidance

## Examples

### Example 1: Convert Markdown note to PlantUML

**Input Markdown**

```markdown
# Building a Promptfoo Demo

## Goals
- Explain generation evals
- Show end-to-end rendering

## Workflow
- Write the skill
  - Add parser script
  - Add render wrapper
```

**Command**

```bash
python scripts/markdown_to_mindmap.py -i note.md -o output/demo.puml
```

### Example 2: Render image directly

**Command**

```bash
PLANTUML_MODE=server python scripts/render_markdown_mindmap.py \
  -i note.md \
  -o output/demo.png
```

## Promptfoo Demo

This skill includes two Promptfoo demos:

- `evals/promptfooconfig.generation.yaml`
  - validates Markdown -> PlantUML generation quality
- `evals/promptfooconfig.e2e.yaml`
  - validates Markdown -> PlantUML -> PNG end-to-end behavior

Run them from the skill directory:

```bash
npx promptfoo@latest eval -c evals/promptfooconfig.generation.yaml
PLANTUML_MODE=server npx promptfoo@latest eval -c evals/promptfooconfig.e2e.yaml
```

If your default npm registry is slow or points to an internal mirror, use:

```bash
npm_config_registry=https://registry.npmjs.org npx -y promptfoo@0.121.5 eval -c evals/promptfooconfig.generation.yaml
npm_config_registry=https://registry.npmjs.org PLANTUML_MODE=server npx -y promptfoo@0.121.5 eval -c evals/promptfooconfig.e2e.yaml
```

## Failure Handling

- Empty Markdown input -> fail fast with a clear error
- Missing render dependency -> return actionable setup guidance
- Unsupported file extension -> reject instead of guessing
- No headings found -> fall back to document stem or provided title

## Verification

### Hard gates

- Source validity: generated output contains `@startmindmap` and `@endmindmap`; on fail, regenerate once or stop with an explicit error
- Structure fidelity: headings and nested bullet lists map to a stable hierarchy; on fail, return the `.puml` with the mismatch called out
- Render result: when PNG rendering is requested, the output image exists and is non-empty; on fail, return source only with render remediation

### Soft gates

- Predictable paths: output paths are explicit and stable; on fail, warn and restate the actual paths used
- Reproducibility: repeated runs on the same Markdown should produce materially equivalent source; on fail, note nondeterministic input or tooling

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Skill does not trigger | Request does not mention Markdown-to-mindmap intent clearly | Expand trigger wording in `description` with more concrete user phrases |
| Generated tree is too flat | Source Markdown lacks headings or nested bullets | Ask for better-structured Markdown or accept a flatter map |
| PNG render fails | `plantuml` or server rendering prerequisites are missing | Return `.puml` only and provide the setup command or mode switch |

### Improvement triggers

- Add a new example when a real Markdown pattern is parsed incorrectly
- Tighten the contract if users repeatedly request non-PlantUML diagram types
- Extend verification gates if a rendering regression escapes the current checks

## Additional Resources

- Detailed usage and Promptfoo notes: [references/detailed-guide.md](references/detailed-guide.md)
