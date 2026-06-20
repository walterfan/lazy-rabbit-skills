---
name: microservice-design-doc
description: Generate comprehensive microservice design documents from requirements. Use when asked to write, draft, or create a design document, design doc, technical design, microservice design, system design, or architecture document. Supports both Chinese and English output. Covers requirements analysis, architecture design, domain modeling, API design, deployment, metrics, testing strategy, and risk assessment.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - design-doc
  - microservice
  - architecture
  - technical-writing
category: architecture
platforms:
  - claude-code
  - cursor
visibility: public
---

# Microservice Design Document Skill

Generate structured design documents for microservice projects following a battle-tested template.

## Contract

- `scope_in`: Microservice or system-level design docs based on requirements, user stories, existing service context, or architecture constraints. Output may be in Chinese or English.
- `scope_out`: Product requirement docs, UI-only specs, legal/compliance approval text, or implementation code changes beyond illustrative snippets and diagrams.
- `preconditions`: The user has provided at least a service/problem statement. Preferred inputs are service name, goals, constraints, dependencies, and capacity/SLA expectations.
- `postconditions`: The output follows the selected template, covers all major sections, marks unknowns as `TBD`, and preserves references to related systems or documents.

## Execution

### Phase 1: Gather context

- Entry: the request is for a design or architecture document.
- Steps:
  1. Extract service purpose, business requirements, constraints, dependencies, and non-functional expectations.
  2. If the prompt is brief, infer a workable draft structure and mark assumptions as `TBD`.
- Exit: there is enough context to draft each major section without inventing hidden facts.
- On fail: stop and ask only for the missing high-impact inputs such as service purpose, core requirement, or target platform.

### Phase 2: Select template

- Entry: context is sufficient to choose an output language.
- Steps:
  1. Use [references/template-cn.md](references/template-cn.md) for Chinese requests.
  2. Use [references/template-en.md](references/template-en.md) for English requests.
  3. Follow [references/section-guide.md](references/section-guide.md) for section depth and common pitfalls.
- Exit: one template and one language are chosen.
- On fail: fall back to the user’s message language; if still ambiguous, ask which language to use before drafting.

### Phase 3: Draft the document

- Entry: template and context are ready.
- Steps:
  1. Fill every required section: introduction, design, dependencies, deployment, metrics, testing, risks, and references.
  2. Include concrete APIs, data structures, dependencies, deployment notes, and risk trade-offs where relevant.
  3. Use diagrams when they clarify architecture or flow.
- Exit: a complete draft exists with no silently skipped sections.
- On fail: produce a partial draft only if necessary, clearly mark incomplete areas as `TBD`, and list the missing inputs blocking completion.

## Verification

### Hard gates

- Template compliance: all major sections from the selected template are present.
- Requirement coverage: the main business and technical requirements are addressed explicitly.
- Traceability: assumptions and unknowns are marked as `TBD` instead of being implied as facts.
- Design completeness: architecture, dependencies, deployment, metrics, testing, and risks are each covered at least once.

### Quality checks

- API descriptions include method, path, request/response shape, and error behavior when APIs are in scope.
- Alternatives include a comparison or rationale when a design choice is non-obvious.
- Terminology stays consistent with the service and domain names supplied by the user.

## Feedback

### Failure modes

- Missing operational detail: ask for capacity, SLA, deployment target, or upstream/downstream dependencies.
- Over-generic design: add concrete domain entities, APIs, data flow, and risk trade-offs from the available context.
- Wrong language or template depth: switch template and regenerate the document structure before refining content.

### Improvement triggers

- Update this skill when the standard design template changes.
- Add new guidance when repeated review feedback shows missing sections, weak risk analysis, or incomplete deployment/testing details.
