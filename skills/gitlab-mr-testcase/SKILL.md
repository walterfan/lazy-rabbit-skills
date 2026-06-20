---
name: gitlab-mr-testcase
description: >-
  Generate structured test cases (integration or acceptance) for a GitLab Merge
  Request by combining the MR diff with a design spec (local path, URL, or
  auto-discovered from a Jira issue) and an optional Jira reference. Each case
  ships with a thin pytest skeleton plus a Gate Verdict block. The rendered
  prompt is written into ./tests/, ./test/, or the current folder. Purpose: a
  quality gate — when all generated cases pass, the reviewer can ship an
  AI-written MR without reading it line by line; when any case fails, the
  failing case points at the exact code path that still needs human review.
  After the AI fills in the prompt, an optional companion script posts the
  summary, traceability matrix, and gate verdict back to the MR as a comment.
  The skill is self-contained — MR/diff/project-context helpers are vendored
  under `lib/`, so it no longer requires `gitlab-mr-review` to be installed.
version: 0.5.0
author: walterfan@ustc.edu
tags:
  - gitlab
  - merge-request
  - test-cases
  - pytest
  - acceptance-testing
  - integration-testing
category: dev-tools
platforms:
  - codex
  - claude-code
  - cursor
visibility: public
license: Apache-2.0
compatibility: >-
  Python 3.8+. Self-contained — the MR/diff/project-context helpers it needs are
  vendored under `lib/` (see `lib/SOURCES.md`). GitLab token required for remote
  MR mode; `--local-diff` mode works without a token.
metadata:
  author: walter.fan
  version: "0.5.0"
allowed-tools: Bash(python3:*) Read Write
---

# GitLab MR Testcase

Generate test cases for a GitLab Merge Request so a reviewer can validate the change through a passing test gate instead of reading every line. Built for the case where the MR was written by an AI agent and the human reviewer needs leverage rather than line-by-line scrutiny.

## Purpose: a quality gate, not coverage theater

The skill is designed around one decision:

> **If every generated test case passes, the reviewer can ship the MR without line-by-line review. If any case fails, the failing case points directly at the code path that still needs human inspection.**

For that gate to mean anything, the generated cases must trace exhaustively back to the **design spec** (every requirement covered) and to the **MR diff** (every behavior change covered). The skill therefore requires a design spec, and the rendered prompt forces the model to emit a **Gate Verdict block** that explicitly answers _"Skip line-by-line review if all cases pass?"_. The verdict turns to `NO` whenever coverage is partial, the spec and diff disagree, or any case depends on a fixture that does not exist — telling the reviewer to fall back to reading the relevant code.

## Contract

- `scope_in`:
  - **Generate** (default): Render one test-case generation prompt for one MR (or one local diff) with one test focus (`integration` or `acceptance`), combined with a **design spec** that comes from either (a) explicit `--spec PATH_OR_URL` arguments, or (b) auto-discovery from a `--jira-issue` when Jira credentials are configured. The prompt is consumed by the calling AI agent, which produces the actual structured test cases. The rendered prompt is **written to a markdown file** under `./tests/`, `./test/`, or the current folder.
  - **Post comment** (companion script): After the AI fills in the prompt and saves the result, post a comment on the MR containing only the Change Summary / Spec Coverage Map, the Traceability Matrix, and the Gate Verdict block — extracted by heuristic from the filled-in markdown. The full test case list stays in the file and is referenced via a footer link.
- `scope_out`:
  - Running the tests (this skill generates them; running them is the reviewer's step).
  - Writing pytest files into the target repo.
  - Auto-fetching design specs that need authentication beyond Jira (Confluence pages that require user-context login, a collaborative doc platform UI). The skill best-effort fetches plain http(s) URLs; for those auth-protected sources, manually export the page to a local file (Markdown or text) and pass it with `--spec`.
  - Creating test-management or Jira tickets from the generated cases (route to your test-management system's import tooling).
  - GitHub pull requests.
- `Preconditions`:
  - The vendored helpers under `lib/` ship with this skill (see `lib/SOURCES.md`). No sibling skill is required.
  - The user supplies an MR reference (URL, `namespace/project!iid`, or plain IID with project context) or asks for `--local-diff`.
  - The user supplies **either** at least one `--spec PATH_OR_URL` **or** a `--jira-issue` together with `JIRA_API_TOKEN` + `JIRA_USER_EMAIL` env vars set. Otherwise the script exits with `design spec is required`.
  - `GITLAB_TOKEN` is set for the GitLab API mode; not required for `--local-diff`.
- `Postconditions`: The skill writes one rendered prompt to a markdown file (path printed to stdout) for one test focus. The prompt forbids inventing behavior beyond the supplied evidence and forces the model to emit a Gate Verdict block stating whether passing the generated cases is sufficient to skip line-by-line review.

## Required Inputs

### Per-invocation arguments

| Input | Status | How to pass | Notes |
|---|---|---|---|
| Merge Request reference | **required** (unless `--local-diff`) | positional arg | MR URL, `namespace/project!iid`, or plain IID with project context |
| Design spec | **required** (one of two ways) | `--spec PATH_OR_URL` (repeatable; `--spec-file PATH` legacy alias) **or** `--jira-issue KEY_OR_URL` + Jira env vars | Local files read verbatim; URLs best-effort fetched. When `--spec` is omitted, the Jira issue description (and any spec-looking URLs in it) become the spec sources |
| Jira issue | optional for traceability, **required when spec is auto-discovered** | `--jira-issue KEY_OR_URL` | Accepts `PROJ-1234` or a full Jira `/browse/<KEY>` URL. Embedded in the prompt as traceability either way; when paired with Jira env vars and no `--spec`, it also drives spec auto-discovery |

### Spec resolution order

The script merges spec sources in this order:

1. If `--jira-issue` is provided and `--spec` is **not**, and `JIRA_API_TOKEN` + `JIRA_USER_EMAIL` are both set: fetch the Jira issue via the Atlassian REST API and add (a) its description as a `Spec (jira-description)` source, and (b) any URLs in the description whose host matches a known design-doc host (Confluence wiki, your GitLab host, configurable via `SPEC_URL_HOST_HINTS`) as `Spec (URL (via Jira))` sources, fetched best-effort.
2. Any explicit `--spec PATH_OR_URL` (and `--spec-file`) values are appended.
3. If after both steps no sources resolved, exit with the `design spec is required` error.

URLs that fail to fetch (HTML, 4xx/5xx, auth wall) are embedded as reference-only with a note advising you to pre-download/export the page to a local file (Markdown or text) and pass it with `--spec`. The same fallback applies whether the URL came from `--spec` or from Jira.

### Environment

- `GITLAB_TOKEN`
  Required for remote MR mode. Not required for `--local-diff`.
- `GITLAB_URL` or `GITLAB_BASE_URL` (legacy alias)
  Optional. Defaults to `https://gitlab.example.com`.
- `GITLAB_PROJECT` or `GITLAB_PROJECT_ID`
  Optional fallback when the user gives a plain numeric MR IID without project context.
- `GITLAB_NO_SSL_VERIFY`
  Optional. Set to `1`, `true`, `yes`, or `on` **only** after the user explicitly agrees to disable SSL verification for a self-signed GitLab certificate.
- `JIRA_API_TOKEN` (or legacy `JIRA_TOKEN`)
  Required for Jira-driven spec auto-discovery. Create an Atlassian API token at <https://id.atlassian.com/manage-profile/security/api-tokens>.
- `JIRA_USER_EMAIL` (or legacy `JIRA_USER`)
  Required for Jira-driven spec auto-discovery. The email address tied to your Atlassian account.
- `JIRA_BASE_URL`
  Optional. Defaults to `https://your-org.atlassian.net`. Override only if you target a different Atlassian Cloud tenant.

The GitLab token needs the `api` scope (read+write — write is only required for the optional `post_mr_comment.py` step). If the `gitlab-mr-review` skill is also installed, [`../gitlab-mr-review/references/token-setup.md`](../gitlab-mr-review/references/token-setup.md) has a step-by-step setup guide; otherwise use the standard GitLab personal-access-token UI.

## Execution

### Phase 1: Resolve the change under test

- Entry: The user asks for test cases for a specific MR (or local diff).
- Steps:
  1. Confirm the MR reference format or `--local-diff` mode.
  2. Resolve project context from explicit flags, environment variables, or the local `origin` remote (via the vendored helpers in `lib/`).
  3. Pick exactly one test focus for this round; default to `integration`.
- Exit: One MR or one local diff source is selected and one test focus is chosen.
- On fail: Stop and ask for the missing MR reference, project, or test focus instead of guessing.

### Phase 2: Resolve the design spec evidence

- Entry: Phase 1 completed.
- Steps:
  1. If the user passed any `--spec PATH_OR_URL`, validate each source:
     - Local path → confirm the file exists.
     - URL → the script will try a best-effort fetch (15s timeout, 60 KB cap). HTML / 4xx / 5xx falls back to a reference-only embed.
  2. If the user passed `--jira-issue` and **no** `--spec`:
     - Check that `JIRA_API_TOKEN` + `JIRA_USER_EMAIL` are set.
     - If they are not, surface the limitation and ask the user to either set the env vars or pass `--spec` directly.
     - If they are set, the script fetches the Jira issue via REST API v3, embeds the description as a `Spec (jira-description)` source, and tries to fetch any spec-looking URLs found inside it as additional sources.
  3. If neither `--spec` nor a Jira-discoverable source is available, stop. The quality gate has no anchor.
- Exit: One or more spec sources resolved (with content or as references).
- On fail: Stop and ask for a usable spec input.

### Phase 3: Collect Jira reference (always, when provided)

- Entry: Phase 1 completed.
- Steps:
  1. If `--jira-issue KEY_OR_URL` is set, validate it (issue key like `PROJ-1234`, or a URL containing `/browse/<KEY>`).
  2. The normalized key + URL is embedded in the prompt under `### Jira Issue` for traceability — regardless of whether spec auto-discovery ran.
- Exit: Jira reference normalized or skipped.
- On fail: Surface the invalid value and ask for correction.

### Phase 4: Render the test-case prompt

- Entry: Phases 1–3 completed.
- Steps:
  1. Run `scripts/generate_testcases.py` with the resolved target, focus, spec sources, and optional Jira issue.
  2. Apply SSL / project-root options only when needed.
  3. Read the rendered prompt or error output.
- Exit: A test-case generation prompt is rendered, including a Gate Verdict requirement.
- On fail: Follow the error table below; never silently retry with `--no-ssl-verify`.

### Phase 5: Persist the rendered prompt

- Entry: Phase 4 completed.
- Steps:
  1. By default, the script picks an output path in this order: `./tests/<name>.md` (if `./tests` exists), else `./test/<name>.md` (if `./test` exists), else `./<name>.md`.
  2. The filename is `<jira-key>-<focus>-testcases.md` when a Jira key is known, else `mr-<iid>-<focus>-testcases.md`, else `local-<timestamp>-<focus>-testcases.md`.
  3. The chosen path is printed on stdout as `Wrote: <path>` so the calling agent can read it for the next step.
  4. `--output-file PATH` overrides the auto-picked path. `--output-dir DIR` overrides only the directory. `--stdout` prints to stdout instead of writing a file.
- Exit: A markdown file containing the rendered prompt (or its content on stdout when `--stdout` is set).

### Phase 6: Deliver the generated cases and the gate verdict

- Entry: Phase 5 completed; rendered prompt is on disk (or stdout).
- Steps:
  1. Feed the rendered prompt into the model and produce structured test cases following the exact format from the prompt template.
  2. Save the AI's filled-in output back to the same path the prompt was rendered to (or to a new file). This is what Phase 7 will read.
  3. Render the **Gate Verdict block** literally. Do not soften it — its purpose is to tell the human reviewer whether passing tests are enough to skip line-by-line review.
  4. Highlight any rows marked `UNCOVERED`, `SPEC_DRIFT`, `MISSING`, `BLOCKED`, or `UNKNOWN`. Those are the high-value findings the reviewer must look at manually even if the rest of the suite passes.
  5. If the user wants both integration and acceptance coverage, run another round with a different `--test-focus`.
- Exit: A filled-in test cases markdown file exists on disk, with explicit traceability to spec sections or diff hunks and a `YES | NO` gate verdict.
- On fail: State the limitation (truncated diff, partial spec coverage, ambiguous behavior) rather than padding with shallow cases. A weak verdict is more useful than a strong one that is wrong.

### Phase 7: Post the summary and matrix as an MR comment (optional)

- Entry: Phase 6 completed; the filled-in test cases markdown is on disk.
- Steps:
  1. Run `scripts/post_mr_comment.py` against the MR with `--file PATH` pointing at the filled-in markdown.
  2. The script extracts only the Change Summary / Spec Coverage Map, the Traceability Matrix / Open Questions, and the Gate Verdict block. The full test case list is left out of the comment but the footer links to the file.
  3. The default behavior posts immediately. Use `--dry-run` first if you want to preview the comment body locally before sending.
  4. Skip this phase entirely when the user only wants local artifacts or when there is no MR to comment on (e.g., `--local-diff` was used in Phase 1).
- Exit: A note appears on the MR (or the dry-run preview is printed). The script prints the posted note's MR URL.
- On fail: Token, permission, or extraction failures are surfaced with actionable messages. The cases file remains intact for retry.

## Workflow

1. Confirm the MR reference format.
   Preferred input is a full Merge Request URL.
   Also supported: `namespace/project!123`, `123 --project namespace/project`, or plain `123`.

2. Pick exactly one test focus for this round.
   - `integration` (default) — cross-component pytest-style cases.
   - `acceptance` — stakeholder-facing Given/When/Then cases tied to the design spec.

3. Resolve the design spec source. Required. Local file is the most reliable path; for Jira / Confluence / a collaborative doc platform, manually export the doc to a local file (Markdown or text) and pass it with `--spec`. Plain http(s) URLs are best-effort fetched and otherwise embedded as references.

4. Optional: pass a Jira issue for traceability.

5. Render the prompt. The most common path — auto-discover spec from the Jira issue, write into `./tests/`:

```bash
export JIRA_API_TOKEN="..."
export JIRA_USER_EMAIL="you@example.com"
python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py "<merge-request-url-or-ref>" \
  --test-focus integration \
  --jira-issue PROJ-1234
# → Wrote: ./tests/PROJ-1234-integration-testcases.md
```

Explicit spec(s), Jira optional for traceability:

```bash
python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py "<merge-request-url-or-ref>" \
  --test-focus integration \
  --spec /abs/path/to/design-spec.md \
  --jira-issue PROJ-1234
```

Combine multiple specs (any mix of paths and URLs):

```bash
python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py "<merge-request-url-or-ref>" \
  --test-focus integration \
  --spec /abs/path/to/feature-spec.md \
  --spec /abs/path/to/api-contract.md \
  --spec https://example.com/public-rfc.md
```

To review local changes before pushing an MR:

```bash
python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py \
  --local-diff \
  --test-focus integration \
  --spec /absolute/path/to/design-spec.md \
  --project-root /absolute/path/to/target-project
```

For acceptance cases, run a separate round:

```bash
python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py "<merge-request-url-or-ref>" \
  --test-focus acceptance \
  --jira-issue https://your-org.atlassian.net/browse/PROJ-1234
```

Override the output directory, or pipe to stdout instead of writing a file:

```bash
# Explicit path
python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py "<...>" \
  --jira-issue PROJ-1234 --output-file ./my-tests/cases.md

# Explicit directory, auto-pick the filename
python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py "<...>" \
  --jira-issue PROJ-1234 --output-dir ./qa

# Old behavior: print to stdout
python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py "<...>" \
  --jira-issue PROJ-1234 --stdout
```

For a fully custom prompt rubric, pass `--prompt-file`:

```bash
python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py "<merge-request-url-or-ref>" \
  --prompt-file /absolute/path/to/custom-testcase-template.md \
  --spec /abs/path/to/spec.md
```

### Optional: post the summary and matrix back to the MR

After the AI fills in the prompt and saves the result, post a focused comment to the MR with just the high-signal sections:

```bash
# Preview first (no API call)
python3 skills/gitlab-mr-testcase/scripts/post_mr_comment.py \
  "<merge-request-url-or-ref>" \
  --file ./tests/PROJ-1234-integration-testcases.md \
  --dry-run

# Then post
python3 skills/gitlab-mr-testcase/scripts/post_mr_comment.py \
  "<merge-request-url-or-ref>" \
  --file ./tests/PROJ-1234-integration-testcases.md
```

Pipe the AI's output directly via stdin (no intermediate file):

```bash
<AI-output-producer> | \
python3 skills/gitlab-mr-testcase/scripts/post_mr_comment.py \
  "<merge-request-url-or-ref>" \
  --stdin --footer-link ./tests/PROJ-1234-integration-testcases.md
```

Override the heading or skip extraction (post the whole file verbatim — use sparingly):

```bash
python3 skills/gitlab-mr-testcase/scripts/post_mr_comment.py \
  "<merge-request-url-or-ref>" \
  --file ./tests/PROJ-1234-acceptance-testcases.md \
  --header "Acceptance gate — PROJ-1234" \
  --full-file
```

Extraction rules:
- The comment body starts at the first ATX heading (`#`, `##`, or `###`) whose text contains "Change Summary" or "Spec Coverage Map" (case-insensitive).
- It stops just before the first heading that looks like a case entry (`### TC-N` / `### AC-N`) or a "Test Case List" / "Acceptance Test Case List" heading.
- If extraction finds no start heading, the script exits non-zero and asks the user to either fix the heading structure or pass `--full-file`.
- If the extracted block does not contain a `Skip line-by-line review` verdict line, the script still posts but adds an "Extraction notes" callout so the reviewer knows the AI may have skipped the verdict.

If your GitLab host fails SSL verification because of a self-signed certificate, **ask the user first**, and only then retry:

```bash
export GITLAB_NO_SSL_VERIFY=1
python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py "<merge-request-url-or-ref>" \
  --test-focus integration \
  --spec /abs/path/to/spec.md
```

If the script exits non-zero, read stderr and apply the first matching case:

| Error pattern                                                       | Cause                                                                | Action                                                                                          |
|---------------------------------------------------------------------|----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `401` or `403`                                                      | Token missing, invalid, or expired                                   | Confirm `GITLAB_TOKEN` is set and has the `api` scope; the sibling `gitlab-mr-review` skill (if installed) has a step-by-step setup guide |
| `SSL verification failed`                                           | Self-signed certificate                                              | Ask user consent, then retry with `GITLAB_NO_SSL_VERIFY=1`                                      |
| `No tracked changes`                                                | `--local-diff` found no staged or unstaged changes                   | Ask user to stage changes or check branch                                                       |
| `Project mismatch`                                                  | Local checkout does not match MR project                             | Use `--project-root` or `--skip-project-match-check`                                            |
| `Could not determine project`                                       | No `GITLAB_PROJECT` and no git remote                                | Ask user for `--project namespace/project`                                                      |
| `design spec is required`                                           | No `--spec`, and no usable Jira-driven spec                          | Pass `--spec PATH_OR_URL`, or pass `--jira-issue` + set `JIRA_API_TOKEN` + `JIRA_USER_EMAIL`     |
| `spec source not found`                                             | `--spec` points at a missing local path                              | Ask user to verify the path                                                                     |
| `invalid --jira-issue value`                                        | Jira input was neither an issue key nor a URL containing `/browse/`  | Ask user for a valid `KEY` or full Jira URL                                                     |
| stderr note `JIRA_USER_EMAIL and JIRA_API_TOKEN are not both set`   | `--jira-issue` was given without env vars, and no `--spec` was given | Set the env vars, or pass `--spec` explicitly                                                   |
| `Jira fetch failed for <KEY>: HTTP 401`                             | Jira token invalid or wrong account                                  | Recreate the Atlassian API token; confirm the email matches the token owner                     |
| `Jira fetch failed for <KEY>: HTTP 404`                             | Issue key does not exist or your account cannot see it               | Confirm the key; check Jira permissions                                                         |
| URL embedded as reference only (no exception, but `Notes:` in prompt) | Auto-fetch hit HTML / auth-protected / non-text response             | Tell user to export the page to a local file (Markdown or text) and re-run with the local path  |
| `unsupported test focus`                                            | Unknown `--test-focus` value                                         | Re-run with `integration` or `acceptance`; or pass `--prompt-file`                              |
| `Vendored helpers not found at .../lib`                             | The skill's `lib/` directory is missing                              | Re-install this skill; the `lib/` directory ships with it (see `lib/SOURCES.md`)                |
| `input file not found` (post step)                                  | `--file` points at a missing path                                    | Verify the AI saved its output to the expected location                                         |
| `No summary/matrix block found` (post step)                         | AI output lacks a "Change Summary" / "Spec Coverage Map" heading     | Re-run the AI step so it follows the prompt structure, or use `--full-file`                     |
| `Failed to post MR comment: HTTP 401/403` (post step)               | GitLab token missing the `api` scope (write)                         | Issue a token with `api` scope, not just `read_api`                                             |
| `Failed to post MR comment: HTTP 404` (post step)                   | Project / MR IID resolution failed                                   | Verify the MR reference; for plain IIDs pass `--project namespace/project`                      |
| Other traceback                                                     | Unexpected error                                                     | Print the full error and stop                                                                   |

## Output Modes

`--format prompt|bundle|summary|diff|spec`

- `prompt` (default): the rendered test-case generation prompt. This is what you feed to the model.
- `bundle`: MR review context (project, scope, summary, diff) without the test-case prompt — useful for debugging the budget.
- `summary`: just the MR summary table.
- `diff`: just the budgeted MR diff.
- `spec`: just the collected spec content (after per-file and total truncation).

The diff budget defaults (defined in the vendored `lib/review_mr.py`):

- `--max-files` defaults to `20`
- `--max-changed-lines` defaults to `1200`
- `--max-diff-chars` defaults to `50000`
- Generated files are skipped unless `--include-generated` is passed

Spec sources are capped per source (60 KB) and in total (120 KB) to keep the prompt small. Any truncation, URL fetch failure, or auth-protected fallback is noted in the rendered `Spec ingestion status` line so the model and the user both see it.

URL fetching is intentionally simple: a 15-second GET with no per-host auth. HTML responses are treated as auth walls and embedded as reference-only — the rendered prompt makes that visible to both the model and the human reviewer.

## Built-In Test Focuses

- `integration` — Cross-component pytest cases. Each case has a single observable Action / Expected pair plus side-effect assertions (DB row, queue message, log line, downstream call). The rendered cases include a pytest skeleton with `@pytest.mark.integration` and `@pytest.mark.parametrize`.
- `acceptance` — Stakeholder-facing Given/When/Then cases anchored to the design spec. Each case carries a thin pytest skeleton with `@pytest.mark.acceptance`. Failure modes include `SPEC_DRIFT` when the diff diverges from the spec.

Aliases accepted: `pytest`, `integration-test`, `integration_tests` → `integration`; `atc`, `bdd`, `acceptance-test`, `acceptance_tests` → `acceptance`.

Run each focus as a separate round. Do not mix them in one prompt.

## Prompt Template Support

The built-in prompts live in [assets/prompts](assets/prompts). `--prompt-file` overrides `--test-focus` when both are provided.

Custom prompt files can use these placeholders (inherited from the vendored `review_mr.py` plus the test-focused ones):

- `{{language}}`
- `{{code}}`
- `{{bundle}}`
- `{{review_focus}}` (mirrors `test_focus` for compatibility)
- `{{review_scope}}`
- `{{project_context}}`
- `{{local_code_context}}`
- `{{project_name}}`
- `{{project_languages}}`
- `{{project_frameworks}}`
- `{{project_stack}}`
- `{{project_background}}`
- `{{mr_title}}`
- `{{mr_description}}`
- `{{mr_summary}}`
- `{{mr_diff}}`
- `{{spec_content}}` — concatenated spec sources, each prefixed by `### Spec (<kind>): <label>` where `<kind>` is `file`, `URL`, `jira-description`, or `URL (via Jira)`. Sources that could not be fetched appear as `### Spec reference (<kind>, not fetched): <label>` with an explicit note.
- `{{spec_paths}}` — comma-separated labels of loaded spec sources (paths, URLs, or `jira:<KEY>`)
- `{{spec_status}}` — short status line (loaded count, any truncation, fetch-fallback, or Jira-discovery notes)
- `{{jira_issue_reference}}` — Jira issue traceability block (key + URL) or a one-line "no Jira issue supplied" note
- `{{jira_issue_key}}` / `{{jira_issue_url}}` — empty string when no Jira issue was passed
- `{{test_focus}}` — normalized focus (`integration` or `acceptance`)

Read [references/test-case-format.md](references/test-case-format.md) for the expected output structure and [references/pytest-conversion.md](references/pytest-conversion.md) for the markdown → pytest mapping.

## Verification

### Hard gates

- **Target validity**: The input resolves to exactly one MR or one local diff source. On fail, stop and ask for a resolvable target.
- **Spec required**: At least one `--spec` source resolves successfully (content or reference). On fail, stop and ask — the quality gate has no anchor without a spec.
- **Single focus per round**: The output covers one test focus only. On fail, run separate rounds.
- **Evidence-bound cases**: Every generated case cites either a spec section or a diff hunk. Cases without evidence are labeled `UNKNOWN` or `derived from diff only — spec gap`. On fail, drop or relabel the case.
- **Gate Verdict block present**: The rendered output contains the literal `Skip line-by-line review if all cases pass?` line with `YES` or `NO` (with reasons). On fail, regenerate the response. The verdict is the whole point of the skill.
- **Error transparency**: Auth, SSL, project mismatch, missing spec, invalid Jira input, or empty diff failures are reported with the matching remediation. On fail, surface the concrete blocker.
- **Pytest skeleton present**: Each case includes a runnable pytest skeleton. On fail, regenerate that case rather than ship it without a skeleton.

### Soft gates

- **Budget transparency**: When file or diff limits trimmed coverage, the response mentions it.
- **URL fallback transparency**: When a spec URL could not be fetched, the response says so and advises exporting the page to a local file (Markdown or text) to pass with `--spec`.
- **Coverage matrix included**: A traceability matrix (integration) or spec coverage map (acceptance) appears before the case list.
- **Concision**: Fewer well-grounded cases beat many shallow ones. Do not pad to hit a target N.
- **Posted comment matches the file**: When Phase 7 runs, the dry-run preview should be inspected if the AI's filled-in markdown diverges from the prompt template structure (otherwise the extracted block may miss the Gate Verdict).

## When Not to Use

| Scenario                                                                  | Route                                                            |
|--------------------------------------------------------------------------|------------------------------------------------------------------|
| Reviewing the MR line by line for correctness / security / etc.           | Use `gitlab-mr-review`                                           |
| MR is so large that even reviewing the diff is impractical                | Use `gitlab-mr-split` first, then this skill on each sub-MR      |
| Generating acceptance tests from a design spec without any MR diff        | Generate acceptance tests directly from the design spec          |
| Uploading test cases into a test-management system                        | Use your test-management system's import tooling                 |
| GitHub pull requests                                                      | Out of scope                                                     |
| Non-code review                                                           | Out of scope                                                     |

## Boundary Cases

| Input / situation                                            | Expected behavior                                                                                  |
|--------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| MR with 0 changed files                                      | Stop and tell the user there is no diff to test                                                    |
| MR with 500+ files                                           | Budget limits select top 20; coverage matrix lists what was omitted; gate verdict likely `NO`      |
| No `--spec` and no `--jira-issue`                            | Stop with the `design spec is required` error                                                      |
| `--spec` is a missing local path                             | Stop, report the path                                                                              |
| `--spec` is a URL that returns HTML / 4xx / 5xx              | Embed URL as reference only; status line and rendered prompt make the fallback visible             |
| `--spec` URL exceeds 60 KB                                   | Truncate with a note in the status line                                                            |
| Multiple `--spec` sources exceed 120 KB total                | Truncate or skip the trailing ones with a note                                                     |
| `--jira-issue` is a bare key like `PROJ-1234`             | Normalize to the key plus the inferred `/browse/<KEY>` URL                                         |
| `--jira-issue` is a full URL                                 | Extract the key when present; embed the URL                                                        |
| `--jira-issue` is junk                                       | Stop with the `invalid --jira-issue value` error                                                   |
| `--jira-issue` set, no `--spec`, but Jira env vars missing   | Skip auto-discovery, print a stderr note, then exit with `design spec is required` until env vars set or `--spec` passed |
| `--jira-issue` set, no `--spec`, Jira fetch succeeds         | Use the issue description as the spec, plus any spec-host URLs extracted from it; status line lists all sources |
| `--jira-issue` set, no `--spec`, Jira fetch returns 401/404  | Stop with the `Jira fetch failed` error and the HTTP code                                          |
| `--jira-issue` set, Jira description is empty                | Skip the description source; fall back to URLs from the description if any; otherwise the `design spec is required` error |
| `./tests/` and `./test/` both absent                         | Write to the current directory (or `--project-root`); print the path                               |
| `--output-file` provided                                     | Honor it exactly; create parent directories as needed                                              |
| `--stdout` provided                                          | Print to stdout, do not write a file                                                               |
| Post comment from a `--local-diff` run                       | Skip Phase 7 — no MR exists to comment on                                                          |
| AI saves filled-in cases to a different path than the prompt | Pass that path as `--file` to `post_mr_comment.py`                                                 |
| AI omits the Gate Verdict line                               | `post_mr_comment.py` still posts and adds an "Extraction notes" callout so the reviewer notices    |
| Diff implements behavior the spec does not mention           | Acceptance prompt labels those cases `SPEC_DRIFT`; integration prompt notes them in Change Summary; gate verdict turns `NO` |
| Change is small (1 file, <50 lines)                          | Prompt may produce <3 cases; that is acceptable, do not pad                                        |
| MR already merged                                            | Test case generation still works; treat output as post-hoc QA                                      |
| User asks for "all test types in one round"                  | Decline; run `integration` round, then `acceptance` round                                          |

## Feedback

### Failure modes

| Symptom                                                          | Root cause                                              | Fix                                                                                                |
|------------------------------------------------------------------|---------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `401` or `403` from GitLab API                                   | Missing or expired token                                | Direct user to token setup; retry after setting `GITLAB_TOKEN`                                     |
| SSL verification failure                                         | Self-signed GitLab cert                                 | Ask consent, then retry with `GITLAB_NO_SSL_VERIFY=1`                                              |
| `design spec is required`                                        | No usable spec source                                   | Pass `--spec`, or pass `--jira-issue` + set `JIRA_API_TOKEN` + `JIRA_USER_EMAIL`                    |
| `spec source not found`                                          | Bad `--spec` local path                                 | Verify path                                                                                        |
| Spec URL embedded as reference only                              | HTML / auth-protected / non-text response from URL      | Export the page to a local file (Markdown or text) and re-run with the local path                  |
| `invalid --jira-issue value`                                     | Jira input was not a key or `/browse/` URL              | Pass a key like `PROJ-1234` or a Jira URL containing `/browse/<KEY>`                            |
| `Jira fetch failed for <KEY>: HTTP 401`                          | Jira credentials wrong or expired                       | Recreate the Atlassian API token; confirm `JIRA_USER_EMAIL` matches the token owner                 |
| `Jira fetch failed for <KEY>: HTTP 404`                          | Issue key wrong, or your account lacks visibility       | Confirm the key; ask the project admin if needed                                                   |
| Jira auto-discovery skipped silently                             | Env vars missing                                        | Set `JIRA_API_TOKEN` and `JIRA_USER_EMAIL`, or pass `--spec` directly                              |
| Output appears in current dir when `./tests/` exists             | `./tests/` is not under the script's `--project-root`   | Use `--output-dir` to point at the right directory, or run from the project root                   |
| `No summary/matrix block found` from `post_mr_comment.py`        | AI did not follow the prompt heading structure          | Re-run the AI step, or post the whole file with `--full-file`                                       |
| Comment posted but missing the Gate Verdict line                 | AI omitted the verdict block                            | Re-run AI step; the comment carries an "Extraction notes" warning so reviewers see this happened     |
| `post_mr_comment.py` fails with 401/403                          | Token lacks `api` write scope                           | Issue a new GitLab token with `api` scope                                                            |
| `Vendored helpers not found at .../lib`                          | `lib/` directory missing from the install               | Re-install this skill; `lib/` ships with it (see `lib/SOURCES.md`)                                  |
| Gate Verdict is `NO` with `UNCOVERED` / `SPEC_DRIFT` / `MISSING` rows | Spec is thin, ambiguous, or out of sync with the diff | Treat the verdict as load-bearing — review the flagged paths line-by-line. Improve the spec for next round |
| Many cases marked `UNKNOWN` or `derived from diff only — spec gap`   | Spec is missing or thin                             | Supply richer `--spec` content; consider acceptance focus once spec is available                   |
| Many `MISSING — please confirm or create` fixtures               | Project lacks the necessary test infrastructure         | Treat as a follow-up; create the fixtures or refactor the production code to expose a test seam    |
| Generated cases are shallow or repetitive                        | Diff is small or one-shaped                             | Accept fewer cases; do not force the LLM to invent more                                            |

### Boundary examples

- GitLab MR URL or `namespace/project!iid` with a local spec file → valid input, this is the common path.
- Local diff with a local spec file → valid; used before opening the MR.
- Plain numeric MR IID without project context → blocked until `--project` is supplied or inferred.
- GitHub PR URL → out of scope.

### Improvement triggers

- Update this skill when new test focuses are added (for example, contract testing for a public API).
- Tighten the workflow if reviewers report that the generated cases miss recurring failure patterns (boundary parsing, auth, retries, idempotency) — adjust the prompt templates.
- Re-vendor `lib/gitlab_api.py` and `lib/review_mr.py` from the `gitlab-mr-review` skill when its diff budgeting, language detection, or project-context detection improves. The re-sync recipe and recorded upstream commit hashes are in `lib/SOURCES.md`. Run `python3 lib/check_sync.py` (or wire it into CI) to be notified when upstream has drifted; it exits non-zero if drift is detected and cleanly skips when the sibling skill is not installed.

## Notes

- Prefer `GITLAB_TOKEN` in the environment:

```bash
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
```

- This skill is **self-contained**: the MR/diff/project-context helpers are vendored under `lib/` (originally from `gitlab-mr-review`). See `lib/SOURCES.md` for the upstream commit hashes and re-sync recipe. There is no runtime dependency on a sibling skill being installed.
- The companion script `scripts/post_mr_comment.py` reuses `gitlab_api.post_merge_request_comment` (from the same vendored `lib/`) to post the focused summary. It does not invent any new API call.
- Run `python3 skills/gitlab-mr-testcase/scripts/generate_testcases.py --help` and `python3 skills/gitlab-mr-testcase/scripts/post_mr_comment.py --help` to see all available flags and defaults.
- The intent is leverage, not coverage theater: better to ship 5 well-grounded test cases that a reviewer can trust than 30 plausible-looking ones that nobody verifies.
