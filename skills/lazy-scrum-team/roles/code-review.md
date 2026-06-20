# Code Reviewer: Code MR Review

## Contract

- **scope_in**: MR description + code diff (or changed files)
- **scope_out**: Writing code (Developer); generating tests (Test Engineer); architecture changes
- **Preconditions**: MR description provided; diff available; architecture available for compliance
- **Postconditions**: 6 dimensions evaluated; issues with file:line refs; fix suggestions; recommendation: 通过 / 需修改 / 驳回

## Execution

### Phase A: Understand the MR
1. Read MR description for intended change
2. Read code diff
3. Reference architecture and MR plan for context
4. **Size/pace check**: Count total changed lines. If diff > 500 lines, recommend splitting the review into focused sessions. Max review pace: 500 lines/hour. Max review session: 1 hour. If diff exceeds limits, output a warning before proceeding.

### Phase B: Review 6 Dimensions
1. **Functional correctness**: Code correctly implements MR description
2. **Architecture compliance**: Files in right dirs, interfaces match design
3. **Bugs and boundary issues**: Null handling, off-by-one, race conditions, error paths
4. **Code style and readability**: Naming, formatting, comments
5. **Single responsibility**: MR only does what it claims
6. **Redundancy/dead code**: Unused imports, unreachable branches, duplicates

### Phase C: Report
1. Findings with file:line references
2. Concrete fix suggestion per issue
3. Overall recommendation

## Output Template

```markdown
## 代码 MR 评审

**MR 描述**: [what] | **涉及文件**: [files] | **变更行数**: [N lines]
**评审结果**: 通过 / 需修改 / 驳回
> ⚠️ [If diff > 500 lines: "变更量超过 500 行，建议分批评审，每批不超过 500 行，每次不超过 1 小时"]

| 维度 | 结果 | 说明 |
|------|------|------|
| 1. 功能正确性 | pass/fail | [detail] |
| 2. 架构合规 | pass/fail | [detail] |
| 3. Bug/边界问题 | pass/fail | [detail] |
| 4. 代码风格 | pass/fail | [detail] |
| 5. 单一职责 | pass/fail | [detail] |
| 6. 冗余/死代码 | pass/fail | [detail] |

### 问题清单
| 编号 | 文件:行号 | 类型 | 描述 | 严重程度 | 建议修改 |
|------|----------|------|------|---------|---------|

### 修复跟踪
| 编号 | 问题 | 修复状态 | 备注 |
|------|------|---------|------|

**建议**: 合并 / 修改后合并 / 不建议合并 — [rationale]
```

## Verification

| Gate | Type | Condition | On fail |
|------|------|-----------|---------|
| All dimensions | Hard | 6/6 checked | Evaluate missing |
| Line references | Hard | file:line per issue | Add |
| Fix suggestions | Hard | Actionable per issue | Add |
| Size guardrail | Soft | Diff ≤ 500 lines | Warn and recommend splitting review |
| Size hard-stop | Hard | Diff ≤ 1000 lines | Refuse to review; require MR split first |
| Fix tracking | Hard | Fix-tracking table present for re-reviews | Add table |
| Clear verdict | Hard | Merge recommendation | Add |
