---
name: gitlab-mr-review
description: >-
  Review a GitLab Merge Request from a Merge Request URL, namespace/project!iid
  reference, or project-scoped MR IID. Fetches MR metadata and diffs through the
  GitLab API, then renders a focused review prompt from a markdown template.
  Use when a user wants MR review, code review from GitLab, merge request
  analysis, or a reusable GitLab review workflow that reviews one aspect per
  round.
version: 1.1.0
author: walterfan@ustc.edu
tags:
  - gitlab
  - merge-request
  - code-review
category: dev-tools
platforms:
  - codex
  - claude-code
visibility: public
license: Apache-2.0
compatibility: Python 3.8+. GitLab token required only for GitLab MR/API review mode; local-diff mode works without a token.
metadata:
  author: walter.fan
  version: "1.1.0"
allowed-tools: Bash(python3:*) Read Write
---

# GitLab MR Review

## Contract

- `scope_in`: Review one GitLab merge request or one local tracked diff using `scripts/review_mr.py`, with a single review focus per run.
- `scope_out`: GitHub pull requests, GitLab write actions such as approve/merge/comment, non-code document review, and multi-focus "review everything" prompts in one round.
- `Preconditions`: The user provides an MR URL/ref or asks for `--local-diff`; the target repository is available locally for repo-context features; `GITLAB_TOKEN` is set for GitLab API review mode.
- `Postconditions`: The skill produces one focused review prompt or findings set, preserves the selected scope, and explains any missing prerequisites or budget limits that affected coverage.

## Required Inputs

- `GITLAB_TOKEN`
  Required for GitLab MR review. Not required for `--local-diff`.
- `GITLAB_URL` or `GITLAB_BASE_URL` (legacy alias)
  Optional. Defaults to `https://gitlab.example.com` unless the MR URL already includes a GitLab host. `GITLAB_BASE_URL` is accepted as a legacy alias for `GITLAB_URL`.
- `GITLAB_PROJECT` or `GITLAB_PROJECT_ID`
  Optional fallback when the user gives a plain numeric MR IID without project context.
  If not set, the script will try `git remote -v` in the current project folder and parse the `origin` remote.
- `GITLAB_NO_SSL_VERIFY`
  Optional. Set to `1`, `true`, `yes`, or `on` only after the user explicitly agrees to disable SSL verification for a self-signed GitLab certificate.

If the user needs help creating a token, read [references/token-setup.md](references/token-setup.md).

## Execution

### Phase 1: Resolve review target

- Entry: The user asks for GitLab MR review or local diff review.
- Steps:
  1. Confirm the MR reference format or `--local-diff` mode.
  2. Resolve project context from explicit flags, environment variables, or the local `origin` remote.
  3. Pick exactly one review focus for this round; default to `correctness`.
- Exit: There is one valid review target and one explicit review angle.
- On fail: Stop and ask for the missing MR reference, project, or review focus instead of guessing.

### Phase 2: Render review prompt

- Entry: Phase 1 completed.
- Steps:
  1. Run `scripts/review_mr.py` with the selected target and focus.
  2. Apply SSL and project-root options only when needed.
  3. Read the rendered prompt or error output.
- Exit: A prompt, bundle, summary, or diff is available for the requested mode.
- On fail: Follow the mapped error action below; if the failure is unmapped, surface the stderr and stop.

### Phase 3: Deliver focused review

- Entry: Phase 2 completed.
- Steps:
  1. Read the rendered prompt and diff context.
  2. Produce findings only for the chosen review aspect.
  3. If the user wants broader coverage, run a separate round for the next focus.
- Exit: The response contains one coherent review pass with no mixed review scopes unless the user explicitly requested that.
- On fail: Fall back to reporting the script limitation or missing context rather than inventing findings.

## Workflow

1. Confirm the MR reference format.
   Preferred input is a full Merge Request URL.
   Also supported: `namespace/project!123`, `123 --project namespace/project`, or plain `123`.
   For plain `123`, the script first uses `GITLAB_PROJECT` if present, otherwise it runs `git remote -v` and extracts the project from the `origin` remote.
2. Pick exactly one review aspect for this round.
   Use a built-in focus such as `correctness`, `security`, `performance`, or `maintainability`.
   If the user does not specify a focus, start with `correctness`.
3. Fetch the MR summary and diff with:

```bash
python3 skills/gitlab-mr-review/scripts/review_mr.py "<merge-request-url-or-ref>" \
  --review-focus correctness
```

If your GitLab host fails SSL verification because it uses a self-signed certificate, do not disable verification silently. Ask the user first, and only if they agree retry with:

```bash
python3 skills/gitlab-mr-review/scripts/review_mr.py "<merge-request-url-or-ref>" \
  --no-ssl-verify
```

Or set:

```bash
export GITLAB_NO_SSL_VERIFY=1
```

If the script exits non-zero, read stderr and apply the first matching case:

| Error Pattern | Cause | Action |
|---------------|-------|--------|
| `401` or `403` | Token missing, invalid, or expired | Direct user to [references/token-setup.md](references/token-setup.md) |
| `SSL verification failed` | Self-signed certificate | Ask user consent, then retry with `--no-ssl-verify` |
| `No tracked changes` | `--local-diff` found no staged/unstaged changes | Ask user to stage changes or check branch |
| `Project mismatch` | Local checkout doesn't match MR project | Use `--project-root` or `--skip-project-match-check` |
| `Could not determine project` | No GITLAB_PROJECT and no git remote | Ask user for `--project namespace/project` |
| Other traceback | Unexpected error | Print full error and ask user to report |

If you are reviewing a different repository, point the skill at that checkout:

```bash
python3 /absolute/path/to/skills/gitlab-mr-review/scripts/review_mr.py "<merge-request-url-or-ref>" \
  --review-focus correctness \
  --project-root /absolute/path/to/target-project
```

If the user wants to review local changes before submitting an MR:

```bash
python3 /absolute/path/to/skills/gitlab-mr-review/scripts/review_mr.py \
  --local-diff \
  --review-focus correctness \
  --project-root /absolute/path/to/target-project
```

4. For another angle, run the script again with a different single focus instead of asking for a broad review in one pass:

```bash
python3 skills/gitlab-mr-review/scripts/review_mr.py "<merge-request-url-or-ref>" \
  --review-focus security
```

5. If the user wants a fully custom one-aspect rubric, pass a custom prompt markdown:

```bash
python3 skills/gitlab-mr-review/scripts/review_mr.py "<merge-request-url-or-ref>" \
  --prompt-file /absolute/path/to/custom-review.md
```

6. Read the rendered prompt and produce findings only for that review angle.
   Do not mix correctness, security, performance, and maintainability feedback in the same round unless the user explicitly asks for a combined review.

## Verification

### Hard gates

- Target validity: The input resolves to exactly one MR or one local diff source. On fail, stop and request a resolvable target.
- Single-focus review: The review output stays within one selected focus unless the user explicitly requests a combined pass. On fail, split the review into separate rounds.
- Error transparency: Authentication, SSL, project mismatch, or empty diff failures are reported with the matching remediation path. On fail, surface the concrete blocker instead of continuing silently.
- Evidence-based findings: Findings must be grounded in the rendered diff or local context. On fail, report that there is insufficient evidence instead of speculating.

### Soft gates

- Budget awareness: Note when file or diff limits trimmed coverage.
- Repo context quality: Use local context only when the checkout matches the MR project.
- Concision: Keep the response focused on actionable findings for the selected review angle.

## Output Modes

The script supports `--format prompt|bundle|summary|diff`.

- Use `--format prompt` for normal review execution.
- Use `--format bundle` when debugging prompt inputs or authoring a custom review rubric.
- Use `--format summary` for quick triage of changed files and line counts.
- Use `--format diff` when the user only wants the selected diff payload without the full prompt.

The script still collects lightweight repo context from the target project root:

- Dominant languages from changed files and common manifests
- Repo stack markers from common manifests
- Background knowledge from the repository `README.md`
- Nearby local file context from the current checkout when the MR matches the local project

If `--project-root` is omitted, it uses the current working directory.
Before using local repo context, the script validates that the local checkout matches the GitLab MR project.
Use `--skip-project-match-check` only when you intentionally want to reuse another checkout for context.
When the MR is confirmed to belong to the local checkout, the script also reads nearby file content from the checked-out codebase so the review can use surrounding code that is not shown in the diff.
For `--local-diff`, the review source is `git diff HEAD`, which includes tracked staged and unstaged changes but not untracked files.
If there are no tracked changes, the script stops instead of rendering an empty review prompt.

The script also applies a review budget by default so very large MRs do not overwhelm the prompt:

- `--max-files` defaults to `20`
- `--max-changed-lines` defaults to `1200`
- `--max-diff-chars` defaults to `50000`
- Generated files are skipped unless `--include-generated` is passed

## Built-In Review Focuses

- `correctness`
  Logic errors, edge cases, invalid assumptions, state handling, and behavior regressions.
- `security`
  Trust boundaries, access control, input handling, secrets, unsafe logging, and exploitable flows.
- `performance`
  Query patterns, hot-path waste, blocking work, fan-out, contention, and avoidable resource costs.
- `maintainability`
  Readability, coupling, API shape, testability, error handling structure, and long-term change cost.

Run these as separate rounds. The skill is intentionally biased toward depth over breadth.

## Prompt Template Support

The built-in prompts live in [assets/prompts](assets/prompts).

`--prompt-file` overrides `--review-focus` when both are provided.

Custom prompt files can use these placeholders:

- `{{language}}`
- `{{code}}`
- `{{bundle}}`
- `{{review_focus}}`
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

Use `{{code}}` when you want the selected MR summary plus the selected diff. Use `{{bundle}}` when you also want project context. Read [references/custom-prompts.md](references/custom-prompts.md) if the user wants to author a new rubric.

## Notes

- Prefer `GITLAB_TOKEN` in the environment:

```bash
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
```

- The skill no longer injects technology-specific review snippets. Keep prompts focused and let the model reason from the diff and repo context.
- Prefer one focused review round at a time. If the user wants broader coverage, run multiple rounds with different `--review-focus` values instead of one overloaded prompt.

- For a plain numeric MR IID, GitLab still needs project context because MR IIDs are project-scoped.
- When inferring the project from git remotes, the script uses the repository at `--project-root` and supports SSH and HTTPS GitLab remotes.
- For URL-based MRs and `namespace/project!iid`, local project context is only used if the target checkout appears to match the GitLab project.
- Example:

```bash
git remote -v
origin  git@gitlab.example.com:group/project.git (fetch)
origin  git@gitlab.example.com:group/project.git (push)
```

This resolves `GITLAB_PROJECT` as `group/project`.
- Run `python3 skills/gitlab-mr-review/scripts/review_mr.py --help` to see all available flags and defaults.
- The bundled Python utility is a conversion of the Go helpers in `internal/util/gitlab.go`, with extra reference parsing for MR URLs and prompt rendering.

## When Not to Use

| Scenario | Route |
|----------|-------|
| GitHub pull request review | Use `code-review:code-review` or `gh pr view` |
| Local code review without GitLab context | Use a local code-review skill or run review on the working-tree diff |
| GitLab operations beyond MR review (approve, merge, comment) | Use the GitLab CLI/API or a dedicated GitLab skill |
| Non-code review (design docs, specs) | Not a code review tool |

## Boundary Cases

| Input | Expected Behavior |
|-------|-------------------|
| MR with 0 changed files | Script stops; tell user MR has no diff to review |
| MR with 500+ files | Budget limits auto-select top 20; note omitted files in review |
| User asks for "full review" | Run correctness first, then offer security/performance/maintainability rounds |
| Review finds no issues | State that briefly; do not invent findings |
| User provides GitHub URL | Decline; suggest `code-review:code-review` or `gh` CLI |
| MR is already merged | Review still works; note that findings are post-merge |

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|------------|-----|
| `401` or `403` from GitLab API | Missing or expired token | Direct the user to [references/token-setup.md](references/token-setup.md) and retry after setting `GITLAB_TOKEN` |
| SSL verification failure | Self-signed GitLab certificate | Ask for explicit consent before retrying with `--no-ssl-verify` or `GITLAB_NO_SSL_VERIFY=1` |
| Plain IID cannot be resolved | No project context from env or git remote | Ask for `--project namespace/project` or set `GITLAB_PROJECT` |
| No findings can be supported | Diff is empty or too limited after budget trimming | Say that clearly and suggest another focus or narrower target |

### Boundary examples

- GitLab MR URL or `namespace/project!iid`: valid input for this skill.
- Plain numeric IID without project context: blocked until the project is supplied or inferred.
- GitHub PR URL: out of scope; route to a GitHub review workflow.

### Improvement triggers

- Update this skill when `review_mr.py` adds new flags, output modes, or review focuses.
- Tighten the workflow if repeated failures appear that are not covered by the error table above.
