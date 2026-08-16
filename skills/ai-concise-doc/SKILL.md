---
name: ai-concise-doc
description: >-
  Compress, rewrite, review, translate, or structure reader-facing documents when
  brevity, fixed section quotas, lossless deletion, or bilingual structural alignment
  is an explicit goal. Use when an AI-generated document is too verbose, the user asks
  to remove filler or AI-sounding prose, a document must follow a constrained
  What/Why/How/Example structure, or editing must preserve every decision, requirement,
  number, and heading. Do not trigger for ordinary document drafting, generic
  translation, proofreading, summarization, or open-ended brainstorming unless the
  user explicitly requests these concision constraints.
---

# AI Concise Docs

Convert vague requests for brevity into a fixed structure, countable budgets, a defined
reader, and a lossless deletion check.

## Route the task

Identify the mode, artifact type, reader, decision or action, source of truth, language,
and user-supplied constraints. If the reader or decision would materially change the
level of detail, ask one concise question; otherwise make the smallest safe assumption.

Apply exactly one primary route:

| Input | Route |
|---|---|
| Existing document to compress or rewrite | Preserve headings, order, facts, and requirements; add no new content; run the deletion pass. |
| Existing document to review | Preserve the source and return `可保留`, `可无损删除/合并`, and `压缩后版本`. |
| Translation requiring alignment | Translate from the normalized source; preserve headings, paragraphs, bullets, decisions, and uncertainty. |
| Technical explainer or RFC with no template | Use the default What/Why/How/Example skeleton and budgets below. |
| Incident report, runbook, weekly report, or another known artifact | Use its native fields and assign each field a sentence or item budget. |
| Brainstorming or exploratory drafting | Do not apply compression; breadth is the requested output. |

Always honor the user's template and limits before these defaults. For compression,
review, and translation, do not browse or introduce outside facts unless the user
explicitly asks for research.

## Apply the reader contract

- State the answer, recommendation, or observable result first when the artifact permits
  one.
- Write only what the named reader needs to decide or act. Do not define terms already
  supplied by the user or known to that reader.
- Use sentence, bullet, and heading counts instead of approximate word or character
  limits.
- Distinguish facts, inferences, decisions, and unknowns. Use `待确认` in Chinese,
  `TBD` in English, or the user's chosen marker.
- List only supplied or actually verified sources. Never invent links, titles, metrics,
  examples, or citations.

## Use the default technical-document template

Use this skeleton only for a technical explainer or RFC when the user supplied no
template:

```markdown
# What

## Abstract

# Why

# How

# Example

# Conclusion

# Reference
```

Apply these default budgets:

| Section | Budget |
|---|---|
| What | One sentence naming the subject or change. |
| Abstract | At most three sentences; put the outcome first. |
| Why | Two or three bullets covering the problem, impact, and consequence of not acting. |
| How | At most five mechanisms or steps; each gets at most two sentences. |
| Example | One concrete, runnable or verifiable example; otherwise mark it `待确认` or `TBD`. |
| Conclusion | At most three bullets, one sentence each. |
| Reference | Only supplied or verified sources. |

Treat the budgets as hard defaults. Exceed one only when required to preserve a
requirement, exception, risk, or user-requested detail; never exceed it merely to make
the prose sound complete.

## Draft without filler

- Keep introductions, background, and summaries to at most three sentences unless the
  user sets another limit.
- Express caveats as a concrete condition, impact, and mitigation.
- Give a recommendation when evidence supports one; do not pad the answer by presenting
  every alternative with equal weight.
- Remove prompt restatements, repeated conclusions, empty transitions, generic
  definitions, pleasantries, and unrequested implementation detail.
- Remove “值得注意的是”“综上所述”“至关重要”“需要综合考虑” and similar phrases when
  they assert importance without adding information.
- Replace vague examples with a specific input, action, output, and verification step;
  otherwise expose the gap.
- Keep a transition or caveat when it expresses a real logical relationship, condition,
  or risk.

## Compress without semantic loss

Before editing, snapshot these semantic invariants:

1. Numbers, units, dates, IDs, links, names, commands, code, and quoted values.
2. Negations and normative terms such as `must`, `must not`, `should`, `不得`,
   `必须`, and `建议`.
3. Preconditions, branches, exceptions, boundaries, and cause-effect relationships.
4. Decisions, requirements, owners, actions, deadlines, risks, evidence, examples, and
   references.

Run the deletion pass:

1. Delete or merge only text that contributes no unique invariant, fact, decision,
   constraint, evidence, or action.
2. Keep each remaining paragraph focused on at least one unique information unit.
3. Preserve the original headings and order unless restructuring was requested.
4. Add no new claim while compressing. Mark a source gap instead of filling it with
   boilerplate.
5. Compare the result with the invariant snapshot. Restore anything lost or weakened;
   preserve numbers, IDs, negations, and normative terms exactly.

For a rewrite request, return the compressed document plus a short gap list only when
unresolved facts affect use. For a review request, return the three review sections
defined in the routing table.

## Translate without drift

- Normalize the source structure before translating; treat that version as canonical.
- Preserve heading, paragraph, and bullet counts, as well as examples, recommendations,
  uncertainty, and semantic invariants.
- Apply the user's terminology table. Preserve product and protocol names when no
  approved translation exists.
- Use `TBD` in English and `待确认` in Chinese unless the source uses another marker.
- Add no Overview, background, transition, explanation, or example absent from the
  source.

## Verify before delivery

| Gate | Pass condition |
|---|---|
| Route | The selected mode and document structure match the input. |
| Budget | Count the headings, bullets, and sentences; all applicable limits pass. |
| Reader | Every section helps the named reader decide or act at the expected knowledge level. |
| Position | State the recommendation, or state the exact missing evidence preventing one. |
| Invariants | Every source invariant remains; numbers, IDs, negations, and normative terms are exact. |
| Unique information | Every paragraph contains information not already stated elsewhere. |
| Source integrity | Compression and translation introduce no new factual claim or reference. |
| Alignment | Bilingual versions have matching heading, paragraph, and bullet counts. |
| Actionability | Examples and next steps contain a specific input, action, output, or owner. |

If a gate fails because the source is incomplete, expose the gap. Do not add generic
prose to make the document look finished.

