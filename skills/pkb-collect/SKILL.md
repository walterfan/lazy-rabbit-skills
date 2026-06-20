---
name: pkb-collect
description: >-
  Use when the user wants to import, collect, or ingest external knowledge into
  an existing Project Knowledge Base (PKB). Triggers on phrases like import docs,
  collect knowledge, ingest into PKB, add to PKB, import from Confluence, import
  from a doc platform, import meeting notes, import design doc, 导入知识, 收集文档,
  导入到 PKB, or any request to bring outside material into PKB pages.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - documentation
  - knowledge-base
  - import
  - pkb
category: dev-tools
platforms:
  - macOS
  - Linux
  - Web
visibility: public
---

# pkb-collect

Import external knowledge into an existing Project Knowledge Base. Accepts documents, web pages, design specs, API definitions, meeting notes, README files, and other structured or semi-structured sources, then maps and merges the extracted facts into the appropriate PKB numbered pages.

The goal is not to copy-paste — it is to **extract verified facts** from outside sources and place them where the PKB's standard page set expects them, preserving the PKB's structure, numbering, and metadata conventions.

## Contract

- **scope_in**:
  - Confluence pages, wiki pages, and other doc-platform articles (via URL or pasted content)
  - Web pages, PDFs, and Markdown files (via URL, file path, or pasted content)
  - Design documents, technical specs, and RFCs
  - API definitions (OpenAPI/Swagger YAML/JSON, Protobuf `.proto`, GraphQL schemas)
  - Meeting notes and summaries (text or AI meeting-assistant output)
  - README files and docs from other repositories
  - Jira ticket descriptions when they contain design context worth preserving

- **scope_out**:
  - Creating a PKB from scratch (use `project-knowledge-base` skill with `/PKB-init` instead)
  - Binary-only content (images, videos) unless accompanied by text descriptions
  - Real-time chat streams — only finalized summaries or transcripts
  - Generating new analysis or opinions — this skill imports existing knowledge, it does not invent

- **Preconditions**:
  - A PKB already exists at `PKB_ROOT` (created by `/PKB-init` or equivalent)
  - `index.md` exists and lists the standard numbered page set
  - The user has provided or pointed to at least one external knowledge source

- **Postconditions**:
  - Extracted facts are placed into the correct PKB page(s) following the standard numbering
  - No existing human-authored content is overwritten without explicit confirmation
  - New content is marked with `<!-- imported-from: <source-url-or-name> -->` provenance tags
  - Each modified PKB page has its `<!-- PKB-metadata -->` footer updated with today's date and current commit
  - A summary report lists what was imported, where it was placed, and what was skipped or flagged as ambiguous

## Execution

### Phase A: Identify and fetch sources

- Entry: user provides one or more knowledge sources (URL, file path, pasted text, or a directive like "import from Confluence page X")
- Steps:
  1. Classify each source by type (web page, Markdown, PDF, API spec, meeting note, etc.)
  2. Fetch or read the source content. For URLs, use available fetch tools; for files, read from disk; for pasted text, accept inline.
  3. If a source is inaccessible (auth required, 404, binary), report the failure and continue with remaining sources.
  4. Extract the raw text content, stripping navigation chrome, footers, and formatting artifacts.
- Exit: raw text available for each successfully fetched source
- On fail: list inaccessible sources, suggest alternatives (e.g., "paste the content directly"), continue with what is available

### Phase B: Extract and classify facts

- Entry: Phase A complete, raw text available
- Steps:
  1. Parse the content to identify discrete facts: definitions, architecture decisions, API endpoints, configuration values, workflow steps, dependency lists, operational procedures, etc.
  2. For each fact, determine the target PKB page by matching to the standard page set:
     - Product scope, users, deployment → `00-overview.md`
     - Setup instructions, prerequisites → `01-quick-start.md`
     - System decomposition, component interactions → `02-architecture.md`
     - Languages, frameworks, versions → `03-tech-stack.md`
     - Directory structure, entry points → `04-repo-map.md`
     - Data models, schemas, APIs, events → `05-data-and-api.md`
     - Business workflows, request flows → `06-workflows.md`
     - Coding standards, naming, error handling → `07-conventions.md`
     - Build, CI, release pipeline → `08-build.md`
     - Test strategy, coverage, cases → `09-testing.md`
     - Debugging, troubleshooting → `10-runbook.md`
     - Logging, metrics, tracing, alerts → `11-observability.md`
     - Doc maintenance process → `12-document.md`
     - Architectural decisions → `adr/`
     - Glossary terms → `appendix-02-glossary.md`
  3. If a fact does not clearly map to any page, flag it as `[UNPLACED]` and ask the user.
  4. If the source contains opinions, speculation, or unverified claims, mark them with `[NEEDS VERIFICATION]` rather than importing them as fact.
  5. Produce a placement plan: a table showing each extracted fact, its target page, and whether it is new content or an update to an existing section.
- Exit: user-reviewed placement plan
- On fail: if the source is too vague to extract structured facts, report it and suggest the user summarize the key points manually

### Phase C: Merge into PKB pages

- Entry: Phase B complete, placement plan approved by user
- Steps:
  1. For each target PKB page, read the current content.
  2. Find the correct section within the page (match by heading or topic).
  3. Merge the new facts:
     - **Append** to existing sections when the new content adds detail.
     - **Update** existing lines only when the source is clearly more current (newer date, higher authority). Ask the user when uncertain.
     - **Never silently delete** existing content.
  4. Add a provenance tag after each imported block: `<!-- imported-from: <source> on YYYY-MM-DD -->`.
  5. Preserve all existing `[NEEDS INPUT]` markers unless the imported content resolves them.
  6. Update the `<!-- PKB-metadata -->` footer: set `last_updated` to today, `commit` to current HEAD, `updated_by` to `human+ai`, and `review_status` to `pending`.
- Exit: modified PKB pages written to disk
- On fail: if a merge conflict arises (imported fact contradicts existing PKB content), stop on that fact, show both versions, and ask the user to resolve

### Phase D: Report

- Entry: Phase C complete
- Steps:
  1. Print a summary table:

```
| Source | Target Page | Facts Imported | Skipped | Needs Review |
|--------|-------------|---------------|---------|--------------|
| ...    | ...         | ...           | ...     | ...          |
```

  2. List any `[UNPLACED]` or `[NEEDS VERIFICATION]` items that still need user attention.
  3. Remind the user to review modified pages and set `review_status: approved` when satisfied.
- Exit: user has a clear picture of what changed and what needs follow-up

## Verification

### Hard gates

| Gate | Condition | On fail |
|------|-----------|---------|
| PKB exists | `PKB_ROOT/index.md` is present | Stop and suggest running `/PKB-init` first |
| At least one source fetched | Phase A produced raw text from at least one source | Stop and ask user to provide accessible sources |
| No silent overwrites | Existing human-authored content preserved or user explicitly approved changes | Revert the merge for that section, show diff, ask user |
| Provenance tagged | Every imported block has an `<!-- imported-from: ... -->` tag | Add missing tags before finishing |
| Metadata updated | Every modified page has a current `<!-- PKB-metadata -->` footer | Stamp the footer before finishing |

### Soft gates

| Gate | Condition | On fail |
|------|-----------|---------|
| Placement coverage | >80% of extracted facts have a clear target page | Warn user about `[UNPLACED]` items |
| Freshness | Imported content is not older than existing PKB content for the same topic | Warn user, suggest keeping the newer version |
| Length balance | No single page grows by more than 50% from one import | Warn user, suggest splitting large imports across multiple updates |

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Skill not triggered | Description missing user's phrasing | Add trigger terms: collect, import, ingest, bring into PKB |
| Source fetch fails | Auth required or URL inaccessible | Ask user to paste content directly or provide credentials |
| Facts placed in wrong page | Classification heuristic too coarse | Show placement plan for user review before merging |
| Existing content silently lost | Merge logic replaced instead of appending | Enforce append-by-default, require explicit user approval for updates |
| Import is shallow / generic | Source was too high-level, LLM padded with filler | Mark sections as `[NEEDS INPUT]` instead of inventing detail |
| Duplicate content after import | Same fact already existed in the PKB page | Deduplicate during Phase C by comparing key phrases before appending |

### Boundary examples

- **Single URL**: import one Confluence page → extract facts, place into 1-3 PKB pages
- **Batch import**: user provides 5 URLs → process all, produce one consolidated placement plan
- **API spec file**: import an OpenAPI YAML → place endpoints into `05-data-and-api.md`
- **Meeting notes**: import an AI meeting-assistant summary → extract action items and decisions into `adr/` or relevant workflow pages
- **Pasted text**: user pastes a design doc section → extract and place without needing a URL
- **Conflicting info**: imported fact contradicts existing PKB content → stop, show both, ask user

### Improvement triggers

- Users frequently reject the placement plan → improve page-matching heuristics
- Users keep re-importing the same source → add deduplication check against provenance tags
- Large imports make pages unwieldy → suggest splitting into sub-sections or appendix pages
