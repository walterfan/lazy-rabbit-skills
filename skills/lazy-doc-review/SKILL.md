---
name: lazy-doc-review
description: >-
  Reviews and selectively rewrites reader-facing documents so humans can read
  and understand them with less effort. Detects uncertain facts, excessive
  verbosity, weak structure, ambiguous language, buried conclusions,
  unsupported agreement, weak reasoning, and mismatched audience assumptions.
  Use when the user asks to review, edit, simplify, shorten, clarify, refine, or
  humanize an
  AI-generated document, RFC, design doc, runbook, report, proposal, memo, or
  article—even if they do not explicitly name this skill.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - document-review
  - writing
  - critical-thinking
  - cognitive-load
category: writing
use_cases:
  - "Review and refine an AI-generated reader-facing document"
  - "Reduce verbosity and cognitive load without losing meaning"
  - "Find unclear reasoning, unsupported facts, and audience mismatches"
  - "Turn a difficult draft into a concise, orderly, human-readable document"
platforms:
  - claude-code
  - codex
  - cursor
visibility: public
license: CC-BY-NC-ND-4.0
metadata:
  author: walterfan@ustc.edu
  version: "0.1"
---

# lazy-doc-review

Review and selectively rewrite documents for human comprehension. Optimize for
the reader's time and cognitive load, not for length, polish, or praise.

Be a critical friend: remain constructive without treating the author's premise
as true merely because it is fluent or confidently stated.

## Contract

- **scope_in**:
  - Reader-facing drafts such as RFCs, design documents, runbooks, reports,
    proposals, memos, articles, tutorials, and operational instructions.
  - Plain text, Markdown, or another format that can be read reliably.
  - Documents written by people or generated with AI.
- **scope_out**:
  - Source-code review, binary or unreadable files, and translation-only tasks.
  - Raw brainstorming notes not yet intended for readers; offer a light
    organization pass instead of publication-level compression.
  - Specialist approval for legal, medical, compliance, safety, or academic
    claims; identify concerns and recommend qualified review.
- **Preconditions**:
  - The document or a readable path is available.
  - The intended audience is known or can be reliably inferred.
  - Source material is available when the user expects factual verification.
- **Postconditions**:
  - The output states the audience, purpose, and central idea.
  - Material problems are prioritized and paired with concrete remedies.
  - The refined document preserves the author's intent and necessary detail.
  - Important factual uncertainty is resolved or marked `待确认`.
  - The result does not invent facts, evidence, quotations, links, or intent.

## The Four Review Questions

Use these questions throughout the review:

| Question | Reviewer responsibility | If unclear |
| --- | --- | --- |
| **Are the facts accurate?** | Separate facts, inferences, opinions, and unknowns. Check supplied evidence when available. | Ask the author to confirm the claim or provide a source. Mark it `待确认`; do not fill the gap. |
| **Are the ideas clear?** | Determine whether the central idea, premises, reasoning, and conclusion form a coherent chain. | Identify the break and recommend how to reorder, add, remove, or qualify content. |
| **Is the language clear?** | Judge structure, paragraphs, sentences, terminology, references, ambiguity, and redundancy from the document itself. | Supply a clearer and more concise formulation directly. |
| **Who is it for?** | Identify the reader's existing knowledge, purpose, and expected action or decision. | Ask the author to clarify the audience before calling the rewrite final. |

Only factual certainty and audience identity require author clarification when
the available material cannot answer them. Clarity of thought and language are
review judgments: diagnose them and propose repairs rather than asking the
author to perform the review.

## Execution

### Phase 1: Establish the reading contract

- **Entry**: a document or readable path has been provided.
- **Steps**:
  1. Read the complete document when practical. For a large document, read its
     overview and structure first, then process coherent sections.
  2. Identify the document type, intended audience, reading purpose, and what
     the reader should understand, decide, or do afterward.
  3. Infer these only when the text or conversation provides strong evidence.
  4. If the audience remains unclear, ask one focused question and pause the
     final rewrite. A diagnosis may still be delivered.
  5. Determine whether fact-checking means internal consistency, checking
     supplied sources, or external verification. Do not silently broaden it.
- **Exit**: audience and purpose are explicit enough to judge relevance,
  terminology, detail, and structure.
- **On fail**: identify the missing input precisely; do not manufacture a
  generic audience or purpose.

### Phase 2: Inspect facts and ideas

- **Entry**: Phase 1 has established the reading contract.
- **Steps**:
  1. Write a private one-sentence statement of the central idea and a short
     outline of the reasoning. Use it to test the draft, not to inflate output.
  2. Classify important claims as fact, inference, opinion, or unknown.
  3. Flag contradictions, missing premises, non sequiturs, buried conclusions,
     and conclusions stronger than their evidence.
  4. Check supplied sources when they are available. Treat an unverified claim
     as unverified, not automatically false.
  5. If a disputed fact could change the conclusion, ask the author before
     finalizing. If it is local, mark it `待确认` and continue elsewhere.
  6. Recommend specific repairs to unclear thinking without choosing a new
     position for the author.
- **Exit**: the reasoning is understandable, and every material factual gap is
  resolved, isolated, or ready to ask about.
- **On fail**: produce the argument break and the smallest useful clarification
  question instead of polishing uncertainty into confidence.

### Phase 3: Inspect reader effort

- **Entry**: Phase 2 has mapped the ideas and uncertainty.
- **Steps**:
  1. Put the purpose or conclusion early enough to orient the reader.
  2. Keep one main job per section and one main idea per paragraph.
  3. Order content by reader dependency: what the reader must know first comes
     first.
  4. Remove repeated claims, duplicated background, generic summaries,
     ceremonial transitions, and content that can be deleted without losing
     information.
  5. Replace overloaded sentences, vague references, abstract filler, and
     unnecessary jargon with direct language.
  6. Explain only terminology the intended audience is unlikely to know.
  7. Preserve constraints, risks, qualifications, counterexamples, and concrete
     examples because compression must not erase meaning.
  8. Use countable budgets—sentences, bullets, or sections—when a length limit
     helps. Avoid relying on vague requests such as "make it concise."
- **Exit**: every retained section earns the reader's attention.
- **On fail**: preserve the disputed passage, flag why it is hard to compress,
  and request the missing meaning or constraint.

### Phase 4: Report material findings

- **Entry**: the review has identified fact, reasoning, audience, and language
  issues.
- **Steps**:
  1. Rank findings by reader impact:
     - **Blocking**: prevents a reliable final rewrite, such as an unknown
       audience or central disputed fact.
     - **Important**: materially harms comprehension, reasoning, or credibility.
     - **Suggestion**: useful compression or polish that does not change meaning.
  2. Give each finding a location or short excerpt, the problem, its reader
     impact, and a concrete revision.
  3. Omit empty severity groups and minor preferences that do not help readers.
  4. Do not pad the review with praise, generic advice, or invented objections.
- **Exit**: the author can act on every reported finding.
- **On fail**: reduce the report to the highest-impact findings rather than
  delivering an exhaustive but unusable list.

### Phase 5: Produce the targeted rewrite

- **Entry**: the audience is known and all central factual blockers are resolved
  or explicitly deferred.
- **Steps**:
  1. Preserve the author's position, facts, qualifications, terminology, and
     necessary examples.
  2. Put the main point first and reorganize supporting content only as much as
     comprehension requires.
  3. Delete losslessly compressible prose and rewrite ambiguous or overloaded
     sentences.
  4. Use headings and parallel lists only when they make relationships clearer.
  5. Use What / Why / How / Example only if the original structure obstructs
     understanding. Preserve a sound domain-specific structure.
  6. Mark unresolved local facts `待确认`. Do not convert inference into fact.
  7. Match the document's language unless the user requests another language.
  8. Briefly state what changed; do not append a second essay about the rewrite.
- **Exit**: the reader can quickly find what the document is about, why it
  matters, its essential content, and the expected action or judgment.
- **On fail**: label the rewrite as a partial draft and list only the facts or
  audience decisions that block finalization.

## Output Format

Use this compact structure. Omit empty sections.

```markdown
## Review verdict
[One sentence: ready, draft with issues, or blocked pending clarification.]

**Audience:** ...
**Purpose:** ...
**Central idea:** ...

## Questions for the author
1. [Only unresolved factual or audience questions.]

## Key findings
### Blocking
- **[Location]** Problem — reader impact. Suggested change.

### Important
- ...

### Suggestions
- ...

## Refined document
[Targeted rewrite, or a clearly labeled partial draft when blocked.]
```

Keep the review shorter than the document unless a short input needs substantive
clarification. Give most of the output budget to the refined document.

## Verification

### Hard gates

| Gate | Pass condition | On fail |
| --- | --- | --- |
| Audience | Audience is explicit before the rewrite is called final | Ask one focused question; label any rewrite partial |
| Factual integrity | Important uncertainty is resolved or marked `待确认` | Restore the qualification and ask for confirmation |
| Intent preservation | No new author position, fact, evidence, quote, or link appears | Remove the invention and return to Phase 2 |
| Meaning preservation | Central idea, necessary reasoning, constraints, and risks survive compression | Restore the missing content in a clearer form |
| Actionable findings | Every Blocking or Important finding has a concrete remedy | Add the smallest specific revision |

### Soft gates

| Gate | Pass condition | On fail |
| --- | --- | --- |
| Orientation | Purpose and central idea are easy to find | Move them earlier |
| Flow | Sections follow reader dependency | Reorder without changing meaning |
| Paragraph focus | Each paragraph has one dominant idea | Split or merge as needed |
| Information density | Repetition and generic transitions are absent | Run another lossless-compression pass |
| Audience fit | Detail and terminology suit the named reader | Remove known basics or explain unfamiliar terms |
| Review economy | Commentary contains only material findings | Delete low-impact commentary |

Before delivery, answer the four review questions again. If any answer conflicts
with the rewrite, return to the relevant phase.

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
| --- | --- | --- |
| The result is shorter but less useful | Compression removed evidence, risk, or constraints | Restore information that changes understanding or action |
| The rewrite sounds certain about weak claims | Inference or opinion was promoted to fact | Reclassify the claim and mark uncertainty |
| The document remains difficult for its readers | Audience knowledge was inferred too broadly | Clarify the audience and repeat Phase 3 |
| The review is nearly as verbose as the document | Too many minor findings or explanations | Keep only material issues and one concrete remedy each |
| The structure feels generic | What / Why / How / Example was applied mechanically | Restore the domain-specific structure that serves the reader |
| The skill agrees with a weak premise | Fluency or user preference replaced evidence | Re-run the fact and reasoning checks as a critical friend |
| The author is asked to diagnose their own prose | Review responsibility was pushed back to the author | Ask only about facts or audience; directly repair ideas and language |

### Boundary examples

- **Minimal input**: a clear two-paragraph memo may need no rewrite. Say so and
  avoid editing for its own sake.
- **Maximum input**: for a large manual, review structure first, then process
  coherent sections while maintaining one findings list.
- **Edge of scope**: for brainstorming notes, offer organization and identify
  unknowns, but do not impose publication-level brevity prematurely.
- **Out of scope**: for a request to approve a legal conclusion, identify
  clarity and evidence gaps, then recommend qualified legal review.

### Improvement triggers

- Readers repeatedly need follow-up explanations after a document passes review.
- Users frequently restore material removed by the rewrite.
- The skill asks authors to clarify ideas or language it should diagnose itself.
- Trigger evaluations confuse document review with code review, translation, or
  fact-checking-only requests.
- A recurring document type needs a specialized output structure or vocabulary.

## Example

**Input excerpt:**

> Given the importance of reliability, it is worth noting that we should
> probably consider adding retries in order to improve the situation.

**Review:** The sentence hides the action, gives no failure condition, and
treats an unverified benefit as fact.

**Refinement:**

> Add bounded retries for transient failures. `待确认`: retryable error classes,
> maximum attempts, and the latency budget.

The refinement is shorter because it is more specific, not merely because it
uses fewer words.

## Source Principles

- [Why AI-generated documents contain so much filler](https://www.fanyamin.com/blog/2026-08-15-ai-verbose-doc.html): fixed structure, countable information budgets, audience awareness, and lossless compression expose missing thinking and reduce reader cost.
- [AI should be a critical friend, not a yes-man](https://www.fanyamin.com/blog/2026-08-15-ai-sycophancy-critical-friend.html): distinguish fact, inference, opinion, and unknown; challenge premises with evidence and proportion rather than automatic agreement.
