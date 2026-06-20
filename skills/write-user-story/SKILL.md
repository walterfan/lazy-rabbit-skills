---
name: write-user-story
description: >-
  Create well-structured Jira user stories following the INVEST principle,
  including size assessment and breakdown of large stories into smaller
  sub-stories. Use when the user wants to write a user story, create a Jira
  story, break down a feature into stories, split a large story, draft user
  stories from requirements, estimate story size, apply INVEST criteria, or
  generate acceptance criteria. Make sure to use this skill when the user says
  things like "write a user story for X", "create stories for this feature",
  "break this down into stories", or "I need Jira stories for ...".
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - jira
  - user-story
  - invest
  - requirements
category: productivity
platforms:
  - claude-code
  - cursor
visibility: public
---

# Write User Story

Create Jira user stories that follow the INVEST principle. Automatically assess story size and break down large stories into smaller, sprint-ready sub-stories. Stories are drafted for user review before Jira creation.

## Contract

- **scope_in**: feature requests, requirement summaries, Jira story drafting, acceptance criteria generation, INVEST-based sizing and breakdown
- **scope_out**: direct Jira creation without user approval, non-story issue types that need a different workflow, unsupported project metadata the user cannot clarify
- **Preconditions**: the user provides enough context to identify the feature, target user, and business value; project key is available or can be confirmed
- **Postconditions**: the output contains a draft story or story breakdown, clear acceptance criteria, an INVEST check, and no Jira issue is created before explicit approval

## Execution

### Phase 1: Gather context

1. **Gather requirements** — understand what the user wants to build
2. Capture feature, user role, value, project key, and optional parent, assignee, and priority.
3. Infer reasonable defaults when context is partial, then confirm them.
- On fail: if the core feature, actor, or value is still ambiguous, stop and ask for the missing fields before drafting.

### Phase 2: Draft and size the story

1. Write the story using the template and the INVEST checklist below.
2. Estimate size using the t-shirt table.
3. If the story is `L` or `XL`, or likely above 8 story points, split it into smaller sub-stories.
- On fail: if the story cannot be made Independent, Small, or Testable, present a partial draft plus the specific reason it needs more detail or a different split.

### Phase 3: Review and create

1. Present the full draft or breakdown to the user for review.
2. Wait for explicit approval.
3. After approval, create the Jira issue(s) with the `helper` CLI and report the created keys and links.
- On fail: if approval is not given or Jira creation fails, do not create or retry silently; return the draft and the exact blocker.

## Step 1: Gather Requirements

Ask the user for the essential inputs. Batch questions to avoid excessive back-and-forth:

- **What feature or change?** — a brief description of the desired functionality
- **Who benefits?** — the target user role (e.g., "admin", "end user", "API consumer")
- **Why?** — the business value or problem being solved
- **Jira project key** — e.g., `PROJ`, `CORE` (ask if not obvious from context)
- **Parent issue** — epic or parent story key, if applicable (optional)
- **Assignee** — who should own this story (optional)
- **Priority** — P1/P2/P3/P4 (default to P2 if not specified)

If the user provides a broad feature description, infer reasonable defaults and confirm.

## Step 2: Draft the User Story

Read [references/user-story-guide.md](references/user-story-guide.md) for the full template and INVEST criteria.

Write the story using this structure:

```
## Summary (Jira title)
As a [role], I want to [action], so that [benefit]

## Description (Jira description, Markdown)

### Problem
[What problem does this solve?]

### Solution
[High-level approach]

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## DoD (Definition of Done)
- [ ] Design document reviewed (if applicable)
- [ ] Code changes in MR, reviewed and approved
- [ ] MR associated with this issue
- [ ] Test cases and results provided
- [ ] No serious bugs; passes acceptance tests

## Metadata
- Priority: P1/P2/P3/P4
- Parent: [epic or parent key]
- Assignee: [name]
- Verifier: @[name]
```

**Quality checklist** — verify each story against INVEST:

| Criterion | Check |
|-----------|-------|
| Independent | No hidden dependency on another story |
| Negotiable | Details can evolve during implementation |
| Valuable | Delivers user-visible or stakeholder value |
| Estimable | Team can estimate with reasonable confidence |
| Small | Fits within one sprint (≤8 story points) |
| Testable | Has clear, verifiable acceptance criteria |

## Step 3: Assess Size and Break Down if Needed

Estimate using t-shirt sizing:

| Size | Duration | Action |
|------|----------|--------|
| S | 1–4 days | Create as single story |
| M | 5–10 days | Create as single story (consider splitting if >8 SP) |
| L | 10–20 days | **Must break down** |
| XL | 20+ days | **Must break down** |

### Breakdown Strategies

When a story is too large, split using one or more of these axes:

1. **By workflow step** — input → processing → output
2. **By data variation** — one story per data type or format
3. **By operation (CRUD)** — separate create, read, update, delete
4. **By layer** — frontend, backend API, database migration
5. **By acceptance criteria** — each criterion becomes its own story
6. **By spike + implementation** — spike for unknowns, then build

Each sub-story must independently satisfy INVEST. If a sub-story is not independently valuable, try a different split axis.

Present the breakdown as a numbered list of sub-stories, each with:
- Summary line (Jira title)
- 1-2 sentence scope description
- Estimated size (S/M)
- Key acceptance criteria

## Step 4: Present for Review

Display the complete story (or list of sub-stories) to the user in a clear, readable format. Explicitly ask:

> "Here is the user story I've drafted. Please review and let me know if you'd like any changes, or confirm it's ready to create in Jira."

For breakdowns, also show:
- The parent story / epic relationship
- A summary table of all sub-stories with sizes

Wait for explicit user confirmation before proceeding to Jira creation. Do NOT create issues without approval.

## Step 5: Create in Jira

After user confirms, create the Jira issue(s) using the `helper` CLI.

### Pre-creation: Discover issue types

```bash
helper tool run jira_get_project_issue_types_metadata \
  --project-id-or-key {PROJECT_KEY}
```

### Create a single story

```bash
helper tool run jira_create_issue \
  --project-key {PROJECT_KEY} \
  --issue-type-name "Story" \
  --summary "{story_title}" \
  --description "{markdown_description}" \
  --parent "{parent_issue_key}"
```

### Create broken-down sub-stories

1. Create the parent story first (if it doesn't already exist)
2. Create each sub-story with `--parent` pointing to the parent
3. Report back all created issue keys with links

### Post-creation

After creating, report:
- Issue key(s) and URL(s): `https://your-org.atlassian.net/browse/{KEY}`
- Summary of what was created
- Any follow-up actions (e.g., "assign to team members", "add to sprint")

### Optional: Set assignee

Look up the user first:

```bash
helper tool run jira_search_users --query "{name_or_email}"
```

Then include `--assignee_account_id` in the create call.

## Verification

### Hard gates

- The draft includes a summary, problem, solution, acceptance criteria, DoD, and metadata.
- The story passes the INVEST checklist or is explicitly broken down until it does.
- No Jira issue is created before explicit user confirmation.
- Created issues, when requested, include the correct project key and reported issue keys.

### Soft gates

- Acceptance criteria are concrete and testable.
- Story size is explained when a breakdown is proposed.
- Defaults for priority, parent, or assignee are clearly labeled for user review.

## Feedback

- **Failure modes**: missing business value, unclear actor, oversized story, missing Jira metadata, Jira CLI failure
- **Boundary examples**: a vague feature request should trigger clarification; an `L` or `XL` story should trigger breakdown instead of single-story output
- **Improvement triggers**: update this skill when Jira fields, helper commands, or the user-story template in `references/user-story-guide.md` changes

## Rules

- ALWAYS present stories for user review before creating in Jira
- ALWAYS break down stories estimated at L/XL size
- ALWAYS apply the INVEST quality check to every story
- Use Markdown in Jira descriptions — it renders correctly
- Use `helper tool run` commands (not MCP tool calls) for Jira operations
- If the user provides a Jira URL, extract the issue key (e.g., `PROJ-1234`)
- If the user references an existing issue as context, fetch it first with `jira_get_issue` to understand scope
