# C++ Service / Project Stack

Concise defaults for modern C++ projects. Always defer to the repo's actual
conventions, build files, and lint configs over this note.

## Detect first, default second

Before writing or reviewing code, gather:

- C++ standard from `CMakeLists.txt` (`CMAKE_CXX_STANDARD`, `cxx_std_*`),
  Bazel `cxxopts`, or compiler flags (`-std=c++20`); fall back to C++20 only
  when the repo gives no signal.
- Compiler family and warning level: gcc, clang, MSVC, `-Wall`, `-Wextra`,
  `-Wpedantic`, `-Werror`.
- Build tool and deps: CMake, Bazel, Make, Meson, Conan, vcpkg, CI commands.
- Format/lint: `.clang-format`, `.clang-tidy`, `.editorconfig`, `cppcheck`,
  include-what-you-use.
- Test framework: GoogleTest, Catch2, doctest, Boost.Test, or local harness.
- Project conventions: `AGENTS.md`, `man/`, `docs/`, nearby files, custom
  strings/containers (`CString`, `QString`, `FString`, `absl::*`), and whether
  exceptions are disabled.

## Core C++ shape

- Match the repo's style exactly: indentation, brace style, member prefixes,
  include order, and naming.
- Prefer RAII and value semantics. Avoid naked owning `new`/`delete`.
- Use `std::make_unique` / `std::make_shared`; avoid `new T(...)` in user code.
- Initialize every variable; prefer brace initialization when it prevents
  narrowing.
- Mark single-argument constructors `explicit` unless conversion is intended.
- Use `const`, `constexpr`, and `noexcept` honestly, not decoratively.
- Prefer `enum class` over plain `enum`.
- Add Doxygen-style comments to new public APIs if the repo does so.

## API and interface design

- Cheap-to-copy values: pass by value.
- Larger read-only inputs: pass by `const T&`.
- Inputs the function stores or consumes: pass by value and move, or use `T&&`
  for move-only sinks.
- Outputs: prefer return-by-value; avoid output parameters unless local style
  requires them.
- Absence: use `std::optional` or the repo's equivalent.
- Failure: use the repo's convention: exceptions, error codes, `std::expected`,
  `tl::expected`, `absl::Status`, or a local result type.
- Non-owning views (`std::span`, `std::string_view`) must document lifetime
  expectations at public boundaries.
- Prefer `T&` or `not_null<T*>`-style contracts when null is invalid.
- Avoid adjacent same-typed parameters that callers can swap accidentally.
- Do not return `T&&` or `const T` by value; do not `return std::move(x)` when
  copy elision applies.

## Class design

- Establish invariants in constructors and fully initialize all members.
- Rule of Five / Rule of Zero: if one special member is custom, decide on all
  of destructor, copy ctor, copy assignment, move ctor, and move assignment.
- Make move operations and `swap` `noexcept` when correct.
- For polymorphic bases, use a virtual destructor or protected non-virtual
  destructor.
- Avoid virtual calls from constructors/destructors.
- Avoid trivial getters/setters that merely expose data; prefer domain
  operations.
- Prefer non-member non-friend functions for symmetric operators.
- Avoid `protected` data members.

## STL, strings, and headers

- Default to `std::vector`, `std::array`, and `std::string` over raw arrays and
  raw `char*`.
- Use `<algorithm>`, `<numeric>`, and ranges when they improve clarity.
- Reserve container capacity when size is known and reallocation would matter.
- Headers must be self-contained, guarded or `#pragma once`, and should not
  depend on include order.
- `.cpp` files include their corresponding header first.
- Never put `using namespace` at global scope in a header.
- Never use unnamed namespaces in headers.
- Break cyclic includes with forward declarations when possible.

## Error handling and security

- Use RAII so unwinding leaves no leaks.
- Throw by value and catch by reference when exceptions are enabled.
- Destructors must not throw.
- If exceptions are disabled, follow the repo's error-code/result convention.
- Never log secrets, tokens, raw JWTs, raw response bodies, or sensitive PII.
- Avoid `system()`, `popen()`, and `exec*` with user input.
- Avoid `strcpy`, `strcat`, `sprintf`, `gets`, and unbounded `scanf` formats.
- Use parameterized SQL/shell helpers; validate uploads, pagination, regex, and
  parsing inputs at boundaries.
- Use CSPRNG/project crypto helpers for security-sensitive randomness.

## Build and tooling

- Prefer project commands: `just`, `make`, `cmake --build`, `bazel build/test`,
  scripts, or CI docs.
- Run `clang-format` / `clang-tidy` only with the repo's existing config.
- Sanitizers when relevant:
  - ASan for memory bugs.
  - UBSan for undefined behavior.
  - TSan for races; run separately from ASan.
- If repo conventions conflict with these defaults, follow the repo and call
  out the deliberate deviation in the response.
