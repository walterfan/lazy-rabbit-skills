---
name: feature-design-doc
description: >-
  Generate feature-level technical design specs based on an Engineer
  Technical Design Spec template, simplified for practical drafting. Use when
  the user asks for a feature design doc, technical design spec, function
  design, feature spec, TDS, or engineer design spec. Make sure to use this
  when the user has a new feature idea, Jira scope, or implementation plan and
  needs a structured English or Chinese design document with security,
  privacy, accessibility, observability, and AI/ML coverage.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - design-doc
  - tds
  - architecture
  - compliance
category: engineering
platforms:
  - claude-code
  - cursor
visibility: public
---

# feature-design-doc

Generate feature-level technical design specs using the official template, simplified into a practical drafting workflow that still preserves the required compliance prompts.

## Contract

- `scope_in`: feature or function level design requests, Jira-backed implementation plans, English or Chinese TDS drafting, and structured expansion of partial notes into a full design doc.
- `scope_out`: product requirement docs, project plans, test plans, legal approvals, and service-wide architecture documents with no concrete feature scope.
- `preconditions`: the user provides at least a feature name or Jira ID plus a short problem statement, and the referenced template files are present.
- `postconditions`: the output contains a complete design-doc structure, includes an architecture diagram, marks unknowns as `**[TBD]**`, and pulls in security, privacy, accessibility, and AI/ML sections only when applicable.

## Execution

### Phase 1: Gather context
- Entry: the request matches `scope_in`.
- Steps:
  1. Collect feature name, Jira ID, purpose, affected platforms, and whether the work touches UI, personal data, or AI/ML.
  2. If the input is brief, expand it into a draft-ready outline and record missing facts as `**[TBD]**`.
- Exit: enough context exists to choose a template and fill the main sections.
- On fail: stop and ask for the missing minimum context instead of guessing scope.

### Phase 2: Choose sources
- Entry: Phase 1 complete.
- Steps:
  1. Chinese request -> use [references/template-cn.md](references/template-cn.md).
  2. English request -> use [references/template.md](references/template.md).
  3. If security, privacy, or accessibility applies, also read [references/security-privacy-checklist.md](references/security-privacy-checklist.md).
- Exit: the correct source template and checklist inputs are identified.
- On fail: fall back to the English template and explicitly note the language assumption.

### Phase 3: Draft the document
- Entry: Phase 2 complete.
- Steps:
  1. Fill the selected template section by section.
  2. Always include an architecture diagram in Section 2 using PlantUML or ASCII.
  3. For each API, include method, path, request and response examples, and error codes.
  4. Include Security, Data Governance, Accessibility, and AI/ML sections only when the feature context says they apply.
- Exit: a complete draft exists with unknowns marked and no required section silently skipped.
- On fail: produce a partial draft with clear `**[TBD]**` markers and a short gap list.

## Verification

### Hard gates
- Template check: the draft contains introduction, architecture, requirements, APIs or interfaces, observability, and review/sign-off sections.
- Compliance check: applicable security, privacy, accessibility, and AI/ML sections are either filled or intentionally skipped based on feature context.
- Diagram check: Section 2 includes an architecture diagram.
- Unknowns check: unresolved facts are marked as `**[TBD]**` with the missing owner or source.

### Soft gates
- Language check: the output language matches the user's request.
- STRIDE check: if the security section is included, at least one relevant threat is documented.
- Brevity check: skipped sections are omitted instead of padded with "Not Applicable" boilerplate.

## Feedback

### Failure modes
- Missing feature context leads to vague requirements or incorrect scope.
- Template misuse can overfill sections that should be skipped.
- Compliance gaps happen when privacy, accessibility, or AI/ML applicability is not checked explicitly.

### Boundary examples
- In scope: "Write a TDS for a new backend API with UI changes and privacy impact."
- Out of scope: "Write a PRD for next quarter's roadmap."

### Improvement triggers
- Update this skill when the template structure changes, the checklist references move, or reviewers repeatedly request a missing section pattern.
