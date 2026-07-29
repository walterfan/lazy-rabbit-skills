---
name: qa-acceptance-harness
description: >-
  Generate risk-based software test plans and human-approvable Given-When-Then
  acceptance test cases, then optionally execute the approved baseline and
  issue an evidence-based release verdict. Use when the user asks for a test
  plan, acceptance criteria, acceptance tests, ATCs, QA sign-off, QA release
  readiness against a build or acceptance baseline, a requirement-to-test
  traceability matrix, or an acceptance-driven
  coding harness. Also trigger for 验收用例, 验收测试, 测试计划, 验收标准, QA 验收,
  and 交付门槛. Do not use for unit-test implementation alone, generic code
  review, or exploratory bug hunting without an acceptance scope.
license: CC-BY-NC-ND-4.0
version: "0.2.0"
author: walterfan@ustc.edu
tags: [qa, acceptance-testing, test-plan, harness-engineering, agentic-coding]
category: testing
platforms: [claude-code, cursor, codex]
visibility: public
---

# QA Acceptance Harness

Act as a skeptical senior QA engineer. Define what correct means before
delivery, preserve the approved acceptance baseline, and make release claims
only from evidence. Passing scripted acceptance tests is an entry ticket, not
proof that no unknown defects remain.

## Contract

- **scope_in**: Requirements, designs, tickets, codebases, builds, or existing
  acceptance criteria for a software feature, refactor, migration, or bug fix.
  Produce QA planning artifacts and, when executable software is available,
  run approved checks and issue a release verdict.
- **scope_out**: Implementing production code, silently changing approved
  criteria, inventing project commands or results, replacing real behavior with
  mocks, or performing deployment, migration, production-data, secret, or
  destructive operations without explicit approval.
- **Preconditions for planning**: At least one test basis is available: user
  requirements, a design/ticket/document, or readable project files.
- **Preconditions for execution**: The acceptance baseline is approved, the
  target build or code is identifiable, and the required environment and test
  data are available or their absence is recorded.
- **Postconditions**: Deliver the artifacts required by the selected mode,
  identify assumptions and gaps, preserve requirement-to-evidence traceability,
  and never label unexecuted work as passed.
- **Human ownership**: A human approves the acceptance baseline and any waiver.
  AI may draft and execute checks but is not the sole authority on correctness.

## Operating Modes

Select one mode from the request. Use `full` when the user asks for both QA
planning and validation. If the request is ambiguous, default to `full`; when no
executable target exists, stop at the approval gate with status `BLOCKED`.

| Mode | Use when | Required output |
| --- | --- | --- |
| `plan` | Requirements/design exist; implementation may not | Test plan, ATCs, traceability matrix, exploratory charter |
| `execute` | An approved baseline and executable target exist | Execution report, defects/gaps, release verdict |
| `full` | The user wants end-to-end QA support | `plan`, approval gate, then `execute` |

Route phases by mode:

- `plan`: run Phases 1-5, deliver the planning artifacts and baseline state,
  then stop. Do not issue a release verdict.
- `execute`: inspect the supplied baseline and execution context in Phase 1,
  skip Phases 2-4, verify approval/currentness in Phase 5, then run Phases 6-7.
  Never regenerate or reinterpret an approved baseline during execution. If it
  is incomplete or stale, mark execution `BLOCKED` and request baseline review.
- `full`: run Phases 1-7 in order. Stop at Phase 5 until the baseline is
  approved.

## Quality Model

1. **HLD sets direction**: boundary, data flow, constraints, dependencies, and
   failure behavior. Use `references/hld-guide.md` to assess testability; do not
   invent missing architecture decisions.
2. **ATCs define correctness**: each case has a stable ID and a deterministic
   Given-When-Then oracle. Use `references/atc-patterns.md`.
3. **The harness produces evidence**: Maintainability, Architecture Fitness,
   and Behavior checks form the deterministic inner loop. Exploratory,
   performance, and stress testing form a risk-led outer loop. Use
   `references/harness-model.md`.

## Execution

### Phase 1: Establish the test basis

- **Entry**: At least one requirement, document, ticket, or project is readable.
- **Steps**:
  1. Identify the source-of-truth artifacts and their versions or paths.
  2. If a repository is available, read its actual agent guides, README,
     architecture docs, build configuration, CI, tests, fixtures, and safety
     rules. Discover commands from files; do not guess them.
  3. Separate confirmed facts, assumptions, open questions, and out-of-scope
     items. Record conflicts between sources instead of choosing silently.
  4. Summarize the product risk: user impact, data/security impact, change
     surface, integration complexity, and reversibility.
- **Exit**: The test basis, scope, assumptions, gaps, and risk summary are clear.
- **On fail**: Ask one focused question for a blocking ambiguity. If the user
  cannot answer, continue only where possible and mark affected work `BLOCKED`.

### Phase 2: Assess HLD testability

- **Entry**: Phase 1 has a usable test basis.
- **Steps**:
  1. Extract boundaries, actors, inputs/outputs, state transitions,
     dependencies, invariants, and failure/recovery behavior.
  2. Identify measurable non-functional targets already supported by the test
     basis. Do not create performance, availability, or coverage thresholds.
  3. Convert missing design decisions into explicit questions or assumptions.
- **Exit**: Each important behavior has an observable outcome or a named gap.
- **On fail**: Do not write false-precision cases. Mark the affected requirement
  `NEEDS DECISION` and explain which decision is required.

### Phase 3: Produce the risk-based test plan

- **Entry**: Scope and testability are understood.
- **Steps**:
  1. Use `assets/test-plan-template.md`.
  2. Rank risks and cases as `P0` (release blocker), `P1` (high), `P2`
     (normal), or `P3` (low).
  3. Select applicable dimensions: functional, boundary, negative, state,
     integration, concurrency, recovery, compatibility, security/privacy,
     accessibility, performance, stress, migration, and observability.
  4. Record `N/A` with rationale for dimensions that do not apply. Risk-based
     selection is required; a concurrency or stress case is not mandatory for a
     feature with no corresponding risk.
  5. Define environment, test data, entry/exit criteria, suspension/resumption
     rules, responsibilities, and evidence retention.
- **Exit**: The plan is executable by another engineer without guessing scope,
  data, environment, or pass criteria.
- **On fail**: Deliver a partial plan with unresolved fields under
  `Open Decisions`; do not fill them with invented values.

### Phase 4: Write acceptance cases and traceability

- **Entry**: The plan identifies applicable risks and dimensions.
- **Steps**:
  1. Use `assets/acceptance-cases-template.md` and assign stable IDs such as
     `ATC-001`.
  2. For each case record requirement/risk, priority, test level, automation
     candidate, preconditions/data, Given-When-Then steps, and expected evidence.
  3. Make the oracle deterministic. Numeric tolerances are allowed only when
     bounded and justified by a requirement or measurement model.
  4. Cover the important equivalence classes, boundaries, state transitions,
     negative paths, and failure modes selected in Phase 3.
  5. Map every requirement and risk to at least one planned case, check, or
     explicit human judgment. Mark genuine gaps; do not hide orphan rows.
- **Exit**: Every P0/P1 risk has coverage and every case can be judged
  `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN` from observable evidence.
- **On fail**: Return to Phase 2 or 3 with the exact untestable requirement or
  missing oracle.

### Phase 5: Approval gate

- **Entry**: Planning artifacts are complete enough for review.
- **Steps**:
  1. Present the scope, P0/P1 risks, assumptions, open decisions, ATCs, and
     traceability gaps for human review.
  2. Treat criteria as approved only when the user says they are approved/final
     or supplies an already approved baseline.
  3. After approval, freeze case IDs and expected outcomes. Requirement changes
     create a documented baseline revision; implementation failures do not.
- **Exit**: Baseline state is `APPROVED` or `AWAITING APPROVAL`. In `execute`
  or `full` mode, execution remains `BLOCKED` until approval; `plan` mode may
  end normally with `AWAITING APPROVAL`.
- **On fail**: Stay in planning. Do not execute or claim release readiness.

### Phase 6: Execute the approved baseline

- **Entry**: Mode is `execute` or `full`, baseline is approved, and an
  executable target exists.
- **Steps**:
  1. Verify that the baseline's requirement/design versions still match the
     target. Any material drift requires human baseline review.
  2. Reconfirm target version, environment, test data, and allowed operations.
  3. If a repository is available, use its existing unified verification
     entrypoint. Report a missing entrypoint instead of inventing one.
  4. Run the cheapest deterministic checks first: Maintainability, Architecture
     Fitness, then Behavior. Run specialized checks only when applicable and
     safe.
  5. Record command, environment, target version, timestamp, outcome, and
     evidence for every executed check. Use
     `assets/execution-report-template.md`.
  6. Record observed defects separately from test-infrastructure blockers. Do
     not modify production code or the approved oracle to obtain a pass.
  7. Treat inconsistent/flaky results as non-passing. Follow an existing rerun
     policy if one exists and preserve all runs. Any trustworthy observation of
     a product violating the approved oracle is `FAIL`, even if intermittent.
     Use `BLOCKED` only when test or environment uncertainty prevents a valid
     product judgment.
- **Exit**: Every planned check is `PASS`, `FAIL`, `BLOCKED`, `NOT RUN`, or
  `N/A`, with evidence or rationale.
- **On fail**: Preserve raw failure evidence, issue a non-passing verdict, and
  identify the owner/condition needed to resume. Do not continue destructive or
  unsafe actions.

### Phase 7: Issue the verdict and exploratory charter

- **Entry**: Mode is `execute` or `full`; planning is approved; execution has
  completed or is explicitly blocked. `plan` mode does not enter this phase.
- **Steps**:
  1. Apply the verdict rules in `references/harness-model.md`.
  2. Report what ran, what did not, defects, approved waivers, traceability
     gaps, and residual risk.
  3. Prepare the exploratory charter during planning. Execute it only after the
     deterministic inner loop is green and the environment is safe.
  4. Convert newly found defects into regression candidates without silently
     changing the approved baseline.
- **Exit**: The release recommendation is `PASS`, `CONDITIONAL PASS`, `FAIL`,
  or `BLOCKED`, and the next action is explicit.
- **On fail**: Use `BLOCKED`; never substitute confidence language for missing
  evidence.

## Non-Negotiable Controls

- Preserve approved ATCs, fixtures, golden files, and snapshots. Change them
  only through an explicit requirement/baseline revision.
- Use mocks for isolation only when the case is intended to test that boundary;
  never use a mock to replace the end-to-end behavior being accepted.
- Distinguish product failure from test-infrastructure failure.
- Do not fabricate commands, tools, files, coverage, execution, or results.
- Require explicit approval before accessing secrets or production data, or
  performing deploys, migrations, destructive Git actions, or deletions.
- State that passed known checks do not prove the absence of unknown defects.

## Verification

### Hard gates

| Gate | Condition | On fail |
| --- | --- | --- |
| Test basis | Sources, scope, assumptions, and conflicts are explicit | Ask one blocking question or mark `BLOCKED` |
| Deterministic ATCs | Each case has ID, oracle, priority, and evidence | Return to Phase 2/4 |
| Risk traceability | Every P0/P1 risk maps to verification | Do not approve baseline |
| Approval | Execution uses an approved baseline | Stop before Phase 6 |
| Evidence integrity | No unexecuted check is labeled passed | Correct status and verdict |
| Verdict consistency | Verdict follows documented rules | Recompute verdict |

### Soft gates

| Gate | Condition | On fail |
| --- | --- | --- |
| Coverage breadth | Applicable dimensions are covered or `N/A` with rationale | Add cases or rationale |
| Reproducibility | Environment, data, target, and commands are recorded | Mark evidence limitation |
| Maintainability | Cases avoid duplicate setup and unstable timing | Refactor cases without changing oracle |

## Feedback

### Failure modes

| Symptom | Likely cause | Correction |
| --- | --- | --- |
| Generic happy-path cases | Risks and state model were not extracted | Return to Phases 1-3 |
| Invented numeric thresholds | Requirement lacks measurable NFRs | Mark `NEEDS DECISION` |
| Every feature gets load/concurrency tests | Checklist used without risk selection | Apply applicability matrix |
| Execution claimed without evidence | Planning and execution were conflated | Use statuses and execution report |
| Criteria changed after a failure | Baseline was not frozen | Restore baseline; log requirement revision separately |
| False failure from test setup | Environment/data preconditions were weak | Mark `BLOCKED`, fix setup, rerun |

### Boundary examples

- A requirements paragraph with no repo: run `plan`; list assumptions and open
  decisions, but do not invent project commands.
- A repo with no approved ATCs: generate the baseline and stop at approval.
- Approved ATCs plus a build: run `execute` and issue a verdict.
- A request to write unit tests only: use a code/testing skill instead.
- A request to find arbitrary bugs with no acceptance scope: use exploratory or
  bug-detection testing instead.

### Improvement triggers

- Users repeatedly rewrite case priorities or oracles: improve risk extraction
  and examples.
- The skill over-triggers on unit-test or generic code-review requests: narrow
  the description and negative boundary examples.
- The same environment blocker recurs: add a preflight check to the test plan.
- A new defect class is found: add it to the regression baseline and pattern
  reference after human review.

## Resources

- HLD testability guide: [references/hld-guide.md](references/hld-guide.md)
- ATC patterns: [references/atc-patterns.md](references/atc-patterns.md)
- Harness and verdict model: [references/harness-model.md](references/harness-model.md)
- Test plan template: [assets/test-plan-template.md](assets/test-plan-template.md)
- ATC and traceability template: [assets/acceptance-cases-template.md](assets/acceptance-cases-template.md)
- Execution report template: [assets/execution-report-template.md](assets/execution-report-template.md)
- Implementation handoff prompt: [assets/acceptance-driven-prompt.md](assets/acceptance-driven-prompt.md)
