# Developer: Single MR Coding

## Contract

- **scope_in**: One MR task description (from approved MR plan) + approved architecture
- **scope_out**: Multiple MRs; architecture decisions; requirement changes; testing
- **Preconditions**: MR plan and architecture approved; user specifies which MR; dependency MRs merged
- **Postconditions**: Complete runnable code for this MR only; approved directory structure; commit message template

## Rules (Non-Negotiable)

1. **One MR at a time** — ignore future tasks
2. **No pre-writing** — don't create files for future MRs
3. **No cross-function changes** — note out-of-scope issues but don't change them
4. **Architecture compliance** — directory, naming, patterns match approved design
5. **Complete code** — no stubs or placeholders
6. **Re-review flow** — on 需修改/驳回, revise only listed issues, resubmit same MR

## Execution

### Phase A: Understand the MR

1. Read MR description, identify single function to implement
2. Review architecture for relevant modules, interfaces, file boundaries
3. Identify files to create/modify (only MR-scoped)
4. Verify dependency MRs are merged — if not, stop and report blocker

### Phase B: Implement

1. Write/modify only MR-scoped files
2. Follow approved directory structure exactly
3. Implement single function — nothing more
4. Comments where logic is non-obvious
5. Follow coding standards from architecture

### Phase C: Prepare for Submission

1. List modified/created files
2. Verify no out-of-scope files touched
3. DoD (Definition of Done) checklist — all must pass before submission:
   - [ ] Code reviewed self-check (no obvious bugs, no dead code)
   - [ ] Unit tests written and passing for new/changed logic
   - [ ] Integration with existing code verified (no broken imports/interfaces)
   - [ ] All acceptance criteria for this MR met
   - [ ] No critical defects or regressions
   - [ ] Documentation updated if public API changed
   - [ ] Code is deployable (no feature flags left open, no debug artifacts)
4. Generate commit message:
```
feat(module): [MR-ID] brief description

- What was implemented
- Key design decisions
- DoD: all items verified ✓

Relates to: TASK-ID
```

## Verification

| Gate | Type | Condition | On fail |
|------|------|-----------|---------|
| Scope compliance | Hard | Only MR-scoped files | Remove out-of-scope |
| Runnable code | Hard | Compiles/runs | Fix errors |
| Architecture compliance | Hard | Correct dirs, interfaces match | Restructure |
| Single function | Hard | MR does one thing | Remove extras |
| No placeholders | Hard | No TODOs or stubs | Complete |
| DoD compliance | Hard | All 7 DoD items checked | Complete missing |
| Line count | Soft | Within estimate +/-20% | Warn |
