---
name: lazy-cpp-dev
description: >-
  Use when working on C++ code, diffs, crashes, reviews, tests, or
  modernization where RAII, lifetime, UB, STL, headers, threading, sanitizers,
  or ISO C++ Core Guidelines-style audits matter. Do not use for non-C++,
  pure C, deploy/infra, or build-only issues without C++ source semantics.
version: 0.1.0
author: walterfan@ustc.edu
tags: [cpp, "c++", modern-cpp, raii, concurrency, testing]
category: dev-tools
use_cases:
  - "implement or review C++ code for ownership, lifetime, UB, and API safety"
  - "write C++ tests and sanitizer-aware verification"
platforms: [claude-code, cursor, codex]
visibility: public
---

# lazy-cpp-dev

Practical modern C++ help with a pitfall-first review mindset. Keep diffs
small, preserve repo style, prefer RAII and value semantics, treat ownership
and lifetime as first-class, and verify with the repo's real build/test path.

## References

- [cpp-service-stack.md](references/cpp-service-stack.md): repo detection,
  APIs, headers, security, build/test tooling.
- [cpp-concurrency-review.md](references/cpp-concurrency-review.md): locks,
  atomics, threads, callbacks, coroutines, lifetime, TSan.
- [cpp-modernization.md](references/cpp-modernization.md): legacy C++ upgrade
  checklist.
- [cpp-testing.md](references/cpp-testing.md): test coverage and sanitizer
  guidance.

## When To Use

- User has a C++ repo, diff, file, stack trace, or snippet and wants code-
  focused help.
- Work touches classes, headers, templates, STL, smart pointers, ownership
  transfer, public APIs, exception safety, concurrency, tests, or sanitizers.
- User mentions UB, crashes, leaks, dangling references, slicing, races, data
  corruption, `std::move`, `string_view`, `span`, mutexes, coroutines, or
  "why does C++ do this".
- Repo has C++ conventions in `AGENTS.md`, `man/`, `.clang-format`,
  `.clang-tidy`, CI, or nearby files that should steer the change.
- User asks for ISO C++ Core Guidelines-style findings or rule IDs; handle
  them directly in this skill.

## When Not To Use

- Non-C++ primary work, pure C, deployment, infra, Jira/GitLab workflow, or
  product ops.
- Build-system-only dependency/linker work unless C++ source semantics are
  part of the fix.
- General C++ history, ecosystem comparison, blog/tutorial writing, or broad
  architecture docs without a concrete code artifact.
- A deliberately non-idiomatic experiment where the user explicitly accepts
  the tradeoff.

## Pitfall Hotspots

Prioritize these C++-specific bug patterns before style:

- Naked `new`/`delete`, raw owning pointers, mismatched `new`/`delete[]`, and
  leaked resources.
- Returning pointer/reference/view to a local; dangling `string_view`, `span`,
  iterator, or pointer after move, mutation, reallocation, or scope exit.
- Use-after-move: reading a moved-from object before reassignment.
- Slicing, missing virtual/protected base destructor, and virtual calls from
  constructors/destructors.
- Rule-of-Five / Rule-of-Zero gaps; custom destructor without copy/move
  decision; non-`noexcept` move or `swap`.
- Container invalidation after `push_back`, `insert`, `erase`, `resize`, or
  rehash.
- Uninitialized values, narrowing, signed/unsigned arithmetic, overflow, and
  division by zero.
- C-style casts, unsafe `const_cast`, type punning, and raw memory operations
  on non-trivially-copyable types.
- Header hygiene: missing guards, global `using namespace`, unnamed namespace
  in a header, cyclic includes, and order-dependent includes.
- Concurrency: data races, naked locks, `volatile` as synchronization, locks
  across callbacks/`co_await`, detached threads, and escaping reference
  captures.
- Unsafe C interop and sensitive logging: `strcpy`, `sprintf`, `system()` with
  input, raw JWTs, secrets, PII, or raw response bodies.

## Contract

- Read build files, lint/format config, nearby code, tests, and docs first.
- Prefer the repo's standard, error model, threading model, types, logging,
  and test framework over generic defaults.
- Make the smallest useful change.
- Handle ISO C++ Core Guidelines rule-ID audits here; cite IDs only when
  confident, otherwise label findings as guideline-aligned.
- Never log secrets, raw tokens, raw JWTs, sensitive PII, or private response
  bodies in examples, tests, logs, or final output.

## Workflow

1. Detect context.
   Read relevant build files, CI, format/lint config, conventions, nearby
   code, and tests. Identify the standard, flags, compiler, build command,
   test framework, exception/error model, logging, custom types, and threading
   choices.

2. Pick the mode.
   Use one primary mode unless the user asks for several: implement, review,
   test, explain, modernize, or tooling.

3. Apply C++ defaults.
   Match repo style, prefer RAII/value semantics, initialize everything, keep
   APIs explicit, validate boundaries, reuse local utilities, and keep diffs
   small.

4. Run the pitfall pass.
   Use the hotspots above, and read the focused references when concurrency,
   modernization, testing, or project-stack details matter.

5. Verify honestly.
   Run nearest relevant repo commands first, then broader checks if justified.
   Use ASan/UBSan/TSan when supported and relevant. State exactly what ran,
   failed, or was not run.

## Response Shape

- For implementation: summarize changes, assumptions, risks, and verification.
- For review: findings first, ordered by severity: UB/lifetime/race/leak,
  security, correctness, API/ABI, missing tests, style.
- For explanation: cover purpose, key components, ownership/lifetime, control
  flow, dependencies, concurrency, and important risks.
- For Core Guidelines-style audits: cite rule IDs only when confident; otherwise
  say "guideline-aligned" and explain the concrete C++ risk.

## Hard Gates

- No new raw ownership, dead views/references, use-after-move, slicing,
  missing polymorphic base destructors, throwing destructors, unsafe header
  namespaces, raw locking where RAII works, `volatile` synchronization, or
  detached threads using stack-owned data.
- Final responses state assumptions, findings/changes, risks, and verification.
