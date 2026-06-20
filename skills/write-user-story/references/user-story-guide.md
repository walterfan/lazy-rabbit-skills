# User Story Writing Guide

## INVEST Principle

Every user story should satisfy the INVEST criteria:

- **Independent**: Self-contained, no inherent dependency on another story
- **Negotiable**: Not a rigid contract; details can be discussed
- **Valuable**: Delivers value to the end user or stakeholder
- **Estimable**: Can be reasonably estimated in effort
- **Small**: Fits within a single sprint/iteration
- **Testable**: Clear criteria to verify completion

## Story Format

Use the canonical format:

> As a **[Role]**, I want to **[Action]**, so that **[Benefit]**.

## Description Structure

Each story description should address:

1. **What is the problem?**
2. **What is the root cause?** (if applicable)
3. **What is the solution?**
   - Success criteria (DoD)
   - UE/UX Impacts
   - Metrics: LMTA (Log, Metrics, Tracing, Alert)
   - Dependencies
   - Risks

## Definition of Done (DoD)

Standard DoD checklist items:

- If there is a design document, provide the document link and confirm it has passed team review.
- For code changes, create a corresponding git merge/pull request, reviewed and approved by team members, then merged into the main development branch.
- The merge request should be associated with the issue of the user story.
- Code changes should have corresponding test cases and test results (Unit testing, API testing, or manual testing).
- Code implementation complies with the detailed design and description requirements, without serious bugs, and passes the Acceptance Test Cases.

## Priority Levels

- **P1 (Must have)**: Critical, blocking — must be in this iteration
- **P2 (Should have)**: Important but not blocking
- **P3 (Could have)**: Nice to have if time permits
- **P4 (Won't have)**: Out of scope for now, tracked for future

## Estimation

### T-shirt Sizing (for large features / epics)

| Size | Duration |
|------|----------|
| S (Small) | 1–4 days |
| M (Medium) | 5–10 days |
| L (Large) | 10–20 days |
| XL (Extra Large) | 20+ days |

### Story Points (for broken-down stories)

Evaluate based on three dimensions:

- **Complexity**: How hard is this to implement?
- **Risk**: Are there third-party dependencies or unknowns?
- **Repetition**: Is this repetitive, one-off, or exploratory work?

A common baseline: one CRUD operation on a standard entity ≈ 1 story point.

## Story Breakdown Guidelines

Break down a story when:

- Estimated size is **L or XL** (>10 days)
- Story points exceed **8**
- It spans multiple components, services, or teams
- It contains multiple independent acceptance criteria

### Breakdown Strategies

1. **By workflow step**: Split along the user's journey (e.g., input → processing → output)
2. **By data variation**: One story per data type or format
3. **By operation (CRUD)**: Separate create, read, update, delete
4. **By interface/layer**: Frontend, backend API, database migration, etc.
5. **By acceptance criteria**: Each criterion becomes its own story
6. **By spike + implementation**: Spike for unknowns, then implement

### Breakdown Quality Check

Each sub-story should still satisfy INVEST. If a sub-story is not independently valuable, consider a different split axis.

## Jira Description Template (Markdown)

```
## Parent Issue

{parent_issue_key}

## Priority

{P1/P2/P3/P4}

## Description

As a **{role}**, I want to **{action}**, so that **{benefit}**.

### Problem
{problem_description}

### Solution
{solution_description}

### Acceptance Criteria
- [ ] {criterion_1}
- [ ] {criterion_2}
- [ ] {criterion_3}

## DoD (Definition of Done)

- [ ] Design document reviewed (if applicable)
- [ ] Code changes in MR, reviewed and approved by team members
- [ ] MR associated with this issue
- [ ] Test cases and results provided (unit / API / manual)
- [ ] No serious bugs; passes acceptance tests

## Verifier

@{verifier}
```
