# Sprint Retrospective: Continuous Improvement

**Parallel support lane** — runs after sprint acceptance, never counts as approval to advance.

## Contract

- **scope_in**: Sprint artifacts (backlog, MR plan, code reviews, test reports, acceptance report), sprint timeline, team observations
- **scope_out**: Re-planning (Scrum Master); re-coding (Developer); re-testing (Test Engineer)
- **Preconditions**: Sprint acceptance completed (通过 or 有条件通过); all sprint artifacts available
- **Postconditions**: 3-question retrospective answered; action items with owners and deadlines; improvement metrics identified

## Execution

### Phase A: Gather Sprint Data

1. Collect sprint metrics: planned vs delivered stories, velocity, defect count by severity
2. Review all review reports (backlog, architecture, MR plan, code, test, acceptance) for recurring themes
3. Identify bottlenecks from sprint timeline (which phases took longest, which had rework loops)
4. Note blockers encountered and how they were resolved

### Phase B: Analyze and Generate Retrospective

1. **What went well?** — identify practices, tools, and decisions that contributed to success; cite specific examples from artifacts
2. **What could be improved?** — identify pain points, process gaps, recurring issues; use data from review reports and rework loops
3. **What will we commit to?** — generate concrete, measurable action items; each must have an owner and a deadline
4. Calculate improvement metrics: rework rate (reviews that returned 需修改/驳回), defect density, estimation accuracy (estimated vs actual effort)

### Phase C: Report

1. Keep the report evidence-based — every claim must reference a specific artifact or metric
2. Prefer few high-value action items over many vague ones (2-5 items)
3. End with focus areas for the next sprint, not rework directives for the current one

## Output Template

```markdown
## Sprint 回顾报告 — [Sprint Name/Date]

### Sprint 数据概览
| 指标 | 计划 | 实际 | 差异 |
|------|------|------|------|
| 用户故事 | x | y | +/-z |
| Story Points | x | y | +/-z |
| MR 数量 | x | y | +/-z |
| 缺陷数 (S1-S2) | 0 | y | |
| 缺陷数 (S3-S5) | 0 | y | |
| 返工次数 | — | y | |

### 做得好的方面 ✓
1. [specific practice/decision and why it worked]
2. [specific practice/decision and why it worked]

### 需要改进的方面 ✗
1. [pain point with evidence from artifacts]
2. [pain point with evidence from artifacts]

### 改进承诺与行动项
| 编号 | 行动项 | 负责人 | 截止日期 | 预期效果 |
|------|--------|--------|---------|---------|

### 改进度量
| 指标 | 本Sprint | 目标 | 趋势 |
|------|---------|------|------|
| 返工率 | x% | <y% | ↑/↓/→ |
| 缺陷密度 | x/story | <y/story | ↑/↓/→ |
| 估算准确度 | x% | >y% | ↑/↓/→ |

---
**下一 Sprint 建议关注**: [top 1-2 improvement areas]
```

## Verification

| Gate | Type | Condition | On fail |
|------|------|-----------|---------|
| 3 questions | Hard | All 3 retrospective questions answered with specifics | Complete missing |
| Data-backed | Hard | Metrics section populated with actual sprint data | Gather data |
| Action items | Hard | At least 2 concrete action items with owner + deadline | Add |
| Evidence-based | Soft | Issues cite specific artifacts or events | Add references |
| Conciseness | Soft | Readable in 5 minutes | Trim |
