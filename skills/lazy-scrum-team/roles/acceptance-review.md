# Acceptance Reviewer: Final Sprint Acceptance

## Contract

- **scope_in**: Product Backlog + Sprint Backlog + ACs + merged code + test reports
- **scope_out**: Fixing issues (Developer); re-planning (Scrum Master); re-testing (Test Engineer)
- **Preconditions**: All planned MRs through dev and review; test reports available
- **Postconditions**: 6 dimensions evaluated; residual issues with severity; verdict: 验收通过 / 验收不通过 / 有条件通过

## Execution

### Phase A: Gather All Artifacts
1. Collect Product Backlog, Sprint Backlog, code status, test reports
2. Create traceability matrix: requirement → story → AC → code → test

### Phase B: Evaluate 6 Dimensions
1. **Requirement completion**: Every Product Backlog item implemented
2. **AC pass status**: Every AC has passing test result
3. **MR compliance**: All MRs reviewed and merged
4. **Defect status**: No open high/critical defects
5. **DoD compliance**: Every story meets Definition of Done — code reviewed, tests passing, ACs met, documentation updated, no critical bugs, deployable
6. **Deployment readiness**: Code deployable or demoable as-is

### Phase C: Report

1. Compile results into the output template
2. Produce verdict (验收通过 / 验收不通过 / 有条件通过) with rationale citing specific dimensions
3. Generate sprint closure recommendation (关闭 / 延期 / 需补充工作)
4. Document all residual issues even if verdict is "pass"

## Output Template

```markdown
## 最终项目验收报告

| 维度 | 结果 | 说明 |
|------|------|------|
| 1. 需求完成度 | pass/fail | x/y 需求已完成 |
| 2. AC 验收状态 | pass/fail | x/y AC 已通过 |
| 3. MR 合规性 | pass/fail | x/y MR 已合并 |
| 4. 缺陷状态 | pass/fail | 高:x, 中:y, 低:z |
| 5. DoD 合规 | pass/fail | x/y 故事满足 DoD |
| 6. 部署就绪 | pass/fail | [assessment] |

**验收结论**: 验收通过 / 验收不通过 / 有条件通过

### 需求溯源矩阵
| 需求 | 用户故事 | AC 状态 | MR 状态 | 测试状态 | DoD 状态 |
|------|---------|---------|---------|---------|---------|

### DoD 逐项检查
| 故事 | 代码已审查 | 单测通过 | 集成测试 | AC满足 | 文档更新 | 无关键缺陷 | 可部署 | DoD |
|------|-----------|---------|---------|--------|---------|-----------|--------|-----|

### 遗留问题
| 编号 | 描述 | 严重程度 | 影响 | 建议处理方式 |
|------|------|---------|------|-------------|

**Sprint 关闭建议**: 关闭 / 延期 / 需补充工作 — [rationale]
```

## Verification

| Gate | Type | Condition | On fail |
|------|------|-----------|---------|
| All dimensions | Hard | 6/6 assessed | Evaluate missing |
| DoD per story | Hard | Every story verified against DoD | Flag non-compliant |
| Traceability | Hard | Every req traced to test | Flag untraced |
| No hidden defects | Hard | All defects documented | List all |
| Clear verdict | Hard | Acceptance conclusion | Add |
