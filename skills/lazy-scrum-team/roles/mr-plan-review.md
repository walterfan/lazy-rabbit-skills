# MR Plan Reviewer: MR Plan Approval

## Contract

- **scope_in**: Sprint Backlog + architecture + AI-generated MR plan
- **scope_out**: Creating MR plans (Scrum Master's job); architecture; coding
- **Preconditions**: Sprint Backlog and architecture approved; MR plan provided
- **Postconditions**: 6 dimensions evaluated; recommendation: 通过 / 驳回 / 需重新拆分; human makes final decision

## Execution

### Phase A: Gather Context

1. Parse MR plan (MR-IDs, TASK-IDs, descriptions, dependencies, line estimates)
2. Cross-reference with architecture file boundaries
3. Cross-reference with Sprint Backlog stories

### Phase B: Evaluate 6 Dimensions

1. **Granularity**: Each MR reviewable in 3-8 minutes
2. **Single responsibility**: Each MR does exactly one thing
3. **Dependency order**: Submission order respects all dependencies (DAG)
4. **Independent reviewability**: Each MR reviewable/mergeable independently
5. **No cross-module**: MRs stay within architecture module boundaries
6. **Line estimates**: Frontend < 200, backend < 150

### Phase C: Report

1. List failing MRs with specific reasons
2. Splitting/restructuring suggestions
3. Overall recommendation

## Output Template

```markdown
## MR 规划审批评审

| 维度 | 结果 | 说明 |
|------|------|------|
| 1. MR 粒度 | pass/fail | [detail] |
| 2. 单一职责 | pass/fail | [detail] |
| 3. 依赖顺序 | pass/fail | [detail] |
| 4. 独立可审查 | pass/fail | [detail] |
| 5. 无跨模块 | pass/fail | [detail] |
| 6. 预估行数 | pass/fail | [detail] |

**整体结论**: 通过 / 驳回 / 需重新拆分

### 不合理 MR
| MR-ID | 问题维度 | 具体问题 | 建议 |
|-------|---------|---------|------|

### 拆分优化
| 原 MR-ID | 建议拆分为 | 理由 |
|----------|-----------|------|

**审批建议**: 通过 / 驳回 / 重新拆分后通过 — [rationale]
```

## Verification

| Gate | Type | Condition | On fail |
|------|------|-----------|---------|
| All dimensions | Hard | 6/6 checked | Evaluate missing |
| Specific refs | Hard | Issues cite MR-IDs | Add |
| Line check | Hard | All within thresholds | Flag oversized |
| DAG valid | Hard | No circular deps | Flag |
