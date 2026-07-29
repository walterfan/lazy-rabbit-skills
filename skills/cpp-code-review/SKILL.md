---
name: cpp-code-review
description: >-
  Review local C++ code — files, directories, or a git diff — for the mistakes
  C++ developers most commonly ship, with a strong bias toward memory errors,
  concurrency bugs, and performance. Reviews one focus per round: correctness/UB,
  memory (RAII/ownership/leaks), concurrency (races/deadlocks/lifetime),
  performance, security, api-lifetime, testing, modern-cpp, or boost. Grounded in
  the ISO C++ Core Guidelines (Iron Rules first) plus a symptom->pitfall triage
  catalog, and cites the concrete rule id. Also reviews modern-C++ usage: it asks
  or detects the target C++ standard (C++11/14/17/20/23) and only suggests
  facilities available in that standard, and when Boost is used it gives
  Boost-specific correctness and STL-modernization suggestions. Use when a user
  wants a C++ code review, wants to check C++ changes before committing, wants to
  modernize C++, review Boost usage, or mentions use-after-move, dangling
  string_view/span, leaks, double-free, data races, deadlocks, object slicing,
  virtual destructors, iterator invalidation, or needless copies/allocations.
  Works entirely on the local filesystem and never calls GitLab or GitHub APIs.
version: 0.2.0
author: walterfan@ustc.edu
source: ISO C++ Core Guidelines
tags:
  - cpp
  - c++
  - code-review
  - memory-safety
  - raii
  - ownership
  - concurrency
  - performance
  - undefined-behavior
  - core-guidelines
category: dev-tools
use_cases:
  - "review local C++ changes before committing (git diff)"
  - "review specific C++ files or a directory"
  - "run a focused memory / concurrency / performance review round"
  - "catch common C++ mistakes mapped to the ISO C++ Core Guidelines"
  - "modernize C++ to the target standard (asks for C++ version if unknown)"
  - "review Boost usage for correctness and STL-replacement opportunities"
platforms: [claude-code, cursor, codex]
visibility: public
license: Apache-2.0
compatibility: Python 3.8+ and git. No network access or VCS server tokens required.
allowed-tools: Bash(python3:*) Bash(git:*) Read Write Grep Glob
---

# cpp-code-review

Focused **local C++ code review**. This skill reviews C++ code that already
exists on your machine — a set of files, a directory, or your working-tree
`git diff` — and produces one severity-ordered review pass per run. It is the
review companion to `lazy-cpp-dev`; use `lazy-cpp-dev` to write or fix C++, use
this to review it.

It is **local-only**: it never fetches merge requests or pull requests and needs
no GitLab/GitHub token. For GitLab MR review over the API, use `gitlab-mr-review`
instead.

The review criteria are grounded in the **ISO C++ Core Guidelines** — the Iron
Rules (crash / UB / out-of-bounds / leak) come first — plus a curated
symptom->pitfall triage catalog. It is deliberately biased toward the three
things that bite C++ hardest: **memory errors, concurrency bugs, and
performance**. Every finding cites the concrete rule id so the author can look
it up.

## Progressive detail

- [references/review-checklist.md](references/review-checklist.md) — fast,
  focus-scoped checklist and finding format
- [references/cpp-pitfalls-catalog.md](references/cpp-pitfalls-catalog.md) — a
  symptom->pitfall triage map keyed to Core Guidelines rule ids and chapters
- [references/core-guidelines/](references/core-guidelines/) — the full ISO C++
  Core Guidelines, chapter by chapter (Iron Rules in `01-iron_rules.md`),
  carrying the reason, examples, and enforcement text for each rule id

## When to use

- User has local C++ code (files, a directory, or uncommitted changes) and wants
  a review rather than an implementation
- User wants a pre-commit sanity check on a C++ diff
- User asks for a specific angle: correctness/UB, memory, concurrency,
  performance, security, api-lifetime, or testing
- User mentions C++ pitfalls: use-after-move, dangling `string_view`/`span`,
  leaks, double-free, data races, deadlocks, slicing, virtual destructors,
  iterator invalidation, Rule of Five, needless copies/allocations

## When not to use

- Reviewing a remote GitLab MR or GitHub PR by URL -> use `gitlab-mr-review`
- Writing, fixing, refactoring, or modernizing C++ -> use `lazy-cpp-dev`
- Non-C++ code (pure C build-only, Go -> `golang-code-review`, etc.)
- Design-doc or architecture review rather than code review

## Contract

- **scope_in**: Review local C++ source obtained from file/dir paths or
  `git diff`/`git diff --cached`; one review focus per round; findings grounded
  in the shown code and cited to the ISO C++ Core Guidelines rule id where
  applicable.
- **scope_out**: GitLab/GitHub API calls; writing or fixing code; multi-focus
  "review everything" in a single pass; non-C++ review; posting comments to any
  server.
- **Preconditions**: `python3` and `git` available; the target C++ code is on
  the local filesystem; for `--diff`/`--staged` the repo has a valid `HEAD`.
- **Postconditions**: One coherent, severity-ordered review pass for the chosen
  focus; scope (included/omitted files) stated; no invented findings; any budget
  trimming noted.

## Execution

### Phase 1: Resolve the review target and focus

- **Entry**: User asks to review C++ code.
- **Steps**:
  1. Determine the source:
     - working-tree changes -> `--diff [REV]` (default `HEAD`)
     - staged changes -> `--staged`
     - specific code -> one or more file/dir `paths`
  2. Pick exactly one focus for this round. Default to `correctness` if the user
     does not specify. Supported: `correctness`, `memory`, `concurrency`,
     `performance`, `security`, `api-lifetime`, `testing`, `modern-cpp`, `boost`.
  3. Establish the target **C++ standard**. Run the collector once and read the
     `C++ standard` line in the rendered project context. If it says `unknown`
     (no `CMAKE_CXX_STANDARD`, `cxx_std_*`, or `-std=` found), **ask the user
     which standard they target** (C++11 / 14 / 17 / 20 / 23) and re-run with
     `--std c++NN`. The standard gates every modernization suggestion.
  4. If the collector reports Boost sub-libraries in the code (the `Boost
     sub-libraries in code` line), offer a `--focus boost` round for
     Boost-specific correctness and modernization suggestions.
- **Exit**: One resolvable target, one explicit focus, and a known C++ standard
  (or an explicit ask for it).
- **On fail**: Ask for the missing path/mode, focus, or C++ standard instead of
  guessing.

### Phase 2: Render the review prompt

- **Entry**: Phase 1 complete.
- **Steps**:
  1. Run the collector to build the focused prompt (see Workflow).
  2. Read the rendered prompt, which embeds the code/diff, repo context
     (build system, C++ standard, libraries, Boost sub-libraries), and the
     focus-specific rubric.
  3. Note the detected C++ standard — it changes what is idiomatic and available
     (e.g. `std::span`/`<=>` in C++20, `std::expected` in C++23). Never suggest a
     facility newer than the target standard. If the standard is `unknown`, ask
     the user before making any modern-C++ recommendation.
- **Exit**: A rendered prompt (or code/context section) is available.
- **On fail**: Apply the error table below; if unmapped, surface stderr and stop.

### Phase 3: Deliver the focused review

- **Entry**: Phase 2 complete.
- **Steps**:
  1. Walk the relevant section of
     [references/review-checklist.md](references/review-checklist.md) and the
     matching entries in
     [references/cpp-pitfalls-catalog.md](references/cpp-pitfalls-catalog.md),
     opening the mapped chapter under `references/core-guidelines/` when you need
     the full rule reasoning.
  2. Check the Iron Rules
     ([references/core-guidelines/01-iron_rules.md](references/core-guidelines/01-iron_rules.md))
     first for any crash / UB / OOB / leak-level defect, regardless of focus.
  3. Produce findings only for the chosen focus, ordered by severity.
  4. Cite the concrete rule id (e.g. "dangling `string_view`, ES.65").
  5. Note which sanitizer (ASan/UBSan/TSan/LeakSan) would likely catch each
     runtime defect.
  6. If the user wants another angle, run a separate round with a new focus.
- **Exit**: One coherent review pass, no mixed scopes unless explicitly asked.
- **On fail**: Report insufficient evidence rather than speculating.

## Workflow

Review uncommitted working-tree changes (default focus = correctness):

```bash
python3 skills/cpp-code-review/scripts/collect_target.py --diff \
  --project-root /absolute/path/to/cpp-project
```

Review staged changes with a memory focus:

```bash
python3 skills/cpp-code-review/scripts/collect_target.py --staged \
  --focus memory \
  --project-root /absolute/path/to/cpp-project
```

Review specific files or a directory with a concurrency focus:

```bash
python3 skills/cpp-code-review/scripts/collect_target.py \
  src/worker.cpp src/pool \
  --focus concurrency \
  --project-root /absolute/path/to/cpp-project
```

Compare against a base branch/commit for a performance pass:

```bash
python3 skills/cpp-code-review/scripts/collect_target.py --diff origin/main \
  --focus performance \
  --project-root /absolute/path/to/cpp-project
```

Run another angle as a separate round instead of asking for a broad review:

```bash
python3 skills/cpp-code-review/scripts/collect_target.py --diff \
  --focus security --project-root /absolute/path/to/cpp-project
```

Modernization pass — pass the user's C++ standard when it cannot be detected:

```bash
python3 skills/cpp-code-review/scripts/collect_target.py --diff \
  --focus modern-cpp --std c++17 \
  --project-root /absolute/path/to/cpp-project
```

Boost correctness + modernization pass (only meaningful when Boost is used):

```bash
python3 skills/cpp-code-review/scripts/collect_target.py --diff \
  --focus boost --std c++17 \
  --project-root /absolute/path/to/cpp-project
```

Use a fully custom one-aspect rubric:

```bash
python3 skills/cpp-code-review/scripts/collect_target.py --diff \
  --prompt-file /absolute/path/to/custom-review.md
```

Then read the rendered prompt and produce findings only for that focus. Do not
mix correctness, memory, concurrency, performance, security, api-lifetime, and
testing feedback in the same round unless the user explicitly asks for a
combined review.

### Error handling

The collector fails **concisely**: every error is a short reason plus a
numbered `Next step:` list — it never echoes a raw `git` usage/help dump. In
`--format json` mode the same information is a stable object
(`{"ok": false, "error": {"code", "message", "suggestions"}}`).

Before running `--diff`/`--staged` it prechecks the git environment (is this a
repo? does `HEAD` exist?) so a non-git directory gives an actionable conclusion
instead of a wall of `git diff --no-index` help.

| `error.code` | Cause | Action |
|--------------|-------|--------|
| `no_input` | No paths and no `--diff`/`--staged` | Pass file/dir paths, or use `--diff [REV]` / `--staged` |
| `not_a_git_repo` | `--diff`/`--staged` outside a git repo | Review files directly, or point `--project-root` at the repo root |
| `no_valid_head` | `--diff` on a repo with no commits | Make an initial commit, use `--staged`, or review files directly |
| `no_cpp_changes` | `--diff`/`--staged` found no C++ changes | Stage/commit C++ changes, or pass file paths |
| `no_cpp_files` | Paths had no C++ files | Give correct paths or a directory containing C++ code |
| `unsupported_focus` | Bad `--focus` value | Use one of correctness/memory/concurrency/performance/security/api-lifetime/testing/modern-cpp/boost |
| `git_command_failed` | Bad revision or git error | Pass `--project-root`, fix the revision, or use file paths instead of `--diff` |
| `git_missing` | `git` not installed | Install git, or review files directly instead of `--diff` |

When the C++ standard cannot be detected, the project context and JSON explain
**why** (no build system found, or the build files declare no
`CMAKE_CXX_STANDARD`/`cxx_std_*`/`-std=`) and tell you to re-run with an explicit
`--std c++17` (or c++11/14/20/23). Do this before any `modern-cpp`/`boost` round.

### Regression tests

`scripts/test_collect_target.py` covers the usability contracts above —
non-git `--diff`, headless repo, standard-detection hint, and the `--format
json` success/error shapes. Run it after changing the collector:

```bash
python3 skills/cpp-code-review/scripts/test_collect_target.py
```

## Script options

`scripts/collect_target.py`:

- Modes: `--diff [REV]` (default `HEAD`), `--staged`, or positional `paths`
- `--focus` — correctness | memory | concurrency | performance | security |
  api-lifetime | testing | modern-cpp | boost (aliases like `ub`, `leak`,
  `raii`, `race`, `perf`, `sec`, `lifetime`, `tests`, `modernize`, `cpp17`,
  `boost-lib` are accepted)
- `--std` — target C++ standard (e.g. `c++11`/`14`/`17`/`20`/`23`); overrides
  auto-detection. Set this from the user's answer when the standard is `unknown`
- `--prompt-file` — custom markdown template (overrides `--focus`)
- `--project-root` — repo root for build-system/standard/library context
- `--include-tests` — include test files (paths containing `test`/`mock`) when
  scanning directories
- `--max-files` (default 25), `--max-chars` (default 60000) — review budget
- `--format` — `prompt` (default), `code`, `context`, or `json`
- `--output-file` — write the result to a file instead of stdout

### JSON output contract (`--format json`)

For agent automation, `--format json` emits a stable object. On success:

```json
{
  "ok": true,
  "language": "C++",
  "focus": "memory",
  "scope": { "mode": "files|diff", "label": "...",
             "changed_files": ["..."], "omitted_files": ["..."] },
  "context": { "build_system": "...", "cpp_standard": "C++17",
               "cpp_standard_source": "user-specified|auto-detected",
               "cpp_standard_known": true,
               "libraries": ["..."], "boost_libraries": ["..."] },
  "project_context_md": "## Project Context ...",
  "code": "...embedded diff or files...",
  "prompt": "...fully rendered review prompt..."
}
```

On failure it is `{"ok": false, "error": {"code", "message", "suggestions": [...]}}`
with a non-zero exit code. Check `context.cpp_standard_known` before running a
`modern-cpp`/`boost` round; if `false`, re-run with `--std`.

The collector auto-detects the build system (CMake, Meson, Bazel, Make, Conan,
vcpkg), the C++ standard, and common libraries (GoogleTest, Catch2, doctest,
Boost, fmt, spdlog, Abseil, gRPC, Protobuf, nlohmann/json, Qt, Eigen, OpenCV,
Asio) from build files, and skips `build/`, `_deps/`, `third_party/`,
`external/`, `vendor/`, and `.git/`. It also scans the **reviewed code** for
`#include <boost/...>` and `boost::` usage and lists the exact Boost
sub-libraries in the project context, so a `boost` round can target them.

When the C++ standard cannot be detected, the project context prints an explicit
`NOTE: C++ standard unknown — ASK THE USER ...`. Ask, then re-run with `--std`.

C++ file extensions recognized: `.cpp .cc .cxx .c++ .hpp .hh .hxx .h++ .h .ipp
.inl .tpp .cppm .ixx`.

Custom prompt files may use these placeholders: `{{language}}`, `{{code}}`,
`{{review_focus}}`, `{{review_scope}}`, `{{project_context}}`,
`{{cpp_standard}}`, `{{project_frameworks}}`, `{{boost_libraries}}`.

## Built-in review focuses

- **correctness** — logic errors and UB: use-after-move, dangling
  references/views, uninitialized reads, signed/unsigned mixing, unsequenced
  side effects, OOB access, slicing, missing virtual destructor, iterator
  invalidation.
- **memory** — RAII, ownership, and resource management: naked `new`/`delete`,
  leaks on error paths, mismatched alloc/free forms, double-free/use-after-free,
  Rule of Five/Zero, `shared_ptr` cycles, smart-pointer misuse.
- **concurrency** — data races, naked locks, deadlocks / lock-order inversion,
  `volatile`-as-sync, detached threads, locks across `co_await`/callbacks,
  atomic memory ordering, condition-variable predicates, dangling captures.
- **performance** — needless copies and allocations, missing `reserve`, range-for
  copies, `std::endl` in loops, wrong container, `shared_ptr` churn, virtual /
  type-erasure overhead on hot paths, false sharing (evidence-first).
- **security** — unsafe C string/buffer APIs, format-string and command
  injection, unvalidated input and size arithmetic, secrets/PII in logs, weak
  crypto/randomness, unsafe deserialization and casts.
- **api-lifetime** — ownership clarity in signatures, idiomatic parameter
  passing, leaked views, `[[nodiscard]]`/`explicit`, Rule of Zero,
  `const`-correctness, preconditions, `enum class`, header hygiene.
- **testing** — error/edge/boundary coverage, move/self-assign tests, TSan for
  concurrency, sanitizer runs in CI, flaky timing, parameterized tests,
  assertion strength, dependency seams.
- **modern-cpp** — modernization to idiomatic C++ for the target standard:
  smart pointers, `nullptr`, `auto`, `override`/`final`, `enum class`, RAII,
  `std::optional`/`variant`/`string_view` (C++17), concepts/`span`/ranges/`<=>`
  (C++20), `std::expected`/`std::print` (C++23). Never suggests a facility newer
  than the user's standard.
- **boost** — Boost-specific correctness (Asio handler/buffer lifetime, strands,
  `work_guard`, thread/lock misuse, `optional`/`variant` misuse, filesystem
  error handling, `lexical_cast` exceptions, serialization of untrusted data)
  plus modernization suggestions to replace Boost with STL equivalents where the
  target standard allows (e.g. `boost::optional` -> `std::optional` on C++17),
  while keeping Boost where there is no STL equivalent.

Run these as separate rounds. The skill is biased toward depth over breadth,
and toward memory/concurrency/performance in particular.

**C++ standard awareness.** The `modern-cpp` and `boost` rounds only recommend a
facility that exists in the target standard. If the standard is unknown, ask the
user (C++11/14/17/20/23) and pass `--std c++NN` before running these rounds.

## Verification

### Hard gates

| Gate | Pass | On fail |
|------|------|---------|
| Local-only | No GitLab/GitHub API call; no token required | Route API MR review to `gitlab-mr-review` |
| Single focus | Output stays within one focus unless a combined pass was requested | Split into separate rounds |
| Iron Rules first | Any crash/UB/OOB/leak defect is surfaced regardless of the chosen focus | Re-scan against `01-iron_rules.md` |
| Evidence-based | Every finding cites shown code | Report insufficient evidence instead of speculating |
| No invented findings | Clean areas are stated as clean, not padded | Remove speculative findings |

### Soft gates

| Gate | Pass | On fail |
|------|------|---------|
| Rule-id citations | Findings reference the matching Core Guidelines rule id (or CWE for security) | Add the id or note it is not in the catalog |
| Standard-aware | Modernization/Boost suggestions never exceed the target standard; unknown standard triggers a question to the user | Recheck the standard, or ask, before recommending newer facilities |
| Boost-aware | When Boost is used, correctness is checked and STL-replacement suggestions are gated on the standard | Run a `boost` round; keep Boost where no STL equivalent exists |
| Sanitizer hint | Runtime defects note which sanitizer would catch them | Add ASan/UBSan/TSan/LeakSan guidance |
| Budget transparency | Note when `--max-files`/`--max-chars` trimmed coverage | State what was omitted |
| Severity ordering | Findings ordered blocker -> minor | Reorder before delivery |

## Feedback

### Failure modes

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Review mixes many concerns | Ran all focuses in one pass | Run one focus per round |
| Recommends C++20/23 facilities on an older codebase | Ignored detected C++ standard | Read `cpp_standard` from project context first |
| Findings not grounded in code | Speculated beyond the payload | Restrict to shown code; note omitted files |
| "No token" or API errors | Tried to use a remote MR flow | This skill is local-only; use `gitlab-mr-review` for API MRs |
| `--diff` errored outside a repo | Ran `--diff`/`--staged` in a non-git dir | Collector now returns `not_a_git_repo` + next steps; review files directly or fix `--project-root` |
| Blocked on "tell me the C++ standard" | Standard undetectable | Read the `--std c++17` hint in the context/JSON and re-run with `--std` |
| Empty review | Diff had no C++ changes | Stage changes or pass file paths |
| Missed a leak/race | Only ran style/idiomatic focus | Always sweep Iron Rules; run memory + concurrency rounds |

### Boundary examples

- **User**: `review my C++ changes before I commit` -> `--diff`, correctness first
- **User**: `check this class for leaks / RAII` -> `--focus memory` on the file
- **User**: `is this thread pool race-free?` -> `--focus concurrency`
- **User**: `where are the needless copies here?` -> `--focus performance`
- **User**: `modernize this to modern C++` -> confirm the standard (ask if
  unknown), then `--focus modern-cpp --std c++NN`
- **User**: `we use Boost, review it` -> `--focus boost`; check Asio/thread
  lifetime and suggest STL replacements allowed by their standard
- **User**: (standard undetectable) -> ask "which C++ standard do you target —
  C++11/14/17/20/23?" before any modernization suggestion
- **User**: `review this GitLab MR <url>` -> out of scope; use `gitlab-mr-review`
- **User**: `write / modernize this class for me` -> out of scope; use `lazy-cpp-dev`

### Improvement triggers

- New C++ standard or common pitfall not covered -> refresh
  `references/cpp-pitfalls-catalog.md` and the relevant chapter under
  `references/core-guidelines/`
- A recurring focus need not covered by the built-in focuses -> add a prompt
  template under `assets/prompts/` and register it in `collect_target.py`
