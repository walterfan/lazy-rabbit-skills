---
name: gitlab-mr-issue
description: >-
  Generate GitLab issue drafts from actionable Merge Request comments and create
  the confirmed issues in the target code repository. Use when a user wants to
  turn MR comments, review discussions, unresolved threads, or merge request
  feedback into GitLab issues, even if they do not explicitly ask for a reusable
  issue workflow.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - gitlab
  - merge-request
  - issue-triage
category: dev-tools
use_cases:
  - "Convert unresolved GitLab MR review threads into issue drafts"
  - "Create follow-up GitLab issues after the user confirms the generated plan"
  - "Summarize MR comments into actionable code-repo backlog items"
platforms:
  - codex
  - claude-code
visibility: public
license: Apache-2.0
compatibility: Python 3.8+. Requires a GitLab token for API access.
allowed-tools: Bash(python3:*) Read Write
---

# GitLab MR Issue

Generate issue drafts from GitLab Merge Request comments, ask the user to confirm
the exact issues, then create them in the MR's code repository only after
confirmation.

## Contract

- **scope_in**: One GitLab Merge Request URL, `namespace/project!iid`, or project-scoped MR IID whose review comments should become follow-up GitLab issues.
- **scope_out**: GitHub pull requests, direct code review, automatic issue creation without user confirmation, and non-GitLab task trackers.
- **Preconditions**: `GITLAB_TOKEN` is configured; the MR reference resolves to exactly one project and IID; the user has not asked to bypass confirmation.
- **Postconditions**: The user sees issue drafts grounded in MR comments; GitLab issues are created only after explicit user confirmation; created issue URLs are reported back.

## Required Inputs

- `GITLAB_TOKEN`
  Required. The token must be able to read the MR and create issues in the target project.
- `GITLAB_URL` or `GITLAB_BASE_URL`
  Optional. Defaults to `https://gitlab.example.com` unless the MR URL already includes a host.
- `GITLAB_PROJECT` or `GITLAB_PROJECT_ID`
  Optional fallback for a plain numeric MR IID.
- `GITLAB_NO_SSL_VERIFY`
  Optional. Set to `1`, `true`, `yes`, or `on` only after the user explicitly agrees to disable SSL verification for a self-signed GitLab certificate.

If the user needs help creating a token, read [references/token-setup.md](references/token-setup.md).

## Execution

### Phase A: Resolve MR and fetch comments
- Entry: User asks to generate issues from MR comments.
- Steps:
  1. Resolve the MR reference.
  2. Fetch MR metadata and discussions with `scripts/generate_mr_issues.py`.
  3. Prefer unresolved/actionable discussions; include resolved comments only when the user asks.
- Exit: Comment-backed issue draft data is available.
- On fail: Stop and report the concrete blocker, such as missing token, invalid MR reference, or no actionable comments.

### Phase B: Draft issues
- Entry: Phase A completed.
- Steps:
  1. Group comments by discussion thread or closely related topic.
  2. Produce concise issue titles and descriptions.
  3. Preserve evidence: MR link, discussion id, comment author, file path, line, and original comment excerpt.
  4. Present the draft issue list to the user for confirmation.
- Exit: The user can approve, reject, or edit the issue plan.
- On fail: Deliver partial drafts and label any draft whose source evidence is weak.

### Phase C: Confirm and create
- Entry: The user explicitly confirms which issues to create.
- Steps:
  1. Write the confirmed draft JSON to a temporary file.
  2. Run `scripts/generate_mr_issues.py --create --confirmed --input-file <file>`.
  3. Report created issue URLs and any skipped drafts.
- Exit: Confirmed issues exist in GitLab and the user has the result links.
- On fail: Report the API error and preserve the confirmed draft JSON so the user can retry.

## Workflow

1. Fetch draft issue data:

```bash
python3 skills/gitlab-mr-issue/scripts/generate_mr_issues.py "<merge-request-url-or-ref>" \
  --format markdown
```

If GitLab fails SSL verification because of a self-signed certificate, ask the user first, then retry with:

```bash
python3 skills/gitlab-mr-issue/scripts/generate_mr_issues.py "<merge-request-url-or-ref>" \
  --format markdown \
  --no-ssl-verify
```

For a plain numeric MR IID:

```bash
python3 skills/gitlab-mr-issue/scripts/generate_mr_issues.py 123 \
  --project namespace/project \
  --format markdown
```

2. Convert the fetched comments into issue drafts. Use this structure for each issue:

```markdown
### Issue N: <title>
**Why**: <problem or follow-up requested by MR comment>
**Scope**: <specific code path or behavior to change>
**Acceptance criteria**:
- <observable completion condition>
- <test or verification expectation>
**Source**: <MR URL, discussion id, file path, line, author>
```

3. Ask the user to confirm before creating issues.
   Do not run a GitLab write command until the user explicitly says to create, approve, confirm, or provides an edited final list.

4. After confirmation, save the confirmed issue plan as JSON and create issues:

```bash
python3 skills/gitlab-mr-issue/scripts/generate_mr_issues.py \
  --create \
  --confirmed \
  --input-file /tmp/confirmed-mr-issues.json
```

The script intentionally rejects `--create` without `--confirmed`.

## JSON Draft Format

Use this JSON shape when creating confirmed issues:

```json
{
  "gitlab_url": "https://gitlab.example.com",
  "project": "namespace/project",
  "merge_request_iid": "123",
  "drafts": [
    {
      "title": "Fix stale cache invalidation after role update",
      "description": "## Context\n...\n\n## Acceptance criteria\n- ...",
      "labels": ["mr-follow-up", "code-review"]
    }
  ]
}
```

## Verification

### Hard gates
| Gate | Condition | On fail |
|------|-----------|---------|
| Target validity | Exactly one GitLab MR is resolved | Ask for a full MR URL or project |
| Evidence-backed drafts | Every issue draft cites at least one MR comment or discussion | Remove unsupported drafts |
| Confirmation required | No issue creation before explicit user confirmation | Stop before write action |
| Write guard | `--create` is paired with `--confirmed` and an input JSON file | Refuse to call the API |
| API transparency | GitLab authentication and permission errors are surfaced | Report the exact blocker |
| SSL consent | SSL verification is disabled only after user approval | Retry only after explicit consent |

### Soft gates
| Gate | Condition | On fail |
|------|-----------|---------|
| Deduplication | Similar comments are grouped into one issue | Ask user whether to merge duplicates |
| Title quality | Titles are action-oriented and under 90 characters | Shorten before confirmation |
| Issue usefulness | Descriptions include context, scope, and acceptance criteria | Add missing sections before confirmation |

## Feedback

### Failure modes
| Symptom | Root cause | Fix |
|---------|------------|-----|
| No comments found | MR has no discussions or token cannot see them | Verify MR URL and token permissions |
| Drafts are too broad | Multiple review topics were grouped together | Split by discussion or file path |
| Issues created too early | Confirmation gate was skipped | Treat as a skill violation; require explicit confirmation next time |
| GitLab returns 403 | Token lacks issue creation permission | Ask user for a token with project write access |

### Boundary examples
- **Minimal input**: A full GitLab MR URL with one unresolved review thread.
- **Maximum input**: A large MR with many discussions; group related comments and ask user to confirm the final set.
- **Edge of scope**: Comments that request immediate MR changes may become follow-up issues only if the user wants backlog tracking.

### Improvement triggers
- Add project-specific label mappings when users repeatedly edit labels.
- Add team-specific issue templates when users repeatedly rewrite descriptions.
- Add deduplication rules if multiple issues are generated for the same discussion topic.
