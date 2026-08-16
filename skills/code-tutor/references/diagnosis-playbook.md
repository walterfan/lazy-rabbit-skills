# Diagnosis Playbook

How to debug a learner's cell fast and correctly. The golden rule: **ground every
claim in what they actually ran**, and always ask "did they even get an error?"
before anything else.

## Step 0: hard error or soft gotcha?

| | Hard error | Soft gotcha |
|---|---|---|
| Signal | Traceback, HTTP 4xx/5xx | No error at all |
| Learner feels | "It crashed" | "It ran but… nothing / wrong?" |
| Fix is usually | A typo, a missing arg, a wrong header | Conceptual (async, pagination, consistency) |
| Where to spend words | The Fix | The Cause |

`build_context.py` sets `has_hard_error`. But also trust the learner: if they
reported no error text, it is a soft gotcha even if the word "error" appears
nowhere. Soft gotchas are where people quit — take them seriously.

## The gotcha families (match symptom → family → fix)

### Auth ordering
- **Symptom:** 401 / 403; or `build_context` reports `token`/`headers` as
  used-but-undefined.
- **Cause:** they ran the call before (or without) the cell that fetches the
  token.
- **Fix:** run the auth cell first; then re-run. Point at the exact prior cell.

### Async / polling (the flagship soft gotcha)
- **Symptom:** `{"status":"processing"}`, `text: null`, empty body — no error.
- **Cause:** the operation is a background job; the result is not ready the
  instant you submit.
- **Fix:** poll until `status == "done"` (small jobs), or configure a webhook
  (production). Show the loop with a `sleep`.

### Pagination
- **Symptom:** only ~20/50/100 items though more exist; counts look truncated.
- **Cause:** the endpoint pages; they read only page one.
- **Fix:** follow `next`/`cursor`/`page` until exhausted. Warn about unbounded
  loops on huge collections.

### Rate limit
- **Symptom:** 429 after a loop; intermittent failures under load.
- **Cause:** too many calls too fast.
- **Fix:** back off (respect `Retry-After`), batch, or cache. Not "retry harder".

### Content-Type / encoding
- **Symptom:** 400/415 on upload or POST; server "can't parse" the body.
- **Cause:** wrong `Content-Type`, or JSON-encoding a file / file-encoding JSON.
- **Fix:** match the body to the header (`files=` vs `json=` vs `data=`).

### Idempotency / retries
- **Symptom:** duplicate resources or double charges after re-running a cell.
- **Cause:** a non-idempotent POST run more than once.
- **Fix:** use an idempotency key, or make the cell check-then-create. **Warn
  before proposing any re-run of a mutating call.**

### Eventual consistency
- **Symptom:** you just created X, immediately read it, and it's "not found".
- **Cause:** the read replica hasn't caught up.
- **Fix:** retry the read with a short backoff; don't assume read-your-writes.

## Using the static findings

`build_context.py` does two checks so you don't have to eyeball it:

- **`undefined_names` non-empty** → almost always "you skipped a step". This is
  frequently the *entire* diagnosis; lead with it. Example answer: "`headers` on
  line 2 was never defined — run cell 0 (the setup/auth cell) first."
- **`syntax_error` set** → point at `line`/`msg` directly; no need to theorize.

These are heuristics: a name defined via `exec`, `globals()[...]`, `import *`, or
injected by the sandbox env will show as "undefined" falsely. If the learner
insists they ran the earlier cell, trust them and move on to runtime causes.

## Writing the fix

- It must run **as-is** in their notebook: only in-scope variables, correct
  order.
- Prefer the tutorial's own patterns (same client, same helper) over a novel
  approach — consistency helps them learn.
- Keep it minimal: the smallest change that makes the step succeed, not a
  refactor.
- If the honest answer is "I'm not sure this field exists," say that and point at
  the reference. Do not emit a confident guess.

## Tone

Short, calm, specific. A stuck beginner is already frustrated; do not lecture,
do not pad. Locate → Cause → Fix → one-line why. Then stop.
