# Acceptance Case Catalog: <Feature or Change>

## ATC-001: <Observable behavior>

| Field | Value |
| --- | --- |
| Requirement / risk | <REQ-ID / R-ID> |
| Priority | P0 / P1 / P2 / P3 |
| Dimension / level | <boundary, recovery, integration, etc.> / <UT, IT, E2E, manual> |
| Automation candidate | Yes / No / Partial - <rationale> |
| Preconditions | <environment, state, permissions> |
| Test data | <exact fixture/input and cleanup> |
| Expected evidence | <assertion output, response, state, log/metric without sensitive data> |

```gherkin
Scenario: <Observable behavior>
  Given <specific initial state>
  And <specific dependency/configuration>
  When <one action or event occurs>
  Then <deterministic user-visible result>
  And <required side effect, error semantic, or invariant>
```

**Oracle notes:** <requirement source and any justified numeric tolerance>

## Traceability Matrix

| Requirement / risk | Priority | ATC / check | Verification mechanism | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| <REQ-1 / R-001> | P0 | ATC-001 | IT | <owner> | DRAFT / APPROVED / PASS / FAIL / BLOCKED / NOT RUN / N/A |

Rules:

- Every P0/P1 row maps to at least one accepted verification mechanism.
- `BLOCKED`, `NOT RUN`, and `N/A` require rationale.
- Human judgment is valid when automation cannot decide semantics, but it needs
  a named reviewer and review evidence.
- Preserve case IDs after approval; requirement changes create a baseline
  revision rather than renumbering historical evidence.
