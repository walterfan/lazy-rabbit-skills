---
name: cpp-core-guide
description: >-
  Use when reviewing, writing, refactoring, or modernizing C++ code against
  the ISO C++ Core Guidelines. Keeps Iron Rules and Flag Rules as the priority
  review entry points, then provides a chapter navigator where each chapter
  maps to its reference file and lists remaining non-priority rules with
  rule id, shortened title, and Focus Scope tags. Trigger for C++ code
  review, API/interface design, RAII and ownership, lifetime/bounds safety,
  concurrency, templates, source layout, standard-library usage, naming and
  layout, enumerations, error handling, performance tuning, or explicit
  CppCoreGuidelines compliance checks; can also act as a post-implementation
  quality gate before code is sent for human review. Do not trigger for pure
  C, build-system-only tasks, test frameworks, or non-C++ languages. For
  general "implement / fix / explain C++" tasks without an explicit rule-by-id
  audit, prefer `lazy-cpp-dev` instead.
version: 0.1.0
author: walterfan@ustc.edu
source: ISO C++ Core Guidelines
tags:
  - cpp
  - c++
  - core-guidelines
  - code-review
  - raii
  - ownership
  - lifetime
  - concurrency
  - templates
  - exception-safety
  - header-hygiene
  - performance
  - pkb
category: dev-tools
use_cases:
  - "review a C++ change against Iron Rules and Flag Rules"
  - "look up a Core Guidelines rule by id (e.g., R.11, CP.20, F.43)"
  - "navigate to the right chapter by Focus Scope (lifetime, concurrency, etc.)"
  - "run as a post-implementation gate before sending C++ code to human review"
platforms: [claude-code, cursor, codex]
visibility: public
---

# C++ Core Guidelines - Review Navigator

Keep `Iron Rules` and `Flag Rules` as the first stop for code review triage. Priority rules listed there are intentionally omitted from the chapter tables below to avoid duplication. After that, use the remaining chapter sections to choose the right `references/*.md` file and jump to the exact rule by id, either by chapter scenario or by the `Focus Scope` column.

**Source:** ISO C++ Core Guidelines
**Rules indexed:** 473 across 18 chapters

## How to Use

1. Start with `Iron Rules` for crash / UB / OOB / leak level review items.
2. Use `Flag Rules` for non-fatal but high-signal code smells and enforcement-driven checks.
3. Pick the matching chapter scenario below if you are reviewing a specific language area such as classes, templates, concurrency, or source layout.
4. Scan the `Focus Scope` column if you are reviewing by concern such as `module boundaries`, `memory management`, `thread & coroutine safety`, `strong type safety`, or `standard algorithms`; a rule may carry multiple comma-separated tags when it spans more than one review concern.
5. Open the mapped reference file to read the full reason, examples, and enforcement text for the matched rule id.
6. Cite the original rule id in review comments.
7. When the agent has just finished writing or modifying C++ code, run this skill before the code is sent for human review.
8. Do not emit a code issue without at least one explicit `Rule ID`.

## Operating Modes

This skill has two modes, and the caller intent determines which one to use:

1. **Gate Mode**: Use after the agent itself has written or modified C++ code and the change is about to be submitted for human review. In this mode, rule violations are blocking and the agent must auto-fix them.
2. **Review-Only Mode**: Use when the user explicitly asks for code review, or when another skill invokes `cpp-core-guide` as a reviewer. In this mode, output a review report only. Do not automatically modify code.

## Mandatory Post-Implementation Gate

Use this section only in **Gate Mode**: after an agent-authored C++ code change and before any manual review or PR handoff.

### Trigger Mechanism

Automatically trigger this skill when any of the following are true:

1. The agent created or edited C++ production code, headers, templates, concurrency logic, memory-management code, or public interfaces.
2. The agent completed a C++ bug fix, refactor, modernization, or feature implementation and is about to ask for human review.
3. The agent claims a C++ change is "done", "ready", "ready for review", "please review", or equivalent.

Do not use Gate Mode when the skill is invoked by a user-requested review or by another skill that only wants a review report.

### Non-Bypassable Gate Semantics

Treat this gate like a compile error or a failing test for agent-generated C++ code.

Rules that actually apply to the changed code are not waivable. The agent must automatically revise the code to satisfy them before the code can move forward.

The code must not advance to human review until all of the following are satisfied:

1. All changed C++ files have been checked against `Iron Rules`.
2. All applicable `Flag Rules` have been checked.
3. Relevant chapter rules have been checked for the touched language areas, APIs, ownership model, concurrency model, and source-layout concerns.
4. Every triggered rule violation has been fixed in code, not merely explained away.
5. No unresolved `Iron Rules` violation remains.
6. No unresolved rule violation remains that would invalidate correctness, lifetime safety, thread safety, resource safety, or reviewability.
7. The agent has rerun the gate after each repair iteration and reached a clean pass.

### Auto-Revision Loop

If the gate finds any violation in Gate Mode:

1. Do not request human review.
2. Treat the violation as blocking, exactly like a compile failure.
3. Output the blocking rule ids and the affected files or code regions.
4. Automatically revise the code according to the matched rules.
5. Re-run this gate on the updated code.
6. Repeat until no blocking rule violation remains, but for at most 3 automatic repair iterations.
7. If 3 repair iterations are exhausted and the gate still fails, stop auto-fixing, keep the change in a blocked state, and report the remaining blocking rule ids and files for manual follow-up.

If the gate passes:

1. Summarize the checked rule families.
2. Call out rule families that were checked but not triggered by the changed code.
3. Mark the code as ready for human review.

## Review-Only Mode

Use this mode when the skill is triggered by the user or another skill for review purposes only.

Review-Only rules:

1. Analyze the code against the relevant Core Guidelines rules.
2. Output a review report with `Rule ID`, `Rule Title`, `Why It Applies`, and `Location` for every issue.
3. Do not automatically modify code.
4. Do not apply the Gate Mode auto-revision loop.
5. Leave the decision to fix, defer, or discuss findings to the caller or human reviewer.

### Issue Output Contract

Every discovered code issue must include all of the following:

1. `Rule ID`: at least one matching Core Guidelines rule id such as `R.11`, `CP.20`, or `F.43`.
2. `Rule Title`: the short rule title or a concise paraphrase of the matched rule.
3. `Why It Applies`: one sentence tying the rule to the actual code, diff, or behavior under review.
4. `Location`: the file and relevant symbol, line, or code region.

Additional output rules:

1. If multiple rules apply, list the primary rule first and keep secondary rules brief.
2. If you cannot map a finding to a concrete rule id, do not output it as a `cpp-core-guide` issue; instead, keep reviewing until you find the correct rule or discard the weak finding.
3. Rule id presence is mandatory for every emitted code issue, whether the issue is Critical, Warning, or Suggestion.

## Focus Scope Routing

Use this as a quick routing map before scanning the de-duplicated chapter tables. A rule may carry multiple `Focus Scope` tags.

| Focus Scope | Start in chapters | Primary references |
|---|---|---|
| `module boundaries` | `A`, `SF`, `C` | `references/17-a-architectural-ideas.md`, `references/15-sf-source-files.md`, `references/05-c-classes-and-hierarchies.md` |
| `global state & initialization` | `I`, `E`, `R` | `references/03-i-interfaces.md`, `references/11-e-error-handling.md`, `references/07-r-resource-management.md` |
| `include hygiene` | `SF` | `references/15-sf-source-files.md` |
| `interface design` | `I`, `F`, `CPL` | `references/03-i-interfaces.md`, `references/04-f-functions.md`, `references/14-cpl-c-style-programming.md` |
| `contract & validation` | `I`, `E` | `references/03-i-interfaces.md`, `references/11-e-error-handling.md` |
| `strong type safety` | `Con`, `Enum`, `ES`, `T` | `references/12-con-constants-and-immutability.md`, `references/06-enum-enumerations.md`, `references/08-es-expressions-and-statements.md`, `references/13-t-templates-and-generic-programming.md` |
| `ownership & lifetime` | `R`, `F`, `SL` | `references/07-r-resource-management.md`, `references/04-f-functions.md`, `references/16-sl-standard-library.md` |
| `memory management` | `F`, `C`, `R`, `ES`, `SL` | `references/04-f-functions.md`, `references/05-c-classes-and-hierarchies.md`, `references/07-r-resource-management.md`, `references/08-es-expressions-and-statements.md`, `references/16-sl-standard-library.md` |
| `object lifecycle` | `C`, `E` | `references/05-c-classes-and-hierarchies.md`, `references/11-e-error-handling.md` |
| `class design` | `C`, `NR` | `references/05-c-classes-and-hierarchies.md`, `references/18-nr-non-rules-and-myths.md` |
| `inheritance & polymorphism` | `C`, `T`, `I` | `references/05-c-classes-and-hierarchies.md`, `references/13-t-templates-and-generic-programming.md`, `references/03-i-interfaces.md` |
| `exception safety` | `E`, `C`, `F` | `references/11-e-error-handling.md`, `references/05-c-classes-and-hierarchies.md`, `references/04-f-functions.md` |
| `thread & coroutine safety` | `CP` | `references/10-cp-concurrency-and-parallelism.md` |
| `performance & cost` | `Per`, `P` | `references/09-per-performance.md`, `references/02-p-philosophy.md` |
| `generic programming` | `T` | `references/13-t-templates-and-generic-programming.md` |
| `standard library usage` | `SL`, `C` | `references/16-sl-standard-library.md`, `references/05-c-classes-and-hierarchies.md` |
| `standard algorithms` | `T`, `SL` | `references/13-t-templates-and-generic-programming.md`, `references/16-sl-standard-library.md` |
| `naming conventions` | `NL`, `SF`, `Enum`, `ES` | `references/19-nl-naming-and-layout.md`, `references/15-sf-source-files.md`, `references/06-enum-enumerations.md`, `references/08-es-expressions-and-statements.md` |
| `readability & maintainability` | `NL`, `ES`, `F`, `NR` | `references/19-nl-naming-and-layout.md`, `references/08-es-expressions-and-statements.md`, `references/04-f-functions.md`, `references/18-nr-non-rules-and-myths.md` |
| `C interop safety` | `CPL`, `SL` | `references/14-cpl-c-style-programming.md`, `references/16-sl-standard-library.md` |

## Iron Rules — Violating These Causes UB, Crashes, or Leaks

Full code examples and detailed explanations in [references/01-iron_rules.md](references/01-iron_rules.md) (41 rules).

| # | Rule | Area | Focus Scope | Enforcement |
|---|------|------|---|-------------|
| CP.2 | Avoid data races | Concurrency | thread & coroutine safety | Use static/dynamic tools (e.g., Thread Sanitizer) |
| CP.20 | Use RAII, never plain `lock()`/`unlock()` | Concurrency | thread & coroutine safety | Flag calls of member `lock()` and `unlock()` |
| P.8, R.1 | Don't leak any resources; manage resources automatically | Resource management | ownership & lifetime | Flag naked `new`, `delete`, `fopen`, `malloc` returning raw pointers |
| R.11, R.20, R.21, ES.24, ES.60, ES.61 | Use `unique_ptr`/`shared_ptr`, avoid naked `new`/`delete` | Resource management | memory management | Flag raw pointers that are targets of `new` |
| C.31, C.33 | Destructor must release all acquired resources | Classes | object lifecycle | Flag owning pointer members without destructor |
| C.35, C.127 | Base class with virtual functions needs virtual or protected destructor | Classes | inheritance & polymorphism | Flag polymorphic class with public non-virtual destructor |
| C.36, C.37, E.16 | Destructors must not fail; make destructors `noexcept` | Classes / Error handling | exception safety | Flag destructors declared `noexcept(false)` |
| C.82 | Don't call virtual functions in constructors/destructors | Classes | inheritance & polymorphism | Flag virtual calls from constructors and destructors |
| C.21 | Rule of Five: define or `=delete` all copy/move/dtor if any is defined | Classes | object lifecycle | Flag class with incomplete set of special member functions |
| C.62, C.65 | Make copy/move assignment safe for self-assignment | Classes | object lifecycle | Flag assignment operators not safe for self-assignment |
| C.67, C.145, ES.63 | Don't slice polymorphic objects | Classes / Expressions | inheritance & polymorphism | Flag polymorphic class with public copy; flag by-value pass of polymorphic type |
| C.152, T.81 | Never assign array-of-derived to pointer-to-base | Classes / Templates | inheritance & polymorphism | Flag array decay combined with base-to-derived conversion |
| ES.65, I.12 | Don't dereference invalid/null pointers | Expressions / Interfaces | ownership & lifetime | Flag null dereference; declare non-null pointers as `not_null` |
| ES.43, ES.44 | Avoid expressions with undefined order of evaluation | Expressions | strong type safety | Flag expressions with multiple unsequenced side effects |
| ES.103, ES.104, ES.105 | Don't overflow; don't underflow; don't divide by integer zero | Expressions | strong type safety | Flag potential signed overflow and division by zero |
| ES.100, ES.106 | Don't mix signed and unsigned arithmetic | Expressions | strong type safety | Flag mixed signed/unsigned operations |
| ES.20 | Always initialize an object | Expressions | object lifecycle | Flag every uninitialized variable |
| R.11, R.12 | No naked `new`/`delete` | Resource management | memory management | Flag naked `new` and `delete` |
| C.183 | Don't use a `union` for type punning | Classes | strong type safety | Flag reading union member that was not the last one set |
| CP.8, CP.200 | `volatile` is not synchronization; use `atomic` | Concurrency | thread & coroutine safety | Flag `volatile T` local/data members; suggest `atomic<T>` |
| CP.52 | Don't hold locks across coroutine suspension points | Concurrency | thread & coroutine safety | Flag lock guards alive at `co_await` |
| CP.53 | Coroutine parameters must not be passed by reference | Concurrency | thread & coroutine safety | Flag all reference parameters to a coroutine |
| CP.26 | Don't `detach()` a thread | Concurrency | thread & coroutine safety | Flag `detach()` |
| CP.21 | Use `std::scoped_lock` to acquire multiple mutexes | Concurrency | thread & coroutine safety | Flag acquisition of multiple mutexes without `scoped_lock` |
| CP.51 | Don't use capturing lambdas that are coroutines | Concurrency | thread & coroutine safety | Flag coroutine lambda with non-empty capture list |
| ES.48, ES.49 | Avoid casts; if you must, use a named cast | Expressions | strong type safety | Flag C-style and functional casts |
| ES.50 | Don't cast away `const` | Expressions | strong type safety | Flag `const_cast` |
| ES.34 | Don't define C-style variadic functions | Expressions | strong type safety | Flag definitions of C-style variadic functions |
| ES.61 | Delete arrays with `delete[]`, non-arrays with `delete` | Expressions | memory management | Flag mismatched `new`/`delete` forms |
| ES.62 | Don't compare pointers into different arrays | Expressions | strong type safety | Flag cross-array pointer comparison |
| F.43 | Never return pointer/reference to a local object | Functions | ownership & lifetime | Compiler warns return-of-local; static analysis for pointer escapes |
| C.90, SL.con.4 | Don't `memset`/`memcpy` non-trivially-copyable types | Classes / Standard library | strong type safety | Flag `memset`/`memcpy` on types that are not trivially copyable |
| SL.con.3 | Avoid container/array bounds errors | Standard library | memory management, standard library usage | Issue diagnostic for non-bounds-checked standard-library calls |
| I.13 | Don't pass an array as a single pointer | Interfaces | interface design | Flag implicit conversion of array type to pointer type |
| R.37 | Don't pass pointer/reference obtained from an aliased smart pointer | Resource management | ownership & lifetime, memory management | Flag raw pointer/reference from non-local or aliased smart pointer used in a call |
| E.13 | Never throw while being direct owner of a resource | Error handling | exception safety | Flag `throw` while holding a naked owning pointer |
| SL.C.1 | Don't use `setjmp`/`longjmp` | Standard library | C interop safety | Flag all occurrences of `longjmp` and `setjmp` |
| F.53 | Don't capture by reference in non-local lambdas | Functions | ownership & lifetime | Flag lambda that captures by reference and escapes its scope |
| ES.65 | Don't dereference invalidated iterators/pointers after container mutation | Expressions / Standard library | ownership & lifetime | Flag dereference of pointer/iterator to container element after `push_back`/`insert`/`erase`/`resize` |
| ES.56, C.64 | Don't read from a moved-from object | Expressions / Classes | object lifecycle | Flag read access to a moved-from object before reassignment |
| ES.65 (lifetime) | Don't let a `string_view` outlive its source | Expressions / Standard library | ownership & lifetime | Flag `string_view` bound to a temporary or to data that may be reallocated |
---

## Flag Rules — Violating These Means Bad Code Smell, Error-Prone

Rules whose enforcement contains an explicit **flag** action. Not immediately UB/crash, but indicate poor style, latent bugs, or maintenance hazards.

| # | Rule | Area | Focus Scope | Enforcement flag |
|---|------|------|---|------------------|
| P.1 | Express ideas directly in code | Philosophy | readability & maintainability | Flag uses of casts (casts neuter the type system) |
| P.6 | What cannot be checked at compile time should be checkable at run time | Philosophy | contract & validation | Flag (pointer, count)-style interfaces |
| P.9 | Don't waste time or space | Philosophy | performance & cost | Flag an unused return value from a user-defined non-defaulted postfix `operator++` or `operator--` |
| I.22 | Avoid complex initialization of global objects | Interfaces | global state & initialization | Flag initializers of globals that call non-`constexpr` functions; flag initializers that access `extern` objects |
| I.30 | Encapsulate rule violations | Interfaces | interface design | Flag rule suppression that enable rule-violations to cross interfaces |
| F.1 | "Package" meaningful operations as carefully named functions | Functions | readability & maintainability | Flag identical and very similar lambdas used in different places |
| F.3 | Keep functions short and simple | Functions | readability & maintainability | Flag functions that do not "fit on a screen" (60 lines × 140 chars); flag cyclomatic complexity > 10 |
| F.6 | If your function must not throw, declare it `noexcept` | Functions | exception safety | Flag low-level functions that are not `noexcept` yet cannot throw; flag throwing `swap`, `move`, destructors, default constructors |
| F.7 | For general use, take `T*` or `T&` rather than smart pointers | Functions | ownership & lifetime | Flag a smart pointer parameter that only calls `operator*`, `->`, or `get()`; flag unused smart pointer parameters |
| F.9 | Unused parameters should be unnamed | Functions | readability & maintainability | Flag named unused parameters |
| F.10 | If an operation can be reused, give it a name | Functions | readability & maintainability | Flag similar lambdas |
| F.18 | For "will-move-from" parameters, pass by `X&&` and `std::move` | Functions | object lifecycle | Flag all `X&&` parameters used without `std::move`; flag access to moved-from objects |
| F.19 | For "forward" parameters, pass by `TP&&` and only `std::forward` | Functions | interface design | Flag a `TP&&` parameter that does anything other than `std::forward`ing |
| F.20 | For "out" output values, prefer return values | Functions | interface design | Flag reference to non-`const` parameters that are not read before being written to |
| F.42 | Return a `T*` to indicate a position (only) | Functions | interface design | Flag `delete`/`std::free()` applied to a plain `T*`; flag `new`/`malloc()` assigned to a plain `T*` |
| F.44 | Return a `T&` when copy is undesirable | Functions | interface design | Flag functions where no `return` expression could yield `nullptr` |
| F.45 | Don't return a `T&&` | Functions | interface design | Flag any use of `&&` as a return type |
| F.49 | Don't return `const T` | Functions | interface design | Flag returning a `const` value |
| F.52 | Prefer capturing by reference in lambdas used locally | Functions | ownership & lifetime | Flag a lambda that captures by reference but is used other than locally |
| F.54 | Don't use `[=]` default capture when capturing `this` | Functions | ownership & lifetime | Flag any lambda capture-list that specifies `[=]` and also captures `this` |
| F.56 | Avoid unnecessary condition nesting | Functions | readability & maintainability | Flag a redundant `else`; flag a function body that is simply a conditional enclosing a block |
| C.5 | Place helper functions in the same namespace as the class | Classes | module boundaries | Flag global functions taking argument types from a single namespace |
| C.7 | Don't define a class or enum and declare a variable in the same statement | Classes | class design | Flag if `}` of a class/enum definition is not followed by `;` |
| C.8 | Use `class` rather than `struct` if any member is non-public | Classes | class design | Flag classes declared with `struct` if there is a `private` or `protected` member |
| C.9, C.133 | Minimize exposure of members; avoid `protected` data | Classes | class design | Flag `protected` data |
| C.12 | Don't make data members `const` or references in a copyable/movable type | Classes | class design | Flag a data member that is `const`, `&`, or `&&` in a type with copy/move |
| C.40, C.42, E.5 | A constructor should establish an invariant | Classes | object lifecycle | Flag classes with `private` state without a constructor |
| C.41 | A constructor should create a fully initialized object | Classes | object lifecycle | Flag classes with a user-defined constructor that do not initialize all data members |
| C.43 | Ensure that a copyable class has a default constructor | Classes | object lifecycle | Flag classes that are `Copyable` but do not have a default constructor |
| C.44 | Prefer default constructors to be simple and non-throwing | Classes | object lifecycle | Flag throwing default constructors |
| C.45 | Don't define a default constructor that only initializes data members | Classes | object lifecycle | Flag a default constructor that only initializes data members using default member initializer syntax |
| C.48 | Prefer default member initializers to member initializers in constructors | Classes | object lifecycle | Flag member initializers in constructors that replicate default member initializers |
| C.49 | Prefer initialization to assignment in constructors | Classes | object lifecycle | Flag assignment in constructor bodies that could use initializer lists |
| C.50 | Use a factory function if you need "virtual behavior" during initialization | Classes | object lifecycle | Flag classes with virtual functions but no factories or friend classes |
| C.51 | Use delegating constructors | Classes | object lifecycle | Flag similar constructor bodies |
| C.60 | Make copy assignment non-`virtual` | Classes | object lifecycle | Flag virtual copy assignment operators |
| C.61 | A copy operation should copy | Classes | object lifecycle | Flag copy operations that don't provide the same value in `*this` and `x` after copy |
| C.63 | Make move assignment non-`virtual` | Classes | object lifecycle | Flag move assignment operators that are virtual |
| C.64 | A move operation should move and leave source valid | Classes | object lifecycle | Flag move operations that do not move or leave the source in a valid state |
| C.66 | Make move operations `noexcept` | Classes | object lifecycle | Flag throwing move operations |
| C.80 | Use `=default` for default semantics | Classes | object lifecycle | Flag definitions of special operations that are equivalent to compiler-generated ones |
| C.83 | For value-like types, provide a `noexcept` swap | Classes | exception safety | Flag non-`noexcept` swap functions |
| C.84, C.85 | A `swap` must not fail; make `swap` `noexcept` | Classes | exception safety | Flag throwing `swap` functions |
| C.86 | Make `==` symmetric with respect to operand types and `noexcept` | Classes | exception safety | Flag `operator==()` where argument types differ or are not `noexcept` |
| C.87 | Beware of `==` on base classes | Classes | inheritance & polymorphism | Flag a virtual `operator==()` |
| C.89 | Make a `hash` `noexcept` | Classes | exception safety | Flag throwing `hash`es |
| C.90 | Rely on constructors, not `memset`/`memcpy` | Classes | strong type safety | Flag uses of `memset` and `memcpy` for non-trivially-copyable types |
| C.102 | Give a container move operations | Classes | object lifecycle | Flag classes with containers as members that are missing move operations |
| C.120 | Use class hierarchies to represent concepts with inherent hierarchical structure (only) | Classes | inheritance & polymorphism | Flag every use of a non-public base class `B` where the derived class `D` does not override a virtual function or access a protected member in `B` |
| C.126 | An abstract class typically doesn't need a user-written constructor | Classes | object lifecycle | Flag abstract classes with constructors |
| C.128 | Virtual functions should specify exactly one of `virtual`/`override`/`final` | Classes | inheritance & polymorphism | Flag virtual function uses that do not `override` |
| C.129 | When designing a class hierarchy, distinguish between implementation inheritance and interface inheritance | Classes | inheritance & polymorphism | Flag a derived to base conversion to a base with both data and virtual functions |
| C.130 | Prefer a virtual `clone` over public copy for polymorphic classes | Classes | inheritance & polymorphism | Flag a class with a virtual function and a non-user-defined copy operation |
| C.131 | Avoid trivial getters and setters | Classes | class design | Flag multiple `get`/`set` member functions that simply access a member without additional semantics |
| C.132 | Don't make a function `virtual` without reason | Classes | inheritance & polymorphism | Flag a class with virtual functions but no derived classes; flag a class where all members are virtual with implementations |
| C.134 | Ensure all non-`const` data members have the same access level | Classes | class design | Flag any class with non-`const` data members at different access levels |
| C.137 | Use `virtual` bases to avoid overly general base classes | Classes | inheritance & polymorphism | Flag mixed interface and implementation hierarchies |
| C.138 | Create an overload set for a derived class and its bases with `using` | Classes | inheritance & polymorphism | Flag hiding |
| C.139 | Use `final` on classes sparingly | Classes | inheritance & polymorphism | Flag uses of `final` on classes |
| C.140 | Do not provide different default arguments for virtual function and overrider | Classes | inheritance & polymorphism | Flag default arguments on virtual functions that differ between base and derived |
| C.146, C.153 | Use `dynamic_cast` where hierarchy navigation is unavoidable; prefer virtual function to casting | Classes | inheritance & polymorphism | Flag all uses of `static_cast` for downcasts |
| C.148 | Use `dynamic_cast` to a pointer type when failure is a valid alternative | Classes | inheritance & polymorphism | Flag `dynamic_cast` to a pointer that is dereferenced without checking for null |
| C.149 | Use `unique_ptr`/`shared_ptr` to avoid forgetting to `delete` | Classes | ownership & lifetime, memory management | Flag naked `new`; flag naked `delete` |
| C.161 | Use non-member functions for symmetric operators | Classes | class design | Flag member operator functions |
| C.164 | Avoid implicit conversion operators | Classes | strong type safety | Flag non-explicit conversion operators |
| C.168 | Define overloaded operators in the namespace of their operands | Classes | module boundaries | Flag operator definitions not in the namespace of their operands |
| C.181 | Avoid "naked" `union`s | Classes | class design | Flag naked `union`s |
| Enum.1 | Prefer enumerations over macros | Enumerations | strong type safety | Flag macros that define integer values |
| Enum.2 | Use enumerations to represent sets of related named constants | Enumerations | strong type safety | Flag `switch`-statements where `case`s cover most but not all enumerators |
| Enum.4 | Define operations on enumerations for safe and simple use | Enumerations | strong type safety | Flag repeated expressions cast back into an enumeration |
| Enum.5 | Don't use `ALL_CAPS` for enumerators | Enumerations | naming conventions | naming conventions |
| Enum.6 | Avoid unnamed enumerations | Enumerations | strong type safety | Flag unnamed enumerations |
| Enum.7 | Specify the underlying type of an enumeration only when necessary | Enumerations | strong type safety | Flag redundant underlying type specifications |
| Enum.8 | Specify enumerator values only when necessary | Enumerations | strong type safety | Flag duplicate enumerator values; flag explicitly specified all-consecutive enumerator values |
| R.2 | In interfaces, use raw pointers to denote individual objects (only) | Resource management | interface design | Flag pointer arithmetic on a pointer not part of a container; flag array names passed as simple pointers |
| R.10 | Avoid `malloc()` and `free()` | Resource management | memory management | Flag explicit use of `malloc` and `free` |
| R.12 | Immediately give explicit resource allocation to a manager object | Resource management | memory management | Flag explicit allocations used to initialize pointers |
| R.13 | Perform at most one explicit resource allocation in a single expression | Resource management | memory management | Flag expressions with multiple explicit resource allocations |
| R.14 | Avoid `[]` parameters, prefer `span` | Resource management | ownership & lifetime | Flag `[]` parameters |
| R.15 | Always overload matched allocation/deallocation pairs | Resource management | memory management | Flag incomplete pairs |
| ES.5 | Keep scopes small | Expressions | readability & maintainability | Flag loop variable declared outside a loop and not used after the loop |
| ES.9 | Avoid `ALL_CAPS` names | Expressions | naming conventions | naming conventions |
| ES.10 | Declare one name (only) per declaration | Expressions | readability & maintainability | Flag variable and constant declarations with multiple declarators |
| ES.11 | Use `auto` to avoid redundant repetition of type names | Expressions | readability & maintainability | Flag redundant repetition of type names in a declaration |
| ES.12 | Do not reuse names in nested scopes | Expressions | naming conventions | naming conventions |
| ES.21 | Don't introduce a variable before you need to use it | Expressions | readability & maintainability | Flag declarations that are distant from their first use |
| ES.22 | Don't declare a variable until you have a value to initialize it with | Expressions | readability & maintainability | Flag declarations with default initialization that are assigned to before first read |
| ES.23 | Prefer the `{}`-initializer syntax | Expressions | strong type safety | Flag uses of `=` to initialize arithmetic types where narrowing occurs |
| ES.25 | Declare an object `const` or `constexpr` unless you want to modify it | Expressions | readability & maintainability | Flag variables that are not mutated |
| ES.26 | Don't use a variable for two unrelated purposes | Expressions | readability & maintainability | Flag recycled variables |
| ES.27 | Use `std::array` or `stack_array` for arrays on the stack | Expressions | standard library usage | Flag arrays with non-constant bounds (VLAs) |
| ES.45 | Avoid "magic constants"; use symbolic constants | Expressions | readability & maintainability | Flag literals in code |
| ES.47 | Use `nullptr` rather than `0` or `NULL` | Expressions | strong type safety | Flag uses of `0` and `NULL` for pointers |
| ES.56 | Write `std::move()` only when you need to explicitly move | Expressions | object lifecycle | Flag use of `std::move()` of a `const` object; flag `std::move()` as argument to `const&` parameter |
| ES.64 | Use the `T{e}` notation for construction | Expressions | strong type safety | Flag the C-style `(T)e` and functional-style `T(e)` casts |
| ES.70 | Prefer a `switch`-statement to an `if`-statement when there is a choice | Statements | readability & maintainability | Flag `if-then-else` chains that check against constants |
| ES.73 | Prefer a `while`-statement to a `for`-statement when there is no obvious loop variable | Statements | readability & maintainability | Flag actions in `for`-initializers/increments that do not relate to the `for`-condition |
| ES.75 | Avoid `do`-statements | Statements | readability & maintainability | Flag `do`-statements |
| ES.76 | Avoid `goto` | Statements | readability & maintainability | Flag `goto`; better: flag all `goto`s that do not jump from a nested loop to the statement immediately after |
| ES.78 | Don't rely on implicit fallthrough in `switch` statements | Statements | readability & maintainability | Flag all implicit fallthroughs from non-empty `case`s |
| ES.79 | Use `default` to handle common cases (only) | Statements | readability & maintainability | Flag `switch`-statements over an enumeration that don't handle all enumerators and do not have a `default` |
| ES.84 | Don't try to declare a local variable with no name | Statements | readability & maintainability | Flag statements that are just a temporary |
| ES.85 | Make empty statements visible | Statements | readability & maintainability | Flag empty statements that are not blocks and don't contain comments |
| ES.86 | Avoid modifying loop control variables inside the body of raw for-loops | Statements | readability & maintainability | Flag variables potentially updated both in the for-statement and in the body |
| ES.102 | Use signed types for arithmetic | Expressions | strong type safety | Flag mixed signed and unsigned arithmetic; flag unsigned literals (e.g. `-2u`) |
| CP.22 | Never call unknown code while holding a lock | Concurrency | thread & coroutine safety | Flag calling a virtual function with a non-recursive `mutex` held; flag calling a callback with a non-recursive `mutex` held |
| CP.24 | Think of a `thread` as a global container | Concurrency | thread & coroutine safety | Flag attempts to pass local variables to a thread that might `detach()` |
| CP.25 | Prefer `gsl::joining_thread` over `std::thread` | Concurrency | thread & coroutine safety | Flag uses of `std::thread`; suggest `gsl::joining_thread` or C++20 `std::jthread` |
| CP.42 | Don't `wait` without a condition | Concurrency | thread & coroutine safety | Flag all `wait`s without conditions |
| CP.43 | Minimize time spent in a critical section | Concurrency | thread & coroutine safety | Flag "naked" `lock()` and `unlock()` |
| CP.44 | Remember to name your `lock_guard`s and `unique_lock`s | Concurrency | thread & coroutine safety | Flag all unnamed `lock_guard`s and `unique_lock`s |
| E.15 | Throw by value, catch exceptions from a hierarchy by reference | Error handling | exception safety | Flag catching by value of a type that has a virtual function; flag throwing raw pointers |
| E.17 | Don't try to catch every exception in every function | Error handling | exception safety | Flag nested try-blocks; flag source files with too high ratio of try-blocks to functions |
| E.30 | Don't use exception specifications | Error handling | exception safety | Flag every exception specification |
| E.31 | Properly order your `catch`-clauses | Error handling | exception safety | Flag all "hiding handlers" |
| Con.1 | By default, make objects immutable | Constants | strong type safety | Flag non-`const` variables that are not modified |
| Con.2 | By default, make member functions `const` | Constants | strong type safety | Flag a member function that is not marked `const` but does not perform a non-`const` operation |
| Con.3 | By default, pass pointers and references to `const`s | Constants | strong type safety | Flag a function that does not modify an object passed by pointer/reference to non-`const`; flag a function that (via cast) modifies an object passed by pointer/reference to `const` |
| Con.4 | Use `const` to define objects with values that do not change | Constants | strong type safety | Flag unmodified non-`const` variables |
| Con.5 | Use `constexpr` for values that can be computed at compile time | Constants | strong type safety | Flag `const` definitions with constant expression initializers |
| T.1 | Use templates to express containers and ranges | Templates | generic programming | Flag algorithms with "overly simple" requirements without a concept |
| T.3 | Use templates to express containers and ranges | Templates | generic programming | Flag uses of `void*`s and casts outside low-level implementation code |
| T.10 | Specify concepts for all template arguments | Templates | generic programming | Flag template type arguments without concepts |
| T.20 | Avoid "concepts" without meaningful semantics | Templates | generic programming | Flag single-operation `concepts` used outside the definition of other `concepts` |
| T.21 | Require a complete set of operations for a concept | Templates | generic programming | Flag classes that support "odd" subsets of a set of operators |
| T.23 | Differentiate a refined concept from its more general case | Templates | generic programming | Flag a concept that has exactly the same requirements as another already-seen concept |
| T.25 | Avoid complementary constraints | Templates | generic programming | Flag pairs of functions with `C<T>` and `!C<T>` constraints |
| T.40 | Use function objects to pass operations to algorithms | Templates | generic programming, standard algorithms | Flag pointer to function template arguments |
| T.42 | Use template aliases to simplify notation | Templates | generic programming | Flag use of `typename` as a disambiguator outside `using` declarations |
| T.43 | Prefer `using` over `typedef` for defining aliases | Templates | generic programming | Flag uses of `typedef` |
| T.44 | Use function templates to deduce class template argument types | Templates | generic programming | Flag uses where explicitly specialized type exactly matches the argument types |
| T.46 | Require template arguments to be at least semiregular | Templates | generic programming | Flag types used as template arguments that are not at least semiregular |
| T.47 | Avoid highly visible unconstrained templates with common names | Templates | generic programming | Flag templates defined in a namespace where concrete types are also defined |
| T.61 | Do not over-parameterize members (SCARY) | Templates | generic programming | Flag member types that do not depend on every template parameter |
| T.68 | Use `{}` rather than `()` within templates to avoid ambiguities | Templates | generic programming | Flag `()` initializers and function-style casts |
| T.69 | Don't make an unqualified non-member function call inside a template unless it's a customization point | Templates | generic programming | Flag unqualified calls to non-member functions that pass dependent-type variables |
| T.80 | Do not naively templatize a class hierarchy | Templates | inheritance & polymorphism | Flag virtual functions that depend on a template argument |
| T.100 | Use variadic templates when you need a function that takes a variable number of arguments of a variety of types | Templates | generic programming | Flag uses of `va_arg` in user code |
| T.123 | Use `constexpr` functions to compute values at compile time | Templates | generic programming | Flag template metaprograms yielding a value; replace with `constexpr` functions |
| T.143 | Don't write unintentionally non-generic code | Templates | generic programming | Flag comparison of iterators using `<` instead of `!=`; flag `x.size() == 0` when `x.empty()` is available |
| T.144 | Don't specialize function templates | Templates | generic programming | Flag all specializations of a function template |
| CPL.2 | If you must use C, use the common subset and compile as C++ | C-style | C interop safety | Flag if using a build mode that compiles code as C |
| SF.3 | Use header files for all declarations used in multiple source files | Source files | module boundaries | Flag declarations of entities in other source files not placed in a `.h` |
| SF.5 | A `.cpp` file must include the header file(s) that defines its interface | Source files | include hygiene | Flag `.cpp` files that don't include their corresponding `.h` |
| SF.7 | Don't write `using namespace` at global scope in a header file | Source files | module boundaries | Flag `using namespace` at global scope in a header file |
| SF.8 | Use `#include` guards for all header files | Source files | include hygiene | Flag `.h` files without `#include` guards |
| SF.9 | Avoid cyclic dependencies among source files | Source files | module boundaries | Flag all cycles |
| SF.21 | Don't use an unnamed namespace in a header | Source files | module boundaries | Flag any use of an anonymous namespace in a header file |
| SL.con.1 | Prefer STL `array` or `vector` instead of a C array | Standard library | standard library usage | Flag declaration of a C array inside a function or class that also declares an STL container |
| SL.con.2 | Prefer STL `vector` by default | Standard library | standard library usage | Flag a `vector` whose size never changes after construction; suggest `array` |
| SL.str.3 | Use `zstring` or `czstring` to refer to a C-style, zero-terminated, sequence of characters | Standard library | C interop safety | Flag uses of `[]` on a `char*`; flag uses of `delete` on a `char*` |
| SL.str.4 | Use `char*` to refer to a single character | Standard library | C interop safety | Flag uses of `[]` on a `char*` |
| SL.io.3 | Prefer `iostream`s for I/O | Standard library | standard library usage | Flag `<cstdio>` and `<stdio.h>` |
| SL.C.1 | Don't use `setjmp`/`longjmp` | Standard library | C interop safety | Flag all occurrences of `longjmp` and `setjmp` |
| NL.9 | Use `ALL_CAPS` for macro names only | Naming | naming conventions | naming conventions |
| NL.11 | Make literals readable | Naming | readability & maintainability | Flag long digit sequences |
| NL.16 | Use a conventional class member declaration order | Naming | readability & maintainability | Flag departures from the suggested order |
| NL.26 | Use conventional `const` notation | Naming | naming conventions | naming conventions |
| NL.27 | Use a `.cpp` suffix for code files and `.h` for interface files | Naming | naming conventions | naming conventions |
## Chapter Navigator

Rules already elevated into `Iron Rules` or `Flag Rules` are not repeated in the chapter tables below.

## P: Philosophy

**Scenario / Theme:** High-level design principles, correctness posture, and codebase-wide decision making.
**Reference:** [references/02-p-philosophy.md](references/02-p-philosophy.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| P.2 | Write in ISO Standard C++ | readability & maintainability |
| P.3 | Express intent | readability & maintainability |
| P.4 | Ideally, a program should be statically type safe | strong type safety |
| P.5 | Prefer compile-time checking to run-time checking | strong type safety |
| P.7 | Catch run-time errors early | exception safety |
| P.10 | Prefer immutable data to mutable data | strong type safety |
| P.11 | Encapsulate messy constructs, rather than spreading through the code | readability & maintainability |
| P.12 | Use supporting tools as appropriate | readability & maintainability |
| P.13 | Use support libraries as appropriate | readability & maintainability |

## I: Interfaces

**Scenario / Theme:** API boundaries, ownership transfer, contracts, globals, and ABI-facing interface design.
**Reference:** [references/03-i-interfaces.md](references/03-i-interfaces.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| I.1 | Make interfaces explicit | interface design |
| I.2 | Avoid non-const global variables | global state & initialization |
| I.3 | Avoid singletons | global state & initialization |
| I.4 | Make interfaces precisely and strongly typed | interface design |
| I.5 | State preconditions | contract & validation |
| I.6 | Prefer Expects for expressing preconditions | contract & validation |
| I.7 | State postconditions | contract & validation |
| I.8 | Prefer Ensures for expressing postconditions | contract & validation |
| I.9 | If an interface is a template, document its parameters using... | generic programming |
| I.10 | Use exceptions to signal a failure to perform a required task | interface design |
| I.11 | Never transfer ownership by a raw pointer or reference | ownership & lifetime |
| I.23 | Keep the number of function arguments low | interface design |
| I.24 | Avoid adjacent parameters that can be invoked by the same... | interface design |
| I.25 | Prefer empty abstract classes as interfaces to class hierarchies | inheritance & polymorphism |
| I.26 | If you want a cross-compiler ABI, use a C-style subset | interface design |
| I.27 | For stable library ABI, consider the Pimpl idiom | interface design |

## F: Functions

**Scenario / Theme:** Function shape, parameter passing, return values, lambdas, and local control-flow style.
**Reference:** [references/04-f-functions.md](references/04-f-functions.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| F.2 | A function should perform a single logical operation | interface design |
| F.4 | If a function might have to be evaluated at compile time, declare... | strong type safety |
| F.5 | If a function is very small and time-critical, declare it inline | performance & cost |
| F.8 | Prefer pure functions | interface design |
| F.11 | Use an unnamed lambda if you need a simple function object in one... | readability & maintainability |
| F.15 | Prefer simple and conventional ways of passing information | interface design |
| F.16 | For "in" parameters, pass cheaply-copied types by value and... | strong type safety |
| F.17 | For "in-out" parameters, pass by reference to non-const | strong type safety |
| F.21 | To return multiple "out" values, prefer returning a struct | interface design |
| F.60 | Prefer T* over T& when "no argument" is a valid option | interface design |
| F.22 | Use T* or owner<T*> to designate a single object | interface design |
| F.23 | Use a not_null<T> to indicate that "null" is not a valid value | strong type safety, ownership & lifetime |
| F.24 | Use a span<T> or a span_p<T> to designate a half-open sequence | ownership & lifetime, interface design |
| F.25 | Use a zstring or a not_null<zstring> to designate a C-style string | C interop safety |
| F.26 | Use a unique_ptr<T> to transfer ownership where a pointer is needed | ownership & lifetime, memory management |
| F.27 | Use a shared_ptr<T> to share ownership | ownership & lifetime, memory management |
| F.46 | int is the return type for main | interface design |
| F.47 | Return T& from assignment operators | object lifecycle |
| F.48 | Don't return std::move | object lifecycle |
| F.50 | Use a lambda when a function won't do | interface design |
| F.51 | Where there is a choice, prefer default arguments over overloading | interface design |
| F.55 | Don't use va_arg arguments | interface design |

## C: Classes and class hierarchies

**Scenario / Theme:** Class invariants, constructors, copy/move, inheritance, operators, and unions.
**Reference:** [references/05-c-classes-and-hierarchies.md](references/05-c-classes-and-hierarchies.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| C.1 | Organize related data into structures | class design |
| C.2 | Use class if the class has an invariant | class design |
| C.3 | Represent the distinction between an interface and an... | interface design |
| C.4 | Make a function a member only if it needs direct access to the... | class design |
| C.10 | Prefer concrete types over class hierarchies | inheritance & polymorphism |
| C.11 | Make concrete types regular | class design |
| C.20 | If you can avoid defining default operations, do | class design |
| C.22 | Make default operations consistent | class design |
| C.30 | Define a destructor if a class needs an explicit action at object... | object lifecycle |
| C.32 | If a class has a raw pointer or reference, consider whether it... | ownership & lifetime |
| C.46 | By default, declare single-argument constructors explicit | interface design |
| C.47 | Define and initialize data members in the order of member... | object lifecycle |
| C.52 | Use inheriting constructors to import constructors into a derived... | inheritance & polymorphism |
| C.81 | Use =delete when you want to disable default behavior | class design |
| C.100 | Follow the STL when defining a container | standard library usage |
| C.101 | Give a container value semantics | standard library usage |
| C.103 | Give a container an initializer list constructor | object lifecycle |
| C.104 | Give a container a default constructor that sets it to empty | object lifecycle |
| C.109 | If a resource handle has pointer semantics, provide * and -> | ownership & lifetime |
| C.121 | If a base class is used as an interface, make it a pure abstract... | inheritance & polymorphism |
| C.122 | Use abstract classes as interfaces when complete separation of... | interface design |
| C.135 | Use multiple inheritance to represent multiple distinct interfaces | inheritance & polymorphism |
| C.136 | Use multiple inheritance to represent the union of implementation... | inheritance & polymorphism |
| C.147 | Use dynamic_cast to a reference type when failure to find the... | exception safety |
| C.150 | Use make_unique to construct objects owned by unique_ptrs | ownership & lifetime, memory management |
| C.151 | Use make_shared to construct objects owned by shared_ptrs | ownership & lifetime, memory management |
| C.160 | Define operators primarily to mimic conventional usage | class design |
| C.162 | Overload operations that are roughly equivalent | class design |
| C.163 | Overload only for operations that are roughly equivalent | class design |
| C.165 | Use using for customization points | class design |
| C.166 | Overload unary & only as part of a system of smart pointers and... | ownership & lifetime |
| C.167 | Use an operator for an operation with its conventional meaning | class design |
| C.170 | If you feel like overloading a lambda, use a generic lambda | generic programming |
| C.180 | Use unions to save memory | class design |
| C.182 | Use anonymous unions to implement tagged unions | class design |

## Enum: Enumerations

**Scenario / Theme:** Enum design, enumerator naming, conversions, and enum-specific operations.
**Reference:** [references/06-enum-enumerations.md](references/06-enum-enumerations.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| Enum.3 | Prefer class enums over "plain" enums | strong type safety |

## R: Resource management

**Scenario / Theme:** RAII, ownership, memory/resource lifetimes, and smart-pointer usage.
**Reference:** [references/07-r-resource-management.md](references/07-r-resource-management.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| R.3 | A raw pointer is non-owning | ownership & lifetime |
| R.4 | A raw reference is non-owning | ownership & lifetime |
| R.5 | Prefer scoped objects, don't heap-allocate unnecessarily | ownership & lifetime |
| R.6 | Avoid non-const global variables | global state & initialization |
| R.22 | Use make_shared to make shared_ptrs | ownership & lifetime, memory management |
| R.23 | Use make_unique to make unique_ptrs | ownership & lifetime, memory management |
| R.24 | Use std::weak_ptr to break cycles of shared_ptrs | ownership & lifetime, memory management |
| R.30 | Take smart pointers as parameters only to explicitly express... | ownership & lifetime |
| R.31 | If you have non-std smart pointers, follow the basic pattern from... | ownership & lifetime |
| R.32 | Take a unique_ptr<widget> parameter to express that a function... | ownership & lifetime |
| R.33 | Take a unique_ptr<widget>& parameter to express that a function... | ownership & lifetime |
| R.34 | Take a shared_ptr<widget> parameter to express shared ownership | ownership & lifetime |
| R.35 | Take a shared_ptr<widget>& parameter to express that a function... | ownership & lifetime |
| R.36 | Take a const shared_ptr<widget>& parameter to express that it... | ownership & lifetime |

## ES: Expressions and statements

**Scenario / Theme:** Declarations, expressions, statements, arithmetic, casts, and lifetime-sensitive syntax.
**Reference:** [references/08-es-expressions-and-statements.md](references/08-es-expressions-and-statements.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| ES.1 | Prefer the standard library to other libraries and to... | standard library usage |
| ES.2 | Prefer suitable abstractions to direct use of language features | strong type safety |
| ES.3 | Don't repeat yourself, avoid redundant code | readability & maintainability |
| ES.6 | Declare names in for-statement initializers and conditions to... | readability & maintainability |
| ES.7 | Keep common and local names short, and keep uncommon and non-... | naming conventions |
| ES.8 | Avoid similar-looking names | naming conventions |
| ES.28 | Use lambdas for complex initialization, especially of const... | strong type safety |
| ES.30 | Don't use macros for program text manipulation | readability & maintainability |
| ES.31 | Don't use macros for constants or "functions" | readability & maintainability |
| ES.32 | Use ALL_CAPS for all macro names | readability & maintainability |
| ES.33 | If you must use macros, give them unique names | readability & maintainability, naming conventions |
| ES.40 | Avoid complicated expressions | strong type safety |
| ES.41 | If in doubt about operator precedence, parenthesize | readability & maintainability |
| ES.42 | Keep use of pointers simple and straightforward | strong type safety |
| ES.46 | Avoid lossy arithmetic conversions | strong type safety |
| ES.55 | Avoid the need for range checking | strong type safety |
| ES.71 | Prefer a range-for-statement to a for-statement when there is a... | readability & maintainability |
| ES.72 | Prefer a for-statement to a while-statement when there is an... | readability & maintainability |
| ES.74 | Prefer to declare a loop variable in the initializer part of a... | readability & maintainability |
| ES.77 | Minimize the use of break and continue in loops | readability & maintainability |
| ES.87 | Don't add redundant == or != to conditions | readability & maintainability |
| ES.101 | Use unsigned types for bit manipulation | strong type safety |
| ES.107 | Don't use unsigned for subscripts, prefer gsl::index | strong type safety |

## Per: Performance

**Scenario / Theme:** Performance-sensitive design, copying, allocation, layout, and algorithmic efficiency.
**Reference:** [references/09-per-performance.md](references/09-per-performance.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| Per.1 | Don't optimize without reason | performance & cost |
| Per.2 | Don't optimize prematurely | performance & cost |
| Per.3 | Don't optimize something that's not performance critical | performance & cost |
| Per.4 | Don't assume that complicated code is necessarily faster than... | performance & cost |
| Per.5 | Don't assume that low-level code is necessarily faster than high-... | performance & cost |
| Per.6 | Don't make claims about performance without measurements | performance & cost |
| Per.7 | Design to enable optimization | performance & cost |
| Per.10 | Rely on the static type system | strong type safety |
| Per.11 | Move computation from run time to compile time | performance & cost |
| Per.12 | Eliminate redundant aliases | performance & cost |
| Per.13 | Eliminate redundant indirections | performance & cost |
| Per.14 | Minimize the number of allocations and deallocations | performance & cost |
| Per.15 | Don't allocate on a critical branch | performance & cost |
| Per.16 | Use compact data structures | performance & cost |
| Per.17 | Declare the most used member of a time-critical struct first | performance & cost |
| Per.18 | Space is time | performance & cost |
| Per.19 | Access memory predictably | performance & cost |
| Per.30 | Avoid context switches on the critical path | performance & cost |

## CP: Concurrency and parallelism

**Scenario / Theme:** Threads, locks, waiting, coroutines, message passing, and parallel execution safety.
**Reference:** [references/10-cp-concurrency-and-parallelism.md](references/10-cp-concurrency-and-parallelism.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| CP.1 | Assume that your code will run as part of a multi-threaded program | thread & coroutine safety |
| CP.3 | Minimize explicit sharing of writable data | thread & coroutine safety |
| CP.4 | Think in terms of tasks, rather than threads | thread & coroutine safety |
| CP.9 | Whenever feasible use tools to validate your concurrent code | thread & coroutine safety |
| CP.23 | Think of a joining thread as a scoped container | thread & coroutine safety |
| CP.31 | Pass small amounts of data between threads by value, rather than... | thread & coroutine safety |
| CP.32 | To share ownership between unrelated threads use shared_ptr | ownership & lifetime, thread & coroutine safety |
| CP.40 | Minimize context switching | thread & coroutine safety |
| CP.41 | Minimize thread creation and destruction | thread & coroutine safety |
| CP.50 | Define a mutex together with the data it guards. Use... | thread & coroutine safety |
| CP.60 | Use a future to return a value from a concurrent task | interface design |
| CP.61 | Use async to spawn concurrent tasks | thread & coroutine safety |
| CP.100 | Don't use lock-free programming unless you absolutely have to | thread & coroutine safety |
| CP.101 | Distrust your hardware/compiler combination | thread & coroutine safety |
| CP.102 | Carefully study the literature | thread & coroutine safety |
| CP.110 | Don't write your own double-checked locking for initialization | thread & coroutine safety |
| CP.111 | Use a conventional pattern if you really need double-checked locking | thread & coroutine safety |
| CP.201 | Signals | thread & coroutine safety |

## E: Error handling

**Scenario / Theme:** Exceptions, error propagation, failure signaling, and recovery strategy.
**Reference:** [references/11-e-error-handling.md](references/11-e-error-handling.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| E.1 | Develop an error-handling strategy early in a design | exception safety |
| E.2 | Throw an exception to signal that a function can't perform its... | exception safety |
| E.3 | Use exceptions for error handling only | exception safety |
| E.4 | Design your error-handling strategy around invariants | exception safety |
| E.6 | Use RAII to prevent leaks | exception safety |
| E.7 | State your preconditions | contract & validation |
| E.8 | State your postconditions | contract & validation |
| E.12 | Use noexcept when exiting a function because of a throw is... | exception safety |
| E.14 | Use purpose-designed user-defined types as exceptions | exception safety |
| E.18 | Minimize the use of explicit try/catch | exception safety |
| E.19 | Use a final_action object to express cleanup if no suitable... | ownership & lifetime |
| E.25 | If you can't throw exceptions, simulate RAII for resource management | exception safety |
| E.26 | If you can't throw exceptions, consider failing fast | exception safety |
| E.27 | If you can't throw exceptions, use error codes systematically | exception safety |
| E.28 | Avoid error handling based on global state | global state & initialization |

## Con: Constants and immutability

**Scenario / Theme:** Constness, immutability, and compile-time constants.
**Reference:** [references/12-con-constants-and-immutability.md](references/12-con-constants-and-immutability.md)

All `Con.*` rules are already elevated into `Iron Rules` or `Flag Rules`, so this chapter has no remaining non-priority entries here.

## T: Templates and generic programming

**Scenario / Theme:** Templates, concepts, generic interfaces, variadics, and metaprogramming.
**Reference:** [references/13-t-templates-and-generic-programming.md](references/13-t-templates-and-generic-programming.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| T.2 | Use templates to express algorithms that apply to many argument... | generic programming, standard algorithms |
| T.4 | Use templates to express syntax tree manipulation | generic programming |
| T.5 | Combine generic and OO techniques to amplify their strengths, not... | generic programming |
| T.11 | Whenever possible use standard concepts | generic programming |
| T.12 | Prefer concept names over auto for local variables | generic programming |
| T.13 | Prefer the shorthand notation for simple, single-type argument... | generic programming |
| T.22 | Specify axioms for concepts | generic programming |
| T.24 | Use tag classes or traits to differentiate concepts that differ... | generic programming |
| T.26 | Prefer to define concepts in terms of use-patterns rather than... | generic programming |
| T.41 | Require only essential properties in a template's concepts | generic programming |
| T.48 | If your compiler does not support concepts, fake them with enable_if | generic programming |
| T.49 | Where possible, avoid type-erasure | generic programming |
| T.60 | Minimize a template's context dependencies | generic programming |
| T.62 | Place non-dependent class template members in a non-templated... | generic programming |
| T.64 | Use specialization to provide alternative implementations of... | generic programming |
| T.65 | Use tag dispatch to provide alternative implementations of a... | generic programming |
| T.67 | Use specialization to provide alternative implementations for... | generic programming |
| T.82 | Linearize a hierarchy when virtual functions are undesirable | inheritance & polymorphism |
| T.83 | Don't declare a member function template virtual | inheritance & polymorphism |
| T.84 | Use a non-template core implementation to provide an ABI-stable... | generic programming |
| T.101 | How to pass arguments to a variadic template | generic programming |
| T.102 | How to process arguments to a variadic template | generic programming |
| T.103 | Don't use variadic templates for homogeneous argument lists | generic programming |
| T.120 | Use template metaprogramming only when you really need to | generic programming |
| T.121 | Use template metaprogramming primarily to emulate concepts | generic programming |
| T.122 | Use templates to compute types at compile time | generic programming |
| T.124 | Prefer to use standard-library TMP facilities | generic programming |
| T.125 | If you need to go beyond the standard-library TMP facilities, use... | generic programming |
| T.140 | If an operation can be reused, give it a name | readability & maintainability |
| T.141 | Use an unnamed lambda if you need a simple function object in one... | generic programming |
| T.150 | Check that a class matches a concept using static_assert | generic programming |

## CPL: C-style programming

**Scenario / Theme:** C interoperability, C-style constructs, and compatibility boundaries.
**Reference:** [references/14-cpl-c-style-programming.md](references/14-cpl-c-style-programming.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| CPL.1 | Prefer C++ to C | C interop safety |
| CPL.3 | If you must use C for interfaces, use C++ in the calling code... | C interop safety |

## SF: Source files

**Scenario / Theme:** Headers, source files, includes, linkage boundaries, and file/module organization.
**Reference:** [references/15-sf-source-files.md](references/15-sf-source-files.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| SF.1 | Use a .cpp suffix for code files and .h for interface files if... | naming conventions |
| SF.2 | A header file must not contain object definitions or non-inline... | module boundaries |
| SF.4 | Include header files before other declarations in a file | include hygiene |
| SF.6 | Use using namespace directives for transition, for foundation... | module boundaries |
| SF.10 | Avoid dependencies on implicitly #included names | include hygiene |
| SF.11 | Header files should be self-contained | include hygiene |
| SF.12 | Prefer the quoted form of #include for files relative to the... | include hygiene |
| SF.13 | Use portable header identifiers in #include statements | include hygiene |
| SF.20 | Use namespaces to express logical structure | module boundaries |
| SF.22 | Use an unnamed namespace for all internal/non-exported entities | module boundaries |

## SL: The Standard Library

**Scenario / Theme:** Standard-library containers, strings, I/O, regex, time, and C-library interop.
**Reference:** [references/16-sl-standard-library.md](references/16-sl-standard-library.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| SL.1 | Use libraries wherever possible | standard library usage |
| SL.2 | Prefer the standard library to other libraries | standard library usage |
| SL.3 | Don't add non-standard entities to namespace std | module boundaries |
| SL.4 | Use the standard library in a type-safe manner | standard library usage |
| SL.str.1 | Use std::string to own character sequences | standard library usage |
| SL.str.2 | Use std::string_view or gsl::span<char> to refer to character... | ownership & lifetime, standard library usage |
| SL.str.5 | Use std::byte to refer to byte values that do not necessarily... | standard library usage |
| SL.str.10 | Use std::string when you need to perform locale-sensitive string... | standard library usage |
| SL.str.11 | Use gsl::span<char> rather than std::string_view when you need to... | ownership & lifetime, standard library usage |
| SL.str.12 | Use the s suffix for string literals meant to be standard-library... | standard library usage |
| SL.io.1 | Use character-level input only when you have to | standard library usage |
| SL.io.2 | When reading, always consider ill-formed input | standard library usage |
| SL.io.10 | Unless you use printf-family functions call... | standard library usage |
| SL.io.50 | Avoid endl | standard library usage |

## A: Architectural ideas

**Scenario / Theme:** Architecture-level structuring ideas and system design boundaries.
**Reference:** [references/17-a-architectural-ideas.md](references/17-a-architectural-ideas.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| A.1 | Separate stable code from less stable code | module boundaries |
| A.2 | Express potentially reusable parts as a library | module boundaries |
| A.4 | There should be no cycles among libraries | module boundaries |

## NR: Non-Rules and myths

**Scenario / Theme:** Common misconceptions, tradeoff reminders, and non-rule clarifications.
**Reference:** [references/18-nr-non-rules-and-myths.md](references/18-nr-non-rules-and-myths.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| NR.1 | Don't insist that all declarations should be at the top of a... | readability & maintainability |
| NR.2 | Don't insist on having only a single return-statement in a function | readability & maintainability |
| NR.3 | Don't avoid exceptions | readability & maintainability |
| NR.4 | Don't insist on placing each class definition in its own source file | module boundaries |
| NR.5 | Don't use two-phase initialization | readability & maintainability |
| NR.6 | Don't place all cleanup actions at the end of a function and goto... | readability & maintainability |
| NR.7 | Don't make data members protected | class design |

## NL: Naming and layout suggestions

**Scenario / Theme:** Naming, formatting, declaration order, and code layout conventions.
**Reference:** [references/19-nl-naming-and-layout.md](references/19-nl-naming-and-layout.md)

| # | Rule Key Points | Focus Scope |
|---|---|---|
| NL.1 | Don't say in comments what can be clearly stated in code | readability & maintainability |
| NL.2 | State intent in comments | readability & maintainability |
| NL.3 | Keep comments crisp | readability & maintainability |
| NL.4 | Maintain a consistent indentation style | readability & maintainability |
| NL.5 | Avoid encoding type information in names | naming conventions |
| NL.7 | Make the length of a name roughly proportional to the length of... | naming conventions |
| NL.8 | Use a consistent naming style | naming conventions |
| NL.10 | Prefer underscore_style names | naming conventions |
| NL.15 | Use spaces sparingly | readability & maintainability |
| NL.17 | Use K&R-derived layout | readability & maintainability |
| NL.18 | Use C++-style declarator layout | readability & maintainability |
| NL.19 | Avoid names that are easily misread | naming conventions |
| NL.20 | Don't place two statements on the same line | readability & maintainability |
| NL.21 | Declare one name per declaration | readability & maintainability |
| NL.25 | Don't use void as an argument type | interface design |
