---
name: tour-builder
description: >-
  Use when a tutorial has to teach a UI/console page (not just code) — turn a
  plain-markdown step script into a runnable interactive product tour that
  overlays the real page. Generates a driver.js tour module, a framework-
  agnostic tour.json, and an anchor contract (the data-tour-id attributes the
  page must add). Steps anchor to stable data-tour-id rather than brittle CSS
  selectors; tour text is HTML-escaped so author content can't inject markup;
  destructive steps and secret-looking text are flagged before shipping. The
  UI-page counterpart of api-to-sandbox in the living-tutorial skill family.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - product-tour
  - onboarding
  - ui-guidance
  - driver-js
  - developer-experience
category: dev-tools
use_cases:
  - "Generate an interactive tour that walks a user through a console/backend UI"
  - "Produce the data-tour-id anchor contract a frontend must add for a tour"
  - "Turn a written step list into a runnable driver.js tour with no hand-coding"
  - "Catch brittle selectors, unmarked destructive steps, and leaked secrets in a tour"
platforms:
  - claude-code
visibility: public
---

# tour-builder

Some things you can't teach with code — you teach them by pointing at the screen:
“click here, then here, and *don't* touch that red button unless you mean it.”
This skill turns a plain-markdown step script into an interactive tour that
overlays the real page, plus the contract the page must satisfy to keep that
tour from rotting.

This is the **UI-page half** of the living-tutorial family. Where
`api-to-sandbox` gives a *code* runtime a safe box to run in, `tour-builder`
gives a *page* an on-screen guide. Same goal — “打开就会用” — different surface.

> The one opinion that makes tours survive: **anchor to `data-tour-id`, never to
> CSS selectors.** A tour wired to `.btn-primary > span:nth-child(2)` breaks the
> first time a designer touches the CSS. A tour wired to
> `[data-tour-id="btn-create-key"]` survives restyles, refactors, and A/B tests.
> The generator warns on raw selectors and emits the anchor contract so frontend
> and tour stay in lockstep.

## What it generates

Into an output directory:

| File | Purpose |
|---|---|
| `tour.js` | driver.js v1 ES module — `steps` + a `startTour()` you call from the page |
| `tour.json` | Framework-agnostic step list (for tests, or a Shepherd.js/other renderer) |
| `anchors.md` | The **contract**: which `data-tour-id` each element needs, with the destructive/action columns |

## Input format

Plain markdown, one step per `##` heading. Fields are optional `key: value`
lines right under the heading; everything else is the tooltip body.

```markdown
# Tour: Console onboarding

## Open the API Keys page
target: nav-api-keys
side: right
Click here to manage your credentials.

## Revoke a leaked key
target: btn-revoke
side: left
action: click
destructive: true
Revoking is instant and irreversible. Confirm the key id first.
```

Fields: `target` (required — the anchor id), `side` (top/right/bottom/left/over),
`action` (informational: click/input/…), `destructive` (true/false). See
`templates/sample_tour.md`.

## Ask First (only if it changes the output)

- **Which page state** the tour assumes (logged in? empty account? a key already
  created?) — a tour that points at an element that isn't rendered yet just fails.
- **Framework** if not driver.js (the JSON is renderer-agnostic; say so and hand
  it to Shepherd.js/Intro.js instead — see the reference).

If the step script is self-evident, infer and proceed.

## Workflow

### 1. Write the step script

Draft the tour in markdown (or have the user hand you the console's page and
describe the flow). Keep steps in the order a newcomer actually moves. One
concept per step; lead with the verb.

### 2. Generate

```bash
python scripts/gen_tour.py TOUR.md --out ./tour
python scripts/gen_tour.py TOUR.md --out ./tour --name "Onboarding"
```

The generator, without opening a browser:

- HTML-escapes every title/body (injection-safe),
- warns on **raw CSS selectors** (prefer `data-tour-id`),
- flags **destructive** steps and auto-warns on delete/revoke/rotate wording,
- **refuses to generate** if a step is missing its `target` or looks like it
  narrates a real secret.

### 3. Wire it into the page

- Add each `data-tour-id` from `anchors.md` to the matching element.
- `npm i driver.js`, then `import { startTour } from "./tour.js"` and call
  `startTour()` (e.g. on a “Take the tour” button or first-run).
- For destructive steps, keep a real confirm dialog — the tour points, it does
  not click for the user.

### 4. Validate

Run the checks in Verification: the JS parses (`node --check tour.js`), every
step has a stable anchor, no unresolved warnings you meant to fix.

## Security

Tours run in the user's browser and render author text into the DOM — so:

- **HTML-escape all step text** (the generator does this). Never bypass it to
  inject raw HTML from an untrusted source; that is a DOM-XSS sink.
- **No secrets in step text.** The generator blocks obvious keys/tokens/JWTs.
  Tours are screenshotted and screen-shared — treat every word as public.
- **The tour never acts for the user.** It highlights and explains; destructive
  actions still go through the page's own confirm. Don't auto-click.
- **Anchors, not selectors.** Beyond reliability, `data-tour-id` avoids coupling
  the tour to incidental markup.

## Verification

Block delivery until:

- Every step has a `target`; the generator exited 0 (no errors).
- `tour.js` parses: `node --check tour.js` (if node is available).
- `anchors.md` lists a `data-tour-id` for every step; destructive steps are
  marked and have a confirm on the page side.
- No step text contains a real secret (generator enforces; eyeball too).

Warn, but still deliver:

- A step used a raw CSS selector — flagged; recommend a `data-tour-id`.
- A step body was empty — the tooltip will be blank; add guidance.
- `side` was invalid and defaulted to bottom.

## Delivery Summary

- Output dir and files written (`tour.js`, `tour.json`, `anchors.md`).
- Tour name and step count.
- The list of `data-tour-id` anchors the frontend must add.
- Destructive steps that need a confirm.
- Any warnings (raw selectors, empty bodies).

## Skill Family

- **`api-to-sandbox`** is the code-runtime counterpart; this is the UI-page one.
  A good living tutorial for a console often uses *both*: a tour to reach the
  right page, a sandbox to run the call it teaches.
- **`tutorial-to-notebook`** handles the executable-code strand; a tour handles
  the click-through strand. Cross-link them from the same tutorial.
- **`faq-harvester`** can feed real “I got stuck on step 3” reports back into new
  or clearer tour steps.

## Resources

- Generator: `scripts/gen_tour.py`
- Design + anti-brittleness guide: `references/tour-design-guide.md`
- Sample input: `templates/sample_tour.md`

<!-- last_updated: 2026-08-01 -->
<!-- maintained-by: walter.fan -->
