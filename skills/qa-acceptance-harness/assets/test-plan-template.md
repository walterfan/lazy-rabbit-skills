# Test Plan: <Feature or Change>

## Document Control

| Field | Value |
| --- | --- |
| Plan ID / version | <TP-ID / vN> |
| Target release/build | <version or not yet available> |
| Test basis | <requirements, HLD, ticket, paths, versions> |
| Owner / reviewers | <QA owner and approvers> |
| Baseline state | DRAFT / AWAITING APPROVAL / APPROVED / REVISED |

## Scope and Objectives

- **Objective:** <quality question this plan answers>
- **In scope:** <behaviors and interfaces>
- **Out of scope:** <explicit exclusions and owner>

## Facts, Assumptions, and Open Decisions

| Type | Item | Impact / owner |
| --- | --- | --- |
| Fact | <confirmed behavior> | <source> |
| Assumption | <proposed interpretation> | <approval needed> |
| Open decision | <missing oracle or target> | <owner> |
| Source conflict | <contradictory statements> | <resolution needed> |

## Risk Assessment

| Risk ID | Failure impact | Likelihood | Priority | Mitigation / test focus |
| --- | --- | --- | --- | --- |
| R-001 | <user/data/business impact> | High/Medium/Low | P0-P3 | <planned evidence> |

## Coverage Applicability

| Dimension | Applicable? | Rationale / target |
| --- | --- | --- |
| Functional | Yes/No | <why> |
| Boundary/equivalence | Yes/No | <why> |
| State/sequence | Yes/No | <why> |
| Negative/error | Yes/No | <why> |
| Integration | Yes/No | <why> |
| Concurrency | Yes/No | <why> |
| Recovery/resilience | Yes/No | <why> |
| Compatibility/migration | Yes/No | <why> |
| Security/privacy | Yes/No | <why> |
| Accessibility | Yes/No | <why> |
| Performance/stress | Yes/No | <requirement-backed target or NEEDS DECISION> |
| Observability | Yes/No | <why> |

## Test Approach

| Layer/type | Scope | Method / real command | Evidence |
| --- | --- | --- | --- |
| Maintainability | <applicable checks> | <repo command or missing> | <artifact> |
| Architecture Fitness | <contracts/invariants> | <check or review> | <artifact> |
| Behavior | <UT/IT/E2E/ATC> | <command/manual procedure> | <artifact> |
| Specialized | <perf/security/a11y/etc.> | <method> | <artifact> |

## Environment and Test Data

- **Environment / dependencies:** <versions, topology, external services>
- **Target build/configuration:** <identifier>
- **Test data:** <fixtures, generators, cleanup, privacy classification>
- **Controls:** <clock, random seed, isolation, reset procedure>
- **Safety boundaries:** <operations requiring approval>

## Entry, Exit, and Interruption Rules

- **Entry criteria:** <approved baseline, build available, environment healthy>
- **Exit criteria:** <P0/P1 and required gates, defect threshold, evidence>
- **Suspend when:** <environment invalid, unsafe action, blocking defect>
- **Resume when:** <owner and measurable recovery condition>

## Cases and Traceability

See the associated acceptance case catalog and traceability matrix. Before
baseline approval, every P0/P1 risk must map to a planned verification method
and expected evidence.

## Responsibilities and Schedule

| Activity | Owner | Dependency / timing |
| --- | --- | --- |
| Baseline approval | <human owner> | <condition> |
| Execution | <owner> | <condition> |
| Defect triage | <owner> | <condition> |
| Release verdict | <owner> | <condition> |

## Exploratory Charter

- **Mission:** <risk hypothesis to investigate>
- **Areas/data/personas:** <focus>
- **Time box:** <duration or NEEDS DECISION>
- **Evidence:** <notes, screenshots, logs, defect IDs>
- **Regression rule:** confirmed defects become proposed ATCs after review.
