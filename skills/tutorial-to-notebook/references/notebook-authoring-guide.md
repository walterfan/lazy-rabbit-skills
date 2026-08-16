# Notebook Authoring Guide (Phase 2)

The converter gives you cells. This guide turns those cells into a *living
tutorial*. Work through it in order; each move has a concrete before/after.

## 0. The bar to clear

> A stranger opens the notebook, runs the cells top to bottom, and gets a real
> success. When they slip in a predictable way, the notebook already warned them.

If the finished notebook does not meet that bar, it is still just prose with run
buttons.

## 1. Setup cell — always first, always self-contained

Insert one code cell at the top that does imports + config + auth, and nothing
that can fail for a boring reason later.

```python
import os, requests

BASE = "https://api.example.com/v1"
# OAuth2 / sandbox injects this; never hardcode a real token.
TOKEN = os.environ["API_TOKEN"]
headers = {"Authorization": f"Bearer {TOKEN}"}
```

Rules:

- Secrets come from `os.environ` or an OAuth2-injected token. Never inline.
- If the reader must set something, say so in a Markdown cell right above:
  "点右上角连接账号授权后，`API_TOKEN` 会自动注入。"
- Keep imports here so later cells stay focused on the teaching point.

## 2. One runnable step per cell, state flowing forward

Each code cell should be a single teachable action. The output of an early cell
(a token, an id) is consumed by a later one — in that order, never backward.

Bad (forward reference — cell 1 uses something defined in cell 2):

```python
r = requests.get(f"{BASE}/things/{thing_id}")   # thing_id not defined yet!
```

Good (create, then use):

```python
# cell A
thing_id = requests.post(f"{BASE}/things", headers=headers).json()["id"]
print(thing_id)          # → 'thing_42'
```
```python
# cell B — uses thing_id from cell A
requests.get(f"{BASE}/things/{thing_id}", headers=headers).json()
```

Prefer many small cells over one wall of code: every step gets its own run
button and its own "did it work?" moment.

## 3. Annotate expected output

The reader must know what success looks like *before* they run. Use a trailing
comment or a one-line Markdown note.

```python
print(job_id)            # → 'job_7c3e1a'
```

For a structured response, show the shape, trimmed:

```python
resp.json()              # → {'status': 'done', 'text': '...'}
```

This is also what a downstream AI tutor compares against when the reader's output
differs.

## 4. Mark editable parameters

Learning is fiddling. Point at the knob and invite the reader to turn it.

```python
data = {"text": "hello", "target": "en"}   # 改成 ja / fr / de 再跑一次看看
```

Pick parameters where a change produces a visibly different, safe result. Do not
invite edits that cost money or mutate shared state.

## 5. Gotcha markers — the highest-value move

At every place a newcomer predictably slips, insert a marker: a Markdown callout
that names the **symptom**, the **cause**, and the **fix**. This is what makes the
tutorial feel like a chaperone, and it is the contract a `code-tutor` skill keys
off.

Format (keep it consistent so it is machine-findable):

```markdown
> ⚠️ **常见坑 · 异步任务**
> 症状：上一步刚提交，这里就查结果，拿到 `{"status": "processing", "text": null}`，没报错但也没内容。
> 原因：转写是异步的，后台还没跑完。
> 修复：轮询直到 `status == "done"`（小文件够用），生产环境改用 webhook。
```

The common gotcha families to scan for:

| Family | Symptom the reader sees |
|---|---|
| Auth ordering | 401 because they skipped the token step |
| Async / polling | `processing` / empty result, no error |
| Pagination | only the first page of results, silently |
| Rate limit | 429 after a loop |
| Content-Type / encoding | 400 on upload with the wrong header |
| Idempotency / retries | duplicate side effects on re-run |

Deliberately let the notebook *walk into* one such gotcha (a cell that returns the
confusing-but-not-erroring result), then resolve it in the next cell. Experiencing
the trap teaches more than a warning box alone.

## 6. Verification cell — prove the whole chain

End the golden path with a cell that asserts success, so the reader (and any
grader) gets an unambiguous "it worked".

```python
assert result["status"] == "done" and result["text"], "转写没成功，回到上一步看轮询"
print("✅ 全链路跑通：", result["text"][:40], "...")
```

## 7. Prune to the golden path

Everything not on the main flow goes below a divider so the first screenful is
pure signal.

```markdown
---
## 进阶 / Beyond the golden path
错误处理、分页、批量、webhook 配置……需要时再看。
```

## 8. Final read-through

- Does the first code cell run without the reader configuring anything except
  the injected token?
- Does every later cell only use variables an earlier cell defined?
- Is there exactly one clear success at the end?
- Would a non-expert know what to type differently to experiment?
- Any secret anywhere? (There must be none.)

## Anti-patterns

| Smell | Fix |
|---|---|
| One giant code cell | Split into one step per cell |
| Cell uses an undefined variable | Reorder; state must flow forward |
| No expected output shown | Add `# → ...` or a Markdown note |
| Warning-only, reader never hits the trap | Let one cell walk into the gotcha, then fix it |
| Hardcoded key `sk-live-...` | Replace with `os.environ[...]`, note it |
| 20 steps, no golden path | Cut to 3–7, push the rest below the divider |
