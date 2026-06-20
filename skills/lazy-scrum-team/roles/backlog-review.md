# Backlog Reviewer: Sprint Backlog Approval

## Contract

- **scope_in**: Product Backlog (original) + AI-generated Sprint Backlog
- **scope_out**: Generating backlogs (PO's job); modifying the backlog (review only)
- **Preconditions**: Both documents provided
- **Postconditions**: 8 dimensions evaluated; recommendation: 通过 / 建议驳回 / 需修改; human makes final decision

## Execution

### Phase A: Gather Inputs

1. Parse Product Backlog items
2. Parse Sprint Backlog (stories, ACs, priorities, scope, dependencies)
3. Create traceability matrix: Sprint Backlog item → Product Backlog source

### Phase B: Evaluate 8 Dimensions

1. **Traceability**: Every story traces to a Product Backlog item
2. **Story clarity**: Complete (role, action, benefit) and developable
3. **AC quality**: Testable, verifiable, unambiguous
4. **Priority**: Reasonable given dependencies and business value
5. **Scope**: Included/excluded boundaries explicit and aligned
6. **Dependencies**: Complete, correct, no cycles
7. **DoR compliance**: Every story meets Definition of Ready — clear value, AC defined, estimated, dependencies identified, testable, no ambiguity
8. **INVEST compliance**: Each story is Independent, Negotiable, Valuable, Estimable, Small (1-3 days), Testable

### Phase C: Report

1. Pass/fail per dimension with specific story/AC references
2. Actionable modification suggestions per issue
3. Overall recommendation based on severity

## Output Template

```markdown
## Sprint Backlog 审批评审

| 维度 | 结果 | 说明 |
|------|------|------|
| 1. 需求溯源 | pass/fail | [detail] |
| 2. 故事清晰度 | pass/fail | [detail] |
| 3. AC 可测试性 | pass/fail | [detail] |
| 4. 优先级合理性 | pass/fail | [detail] |
| 5. 范围明确性 | pass/fail | [detail] |
| 6. 依赖关系 | pass/fail | [detail] |
| 7. DoR 就绪度 | pass/fail | [detail] |
| 8. INVEST 合规 | pass/fail | [detail] |

**通过项**: x/8 | **整体结论**: 通过 / 建议驳回 / 需修改

### 问题清单
| 编号 | 维度 | 具体问题 | 严重程度 | 建议 |
|------|------|---------|---------|------|

**审批建议**: 通过 / 驳回 / 完善后通过 — [rationale]
```

## Verification

| Gate | Type | Condition | On fail |
|------|------|-----------|---------|
| All dimensions | Hard | 8/8 evaluated | Evaluate missing |
| Specific refs | Hard | Issues cite story/AC IDs | Add references |
| Actionable | Hard | Each issue has fix suggestion | Add suggestions |
| Clear verdict | Hard | Has overall conclusion | Add conclusion |
