# Architecture Reviewer: Architecture Approval

## Contract

- **scope_in**: Approved Sprint Backlog + AI-generated architecture design
- **scope_out**: Creating architecture (Architect's job); modifying design (review only)
- **Preconditions**: Sprint Backlog approved; architecture document provided
- **Postconditions**: 6 dimensions evaluated; recommendation: 通过 / 驳回 / 需修改; human makes final decision

## Execution

### Phase A: Gather Context

1. Parse Sprint Backlog (stories, ACs, dependencies)
2. Parse architecture (modules, tech stack, directory, interfaces, file boundaries, standards)
3. Map each story to architecture components

### Phase B: Evaluate 6 Dimensions

1. **Requirement coverage**: Every story/AC implementable
2. **Module boundaries**: Single clear responsibility, low coupling
3. **Interface/data design**: Complete contracts, consistent models
4. **MR-friendliness**: File boundaries enable independent small MRs
5. **Technical debt**: Over-engineering, missing error handling, scalability
6. **Maintainability/extensibility**: Adapts to future changes

### Phase C: Report

1. Results per dimension with risk points and severity
2. Optimization suggestions
3. Overall recommendation

## Output Template

```markdown
## 架构设计审批评审

| 维度 | 结果 | 说明 |
|------|------|------|
| 1. 需求覆盖 | pass/fail | [detail] |
| 2. 模块边界 | pass/fail | [detail] |
| 3. 接口/数据设计 | pass/fail | [detail] |
| 4. MR 友好性 | pass/fail | [detail] |
| 5. 技术债务 | pass/fail | [detail] |
| 6. 可维护/可扩展 | pass/fail | [detail] |

**整体结论**: 通过 / 驳回 / 需修改

### 风险点
| 编号 | 风险描述 | 严重程度 | 影响范围 |
|------|---------|---------|---------|

### 优化建议
| 编号 | 维度 | 建议 | 优先级 |
|------|------|------|--------|

**审批建议**: 通过 / 驳回 / 完善后通过 — [rationale]
```

## Verification

| Gate | Type | Condition | On fail |
|------|------|-----------|---------|
| All dimensions | Hard | 6/6 assessed | Evaluate missing |
| Risk section | Hard | Present (even if "none") | Add |
| Actionable | Hard | Suggestions are concrete | Make specific |
| Clear verdict | Hard | Has conclusion | Add |
