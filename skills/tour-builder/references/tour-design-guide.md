# Tour Design Guide: guides that don't rot, don't annoy, don't lie

A product tour is easy to make and easy to make badly. The two failure modes are
**brittle** (breaks when the UI changes) and **annoying** (fires when nobody asked,
narrates the obvious). This guide is how to avoid both, plus the security notes
that matter when your "documentation" runs as code in the user's browser.

## 1. Anchor to `data-tour-id`, never to CSS

The single biggest reason tours break: they target `.btn-primary`,
`nav > ul > li:nth-child(3)`, or `#app-root .sidebar a`. All three change the
moment someone restyles, reorders a menu, or renames a class. The element is
still there; the selector no longer finds it; the tour dies silently.

Fix: give the *element* a stable, semantic id that exists only for the tour (and
tests):

```html
<button data-tour-id="btn-create-key" class="whatever-the-designer-wants">
  Create key
</button>
```

`data-tour-id` is a contract. Designers can restyle freely; as long as the
attribute rides along, the tour holds. The generator emits `anchors.md` precisely
so the frontend knows which attributes to add. Keep that list in version control
next to the component, and a lint/test can assert every `data-tour-id` the tour
references actually exists in the DOM.

## 2. One step, one idea, one verb

- Lead with the action: “**点这里**创建 key”, not “这个按钮是用来创建 key 的”.
- Say *why* only when it changes behavior: “创建后密钥只显示一次，**立刻复制**”.
- If a step needs three sentences, it's probably two steps.
- Order steps the way a real newcomer moves, not the way the menu is laid out.

## 3. Don't ambush the user

- **First-run or on-demand, not every load.** Fire once, then offer a “重新开始
  导览” entry point. Persist “seen it” (localStorage / a user flag).
- **Let them leave.** `allowClose: true`. A tour you can't escape is a hostage
  situation.
- **Assume the right page state.** A step that points at `btn-revoke` fails if no
  key exists yet. Either seed the state, gate the step, or branch the tour.
- **Advance on the real event when it matters.** For a “click Create” step, let
  the user's actual click advance the tour instead of a fake Next button — it
  teaches the real muscle memory. (driver.js: drive to the next step from your
  own click handler.)

## 4. The tour points; it does not act

Never let a tour click destructive buttons “to demonstrate.” Highlight the
Revoke button, explain the consequence, and let the user go through the page's
own confirm dialog. This is why the generator flags `destructive: true` steps and
auto-warns on delete/revoke/rotate wording — those are exactly the steps where a
helpful auto-click becomes an incident.

## 5. Security: your docs are now executing code

A tour renders author-supplied text into the DOM and often as HTML (driver.js
`description` allows markup). That makes it a potential DOM-XSS sink.

- **Escape at generation time.** The generator HTML-escapes every title/body, so
  a stray `<img onerror=...>` in the source becomes inert text. Don't add a
  “render raw HTML” bypass fed by untrusted content.
- **Never narrate secrets.** Tours get screenshotted, recorded, and screen-shared
  in onboarding calls. A real key in a tooltip is a leaked key. The generator
  refuses to build if a step looks like it contains one.
- **No inline event handlers / no remote scripts** in tour content. Keep the tour
  module a static asset; don't build step HTML by string-concatenating user data.

## 6. driver.js quick reference (the default renderer)

```js
import { startTour } from "./tour.js";
document.querySelector("#take-the-tour").addEventListener("click", () => startTour());
```

- `steps[].element` — the `[data-tour-id="…"]` selector (generated for you).
- `popover.title` / `popover.description` — escaped text (generated).
- `popover.side` — top/right/bottom/left/over.
- Global options you may pass to `startTour({...})`: `showProgress`,
  `allowClose`, `nextBtnText`, `onDestroyed` (fire your “mark as seen” here).

## 7. Not driver.js? Use the JSON

`tour.json` is renderer-agnostic. Mapping to other libraries:

| Field | driver.js | Shepherd.js | Intro.js |
|---|---|---|---|
| anchor | `element` | `attachTo.element` | `element` |
| title | `popover.title` | `title` | (in `intro` html) |
| body | `popover.description` | `text` | `intro` |
| placement | `popover.side` | `attachTo.on` | `position` |

Whatever the renderer, keep the two rules: **escape the text**, **anchor by
`data-tour-id`**.

## 8. When a tour is the wrong tool

- **Deep, branching workflows** → a real interactive sandbox or a short video,
  not a 20-step tour nobody finishes.
- **One-off admin task** → a screenshot with callouts beats maintaining a tour.
- **Something that changes weekly** → the tour will always be stale; document the
  principle, not the exact clicks.

A tour is best for the stable, linear, first-run “where is everything” path. For
the rest, hand off to the other living-tutorial pieces.
