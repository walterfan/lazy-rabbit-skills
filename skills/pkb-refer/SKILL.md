---
name: pkb-refer
description: >-
  Use when the AI needs to consult a Project Knowledge Base before answering
  questions, implementing features, debugging, or reviewing code. Triggers on
  phrases like check the PKB, refer to project docs, read the knowledge base,
  what does the PKB say, consult project docs, look up in PKB, use PKB context,
  查阅 PKB, 参考项目文档, 查知识库, or any situation where the AI should ground
  its response in existing project documentation rather than guessing.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - documentation
  - knowledge-base
  - context
  - pkb
  - grounding
category: dev-tools
platforms:
  - claude-code
  - codex
  - cursor
visibility: public
---

# pkb-refer

Ground AI responses in the Project Knowledge Base. Read `index.md` to discover available pages, load only the pages relevant to the current task, and cite PKB sources when answering — so the AI gives project-specific answers instead of generic guesses.

The skill follows a **baseline + on-demand** strategy: always start by reading `index.md` and `00-overview.md` to build a minimal mental model, then pull in additional pages only when the task requires them. This keeps context small and accurate.

## Contract

- **scope_in**:
  - Any question, task, or review where project-specific knowledge would improve the answer
  - Feature implementation, bug fixing, code review, architecture discussion, debugging, onboarding
  - Questions like "how does X work in this project?", "where is Y configured?", "what was the decision behind Z?"

- **scope_out**:
  - Creating or initializing a PKB (use `project-knowledge-base` skill with `/PKB-init`)
  - Importing external knowledge into the PKB (use `pkb-collect`)
  - Generating new PKB pages (use `project-knowledge-base` skill with specific `/PKB-*` commands)
  - Questions that have nothing to do with the current project (general programming, math, etc.)

- **Preconditions**:
  - A PKB exists at `PKB_ROOT` with at least `index.md` and `00-overview.md`
  - The AI has read access to `PKB_ROOT`

- **Postconditions**:
  - The AI's response is grounded in PKB content where relevant
  - Every project-specific claim cites the PKB page it came from (e.g., "per `02-architecture.md`, the system uses...")
  - If the PKB does not cover the topic, the AI states that explicitly rather than guessing
  - If the PKB content appears stale or contradicts the code, the AI flags the discrepancy

## Execution

### Phase A: Discover the PKB

- Entry: the AI needs project context to answer a question or complete a task
- Steps:
  1. Locate `PKB_ROOT`. Check in order: `man/index.md`, `doc/index.md`, or the path recorded in session/project notes.
  2. Read `index.md` to get the table of contents — the list of available PKB pages and their topics.
  3. Read `00-overview.md` to build a baseline mental model of the project: purpose, users, deployment, and high-level architecture.
  4. If `index.md` or `00-overview.md` is missing, stop and tell the user: "No PKB found at the expected location. Run `/PKB-init` to create one, or tell me where the PKB lives."
- Exit: the AI knows which PKB pages exist and has a baseline understanding of the project
- On fail: report the missing PKB and suggest creating one

### Phase B: Select relevant pages

- Entry: Phase A complete, user's question or task is known
- Steps:
  1. Match the user's intent to PKB pages using the topic map from `index.md`:
     - Architecture / system design → `02-architecture.md`
     - "Where is X?" / directory structure → `04-repo-map.md`
     - API, data model, schema → `05-data-and-api.md`
     - Workflow, request flow, business logic → `06-workflows.md`
     - Build, CI, release → `08-build.md`
     - Testing, coverage → `09-testing.md`
     - Debugging, troubleshooting → `10-runbook.md`
     - Logging, metrics, alerts → `11-observability.md`
     - Past decisions, rationale → `adr/index.md` then specific ADR files
     - Setup, getting started → `01-quick-start.md`
     - Tech stack, dependencies → `03-tech-stack.md`
     - Coding standards → `07-conventions.md`
     - Doc maintenance → `12-document.md`
     - Terminology → `appendix-02-glossary.md`
  2. Read only the selected page(s). Prefer reading 1-3 pages; read more only when the question genuinely spans multiple concerns.
  3. If a selected page references specific code files, note them for later reading if the answer requires code-level detail.
  4. Parse the `<!-- PKB-metadata -->` footer to check staleness:
     - If `last_updated` is more than 60 days ago, warn: "This PKB page may be stale (last updated YYYY-MM-DD). Cross-check with the actual code."
     - If `review_status` is `pending`, note that the page has not been human-approved yet.
- Exit: relevant PKB content loaded into context
- On fail: if the needed page does not exist or is a stub (`[NEEDS INPUT]`), tell the user and suggest running the corresponding `/PKB-*` command to generate it

### Phase C: Answer with grounding

- Entry: Phase B complete, relevant PKB content in context
- Steps:
  1. Formulate the answer using PKB content as the primary source of project-specific truth.
  2. Cite the PKB page for every project-specific claim: "According to `06-workflows.md`, the auth flow starts at..."
  3. If the PKB content is insufficient for a complete answer, clearly separate what comes from the PKB versus what is the AI's general reasoning or inference.
  4. If the PKB and the actual code appear to contradict each other, flag it: "Note: `04-repo-map.md` says the entry point is `cmd/main.go`, but the current tree shows `src/main.ts`. The PKB may need updating."
  5. If the question falls entirely outside the PKB's coverage, say so: "The PKB does not cover [topic]. I'll answer based on general knowledge, but consider adding this to the PKB."
- Exit: grounded, cited answer delivered to the user
- On fail: if context is too large (too many pages loaded), summarize and point the user to the specific sections instead of quoting everything

### Phase D: Suggest PKB improvements (optional)

- Entry: Phase C complete
- Steps:
  1. If the question revealed a PKB gap (missing page, stale content, or unclear section), suggest a specific improvement:
     - "Consider running `/PKB-architecture` to update the architecture page."
     - "The glossary is missing a definition for [term]. You could add it to `appendix-02-glossary.md`."
  2. If the AI had to rely on code reading because the PKB was insufficient, note which PKB page should be enriched.
  3. Keep suggestions brief — one or two sentences, not a lecture.
- Exit: user is aware of any PKB gaps discovered during this interaction

## Page Selection Quick Reference

| User intent | Primary pages | Secondary pages |
|------------|---------------|-----------------|
| "How does X work?" | `06-workflows.md` | `02-architecture.md`, `05-data-and-api.md` |
| "Where is X?" | `04-repo-map.md` | `02-architecture.md` |
| "Why was X chosen?" | `adr/` | `02-architecture.md`, `03-tech-stack.md` |
| "How do I set up?" | `01-quick-start.md` | `03-tech-stack.md`, `08-build.md` |
| "How do I debug X?" | `10-runbook.md` | `11-observability.md`, `06-workflows.md` |
| "What tests exist?" | `09-testing.md` | `07-conventions.md` |
| "What API does X expose?" | `05-data-and-api.md` | `06-workflows.md` |
| Implement a feature | `02-architecture.md`, `06-workflows.md` | `07-conventions.md`, `09-testing.md` |
| Code review | `07-conventions.md` | `02-architecture.md`, `09-testing.md` |
| "What does [term] mean?" | `appendix-02-glossary.md` | `00-overview.md` |

## Verification

### Hard gates

| Gate | Condition | On fail |
|------|-----------|---------|
| PKB discovered | `index.md` found and readable | Stop, tell user no PKB found, suggest `/PKB-init` |
| Baseline loaded | `00-overview.md` read successfully | Warn user that context is limited, proceed with `index.md` only |
| Citations present | Every project-specific claim in the answer cites a PKB page | Add citations before delivering the answer |
| Gaps disclosed | If the PKB lacks coverage for part of the answer, that gap is stated explicitly | Add a disclaimer before delivering |

### Soft gates

| Gate | Condition | On fail |
|------|-----------|---------|
| Minimal context | No more than 5 PKB pages loaded for a single question | Warn that context is large, summarize instead of quoting |
| Staleness checked | `<!-- PKB-metadata -->` footer parsed for loaded pages | Warn if any page is older than 60 days or `review_status: pending` |
| Improvement suggested | If a gap was found, a concrete PKB improvement is suggested | Skip — this phase is optional |

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| AI gives generic answers ignoring PKB | Skill not triggered, or PKB not discovered | Check `PKB_ROOT` path; use trigger phrases like "check the PKB" |
| AI loads too many pages, hits context limits | Page selection too broad | Narrow to 1-3 pages; use the quick reference table |
| AI cites stale PKB content | Page metadata not checked | Parse `<!-- PKB-metadata -->` footer and warn when stale |
| AI silently guesses when PKB has no answer | Gap disclosure gate skipped | Enforce the "Gaps disclosed" hard gate |
| AI overwrites or edits PKB pages | Skill scope confused with `project-knowledge-base` or `pkb-collect` | This skill is read-only; redirect write requests to the appropriate skill |
| Answer contradicts actual code | PKB is outdated | Flag the contradiction, suggest a PKB refresh command |

### Boundary examples

- **PKB exists, question is covered**: read 1-2 pages, cite them, answer confidently
- **PKB exists, question is partially covered**: answer from PKB, clearly mark the inferred parts, suggest enriching the PKB
- **PKB exists but is stale**: answer from PKB with a staleness warning, cross-check with code if possible
- **PKB does not exist**: stop, tell the user, suggest `/PKB-init`
- **Question is unrelated to the project**: answer normally without PKB, do not force irrelevant PKB context
- **Very broad question** ("tell me everything about this project"): follow the 3-round learning process from `ai-guide.md` instead of dumping all pages

### Improvement triggers

- Users frequently say "that's outdated" → strengthen staleness checking, lower the warning threshold
- Users ask questions the PKB should cover but doesn't → log the gap pattern, suggest batch PKB updates
- AI loads too many pages → refine the page selection heuristics in Phase B
- Users never see PKB citations → make the citation format more visible
