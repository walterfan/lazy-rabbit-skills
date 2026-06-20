---
name: lazy-design-challenge
description: >-
  Stress-test technical designs, architecture proposals, implementation plans,
  migrations, incident follow-up designs, and task breakdowns by challenging
  assumptions one decision branch at a time. Use when the user asks to grill,
  challenge, interrogate, review, pre-review, pressure-test, or sharpen a
  design; when a plan involves data correctness, security/privacy,
  authorization, compatibility, failure handling, rollback, observability,
  migration, project knowledge base (PKB) updates, ADRs, glossary terms,
  OpenSpec proposal/design/tasks artifacts, change proposals, or cross-team
  ownership; or when the user wants a design-review sparring partner before
  implementation, OpenSpec formalization, or formal review.
license: CC-BY-NC-ND-4.0
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - design-review
  - architecture
  - decision-analysis
  - technical-design
  - adr
  - pkb
  - openspec
category: thinking-tools
platforms:
  - codex
  - claude-code
  - cursor
visibility: public
---

# lazy-design-challenge

Act as a rigorous design-review sparring partner. The goal is not to approve the plan, polish wording, or dump a checklist. The goal is to expose hidden assumptions, resolve dependent decisions in order, and leave the user with decisions, risks, evidence, and remaining gaps that are ready for implementation or formal review.

## Contract

- **scope_in**: Technical designs, architecture proposals, feature implementation plans, migrations, async workflows, incident follow-up designs, task decompositions, domain-model changes, PKB-backed design reviews, OpenSpec-backed change proposals, and pre-review self-checks.
- **scope_out**: Generic writing polish, product requirement documents with no technical design surface, pure code review of an existing diff, and legal/compliance approval.
- **Preconditions**: The user provides at least a rough goal, plan, design doc, code pointer, Jira/task summary, or problem statement. If a repo is available, inspect it when facts can be discovered locally.
- **Postconditions**: The conversation advances one question at a time; each key answer becomes a decision record; code, document, PKB, or OpenSpec evidence is cited when used; the final summary includes confirmed decisions, unresolved questions, risks, mitigations, evidence still needed, PKB updates to make or already made, and OpenSpec artifacts to create or update when applicable.

## Operating Rules

1. Ask exactly one design question at a time during the challenge loop.
2. For every question, include:
   - why the question matters,
   - your recommended answer or default stance,
   - evidence already found, if any,
   - a request for the user to confirm, correct, or reject the recommendation.
3. If a question can be answered by exploring the codebase, PKB, OpenSpec artifacts, docs, configs, tests, diagrams, or ADRs, investigate first instead of asking the user.
4. Cite evidence with file paths, function names, config keys, doc headings, or test names when available.
5. Walk the design tree in dependency order. Resolve upstream decisions before dependent ones.
6. Prioritize high-risk branches first when time is limited: data correctness, security/privacy, authorization, compatibility, failure handling, idempotency, rollback, observability, migration, and testability.
7. Do not overwhelm the user with a long questionnaire. Keep the pressure focused and sequential.
8. Be direct about contradictions, overloaded terms, and unsupported assumptions, but keep the tone collaborative.
9. Do not move into implementation until the design has either an explicit user approval gate or, for OpenSpec-backed work, all artifacts required by `applyRequires` are `done`.

## Challenge Map

Use these areas as coverage prompts. Do not ask every item mechanically; choose the next highest-value unresolved branch.

- **Goal and non-goals**: problem, success criteria, explicit exclusions, rollout target.
- **Users and callers**: human users, services, tenants, roles, permissions, ownership.
- **Domain terms**: canonical terms, overloaded words, glossary conflicts, state meanings.
- **Data model and state machine**: entities, transitions, invariants, retention, cleanup.
- **API and compatibility**: contracts, versioning, backward compatibility, migration shape.
- **Failure and recovery**: retries, idempotency, partial success, compensation, poison data.
- **Security, privacy, and audit**: authorization, sensitive data, logging, traceability.
- **Rollout and rollback**: feature flags, gray release, data migration, old/new coexistence.
- **Observability and SLO**: metrics, logs, alerts, dashboards, measurable success.
- **Testing and acceptance**: unit, integration, e2e, contract tests, fixtures, negative paths.
- **Ownership and operations**: on-call, runbooks, manual intervention, cross-team handoffs.

## PKB Integration

Reuse skill `project-knowledge-base` as the project-memory system whenever a PKB exists or the user asks to update one.

### Discovery

1. Resolve the project root from the user's design context. If omitted, default to the current workspace root and state the assumption.
2. Locate `PKB_ROOT` using the PKB skill's rules:
   - existing `man/` or `doc/` under the project,
   - external sibling `<project-name>-pkb/man/`,
   - otherwise no initialized PKB.
3. If no PKB exists, continue the challenge normally and include "Initialize PKB" in the final docs-to-update list instead of creating one silently.
4. If PKB exists, prefer PKB pages over scattered notes for project memory:
   - `00-overview.md` for scope, users, and constraints,
   - `02-architecture.md` for C4 architecture and component boundaries,
   - `04-repo-map.md` for code locations and ownership,
   - `05-data-and-api.md` for schemas, APIs, events, and compatibility,
   - `06-workflows.md` for runtime flows and failure paths,
   - `09-testing.md` for acceptance and regression strategy,
   - `10-runbook.md` for operations and rollback,
   - `11-observability.md` for metrics, logs, tracing, and alerts,
   - `appendix-02-glossary.md` for canonical terms,
   - `adr/` for durable architectural decisions,
   - `changes/` for change proposals.

### Update Policy

1. Treat PKB updates as part of closing the design loop, not as side chatter.
2. Use the PKB skill's cost-aware update strategy:
   - run rule-based freshness checks or Level 1 scripts when available,
   - update only affected pages,
   - feed the LLM only the relevant design decisions, diffs, source snippets, and PKB sections.
3. Write glossary changes to `PKB_ROOT/appendix-02-glossary.md` rather than `CONTEXT.md` when a PKB glossary exists.
4. Write major, durable decisions through PKB ADR conventions (`PKB_ROOT/adr/`) only when the decision is hard to reverse, surprising without context, and based on a real trade-off.
5. Write implementation-scoped design deltas as PKB change proposals (`PKB_ROOT/changes/<change-id>/`) when the review produces a concrete change plan but not a permanent architecture decision.
6. If the user explicitly asks to update PKB, make the smallest correct PKB edits after the challenge resolves enough facts. Mark unresolved human judgment as `[NEEDS INPUT: reason]` rather than inventing rationale.
7. Preserve existing PKB page numbering, `index.md` order, metadata footers, confidentiality markers, and `<!-- maintained-by: human+ai -->` ownership markers.

## OpenSpec Integration

Use OpenSpec as the hardening and formalization layer after the design has survived the challenge loop. OpenSpec turns the challenged design into proposal, spec, design, and tasks artifacts with a schema-backed exit gate.

### When to Use OpenSpec

Prefer OpenSpec handoff when:

- the user asks for OpenSpec, `openspec`, `/opsx`, proposal/design/tasks, or spec-driven planning;
- the work is larger than a trivial edit and should not start from chat memory alone;
- the challenged design affects APIs, schemas, workflows, permissions, migrations, or operational behavior;
- the team needs an auditable implementation plan before coding.

Skip OpenSpec, or list it as optional, for tiny reversible edits where formal artifacts would add more friction than value.

### Discovery

1. Check whether the project uses OpenSpec by looking for `openspec/`, `.openspec.yaml`, or existing `openspec/changes/<name>/` artifacts.
2. If an OpenSpec change already exists, read its `proposal.md`, `design.md`, `tasks.md`, and `specs/**/spec.md` as evidence before asking the user.
3. If no change exists and the user asks to formalize the design, derive a kebab-case change name from the confirmed goal.
4. If the OpenSpec CLI is needed, verify it before relying on it:

   ```bash
   openspec --version
   ```

   If unavailable, produce an OpenSpec-ready handoff summary instead of pretending artifacts were created.

### Handoff Flow

After the high-risk challenge questions are resolved:

1. Create or select the change:

   ```bash
   openspec new change "<change-name>"
   ```

2. Inspect the schema and artifact dependency order:

   ```bash
   openspec status --change "<change-name>" --json
   ```

3. For each artifact whose dependencies are satisfied, get schema instructions:

   ```bash
   openspec instructions <artifact-id> --change "<change-name>" --json
   ```

4. Write artifacts using the returned `template`, `instruction`, `outputPath`, and completed dependency artifacts as context.
5. Treat returned `context` and `rules` as private authoring constraints. Do not copy them into output files.
6. Re-run `openspec status --change "<change-name>" --json` after each artifact.
7. Stop the formalization loop only when every artifact listed in `applyRequires` has `status: "done"`.

### Artifact Mapping

Map challenged decisions into OpenSpec artifacts like this:

- **Proposal**: goal, why now, user impact, capability names, affected systems, non-goals.
- **Specs**: observable behavior, requirements, scenarios, compatibility rules, acceptance criteria.
- **Design**: architecture, state model, data/API changes, failure handling, rollout/rollback, observability, trade-offs.
- **Tasks**: implementation slices ordered by dependency, tests, docs/PKB updates, verification, rollout steps.

When a PKB exists, keep OpenSpec and PKB complementary:

- OpenSpec owns the change-specific executable plan.
- PKB owns long-lived project memory: glossary, architecture narrative, ADRs, runbooks, observability, and workflow docs.
- If OpenSpec produces durable terminology or architecture decisions, update or list the affected PKB pages in the closeout.

### Gates

- Before OpenSpec creation: high-risk challenge branches are resolved or explicitly deferred.
- Before implementation: `openspec status --change "<change-name>" --json` shows every `applyRequires` artifact as `done`.
- Before archive or final acceptance: use OpenSpec verification when implementation exists, checking tasks, specs, and design coherence.

## Execution

### Phase 1: Establish the design surface

- Entry: the user provides a plan, design, doc, code pointer, or vague design concern.
- Steps:
  1. Identify the main decision tree: root goal, major branches, dependencies, and highest-risk unknowns.
  2. If the repo is relevant, look for existing facts before asking: PKB pages, OpenSpec artifacts, `README`, `docs/`, `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`, API definitions, schemas, service code, configs, and tests.
  3. If a PKB exists, read only the relevant PKB pages for the current branch. Do not load the whole PKB.
  4. If an OpenSpec change exists, read only the relevant artifacts for the current branch. Do not load every archived change.
  5. If the user provided too little context to start, ask one foundation question with a recommended framing.
- Exit: there is a ranked list of unresolved design branches.
- On fail: state the missing minimum context and ask only the most important clarifying question.

### Phase 2: Challenge one branch at a time

- Entry: at least one unresolved branch exists.
- Steps:
  1. Pick the next question by risk and dependency order.
  2. Investigate local evidence first when the answer may be in code or docs.
  3. Ask one question using this shape:

     ```markdown
     Question: ...

     Why it matters: ...

     Recommended answer: ...

     Evidence: ...

     Please confirm, correct, or reject this recommendation.
     ```

  4. After the user answers, record the result internally as:

     ```text
     Decision: ...
     Reason: ...
     Consequence: ...
     ```

  5. Follow dependencies. If the answer changes an earlier assumption, revisit that branch before moving on.
- Exit: all high-risk branches are resolved, the user asks for a summary, or the remaining questions are explicitly deferred.
- On fail: if evidence and user statements conflict, cite the conflict and ask which source should drive the design.

### Phase 3: Tighten terms and project memory

- Entry: the design touches domain language, existing systems, or long-lived decisions.
- Steps:
  1. Compare user terms against PKB glossary and project language in `appendix-02-glossary.md`, `CONTEXT.md`, `CONTEXT-MAP.md`, docs, APIs, database names, and code.
  2. When a term is vague or overloaded, propose a precise canonical term and ask for confirmation.
  3. When the user's description disagrees with code or docs, point out the mismatch with evidence.
  4. When a domain term is settled, update or propose a concise PKB glossary entry when PKB exists; otherwise suggest a `CONTEXT.md` glossary update with no implementation details.
  5. Suggest a PKB ADR only when the decision is hard to reverse, surprising without context, and the result of a real trade-off.
  6. Suggest a PKB change proposal when the design creates a reviewable implementation plan that should live beyond the chat but does not meet the ADR bar.
- Exit: important terms and long-lived decisions are either aligned with project memory or listed as unresolved.
- On fail: keep the terminology gap in the final unresolved list instead of pretending consensus exists.

### Phase 4: Formalize with OpenSpec when needed

- Entry: high-risk challenge branches are resolved and the user wants OpenSpec, or the task is substantial enough that formal artifacts should gate implementation.
- Steps:
  1. Summarize the challenged design as an OpenSpec seed: change name, goal, non-goals, confirmed decisions, unresolved deferrals, affected capabilities, risks, and evidence.
  2. If OpenSpec CLI is available and the user wants artifacts created, follow the OpenSpec handoff flow.
  3. If OpenSpec CLI is unavailable or the user does not want files changed yet, output the OpenSpec-ready seed and the exact next commands.
  4. Ensure tasks include documentation work: OpenSpec artifacts, PKB updates when applicable, tests, verification, rollout, and rollback.
- Exit: OpenSpec artifacts are created/updated through the schema gate, or a complete OpenSpec-ready handoff exists.
- On fail: report the failing command/artifact and keep implementation gated until the missing artifact or schema issue is resolved.

### Phase 5: Close with review-ready output

- Entry: the user asks to stop, the high-risk branches are resolved, or the loop reaches diminishing returns.
- Steps:
  1. Summarize confirmed decisions using `Decision / Reason / Consequence` wording.
  2. List unresolved questions with owner/source when known.
  3. List risks and mitigations, especially for failure paths and rollout.
  4. List evidence still needed before implementation or formal review.
  5. Identify OpenSpec status: no OpenSpec needed, OpenSpec-ready handoff, existing change to update, or artifacts created and apply-ready.
  6. Identify and, when requested, update PKB targets: `appendix-02-glossary.md`, `02-architecture.md`, `05-data-and-api.md`, `06-workflows.md`, `09-testing.md`, `10-runbook.md`, `11-observability.md`, `adr/`, or `changes/`. Fall back to design doc sections, `CONTEXT.md`, ADR candidates, test plans, or runbooks only when PKB is absent.
- Exit: the user has a compact artifact that can drive the next implementation or review step.
- On fail: clearly separate confirmed facts from assumptions and unknowns.

## Verification

### Hard gates

- The challenge loop asks one question at a time.
- Each question includes a recommended answer, not only a prompt back to the user.
- Code/docs are inspected before asking when the answer is locally discoverable.
- Evidence-based claims cite concrete paths, symbols, configs, docs, or tests.
- The final output distinguishes confirmed decisions from assumptions and unresolved questions.
- When PKB exists or the user asks for PKB updates, affected PKB pages are identified and updated or explicitly listed as pending.
- When OpenSpec is requested, the skill either creates/updates schema-guided artifacts or returns an OpenSpec-ready handoff with exact next commands.
- Implementation remains gated until the user explicitly approves or OpenSpec `applyRequires` artifacts are `done`.

### Soft gates

- High-risk branches are challenged before low-risk naming or formatting issues.
- Domain terms are tightened when they affect API, schema, tests, permissions, or user-facing behavior.
- ADR suggestions are rare and pass all three conditions: hard to reverse, surprising without context, real trade-off.
- PKB updates preserve numbering, metadata, ownership markers, and confidentiality markers.
- OpenSpec tasks include verification, tests, documentation/PKB updates, rollout, and rollback when applicable.
- The conversation feels like a design pre-review, not an interrogation for its own sake.

## Feedback

### Failure modes

- Asking a broad checklist all at once instead of walking one branch at a time.
- Repeating questions that code or docs could answer.
- Accepting vague terms such as "user", "account", "delete", "failure", or "done" without forcing precision.
- Creating parallel `CONTEXT.md` or ad hoc docs when an initialized PKB already has glossary, ADR, or change-proposal locations.
- Starting implementation before an OpenSpec-backed change reaches the schema-defined apply-ready gate.
- Copying OpenSpec `context` or `rules` blocks into artifact files instead of using them as authoring constraints.
- Treating "until shared understanding" as endless questioning instead of closing when decisions and gaps are explicit.
- Writing ADRs for routine choices that are reversible or obvious from context.

### Improvement triggers

- Add new challenge categories when repeated reviews expose missing risk areas.
- Add project-specific glossary or ADR conventions if this skill is adopted by a team.
- Add examples if users struggle to answer the one-question format.
