---
name: TODO-skill-name
description: >-
  TODO: Write in third person. State WHAT the skill does AND WHEN to use it.
  Include specific trigger terms. End with "even if not explicitly asked" to
  ensure the AI applies it proactively.
version: 0.1.0
author: TODO-your-name
tags:
  - TODO-tag1
  - TODO-tag2
category: TODO-category
use_cases:
  - "TODO: describe a concrete use case"
platforms:
  - claude-code
visibility: public
---

# TODO-skill-name

TODO: One-line summary of what this skill does and for whom.

## Contract

- **scope_in**: TODO: what inputs does this skill accept?
  - e.g., Python source files, customer support tickets, marketing briefs
- **scope_out**: TODO: what inputs should this skill refuse?
  - e.g., binary files, legal documents, inputs in unsupported languages
- **Preconditions**: TODO: what must be true before execution?
  - e.g., user has provided the input document, required CLI tools installed
- **Postconditions**: TODO: what must be true after execution?
  - e.g., output follows template, all required sections present, length within bounds

## Execution

### Phase A: Gather context
- Entry: user has provided input matching scope_in
- Steps:
  1. TODO: first step
  2. TODO: second step
- Exit: TODO: what is true when this phase is done?
- On fail: TODO: what to do if this phase fails

### Phase B: Process
- Entry: Phase A complete
- Steps:
  1. TODO: main processing steps
- Exit: TODO: exit criteria
- On fail: TODO: failure handling

### Phase C: Deliver
- Entry: Phase B complete
- Steps:
  1. Verify all postconditions
  2. Present output to user
- Exit: user has received the output
- On fail: deliver partial output with clear notes on what's missing

## Verification

### Hard gates
| Gate | Condition | On fail |
|------|-----------|---------|
| Non-empty output | Output has content | Retry once, then stop with error |
| Template compliance | All required sections present | Re-generate with explicit section list |
| TODO | TODO | TODO |

### Soft gates
| Gate | Condition | On fail |
|------|-----------|---------|
| Length target | Output within expected range | Warn user |
| TODO | TODO | TODO |

## Feedback

### Failure modes
| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Skill never triggers | Description too passive | Add specific trigger terms |
| Output is generic | Domain knowledge missing | Add examples and context |
| TODO | TODO | TODO |

### Boundary examples
- **Minimal input**: TODO
- **Maximum input**: TODO
- **Edge of scope**: TODO

### Improvement triggers
- TODO: when should this skill be revised?
