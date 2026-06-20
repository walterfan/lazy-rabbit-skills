---
name: lazy-skill-write
description: >-
  Guide users through creating effective AI Skills for any domain using the
  CEVF (Contract-Execution-Verification-Feedback) quality framework. Use when
  user wants to create, write, author, or improve a skill — whether for coding,
  operations, writing, design, data analysis, support, or any other domain.
  Make sure to use this skill when the user mentions "make a skill", "write a
  skill", "turn this into a skill", "capture this workflow", or describes a
  repeatable process they want to package — don't wait for explicit requests.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - skill-authoring
  - cevf
  - workflow
  - domain-agnostic
category: dev-tools
use_cases:
  - "User wants to create a new AI skill for any domain"
  - "User wants to capture a repeatable workflow as a skill"
  - "User asks about SKILL.md structure, best practices, or CEVF"
  - "User wants to improve an existing skill's reliability"
  - "User describes a process they keep repeating and wants to automate"
platforms:
  - claude-code
  - cursor
visibility: public
---

# lazy-skill-write

Create reliable AI Skills for any domain — coding, ops, writing, design, data, support, and beyond. This skill applies the **CEVF (Contract-Execution-Verification-Feedback)** framework to ensure every skill you build is well-scoped, resilient, and self-improving.

## CEVF at a Glance

| Layer | Question it answers | Analogy |
|-------|-------------------|---------|
| **Contract** | What goes in? What comes out? What's off-limits? | A function signature with pre/postconditions |
| **Execution** | How does the work get done, step by step? | The function body, with error handling |
| **Verification** | How do we know the output is good enough? | Assertions and tests |
| **Feedback** | What goes wrong, and how do we get better? | Code review comments and postmortems |

---

## Phase 1: Contract — Define the Boundaries

Before writing anything, establish the skill's contract. Scan the current conversation first — extract what you already know, then ask only about genuine gaps.

### 1.1 Gather Intent

| Element | Question | Example (ops domain) | Example (writing domain) |
|---------|----------|---------------------|-------------------------|
| Purpose | What task does this skill handle? | Deploy a service safely | Write a press release |
| Trigger | When should the AI use it? | User mentions deploy, rollback, release | User asks to draft PR, announce launch |
| Domain knowledge | What does the AI not already know? | Internal deploy pipeline steps | Company tone guide, boilerplate |
| Output format | What should the result look like? | Terminal commands + status report | Structured document with sections |

### 1.2 Define Scope

Every skill needs explicit boundaries — a skill that tries to handle everything handles nothing well.

```markdown
## Contract
- **scope_in**: [What the skill accepts]
  e.g., customer support tickets in English; Python source files; marketing briefs
- **scope_out**: [What the skill refuses or redirects]
  e.g., legal documents (redirect to legal-review skill); binary files; languages other than English
- **Preconditions**: [What must be true before execution]
  e.g., user has provided the input document; API credentials are configured
- **Postconditions**: [What must be true after execution]
  e.g., output follows the template; all required sections are present; word count is 200-500
```

Write these directly in your SKILL.md. A missing contract is the root cause of most skill failures — scope creep, unpredictable output, silent errors.

### 1.3 Description Rules

The description field is injected into the AI's system prompt — it is the primary trigger mechanism. A weak description is the #1 reason skills don't fire.

| Rule | Good | Bad |
|------|------|-----|
| Third person | "Generates incident reports from..." | "I help you write incident reports" |
| WHAT + WHEN | "...Use when user mentions outage or incident" | "Helps with incidents" |
| Concrete triggers | lists "outage, incident, postmortem, RCA" | "Helps with operations" |
| Appropriately assertive | "Make sure to use this even when not explicitly asked" | "Use when relevant" |

```yaml
# Weak
description: >-
  Helps write reports. Use when asked about reports.

# Strong
description: >-
  Generate structured incident reports, postmortems, and RCA documents.
  Make sure to use this skill whenever the user mentions an outage,
  incident, service degradation, or wants to write a postmortem — even
  if they don't explicitly ask for a report.
```

---

## Phase 2: Execution — Design the Process

Structure the skill's core logic as ordered phases with clear transitions, rollbacks, and degradation paths.

### 2.1 Phase Design

Break the workflow into sequential phases. Each phase has:
- **Entry criteria**: what must be true to start this phase
- **Steps**: the actual work
- **Exit criteria**: what must be true to move on
- **Failure path**: what to do if this phase fails

```markdown
## Execution

### Phase A: Gather context
- Entry: user has provided input matching scope_in
- Steps:
  1. Read and parse the input
  2. Identify key entities, dates, and facts
- Exit: structured data extracted, no ambiguous fields
- On fail: ask user to clarify ambiguous fields before proceeding

### Phase B: Generate draft
- Entry: Phase A complete
- Steps:
  1. Apply the output template
  2. Fill each section using extracted data
  3. Flag any section where data is insufficient
- Exit: complete draft with all required sections
- On fail: produce partial draft, clearly mark incomplete sections with [TODO]

### Phase C: Refine
- Entry: Phase B complete
- Steps:
  1. Check tone, terminology, and formatting
  2. Remove redundancy
  3. Verify postconditions are met
- Exit: final output ready for delivery
- On fail: deliver draft with a note listing what didn't pass
```

### 2.2 Resilience Patterns

Good skills don't just handle the happy path:

- **Rollback**: "If Phase C finds postconditions violated, return to Phase B with specific feedback on what to fix"
- **Degradation**: "If the external tool is unavailable, fall back to manual steps and note the limitation"
- **Scope guard**: "If input doesn't match scope_in, stop immediately and explain why — don't attempt partial processing"

### 2.3 Content Patterns

Choose the pattern that fits your skill's domain:

**Workflow Pattern** — step-by-step processes (deployments, review flows, approval chains):
```markdown
1. Check prerequisites: `command or action`
2. Execute main task: `command or action`
3. Verify result: `command or action`
4. If failed → rollback: `command or action`
```

**Template Pattern** — consistent output formats (reports, documents, emails):
```markdown
Use this structure:
## [Title]
**Context**: ...
**Analysis**: ...
**Recommendation**: ...
**Next steps**: ...
```

**Examples Pattern** — quality depends on seeing real samples (writing, naming, classification):
```markdown
Input: [real example input]
Output: [real example output]
Why: [brief explanation of the decision]
```

**Conditional Pattern** — branching workflows (triage, routing, classification):
```markdown
1. Classify the input:
   - Type A → follow "Type A workflow" below
   - Type B → follow "Type B workflow" below
   - Unknown → ask user to clarify
```

---

## Phase 3: Verification — Set Quality Gates

Verification turns subjective "looks good" into objective pass/fail. Define gates with measurable thresholds and explicit actions on failure.

### 3.1 Hard Gates (block output if failed)

These must pass before the skill delivers its result:

```markdown
## Verification

### Hard gates
| Gate | Condition | On fail |
|------|-----------|---------|
| Non-empty output | Output has content | Retry generation once, then stop with error |
| Template compliance | All required sections present | Re-generate with explicit section list |
| Scope compliance | Output only covers scope_in topics | Remove out-of-scope content, warn user |
| Postcondition met | Output satisfies stated postconditions | Return to Phase B with specific violation |
```

### 3.2 Soft Gates (warn but deliver)

These improve quality but don't block delivery:

```markdown
### Soft gates
| Gate | Condition | On fail |
|------|-----------|---------|
| Length target | Output within word/line count range | Warn user, suggest edits |
| Completeness | All input items addressed | Note skipped items in output |
| Consistency | Terminology uniform throughout | Highlight inconsistencies |
```

### 3.3 Domain-Specific Gates

Tailor verification to your domain:

- **Code skills**: lint passes, no syntax errors, tests run
- **Writing skills**: tone matches guide, no placeholder text remains, all sections filled
- **Ops skills**: commands are valid, rollback path exists, no destructive commands without confirmation
- **Data skills**: output schema matches expected, no null required fields, row count within bounds
- **Support skills**: response addresses the customer's question, includes next steps, tone is empathetic

---

## Phase 4: Feedback — Learn from Failure

The Feedback layer is what most skills miss. It documents what goes wrong, shows boundary behavior, and defines when the skill needs updating.

### 4.1 Failure Mode Dictionary

Document known failure patterns so future users (and the AI) can recognize and fix them:

```markdown
## Feedback

### Failure modes
| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Skill never triggers | Description too vague or passive | Add specific trigger terms, make description more assertive |
| Output is generic/shallow | Domain knowledge section missing | Add examples, terminology, and context the AI wouldn't know |
| Output too long/noisy | No upper bound in postconditions | Add length limits and filtering criteria |
| Wrong format | Template not explicit enough | Show exact output structure with a complete example |
| Partial output silently delivered | No verification gates | Add hard gates that catch incomplete output |
```

### 4.2 Boundary Examples

Show where the skill's behavior changes — this prevents both over-triggering and under-triggering:

```markdown
### Boundary examples
- **Minimal input**: a single sentence → should still produce structured output (just shorter)
- **Maximum input**: very large document → should summarize or sample, not process verbatim
- **Edge of scope**: input partially matches scope_in → process matching parts, flag the rest
- **Out of scope**: input clearly outside scope_in → refuse politely, suggest alternative skill if known
```

### 4.3 Improvement Triggers

Define conditions that signal the skill needs a revision:

```markdown
### Improvement triggers
- Users frequently override or rewrite >30% of output → review template and examples
- Skill fires on unrelated conversations → narrow trigger terms in description
- Users ask follow-up questions the skill should have answered → expand coverage
- A new tool or process replaces part of the workflow → update execution phases
```

---

## Writing Style Guide

These apply to the SKILL.md content you write:

- **Imperative form**: "Read the input", "Generate the report", not "You should read the input"
- **Explain why**: the AI reasons better with context than rigid rules — "Check for duplicates because downstream systems reject them" beats "ALWAYS remove duplicates"
- **Avoid ALWAYS/NEVER in caps**: reframe as reasoning instead of commands
- **Generalize**: write instructions that work across inputs, not tuned to one example
- **Stay lean**: every token competes for context space — remove anything that isn't earning its keep
- **One default per choice**: "Use JSON format (override with `--format csv` if needed)" not "You can use JSON, CSV, or YAML"

---

## Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| No contract | Scope creep, unpredictable behavior | Define scope_in/scope_out and pre/postconditions |
| No verification | "Looks good" is not a quality gate | Add hard gates with thresholds and fail actions |
| No feedback layer | Same failures repeat | Document failure modes and improvement triggers |
| Passive description | AI never triggers the skill | List specific trigger terms, add "even if not explicitly asked" |
| Too many options | AI can't decide | Pick one default, mention one escape hatch |
| Vague description | "Helps with stuff" | List concrete capabilities and trigger phrases |
| Time-sensitive info | Outdated in weeks | Avoid dates and version numbers in instructions |
| Deep file nesting | Linked files may not be read | Keep references one level deep |
| Heavy-handed MUSTs | Brittle, ignores context | Explain reasoning instead |
| Coding-only assumptions | Excludes non-technical domains | Use domain-neutral language and examples |

---

## Pre-Publish Checklist

Before publishing, verify every CEVF layer:

```
Contract:
- [ ] scope_in and scope_out explicitly defined
- [ ] Preconditions and postconditions stated with measurable criteria
- [ ] Description: third person, WHAT + WHEN, specific triggers, appropriately assertive

Execution:
- [ ] Phases have clear entry/exit criteria
- [ ] At least one failure path with rollback or degradation
- [ ] Content pattern matches the skill's domain

Verification:
- [ ] At least 2 hard gates with measurable pass/fail conditions
- [ ] Each gate has an explicit action-on-fail
- [ ] Domain-appropriate checks included

Feedback:
- [ ] At least 3 failure modes documented
- [ ] At least 1 boundary example
- [ ] At least 1 improvement trigger defined

General:
- [ ] SKILL.md body < 500 lines (use progressive disclosure for the rest)
- [ ] Examples use real input → real output, not abstract placeholders
- [ ] Consistent terminology throughout
- [ ] Instructions explain *why*, not just *what*
```

---

## Toolchain

This skill includes scripts, templates, agents, and references to support the full skill lifecycle.

### Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/validate_skill.py` | Validate SKILL.md against CEVF framework | `python scripts/validate_skill.py <skill-dir>` |
| `scripts/run_eval.py` | Run trigger and quality eval cases | `python scripts/run_eval.py <skill-dir> [--verbose]` |
| `scripts/package_skill.py` | Package skill into distributable .skill archive | `python scripts/package_skill.py <skill-dir> [output-dir]` |

### Templates

| Template | Purpose |
|----------|---------|
| `templates/SKILL_TEMPLATE.md` | Starter SKILL.md with all CEVF sections pre-structured with TODO markers |
| `templates/evals_template.json` | Starter eval cases covering trigger, boundary, and verification tests |

Copy the template into your new skill directory and replace the TODOs:
```bash
cp templates/SKILL_TEMPLATE.md <your-skill>/SKILL.md
cp templates/evals_template.json <your-skill>/evals/evals.json
```

### Agents

| Agent | Purpose |
|-------|---------|
| `agents/reviewer.md` | Review a SKILL.md and score each CEVF layer (0-10) with specific improvement suggestions |
| `agents/comparator.md` | Blind-compare two skill outputs to determine which is better |

### References

| Reference | Purpose |
|-----------|---------|
| `references/cevf-guide.md` | Deep dive into every CEVF layer with design principles and maturity levels |
| `references/schemas.md` | JSON schemas for evals, results, reviews, and frontmatter |
| `references/examples.md` | Complete CEVF examples across 4 domains: ops, writing, data, and support |

---

## Progressive Disclosure

Keep SKILL.md under 500 lines. Move detailed content to supporting files:

```markdown
## Additional resources
- Domain-specific examples: [examples.md](examples.md)
- Full failure mode catalog: [failure-modes.md](failure-modes.md)
- Output templates: [templates.md](templates.md)
```

Link directly from SKILL.md — deeply nested references (file linking to another file) may not be read by the AI.
