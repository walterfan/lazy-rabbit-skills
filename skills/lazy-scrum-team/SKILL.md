---
name: lazy-scrum-team
description: >-
  All-in-one AI Virtual Scrum Team covering the full sprint lifecycle: PO, Backlog
  Review, Architect, Architecture Review, Scrum Master, MR Plan Review, Developer,
  Code Review, Test Engineer, Final Acceptance, Daily Standup, and Sprint
  Retrospective. Routes to the correct role, enforces approval gates, and handles
  rework loops. Use when the user mentions virtual scrum team, AI scrum team, sprint
  planning, backlog, architecture design, task splitting, MR planning, coding a
  task, code review, testing, final acceptance, daily standup, retrospective, or any
  Scrum role activity.
version: 0.6.0
author: walterfan@ustc.edu
tags: [scrum, agile, orchestration, virtual-team, workflow]
category: agile
platforms: [claude-code, cursor, codex]
visibility: public
---

# AI Virtual Scrum Team

One skill, twelve roles, full sprint lifecycle. The orchestrator selects the right role, enforces approval gates, and handles rework routing. Each role's detailed execution, templates, and verification live in [roles/](roles/).

## Sub-Commands

Users can directly invoke a role with `/lazy-scrum-team <sub-command> [args]`. When a sub-command is provided, **skip Phase A** (auto-detection) and go straight to the matched role. Gates (Phase C) still apply unless the user adds `--force`.

| Sub-command | Aliases | Role | File | Example |
|-------------|---------|------|------|---------|
| `po` | `backlog`, `plan` | Product Owner | `roles/po.md` | `/lazy-scrum-team po` |
| `backlog-review` | `br` | Backlog Reviewer | `roles/backlog-review.md` | `/lazy-scrum-team br` |
| `architect` | `arch`, `design` | Architect | `roles/architect.md` | `/lazy-scrum-team arch` |
| `arch-review` | `ar` | Architecture Reviewer | `roles/architecture-review.md` | `/lazy-scrum-team ar` |
| `scrum-master` | `sm`, `split` | Scrum Master | `roles/scrum-master.md` | `/lazy-scrum-team sm` |
| `mr-review` | `mrr` | MR Plan Reviewer | `roles/mr-plan-review.md` | `/lazy-scrum-team mrr` |
| `dev` | `code`, `implement` | Developer | `roles/developer.md` | `/lazy-scrum-team dev MR-003` |
| `code-review` | `cr`, `review` | Code Reviewer | `roles/code-review.md` | `/lazy-scrum-team cr` |
| `test` | `qa` | Test Engineer | `roles/test-engineer.md` | `/lazy-scrum-team test` |
| `accept` | `final`, `done` | Acceptance Reviewer | `roles/acceptance-review.md` | `/lazy-scrum-team accept` |
| `standup` | `status`, `daily` | Standup Assistant | `roles/standup.md` | `/lazy-scrum-team standup` |
| `retro` | `retrospective`, `reflect` | Sprint Retrospective | `roles/retro.md` | `/lazy-scrum-team retro` |
| `roadmap` | `overview` | Orchestrator (Roadmap Mode) | — | `/lazy-scrum-team roadmap` |
| `help` | — | Show this sub-command table | — | `/lazy-scrum-team help` |

**Argument passing**: Any text after the sub-command is passed as context to the role. For example:
- `/lazy-scrum-team dev MR-003` → Developer role, implement MR-003
- `/lazy-scrum-team po <paste product backlog>` → PO role with input
- `/lazy-scrum-team cr` → Code Reviewer, will ask for MR diff if not provided

**Flags**:
- `--force`: Skip gate enforcement (Phase C). Use when you know the prerequisites and want to proceed anyway
- `--no-header`: Skip the coordinator header (Template A) and output only the role's result

## Contract

- **scope_in**: Multi-phase Scrum coordination — backlog, architecture, MR planning, development, code review, testing, acceptance, standup, retrospective
- **scope_out**: Skipping human approvals; implementing multiple MRs at once; inventing missing artifacts instead of asking
- **Preconditions**: User wants Scrum support; current phase is inferable or can be clarified; upstream artifacts exist or are explicitly missing
- **Postconditions**: One active role chosen (unless roadmap requested); artifact states listed; missing items explicit; next role/gate/rework-owner clear
- **Language convention**: Output templates use Chinese section headers and column headers. Technical values (pass/fail, Y/N, severity codes S1-S5, P1-P4) remain in English.

## Team Roster & Delivery Lane

```
PO → Backlog Review → Architect → Arch Review → Scrum Master → MR Plan Review
  → Developer → Code Review → Test → Acceptance Review → Human closes sprint
                        ↕ Daily Standup (parallel, any time)
                        ↕ Sprint Retrospective (parallel, after acceptance)
```

| # | Role | Detail | Input | Output | Approval gate |
|---|------|--------|-------|--------|---------------|
| 1 | Product Owner | [po.md](roles/po.md) | Product Backlog | Sprint Backlog with ACs, estimates, risks, DoR, DoD | 【等待人工审批：Sprint Backlog】 |
| 2 | Backlog Reviewer | [backlog-review.md](roles/backlog-review.md) | Product Backlog + Sprint Backlog | 8-dimension review recommendation | Human approve/reject |
| 3 | Architect | [architect.md](roles/architect.md) | Approved Sprint Backlog | Architecture design | 【等待人工审批：架构设计】 |
| 4 | Architecture Reviewer | [architecture-review.md](roles/architecture-review.md) | Approved Sprint Backlog + architecture | Review recommendation | Human approve/reject |
| 5 | Scrum Master | [scrum-master.md](roles/scrum-master.md) | Approved backlog + architecture | Task list + MR plan + effort estimates | 【等待人工审批：任务与MR规划】 |
| 6 | MR Plan Reviewer | [mr-plan-review.md](roles/mr-plan-review.md) | Backlog + architecture + MR plan | Review recommendation | Human approve/reject |
| 7 | Developer | [developer.md](roles/developer.md) | Approved MR plan + one MR | Code changes | Code ready for review |
| 8 | Code Reviewer | [code-review.md](roles/code-review.md) | MR description + diff | Review recommendation + fix tracking | Human merge decision |
| 9 | Test Engineer | [test-engineer.md](roles/test-engineer.md) | ACs + merged code | Test report + bug reports | Human test acceptance |
| 10 | Acceptance Reviewer | [acceptance-review.md](roles/acceptance-review.md) | All sprint artifacts | Acceptance report + DoD traceability | Human sprint closure |
| 11 | Standup Assistant | [standup.md](roles/standup.md) | Current status/blockers | Standup briefing | None (parallel lane) |
| 12 | Sprint Retrospective | [retro.md](roles/retro.md) | All sprint artifacts + timeline | Retro report + action items | None (parallel lane) |

## Shared Artifact State Model

| Artifact | States | Forward when | Rework when |
|----------|--------|-------------|-------------|
| Product Backlog | `provided`, `clarify-needed` | `provided` → PO | `clarify-needed` → Human |
| Sprint Backlog | `missing`, `draft`, `review-failed`, `approved` | `approved` → Architect | `review-failed` → PO |
| Architecture | `missing`, `draft`, `review-failed`, `approved` | `approved` → Scrum Master | `review-failed` → Architect |
| Task & MR Plan | `missing`, `draft`, `review-failed`, `approved` | `approved` → Developer | `review-failed` → Scrum Master |
| MR Implementation | `pending`, `in-dev`, `in-review`, `changes-requested`, `merged` | `merged` → Test | `changes-requested` → Developer |
| Test Report | `missing`, `draft`, `failed`, `passed` | `passed` → Acceptance | `failed` → Developer → retest |
| Final Acceptance | `pending`, `conditionally-passed`, `passed`, `failed` | `passed` → Human closes | `failed` → root-cause owner |

## Cross-Role Quality Gates

| Gate | Produced by | Reviewed by | Used to unblock |
|------|-------------|-------------|-----------------|
| DoR (Definition of Ready) | Product Owner | Backlog Reviewer | Architecture design and downstream planning |
| DoD (Definition of Done) | Developer self-check per MR/story | Acceptance Reviewer | Sprint acceptance and closure |
| Structured defect reports | Test Engineer | Human + Developer | Rework prioritization and retest flow |

## Execution

### Phase 0: Parse Sub-Command (if present)

1. Check if user input starts with a known sub-command or alias from the table above
2. If **sub-command found**: extract the role, args, and flags → skip Phase A → go to Phase B
3. If **`help`**: print the sub-command table and stop
4. If **`roadmap`**: enter Roadmap Mode directly → go to Phase B
5. If **no sub-command**: fall through to Phase A (auto-detection)

### Phase A: Detect Current Sprint Phase (auto-detection)

Skipped when a sub-command is provided.

1. Inventory user's artifacts: Product Backlog, Sprint Backlog, approvals, architecture, MR plan, selected MR, code diff, merged code, test report, sprint status, sprint timeline
2. Match to one of: backlog generation, backlog review, architecture generation, architecture review, MR planning, MR plan review, single-MR implementation, code review, testing, final acceptance, daily standup, retrospective, or broad coordination
3. Select operating mode:
   - **Routing** (default): one concrete request → pick one role, execute it
   - **Roadmap**: broad request ("run this sprint") → produce phased plan, stop at first unresolved gate
   - **Recovery**: a review/test failed → route back to rework owner
- On fail: ask user which phase to start from

### Phase B: Sync Artifact States

1. Infer latest state of each artifact from conversation context
2. Latest human/reviewer decision is source of truth
3. Mark unknowns as `missing`
- On fail: ask user to confirm ambiguous artifact state

### Phase C: Enforce Gates

1. Verify upstream artifacts are in correct state (`approved` / `merged` / `passed`)
2. If review/test failed → Recovery Mode → route backward via rework matrix
3. If user jumps ahead → explain missing approval, don't guess
4. Exceptions: Standup runs independently anytime; retrospective runs after acceptance without advancing any gate
- On fail: produce blocker report (artifact state, missing approval, rework owner, next role)

### Phase D: Route to Role

1. Match phase to role using the routing matrix below
2. **Read the matched role file** — use the exact path from the "File" column. The role file contains the role's full contract, execution steps, output template, and verification gates. You MUST read it before generating output
3. Follow that role's contract, execution, and verification exactly
4. Prepend a coordinator header (Template A) when executing; use Template B for roadmaps; use Template C for handoffs

### Routing Matrix

| User has / asks for | Role | File |
|---------------------|------|------|
| Raw requirements, Product Backlog, sprint planning, DoR definition | PO | `roles/po.md` |
| Sprint Backlog needing review, DoR validation, INVEST check | Backlog Reviewer | `roles/backlog-review.md` |
| Approved Sprint Backlog, wants design | Architect | `roles/architect.md` |
| Architecture needing review | Architecture Reviewer | `roles/architecture-review.md` |
| Approved backlog + architecture, wants task/MR split | Scrum Master | `roles/scrum-master.md` |
| MR plan needing review | MR Plan Reviewer | `roles/mr-plan-review.md` |
| Approved MR plan + one specific MR | Developer | `roles/developer.md` |
| MR diff to review, review-size guardrail, re-review tracking | Code Reviewer | `roles/code-review.md` |
| Merged code + ACs to validate, structured bug capture | Test Engineer | `roles/test-engineer.md` |
| Sprint closure / release readiness, DoD validation | Acceptance Reviewer | `roles/acceptance-review.md` |
| Current status / blockers / daily plan | Standup Assistant | `roles/standup.md` |
| Sprint complete, wants retrospective / improvement review | Sprint Retrospective | `roles/retro.md` |

### Rework Matrix

| Failure trigger | Return to | Resume when |
|-----------------|-----------|-------------|
| Backlog review: 建议驳回/需修改 | PO | Sprint Backlog `approved` |
| Architecture review: 驳回/需修改 | Architect | Architecture `approved` |
| MR Plan review: 驳回/需重新拆分 | Scrum Master | MR plan `approved` |
| Code review: 需修改/驳回 | Developer | MR re-reviewed and `merged` |
| Test: failed/blocking issues | Developer | Test report `passed` |
| Acceptance: failed (scope) | PO | Acceptance rerun |
| Acceptance: failed (design) | Architect | Acceptance rerun |
| Acceptance: failed (sequencing) | Scrum Master | Acceptance rerun |
| Acceptance: failed (defects) | Developer | Code merged, tests rerun |
| Acceptance: failed (coverage) | Test Engineer | Test report `passed` |
| Acceptance: failed (DoD) | Developer | Code merged, DoD items completed |

Sprint Retrospective does not trigger rework — its action items feed into the next sprint's Product Backlog.

## Rules (Non-Negotiable)

1. **One active role at a time** — unless user asks for a roadmap
2. **Approval-gated progression** — never skip a gate
3. **One MR at a time** — for development phase
4. **Human stays in charge** — approvals and final acceptance are human decisions
5. **Every failed gate names a return owner**
6. **Standup and retrospective are observational** — never count as approval

## Output Templates

### Template A: Routing Response

```markdown
## 虚拟 Scrum 团队协调结果
- **当前阶段**: [phase]  |  **当前角色**: [role]
- **工件状态**: `[SB=approved, ARCH=draft, MRP=missing, ...]`
- **缺失/阻塞**: [missing artifact or "无"]
- **本轮动作**: [what this role does now]
- **下一审批点**: [gate]  |  **下一角色**: [role]  |  **回流目标**: [owner or "无"]
---
[Role-specific output follows]
```

### Template B: Roadmap

```markdown
## 虚拟 Scrum 团队协作路线图
| 阶段 | 角色 | 输入 | 输出 | 审批点 | 不通过回流 |
|------|------|------|------|--------|------------|
| 1-12 | ... | ... | ... | ... | ... |

**当前应从第 [n] 阶段开始** — [reason] — 缺失: [what] — 下一步: [action]
```

### Template C: Handoff Packet

```markdown
## 交接包
- **来源→目标**: [previous role] → [next role]
- **工件**: [name] = [state]  |  **结论**: [approve/reject/pass/fail]
- **必须处理**: [issues]
- **恢复前进条件**: [what must become approved/merged/passed]
```

## Verification

### Hard gates

| Gate | Condition | On fail |
|------|-----------|---------|
| Correct role | Exactly one role in Routing Mode | Re-route from artifact inventory |
| No skipped approvals | Downstream never starts without approved upstream | Stop, list missing approval |
| Rework owner named | Every failed gate has a return owner | Add explicit return path |
| One MR discipline | Dev never attempts multiple MRs | Ask user to pick one |
| Clear next step | Output names next role, gate, or rework owner | Add next-step section |

### Soft gates

| Gate | Condition | On fail |
|------|-----------|---------|
| Artifact visibility | Existing and missing artifacts both listed | Improve summary |
| Handoff completeness | Packet has state, target, resume condition | Fill in packet |
| Conciseness | Routing summary scannable quickly | Trim repetition |

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Wrong role selected | Incomplete artifact inventory | Re-check user artifacts before routing |
| Jumps ahead too early | Gates not enforced | Stop at missing approval |
| Does everything at once | Broad request = execution | Switch to Roadmap Mode |
| Failed gate, no owner | Rework path not explicit | Use rework matrix |
| Dev implements too much | MR granularity ignored | Enforce one MR |
| Standup or retrospective treated as approval | Parallel lanes not separated | Mark parallel-only |

### Boundary examples

- **Only Product Backlog** → PO
- **Approved Sprint Backlog** → Architect
- **Approved arch + MR plan + selected MR** → Developer
- **Architecture review failed** → back to Architect, not forward
- **Test failed** → Developer, then retest
- **"Run the whole sprint"** → Roadmap, stop at first gate
- **"Daily status"** → Standup (parallel)
- **"Sprint retrospective"** / **"What can we improve next sprint?"** → Sprint Retrospective (parallel, after acceptance)

### Improvement triggers

- Users frequently correct role selection → improve phase detection
- Outputs too long before useful work → shorten coordinator preamble
- Users lose track of artifact states → surface states more prominently
- Downstream blocked by missing approvals → surface gates earlier

## Example Flow

```
User:  Here is my Product Backlog: [requirements…]
AI:    → PO generates Sprint Backlog → 【等待人工审批：Sprint Backlog】
User:  批准
AI:    → Backlog Reviewer evaluates 8 dimensions → 审核通过
       → Architect produces architecture design → 【等待人工审批：架构设计】
User:  批准
AI:    → Architecture Reviewer evaluates → 审核通过
       → Scrum Master decomposes into tasks & MRs → 【等待人工审批：任务 & MR 计划】
…and so on through Developer → Code Review → Test → Acceptance.
```

Each `【等待人工审批】` marker is a gate — the AI stops and waits for user approval before advancing.

## Additional resources

- Role details (execution, templates, verification): [roles/](roles/)
