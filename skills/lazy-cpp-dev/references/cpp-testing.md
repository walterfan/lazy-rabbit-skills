# C++ Testing

Use this reference when writing or reviewing C++ tests for classes, services,
free functions, public APIs, async code, or low-level utilities. Keep the
framework the repo already uses: GoogleTest, Catch2, doctest, Boost.Test, or a
local harness.

## Default test style

- Cover happy path, edge cases, and error paths.
- Keep tests independent; no test relies on another test's state.
- Prefer table/parameterized tests for input matrices.
- Mock external dependencies through small interfaces; do not mock value types,
  the standard library, or the type under test.
- Test public behavior instead of private implementation details.
- Avoid sleeps and timing guesses; synchronize concurrent tests deliberately.
- Run under ASan/UBSan for ownership/lifetime changes and TSan for races when
  supported.

## GoogleTest example

```cpp
#include <gtest/gtest.h>
#include "service.h"

namespace {

TEST(ServiceTest, ReturnsValueOnValidInput) {
    Service service;
    auto result = service.Lookup("alice");
    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(result->name, "alice");
}

TEST(ServiceTest, ReturnsErrorOnEmptyInput) {
    Service service;
    auto result = service.Lookup("");
    EXPECT_FALSE(result.has_value());
}

struct LookupCase {
    std::string input;
    bool expect_ok;
};

class LookupParamTest : public ::testing::TestWithParam<LookupCase> {};

TEST_P(LookupParamTest, BehavesAsExpected) {
    Service service;
    EXPECT_EQ(service.Lookup(GetParam().input).has_value(),
              GetParam().expect_ok);
}

INSTANTIATE_TEST_SUITE_P(
    LookupCases, LookupParamTest,
    ::testing::Values(LookupCase{"alice", true}, LookupCase{"", false}));

}  // namespace
```

## Catch2 example

```cpp
#include <catch2/catch_test_macros.hpp>
#include "service.h"

TEST_CASE("Service::Lookup rejects empty input", "[service]") {
    Service service;
    auto result = service.Lookup("");
    CHECK_FALSE(result.has_value());
}
```

## What to cover per change

- New happy path through the public API.
- New error paths: invalid input, exception, error code, timeout, empty/max/min
  values, and off-by-one boundaries.
- Ownership/lifetime: construct, move, copy, and destroy in the risky order;
  prefer ASan coverage.
- Concurrency: deterministic shared-path tests, ideally gated by `std::latch`,
  `std::barrier`, promises, or explicit test hooks; prefer TSan coverage.

## Common test smells

- Constructing objects without assertions.
- One large test that hides which behavior failed.
- Timing-based thread tests.
- Shared global state that breaks with order or parallelism.
- `friend` / `#define private public` to inspect implementation details.
- Mock matrices that assert call choreography instead of behavior.

## Running tests

- Prefer project commands: `just test`, `make test`, `scripts/test.sh`, CI docs.
- CMake + CTest: configure/build, then
  `ctest --test-dir build --output-on-failure`.
- Bazel: `bazel test //path/to:target_test --test_output=errors`.
- Sanitizers: ASan/UBSan together when supported; TSan in a separate build.
