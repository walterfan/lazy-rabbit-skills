# Harvesting Guide: turn failures into the next revision

A tutorial is never finished; it's just at some point in a loop. People use it,
fail in specific ways, and those failures are the highest-signal to-do list you
will ever get — because they're what *actually* happened, ranked by how often.
This guide is how to run that loop without lying to yourself.

## The loop, in one picture

```
tutorial-to-notebook / api-to-sandbox / tour-builder   →  learner uses it
                        ↑                                        ↓
                 enrich 原因/修复                          hits a real failure
                        ↑                                        ↓
   faq-harvester: cluster + rank + coverage gap   ←   code-tutor / support ticket
```

The harvester is the upward arrow: it takes what broke and tells you what to fix,
in priority order, and in a format that pastes straight back in.

## Why cluster, and how it decides

Ten tickets that are all "I got a 401" should be **one** FAQ entry with count 10,
not ten entries. Clustering turns raw volume into priorities. The key it groups by,
in order:

1. **HTTP status.** `401` vs `429` vs `500` is the strongest, cleanest signal for
   an API tutorial. All the 401s land together however they're phrased.
2. **Exception class.** `AttributeError`, `ConnectionError`, `KeyError` — the class
   name is a stable identity even when the surrounding prose differs.
3. **Keyword overlap (fallback).** For everything else, incidents join the most
   similar existing cluster if they share enough significant tokens (Jaccard ≥
   0.4), else start a new one.

Before keying, each error line is **normalized**: numbers → `<N>`, uuids/long hex
→ `<ID>`, paths → `<PATH>`, urls → `<URL>`, quoted strings → `<STR>`. That strips
the per-incident noise (this user's job id, that user's file path) so the shared
*shape* is what matters. HTTP status is deliberately kept, never blurred into
`<N>`, because it's the whole point.

## What it can't do (and why that's fine)

- **It doesn't understand meaning.** Two tickets describing the same bug in wildly
  different words may not merge. So treat every count as a **floor**, not an exact
  tally. The high-frequency clusters are trustworthy; the long tail still needs a
  human read.
- **HTTP clusters are status-level.** Two different causes of `500` share a
  cluster. That's usually the right granularity for a first FAQ pass; the up-to-3
  example lines per cluster show the variety, and you split during enrichment if
  the causes genuinely differ.
- **It never invents a fix.** `原因/修复` come out as `TODO` on purpose. A
  confidently-wrong FAQ answer wastes more time than a missing one.

## Coverage: the part that earns the skill its name

Point `--against` at the tutorials/notebooks you already ship. The harvester
parses their gotcha markers (the family's `症状/原因/修复` format, including inside
`.ipynb` markdown cells) and matches each cluster:

- **shared HTTP status** → covered (strong match);
- **enough keyword overlap** with a documented symptom → covered;
- **neither** → **NEW**, added to the work list.

`coverage.md`'s "New" table is the deliverable. It answers the only question that
matters here: *given what really breaks, what is my tutorial still silent about?*

## Running a good harvest

1. **Gather widely.** More incidents = better ranking. Pull from support tickets,
   error-tracking (Sentry-style), Slack/forum questions, and `code-tutor` logs if
   you keep them. Duplicates are data, not noise — don't dedupe upstream.
2. **Scrub for secrets on the way in and out.** Real tickets paste real tokens and
   PII. The normalizer removes ids from *signatures*, but an example line may
   still quote a pasted key. Review `faq.md`/`gotchas.md` before anyone else sees
   them. Store the raw corpus access-controlled.
3. **Use `--min-count`** to cut the long tail when you only want recurring pain
   (`--min-count 2` or `3`). Do a full run occasionally to catch rare-but-nasty
   ones too.
4. **Enrich honestly.** For each new cluster, find the *real* root cause (reproduce
   it if you can) before writing 修复. Verify, then paste the completed marker back
   into the notebook / playbook / tour.
5. **Re-run after shipping fixes.** Next cycle, those clusters should show as
   "covered". If they keep reappearing, the fix — or the doc — didn't land.

## The format contract (keep it identical)

Everything downstream depends on the marker shape. Emit exactly:

```
> ⚠️ **常见坑 · <label>**（出现 N 次）
> 症状: <the real symptom>
> 原因: <cause>
> 修复: <copy-pasteable fix>
```

`code-tutor`'s context builder and `tutorial-to-notebook`'s enrichment both read
this. Change the labels (`症状/原因/修复` or `symptom/cause/fix`) and you break the
handoff. Expected-output annotations stay `# → …`. Consistency is what makes the
five skills one system instead of five scripts.
