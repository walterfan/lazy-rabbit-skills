# QA Execution Report: <Feature or Change>

## Execution Context

| Field | Value |
| --- | --- |
| Approved baseline | <plan/case version> |
| Baseline currency check | CURRENT / STALE / UNKNOWN - <requirement/design versions> |
| Target build / commit | <identifier> |
| Environment / configuration | <identifier> |
| Test data version | <identifier> |
| Executed by / time | <owner / timestamp> |

## Gate Summary

| Gate | Command / procedure | Result | Evidence |
| --- | --- | --- | --- |
| Maintainability | <real command> | PASS/FAIL/BLOCKED/NOT RUN/N/A | <path or concise output> |
| Architecture Fitness | <real command> | ... | ... |
| Behavior | <real command> | ... | ... |
| Specialized | <procedure> | ... | ... |

## Acceptance Results

| ATC | Priority | Result | Evidence / defect / blocker |
| --- | --- | --- | --- |
| ATC-001 | P0 | PASS/FAIL/BLOCKED/NOT RUN/N/A | <observable evidence> |

## Findings and Gaps

- **Product defects:** <IDs, severity, affected ATCs>
- **Test blockers:** <environment/data/tool issue and resume owner>
- **Flaky/inconsistent results:** <all observed runs and deterministic-fix owner>
- **Approved waivers:** <owner, reason, expiry>
- **Not run / N/A:** <rationale>
- **Residual risk:** <what remains unknown>

## Release Verdict

**Verdict:** PASS / CONDITIONAL PASS / FAIL / BLOCKED

**Basis:** <apply the verdict rules; do not substitute confidence language for evidence>

**Next action:** <release, obtain waiver, fix defect, restore environment, rerun>

## Exploratory Follow-up

- <charter executed or still planned>
- <new regression candidates>
