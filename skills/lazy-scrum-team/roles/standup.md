# Standup Assistant: Daily Standup Briefing

**Parallel support lane** — runs at any time, never counts as approval to advance.

## Contract

- **scope_in**: Completed MRs, in-progress MRs, pending MRs, blockers
- **scope_out**: Code review, task creation, architecture decisions
- **Preconditions**: User provides current sprint status; blockers stated (or explicitly none)
- **Postconditions**: 5 sections present; blockers highlighted; readable in 2-3 minutes

## Execution

### Phase A: Gather Status

1. Parse completed, in-progress, and pending MRs/tasks
2. Identify blockers, risks, dependencies at risk

### Phase B: Generate Briefing

1. Summarize completed work
2. List in-progress with status and expected completion
3. Pending items by dependency urgency
4. Risks/blockers with impact and suggested resolution
5. Today's action plan

## Output Template

```markdown
## 每日站会简报 — [Date]

### 已完成工作
| MR/任务 | 描述 | 完成时间 |
|---------|------|---------|

### 进行中工作
| MR/任务 | 描述 | 当前状态 | 预计完成 |
|---------|------|---------|---------|

### 待处理事项
| MR/任务 | 描述 | 优先级 | 依赖 |
|---------|------|--------|------|

### 风险与阻塞点
| 问题 | 影响 | 建议解决方案 |
|------|------|-------------|

### 今日推进计划
1. [action item]
2. [action item]

---
**Sprint 进度**: x/y 任务完成 (xx%)
```

## Verification

| Gate | Type | Condition | On fail |
|------|------|-----------|---------|
| 5 sections | Hard | All present (empty = "无") | Add missing |
| Blockers | Hard | All known blockers addressed | Add |
| Actionable plan | Hard | Concrete items | Make specific |
| Conciseness | Soft | Readable in 2-3 min | Trim |
