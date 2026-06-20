# Test Case Output Format

This skill renders a prompt; the LLM then produces the actual test cases. To keep downstream tooling stable (pytest conversion, TMS upload, traceability), the prompt enforces a strict markdown shape.

## Common shape

Every rendered output, regardless of focus, includes four top-level sections in this order:

1. **Change Summary / Spec Coverage Map** — what changed and which spec items are covered.
2. **Traceability / Open Questions** — explicit list of uncovered requirements or spec drift.
3. **Gate Verdict block** — three lines, ending with `Skip line-by-line review if all cases pass? YES | NO — <reasons>`. This is the load-bearing signal for the reviewer.
4. **Test Case List** — the actual cases, one per `### TC-NN` or `### AC-NN` heading.

Treat each `###` heading as the start of a case. Anything between two case headings is the body of the preceding case.

### Gate Verdict semantics

The verdict says whether passing every generated case is sufficient evidence to skip line-by-line review of the MR. It is `NO` whenever any of the following hold:

- A row in the traceability matrix is `UNCOVERED`, `MISSING`, or `Partial`.
- Any case is labeled `SPEC_DRIFT` or `derived from diff only — spec gap`.
- Any case lists a fixture under `Preconditions / Fixtures` as `MISSING — please confirm or create`.
- The diff was budget-trimmed and the omitted files include source files (not just lockfiles or generated assets).

The reviewer relies on this verdict. Do not soften it to keep the output looking complete.

## Field semantics

| Field                          | Required | Meaning                                                                  |
|-------------------------------|----------|--------------------------------------------------------------------------|
| `Type`                        | yes      | One of: integration, acceptance, regression, negative, boundary          |
| `Priority`                    | yes      | P0 / P1 / P2                                                             |
| `Source > Spec`               | yes      | Spec section reference; `n/a` only when no spec was provided             |
| `Source > Diff`               | yes      | File path and line range or hunk identifier                              |
| `Preconditions / Fixtures`    | yes      | Bullet list; `MISSING — please confirm or create` allowed                |
| `Inputs`                      | yes      | Named input → value; one bullet per input                                |
| `Action`                      | yes      | Exactly one observable trigger                                           |
| `Expected`                    | yes      | One bullet per assertion                                                 |
| `Side-effects to verify`      | optional | DB / queue / log / downstream call assertions                            |
| `Out of scope / Not asserted` | yes      | What this case deliberately does not cover                               |
| `Risks if this case fails`    | yes      | One line, plain language                                                 |
| `Pytest skeleton`             | yes      | Fenced python block, ready to drop into a test file                      |

Acceptance cases (`AC-NN`) replace `Inputs / Action / Expected` with `Given / When / Then / And`, but the other fields stay the same.

## What "evidence-based" means here

If a case asserts behavior, that behavior must be traceable to either:

- a quoted line or section in the supplied design spec, or
- a specific hunk in the MR diff payload.

The prompts forbid invented behavior. If the LLM does not have evidence for a claim, it must label the case `UNKNOWN` or `derived from diff only — spec gap` rather than guessing.

This is the same discipline `gitlab-mr-review` applies to review findings, applied here to test case design.

## Round structure

This skill is intentionally single-focus per round, like `gitlab-mr-review`:

- One run per focus (`integration` or `acceptance`).
- If you need both, run twice and concatenate.
- Do not pad cases to hit a number — fewer well-grounded cases beat many shallow ones.

## Downstream consumers

- **Engineer converting to pytest**: see `pytest-conversion.md` — there is a 1:1 mapping for every markdown field.
- **TMS upload**: the `### TC-NN: <title>` heading becomes the case title; `Type` + `Priority` map to the corresponding TMS fields; `Source` and `Risks if this case fails` populate the description.
- **Reviewer doing quality assurance**: scan the Traceability Matrix / Spec Coverage Map first to spot `UNCOVERED` and `SPEC_DRIFT` rows; those are where the AI-written MR is most likely to be wrong.

## When the prompt under-produces

If the rendered output has very few cases or many `UNKNOWN` entries, it usually means:

- Spec is thin → supply richer `--spec` content. If you passed a URL that the script could only embed as a reference, export the page to a local file (Markdown or text) and pass that local file with `--spec`.
- Diff is truncated by budget → raise `--max-diff-chars` or `--max-files`, or run twice with different focus.
- Change is small and boring → fewer cases is the correct outcome, not a defect.

If the Gate Verdict is `NO`, treat the listed reasons as your line-by-line review checklist instead of trying to force the verdict to `YES`.
