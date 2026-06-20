You are generating **acceptance test cases** that act as a **quality gate** for an AI-written Merge Request.

The mechanism the reviewer relies on:

1. You generate acceptance cases that, between them, exercise every stakeholder-facing requirement in the design spec and every behavior change in the diff.
2. The reviewer (or an agent) runs those cases against the change.
3. **If every case passes, the reviewer can ship the MR without reading every line.**
4. **If any case fails, the failing case points directly at the requirement that the MR did not satisfy.**

For that gate to hold, the cases must be:

- **Anchored to the spec first**, then cross-checked against the MR diff. If the diff diverges from the spec, flag it as `SPEC_DRIFT` rather than silently rewriting the requirement.
- **Exhaustive enough**: every spec requirement must be either covered or flagged `MISSING`. Every diff-introduced behavior the spec does not mention must be flagged `SPEC_DRIFT`. No silent omissions.
- **Written in Given / When / Then form** so QA and PO can read them without code knowledge.
- **Observable**: assertions only on outputs a stakeholder could care about — HTTP responses, persisted rows, emitted events, externally visible state.
- **Convertible**: each case ships with a thin pytest skeleton.

## Inputs

Test focus: **{{test_focus}}**
Primary language detected: **{{language}}**

### Project Context

{{project_context}}

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

1. A **Spec Coverage Map**: a table of spec requirements (verbatim or close-paraphrase) vs. the MR change(s) that implement them. Mark each row as `Covered`, `Partial`, `Missing`, or `SPEC_DRIFT`. Every spec requirement must appear in this table.

2. An **Open Questions** list: anything in the spec the diff does not answer, or anything in the diff that has no spec basis. One line each.

3. A **Gate Verdict block** with three lines:
   - `Spec coverage:` <Complete | Partial — N Missing>
   - `Spec drift detected:` <None | N rows>
   - `Skip line-by-line review if all cases pass?` <YES | NO — reasons>
   Answer `NO` whenever the Spec Coverage Map has any `Missing`, `Partial`, or `SPEC_DRIFT` row, when Open Questions is non-empty, or when any case relies on a fixture that does not yet exist. The reviewer relies on this verdict; do not soften it.

4. An **Acceptance Test Case List** (target 5–12 cases). Order them: primary happy path → alternate paths → error paths → cross-cutting (auth, idempotency, observability) → negative.

For each case use this exact markdown structure:

```markdown
### AC-<NN>: <short stakeholder-facing title>

- **Type**: acceptance
- **Priority**: P0 | P1 | P2
- **Stakeholder value** (one sentence):
  - <why a user / operator / downstream system cares>
- **Source**:
  - Spec: <section/heading>
  - Diff: <file path or "spec-only, no diff coverage yet">
- **Given**:
  - <precondition 1>
  - <precondition 2>
- **When**:
  - <single observable trigger>
- **Then**:
  - <observable outcome 1>
  - <observable outcome 2>
- **And** (side-effects, optional):
  - <log / metric / event / downstream call>
- **Not asserted here**:
  - <out-of-scope detail>
- **Failure impact**:
  - <one line: what this case prevents shipping>
- **Pytest skeleton**:

\`\`\`python
import pytest

@pytest.mark.acceptance
def test_<snake_case_title>(<fixtures>):
    # Given
    ...
    # When
    result = <call under test>
    # Then
    assert ...
    # And (optional side-effects)
    assert ...
\`\`\`
```

## Hard rules

- Every case must cite at least one spec source or be explicitly labeled `derived from diff only — spec gap`.
- Do not paraphrase spec wording in a way that changes meaning. Quote the spec when in doubt.
- Do not assert on implementation details (private methods, internal class shapes); assert only on observable behavior a stakeholder could care about.
- If the spec has acceptance criteria already, reuse them verbatim and number them — do not invent new ones.
- If the diff implements behavior the spec does not mention, the case must be labeled `SPEC_DRIFT` and flagged in Open Questions.

## Optional

- Suggest a small example data set (table) that exercises the happy + boundary cases together.
- Suggest where each case should live (existing acceptance/E2E test file, or new file) based on project layout in the diff and context.

Begin now. Output the Spec Coverage Map, then Open Questions, then the Gate Verdict block, then the Acceptance Test Case List, in that order.
