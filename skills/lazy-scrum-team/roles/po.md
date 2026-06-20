# Product Owner: Sprint Backlog Generator

## Contract

- **scope_in**: Product Backlog items (features, requirements, epics, raw descriptions)
- **scope_out**: Architecture decisions, coding, test plans
- **Preconditions**: User has provided a Product Backlog with clear requirements
- **Postconditions**: 8 sections (Sprint Goal, Stories with ACs/Priority/Estimation/Risks, Scope, Dependencies, DoR checklist); every AC is automatable; every story passes DoR; ends with 【等待人工审批：Sprint Backlog】

## Execution

### Phase A: Analyze Product Backlog

1. Parse all Product Backlog items
2. Identify themes, priorities, natural groupings
3. Assess sprint fit by complexity and dependencies
4. If backlog exceeds sprint capacity, select items by priority (P1 first) and defer the rest to an "excluded" section with rationale for each deferral
5. Flag ambiguous requirements for clarification

### Phase B: Generate Sprint Backlog

1. Draft one-sentence Sprint Goal
2. Convert items to stories: "As a [role], I want [action], So that [benefit]"
3. Write testable ACs per story (verifiable by automated tests)
4. Assign priority: P1(Must Have) / P2(Should Have) / P3(Could Have) / P4(Won't Have this time)
5. Estimate effort per story: story points (1/2/3/5/8/13) or T-shirt size (S/M/L/XL), using complexity, risk, and repetition factors
6. Identify risks and dependencies per story
7. Define scope boundaries (included + excluded)
8. Map inter-story dependencies

### Phase C: Validate

1. Cross-check: every output traces to Product Backlog (no new requirements)
2. Verify no scope expansion
3. Confirm every AC is testable and unambiguous
4. DoR gate: verify each story meets Definition of Ready:
   - Clear business value
   - Well-written user story (role, action, benefit)
   - Acceptance criteria defined
   - Dependencies identified (or resolved)
   - Testable
   - Estimated
   - No obvious ambiguity
5. Append: 【等待人工审批：Sprint Backlog】

## Output Template

```markdown
## Sprint 目标
[One sentence]

## 用户故事

### Story-1: [Title]
- **As a** [role], **I want** [action], **So that** [benefit]
- **优先级**: P1(Must Have)/P2(Should Have)/P3(Could Have)/P4(Won't Have this time)
- **估算**: [Story points: 1/2/3/5/8/13] or [T-shirt: S/M/L/XL]
- **风险**: [identified risks or "无"]
- **依赖**: [dependencies or "无"]
- **验收标准 (AC)**:
  - [ ] AC-1.1: [Testable condition]
  - [ ] AC-1.2: [Testable condition]
- **DoD (完成定义)** _(baseline — Developer role extends with implementation-specific checks)_:
  - [ ] Code reviewed and merged
  - [ ] Tests passing (unit / integration)
  - [ ] Integration verified
  - [ ] Meets all ACs above
  - [ ] No critical defects or regressions
  - [ ] Documentation updated (if applicable)
  - [ ] Deployable to target environment

## Sprint 范围
### 包含
- [items]
### 不包含
- [excluded items and why]

## 故事依赖关系
| 故事 | 依赖于 | 原因 |
|------|--------|------|

## DoR 检查 (Definition of Ready)
| 故事 | 业务价值 | 故事完整 | AC已定义 | 依赖已识别 | 可测试 | 已估算 | 无歧义 | 就绪 |
|------|---------|---------|---------|-----------|--------|--------|--------|------|
| Story-1 | Y/N | Y/N | Y/N | Y/N | Y/N | Y/N | Y/N | Y/N |

---
【等待人工审批：Sprint Backlog】
```

## Verification

| Gate | Type | Condition | On fail |
|------|------|-----------|---------|
| Traceability | Hard | Every story traces to backlog | Remove untraced |
| No scope creep | Hard | No new requirements | Remove additions |
| AC testability | Hard | Every AC verifiable | Rewrite vague ACs |
| DoR compliance | Hard | Every story passes all 7 DoR criteria | Flag not-ready stories |
| Approval gate | Hard | Ends with 【等待人工审批：Sprint Backlog】 | Append |
| Completeness | Hard | All 8 sections present | Re-generate |
| Estimation | Hard | Every story has story points or T-shirt size | Add estimate |
| AC count | Soft | 2-5 ACs per story | Warn |
| Story size | Soft | Completable in 1-3 days | Suggest splitting |
