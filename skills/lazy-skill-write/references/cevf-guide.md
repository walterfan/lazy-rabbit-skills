# CEVF Framework Reference

**CEVF (Contract-Execution-Verification-Feedback)** is a quality engineering framework for AI Skills. It borrows from Design-by-Contract (Meyer, 1992) and Hoare Logic, adapted for the unique challenges of prompt-driven AI systems.

## Why CEVF?

Without structure, skills degrade in predictable ways:

| Problem | Root cause | CEVF layer that prevents it |
|---------|-----------|---------------------------|
| Skill handles things it shouldn't | No scope boundaries | **Contract** (scope_in/scope_out) |
| Output is unpredictable | No defined process | **Execution** (phases with criteria) |
| Bad output reaches the user | No quality checks | **Verification** (hard gates) |
| Same failures keep happening | No learning mechanism | **Feedback** (failure modes) |

## Layer Details

### Contract

The Contract defines what the skill promises. It has four elements:

**scope_in** — what the skill accepts:
- Be specific: "Python files (.py)" not "code files"
- Include formats: "JSON config files under 1MB"
- Include contexts: "when the user is debugging a production issue"

**scope_out** — what the skill rejects:
- Explicit exclusions prevent scope creep
- Always include a redirect: "For legal documents, suggest the legal-review skill"
- Include format limits: "Files over 10,000 lines — suggest splitting first"

**Preconditions** — what must be true before execution:
- Environmental: "Git repository initialized", "API key configured"
- Input quality: "At least one file provided", "Input is in English"
- State: "No uncommitted changes", "User has confirmed the target branch"

**Postconditions** — what must be true after execution:
- Output format: "Report follows the incident template"
- Output quality: "All findings have severity, description, and suggestion"
- Bounds: "Between 2 and 20 findings", "Under 500 words"

### Execution

The Execution layer defines how work gets done. Structure it as phases:

```
Phase A (entry criteria) → steps → (exit criteria) → Phase B → ... → Phase N → output
         ↓ on fail                    ↓ on fail
     failure path                 failure path
```

**Entry criteria**: what must be true to start the phase. Usually the exit criteria of the previous phase.

**Exit criteria**: what must be true to proceed. This is what makes phases testable.

**Failure paths** come in three flavors:
1. **Retry**: try the same phase again with adjusted parameters
2. **Rollback**: return to a previous phase with new information
3. **Degrade**: produce partial output and clearly mark limitations

**Degradation strategy** — when a tool or resource is unavailable:
- Name the dependency explicitly
- Define the fallback behavior
- Ensure the user knows degradation occurred

### Verification

Verification gates are the skill's unit tests. They run after execution, before delivery.

**Hard gates** block output delivery:
- Must have a measurable condition (not "looks good")
- Must have an explicit action on failure
- Example: "Finding count must be 2-20; if outside range, re-run with adjusted filters"

**Soft gates** warn but allow delivery:
- Quality improvements that shouldn't block the user
- Example: "Output over 1000 words — suggest trimming but deliver anyway"

**Gate design principles**:
- Every gate needs a threshold (a number, a pattern, a condition)
- Every gate needs an action on failure (retry, rollback, warn, stop)
- Prefer false negatives over false positives — don't block good output
- Test gates against known-good and known-bad inputs

### Feedback

The Feedback layer turns failures into improvements. It has three components:

**Failure mode dictionary** — catalog of known failure patterns:

```
Symptom → Root cause → Fix
```

This prevents the same debugging session from happening twice. Populate it from:
- Your own testing
- User reports
- Verification gate failures

**Boundary examples** — inputs at the edge of the skill's scope:
- Minimal valid input (smallest thing that should still work)
- Maximum valid input (largest thing the skill should handle)
- Edge of scope (partially matching input — what happens?)
- Just outside scope (should clearly refuse)

These prevent both over-triggering and under-triggering.

**Improvement triggers** — conditions that signal the skill needs revision:
- Quantitative: "Users override >30% of output"
- Qualitative: "Users ask follow-up questions the skill should have answered"
- Environmental: "A new tool replaces part of the workflow"

## CEVF Maturity Levels

| Level | Name | What you have |
|-------|------|--------------|
| 0 | Ad-hoc | Just instructions, no structure |
| 1 | Contracted | scope_in/scope_out and postconditions defined |
| 2 | Structured | Phases with entry/exit criteria |
| 3 | Verified | Hard gates with measurable thresholds |
| 4 | Learning | Failure modes documented, improvement triggers active |

Most skills in the wild are Level 0-1. Level 3+ is where reliability becomes predictable.

## Quick Reference: Minimum Viable CEVF

If you're short on time, add at minimum:

1. **Contract**: scope_in + scope_out + one postcondition with a number in it
2. **Execution**: at least 2 phases with "On fail" lines
3. **Verification**: at least 1 hard gate with a threshold and action-on-fail
4. **Feedback**: at least 2 failure modes with symptom/cause/fix
