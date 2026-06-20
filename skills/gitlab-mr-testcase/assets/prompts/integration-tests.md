You are generating **integration test cases** that act as a **quality gate** for an AI-written Merge Request.

The mechanism the reviewer relies on:

1. You generate a set of integration test cases grounded in the design spec and the MR diff.
2. The reviewer (or an agent) runs those cases against the change.
3. **If every case passes, the reviewer can ship the MR without reading every line.**
4. **If any case fails, the failing case points directly at the code path that needs line-by-line review.**

For that gate to work, the cases must be:

- **Sufficient**: every requirement in the design spec must be mapped to at least one case; every meaningful behavior change in the diff must be mapped to at least one case. Gaps must be called out explicitly, not hidden.
- **Grounded only** in the supplied MR diff, MR description, project context, design spec(s), and (if provided) Jira issue reference. If something is not in those sources, mark it `UNKNOWN` instead of inventing behavior.
- **Cross-component**: focused on handler → service → repository → external-dep interactions, not unit-level isolated logic.
- **Verifiable**: every assertion is observable (HTTP response, return value, persisted row, emitted event, log line, metric). No assertions on private internals.
- **Convertible**: each case ships with a thin pytest skeleton so an engineer can wire it up with minimal rewriting.

## Inputs

Test focus: **{{test_focus}}**
Primary language detected: **{{language}}**

### Project Context

{{project_context}}

### Local Code Context (when available)

{{local_code_context}}

### Design Spec(s) — required anchor for the quality gate

Spec sources: {{spec_paths}}
Spec ingestion status: {{spec_status}}

{{spec_content}}

### Jira Issue (optional, for traceability)

{{jira_issue_reference}}

### Review Scope

{{review_scope}}

### MR Summary

{{mr_summary}}

### MR Diff

{{mr_diff}}

## What to produce

1. A **Change Summary** (≤6 bullets) explaining the behavior under test in plain language. Cite which spec section or which file/line range supports each claim. If the spec and diff disagree, flag it.

2. A **Traceability Matrix** mapping each spec requirement **and** each meaningful behavior change in the diff to one or more test case IDs. Every spec requirement and every diff-introduced behavior must appear here. Anything you cannot cover must be marked `UNCOVERED — needs line-by-line review of <file:lines>`; treat that as a load-bearing signal — the reviewer will use it to decide which parts of the MR they still have to read manually.

3. A **Gate Verdict block** with three lines:
   - `Spec coverage:` <Complete | Partial — N uncovered>
   - `Diff coverage:` <Complete | Partial — N hunks uncovered>
   - `Skip line-by-line review if all cases pass?` <YES | NO — reasons>
   Answer `NO` whenever the Traceability Matrix has any `UNCOVERED` row, any `SPEC_DRIFT` row, any case with `MISSING` fixtures the team does not have, or any case marked `derived from diff only — spec gap`. The reviewer relies on this verdict; do not soften it.

4. A **Test Case List** of N integration test cases (target 6–15, never fewer than 3 unless the change really is that small). Order them: happy path first, then boundary, then negative, then regression.

For each test case use this exact markdown structure:

```markdown
### TC-<NN>: <short imperative title>

- **Type**: integration | regression | negative | boundary
- **Priority**: P0 | P1 | P2
- **Source**:
  - Spec: <section/heading or "n/a">
  - Diff: <file path>:<line range or hunk>
- **Preconditions / Fixtures**:
  - <fixture or environment requirement>
- **Inputs**:
  - <named input>: <value or range>
- **Action**:
  - <single, observable action under test>
- **Expected**:
  - <verifiable assertion 1>
  - <verifiable assertion 2>
- **Side-effects to verify** (DB row, queue message, log line, downstream call):
  - <named side-effect>: <expected state>
- **Out of scope / Not asserted**:
  - <thing this case intentionally does not cover>
- **Risks if this case fails**:
  - <1 line: what regression this catches>
- **Pytest skeleton**:

\`\`\`python
import pytest

@pytest.mark.integration
@pytest.mark.parametrize(
    "<param_name>",
    [
        pytest.param(<value>, id="<happy|boundary|negative>"),
    ],
)
def test_<snake_case_title>(<fixtures>, <param_name>):
    # Arrange
    ...
    # Act
    result = <call under test>
    # Assert behavior
    assert ...
    # Assert side-effects
    assert ...
\`\`\`
```

## Hard rules

- Do not output cases that cannot point back to a specific spec section, file, or hunk.
- Do not assert on private internals; assert on observable outputs (HTTP responses, return values, persisted rows, emitted events, log lines, metrics).
- Do not invent fixtures that have no corollary in the codebase. If a required fixture does not exist, list it under `Preconditions / Fixtures` with `MISSING — please confirm or create`.
- Do not mix unit-only ideas (single-function pure logic) into this round; route those to a separate unit-test pass.
- Boundary, negative, and idempotency cases are required when the diff touches input parsing, auth, retries, or persistence — if none apply, state that explicitly.
- If the diff is too small or too narrow to justify N≥3 integration cases, say so plainly and explain why instead of padding.

## Optional but recommended

- Suggest the smallest set of test data (CSV-style or table) that exercises all cases together.
- Suggest which existing test file each TC should live in, based on the project layout shown in the diff / local context. If unclear, propose a new file path.
- Mention any test infrastructure (mocks, containers, fakes) the team will need but does not yet have.

Begin now. Output the Change Summary, then the Traceability Matrix, then the Gate Verdict block, then the Test Case List, in that order.
