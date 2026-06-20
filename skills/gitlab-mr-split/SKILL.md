---
name: gitlab-mr-split
description: >-
  Use when a GitLab merge request is too large to review confidently, when the
  user asks to split MR or break up a merge request, or when mechanical
  file-based grouping is not enough and reviewer judgment is needed to find
  smaller, safer sub-MRs.
version: 1.0.0
author: walterfan@ustc.edu
tags:
  - gitlab
  - merge-request
  - code-review
  - workflow
category: dev-tools
platforms:
  - claude-code
  - cursor
visibility: public
license: Apache-2.0
compatibility: Python 3.8+. GitLab token with api scope required.
metadata:
  author: walter.fan
  version: "1.0.0"
allowed-tools: Bash(python3:*) Read Write Edit
---

# GitLab MR Split

Split a large GitLab Merge Request into smaller, sequential sub-MRs that reviewers can validate with confidence. Prefer the smallest semantically coherent slice that preserves correctness, keep each sub-MR focused on one clear review story, and keep each part at or below 500 non-test code lines by default.

Tests should usually travel with their production change, but test lines do not count toward the 500-line budget. If a cohesive change cannot be split below that limit without making review quality worse, call out the exception explicitly instead of silently relaxing the rule.

## Contract

- **scope_in**: A GitLab Merge Request URL, `namespace/project!iid` reference, or plain MR IID with project context. The MR should have multiple changed files that can be split into smaller, confidence-preserving review units.
- **scope_out**: GitHub PRs (use `gh` CLI instead). MRs that are already confidence-sized and easy to review as-is (for example, fewer than 3 changed files and fewer than 200 non-test lines). Non-code MRs (wiki, docs-only) unless the user insists.
- **Preconditions**:
  - `GITLAB_TOKEN` environment variable set with `api` scope (read + write)
  - `GITLAB_URL` or defaults to `https://gitlab.example.com`
  - The source branch of the original MR exists on the remote
- **Postconditions**:
  - N sub-MRs created, each titled `<original-title> -k/N` (e.g., `Add auth module -1/3`)
  - Each sub-MR targets either the previous sub-branch or the original target branch
  - Each sub-MR has the confirmed assignee and reviewer(s) set
  - Each planned sub-MR has one primary review narrative and should normally stay within 500 non-test code lines
  - A summary table printed showing all created sub-MRs with their URLs
  - The original MR is NOT closed automatically (user decides)

## Required Inputs

- `GITLAB_TOKEN`
  Required. Needs `api` scope for creating branches and merge requests.
- `GITLAB_URL` or `GITLAB_BASE_URL`
  Optional. Defaults to `https://gitlab.example.com`.
- `GITLAB_PROJECT` or `GITLAB_PROJECT_ID`
  Optional fallback when the user gives a plain numeric MR IID.
- Assignee and reviewer identities
  Required before creating sub-MRs. If the original MR already has an assignee and reviewer(s), reuse those GitLab user IDs for every sub-MR without asking the user. Ask the user only for missing assignee/reviewer information or for an explicit override. GitLab's merge request create API expects numeric user IDs (`assignee_ids` / `assignee_id` and `reviewer_ids`), not names or emails; resolve any user-provided usernames or emails through the GitLab users API before creating an MR.

If the user needs help creating a token, refer them to the gitlab-mr-review skill's [token setup guide](../gitlab-mr-review/references/token-setup.md).

## Execution

### Phase A: Analyze the MR

- Entry: user provides an MR reference
- Steps:
  1. Parse the MR reference (URL, namespace/project!iid, or plain IID).
  2. Fetch MR metadata, including assignee/reviewer user IDs, and full diff via GitLab API.
  3. Analyze the changed files using LLM judgment, not just directory names:
     - identify the main change intent of each file or cluster
     - distinguish behavior changes, refactors, config churn, migrations, and follow-up cleanup
     - check dependency direction, rollout safety, and likely reviewer confidence
     - estimate which lines belong to non-test code versus tests, fixtures, mocks, or snapshots
  4. Flag any files whose classification is ambiguous instead of pretending the line budget is exact.
  5. If the MR has fewer than 3 files and already feels small enough to review confidently, advise the user it may not benefit from splitting and ask whether to proceed.
- Exit: MR metadata fetched and file list available
- On fail: print the GitLab API error and suggest checking token / MR reference

```bash
python3 skills/gitlab-mr-split/scripts/split_mr.py analyze "<merge-request-url-or-ref>"
```

The `analyze` subcommand outputs a JSON summary of changed files grouped by detected concern (directory, module, or file type). Treat that output as a starting point only: the current script does not calculate reviewer confidence or enforce the non-test-code budget automatically, so supplement it with manual judgment before proceeding.

### Phase B: Plan the split

- Entry: Phase A complete, file grouping available
- Steps:
  1. Start from the grouping that gives reviewers the clearest narrative, not the grouping that is easiest to compute.
  2. Use the default strategy as a draft only. Alternative strategies:
     - `by-directory`: group by immediate parent directory
     - `by-layer`: group by architectural layer (model, service, controller, test, config)
     - `by-dependency`: topological sort based on import/include analysis
     - `custom`: user provides explicit file-to-group mapping via JSON
  3. Apply confidence-first planning rules:
     - Prefer one clear purpose per sub-MR.
     - Prefer smaller confidence-preserving slices over fewer larger slices.
     - Keep prerequisites before consumers.
     - Separate mechanical renames or scaffolding from behavioral changes when possible.
     - Keep each planned sub-MR at or below 500 non-test code lines by default.
     - Keep tests with the source files they validate, but do not count those test lines toward the 500-line budget.
  4. Let the user adjust groupings — move files between groups, rename groups, reorder, or approve a clearly documented exception.
  5. Confirm the final plan: N groups, each with a name, file list, dependency order, and any explicit exception note if a group exceeds the default budget.
- Exit: user-approved split plan with N ordered groups and any exceptions called out explicitly
- On fail: loop back to let user re-adjust groupings

```bash
python3 skills/gitlab-mr-split/scripts/split_mr.py plan "<merge-request-url-or-ref>" \
  --strategy by-directory
```

Add `--num-parts N` to suggest splitting into exactly N groups. Add `--output plan.json` to save the plan for editing.

When the script's default grouping hurts review confidence, override it. Directory purity is less important than creating sub-MRs that a reviewer can understand, validate, and merge with low risk.

### Phase C: Execute the split

- Entry: Phase B complete, split plan confirmed by user
- Steps:
  1. Determine assignee/reviewer IDs from the original MR first:
     - If the original MR has an assignee and one or more reviewers, reuse those IDs for every sub-MR without asking the user.
     - If the original MR is missing either field, ask only for the missing assignee or reviewer information.
     - If the user explicitly asks to change assignee/reviewer, use the user-provided identities instead of the original MR values.
  2. Resolve any user-provided assignee/reviewer to a GitLab numeric user ID before creating sub-MRs:
     - Prefer exact `username` lookup when a username is provided.
     - Use user search for emails or display names, then ask the user to choose if multiple users match.
     - Stop before creating MRs if any assignee or reviewer cannot be resolved unambiguously.
  3. For each group k of N (in dependency order):
     a. Create a new branch `<source-branch>-split-k` from the original target branch (or from the previous split branch for k > 1).
     b. Cherry-pick or apply the diffs for the files in group k.
     c. Push the branch.
     d. Create an MR titled `<original-title> -k/N` targeting:
        - The original target branch (for k = 1)
        - The previous split branch `<source-branch>-split-(k-1)` (for k > 1)
     e. Include assignee/reviewer fields in the create-MR API payload:
        - `assignee_ids: [<assignee_user_id>]` preferred, or `assignee_id: <assignee_user_id>` if the GitLab instance only supports the legacy field
        - `reviewer_ids: [<reviewer_user_id>, ...]`
     f. Set the MR description to include:
        - A reference to the original MR
        - The list of files in this sub-MR
        - A note: "Part k/N — depends on part (k-1)/N" (if k > 1)
  4. Print a summary table of all created sub-MRs.
- Exit: all N sub-MRs created and URLs printed
- On fail: report which sub-MR failed, print partial results, suggest manual cleanup

```bash
python3 skills/gitlab-mr-split/scripts/split_mr.py execute "<merge-request-url-or-ref>" \
  --plan plan.json
```

Or combine plan + execute in one step (prompts for confirmation before creating):

```bash
python3 skills/gitlab-mr-split/scripts/split_mr.py split "<merge-request-url-or-ref>" \
  --strategy by-directory \
  --num-parts 3
```

Add `--yes` (or `-y`) to skip the confirmation prompt. Add `--dry-run` to preview without creating anything.

If the helper script or local tooling does not accept assignee/reviewer parameters, do not treat MR creation as complete after the command returns. Immediately create or update each sub-MR through the GitLab API so the final MR has the confirmed `assignee_ids`/`assignee_id` and `reviewer_ids` fields before Phase D verification.

### Phase D: Verify and report

- Entry: Phase C complete
- Steps:
  1. For each created sub-MR, verify it exists, has the expected diff, and has the expected assignee/reviewer(s).
  2. Print a markdown summary table:

```
| # | Sub-MR Title | Branch | Target | Assignee | Reviewers | Files | Lines Changed | URL |
|---|-------------|--------|--------|----------|-----------|-------|---------------|-----|
| 1 | Add auth -1/3 | feat-split-1 | main | alice | bob | 5 | +120/-30 | https://... |
| 2 | Add auth -2/3 | feat-split-2 | feat-split-1 | alice | bob | 4 | +80/-10 | https://... |
| 3 | Add auth -3/3 | feat-split-3 | feat-split-2 | alice | bob | 3 | +60/-20 | https://... |
```

  3. Remind the user to:
     - Review and merge sub-MRs in order (1/N first, then 2/N, etc.)
     - After all sub-MRs are merged, close the original MR
     - If a sub-MR needs changes, subsequent sub-MRs may need rebasing
- Exit: user has the full summary and next steps
- On fail: list any verification failures

## Confidence-First Split Heuristics

| Signal | Preferred action |
|--------|------------------|
| One directory contains multiple unrelated concerns | Split by review narrative, not by directory |
| A change mixes refactor and behavior change | Separate them when correctness allows |
| A prerequisite change enables later consumers | Put the prerequisite in an earlier sub-MR |
| Tests are large but production diff is small | Keep tests with the source change, but exclude test lines from the size budget |
| A group is still risky to review even if file count is small | Split again until the review story becomes clear |

Use the LLM's reasoning to answer one question for each proposed sub-MR: "Would a reviewer be comfortable approving this in one pass with high confidence?" If the answer is no, split again unless that would break correctness.

## Counting The 500-Line Budget

Count toward the 500-line limit:
- production source code
- runtime or deployment configuration that changes behavior
- schema or migration changes
- build or automation logic when it materially affects shipped behavior

Do not count toward the 500-line limit:
- test files
- fixtures
- mocks
- snapshots
- other test-only support files

If a file is ambiguous, do not claim an exact budget. State that the number is an estimate and ask the user whether the file should be treated as production or test-only.

## Grouping Strategies

| Strategy | Best for | How it works |
|----------|----------|-------------|
| `by-directory` | Monorepo, multi-module projects | Groups files by their top-level or second-level directory |
| `by-layer` | Layered architecture (MVC, clean arch) | Groups by architectural role: models, services, controllers, tests, config |
| `by-dependency` | Tightly coupled changes | Analyzes imports to build a dependency graph, then splits into topological layers |
| `custom` | When auto-grouping doesn't fit | User provides a JSON mapping of `{ "group-name": ["file1", "file2"] }` |

## Verification

### Hard gates
| Gate | Condition | On fail |
|------|-----------|---------|
| MR exists | Original MR is accessible via API | Stop and report auth/reference error |
| Non-empty groups | Every group has at least 1 file | Remove empty groups, re-number |
| All files covered | Union of all groups equals original changed files | Report missing files, ask user to assign them |
| No file in multiple groups | Each file appears in exactly one group | Report duplicates, ask user to resolve |
| Clear review narrative | Each proposed sub-MR has one primary purpose and does not mix unrelated concerns | Re-split by semantic concern, not just by path |
| Non-test code budget | Each proposed sub-MR is at or below 500 estimated non-test code lines, unless the skill explicitly records a user-visible exception | Re-split, move low-risk files out, or ask the user to approve a documented exception |
| Branch created | Each sub-branch exists after push | Retry once, then report failure |
| Assignee/reviewer resolved | Every assignee/reviewer has a numeric GitLab user ID, either reused from the original MR or resolved from user-provided username/email before MR creation | Ask the user to clarify only missing or ambiguous identities; do not create partial MRs |
| Sub-MR created | Each sub-MR exists with correct target, assignee, and reviewer(s) | Retry once, then report failure |

### Soft gates
| Gate | Condition | On fail |
|------|-----------|---------|
| Balanced groups | No group has >60% of total changes | Warn user, suggest re-splitting |
| Sequential naming | All sub-MRs follow -k/N pattern | Warn but proceed |

## Feedback

### Failure modes
| Symptom | Root cause | Fix |
|---------|-----------|-----|
| 403 on branch creation | Token lacks `api` scope | User needs to regenerate token with full `api` scope |
| Cherry-pick conflicts | Files in a group depend on changes in another group | Re-group dependent files together, or reorder groups |
| Sub-MR has no diff | All files in the group were moved to another group | Remove empty group and re-number |
| Merge conflicts in sub-MR | Target branch diverged | Rebase sub-branches in order |
| Sub-MR is small by file count but still hard to review | Grouping followed directory boundaries instead of one clear review story | Re-split by semantic concern and dependency direction |
| Group is under 500 total lines but still over budget | Test-only files masked that the non-test code slice is still too large | Recalculate using the non-test-code budget and split again |
| Agent claims an exact non-test count for ambiguous files | Test/support classification was guessed instead of made explicit | Mark the count as an estimate and ask the user to confirm the file classification |
| Assignee or reviewer is missing on created sub-MRs | The agent passed username/email directly instead of resolving numeric GitLab user IDs, or skipped the API fields | Resolve users first, then create MRs with `assignee_ids`/`assignee_id` and `reviewer_ids`; update existing MRs if needed |
| Agent asks for assignee/reviewer even though the original MR already has them | The workflow ignored original MR metadata and treated assignment as a required user input | Reuse the original MR's assignee/reviewer IDs by default; ask only for missing fields or explicit overrides |
| User lookup returns multiple matches | Email/name search is ambiguous | Show the candidate usernames/emails and ask the user to choose the exact account |
| Create-MR API rejects `assignee_ids` | GitLab instance only supports the legacy assignee field | Retry with `assignee_id` for a single assignee and keep `reviewer_ids` unchanged |
| Skill never triggers | Description too vague | Use trigger terms like split MR, break up MR, review confidence, smaller reviewable MR |

### Boundary examples
- **Small MR (1-2 files)**: advise that splitting is unnecessary, proceed only if user insists
- **Huge MR (100+ files)**: use `by-directory` or `by-layer` strategy; warn about API rate limits
- **Single-directory MR**: `by-directory` may not help; override it with `by-layer`, `by-dependency`, or `custom` if that gives reviewers more confidence
- **MR with test files**: by default, group tests with their corresponding source files, but exclude test-only lines from the 500-line budget
- **Group under 500 total lines but over 500 non-test lines**: still treat it as too large and split again
- **Large MR with many tests but small production changes**: the production slice may already be acceptable even if the combined total line count looks large
- **Ambiguous support file**: call out the uncertainty and ask whether it should count as production or test-only code

### Improvement triggers
- Users frequently re-group files after the initial suggestion -> improve auto-grouping heuristics
- Cherry-pick failures are common -> consider using patch-apply instead
- Users want to split by commit rather than by file -> add `by-commit` strategy

## Notes

- The skill reuses `gitlab_api.py` from the `gitlab-mr-review` skill for API calls.
- Sub-MRs are created in dependency order: MR -1/N targets the original target branch, MR -k/N targets the branch of MR -(k-1)/N.
- The merge order matters: always merge -1/N first, then -2/N, and so on.
- After merging all sub-MRs, close the original MR manually.
- Use `--dry-run` to preview what would be created without actually creating branches or MRs.
- The current script does not automatically compute reviewer confidence or exact non-test-code budgets; the agent must apply those judgments during analysis and planning.
- The current script may not automatically set assignee/reviewer fields; the agent must verify the final sub-MRs and use the GitLab API to set those fields if needed before reporting success.
- If a group cannot be kept at or below 500 non-test code lines without harming correctness or reviewer confidence, document the exception explicitly instead of treating the budget as silently waived.

## When Not to Use

| Scenario | Route |
|----------|-------|
| MR is already small (<3 files, <200 non-test lines) | Just review it directly |
| GitHub pull request | Use GitHub's built-in tools or `gh` CLI |
| Want to review but not split | Use `gitlab-mr-review` |
| Want to split by commits, not files | Not yet supported; consider `git rebase -i` |
