# C++ Modernization

Use this reference when the user explicitly asks to modernize legacy C++ or
replace old idioms while preserving behavior and reviewability.

## Migration playbook

1. Confirm target standard from build files and CI.
2. Skim for naked ownership, C strings, manual cleanup, unsafe casts, raw
   arrays, old typedefs, missing `override`, `NULL`, `volatile` sync, and
   handwritten loops.
3. Pick the smallest coherent batch. Good batches are ownership, nullability,
   casts, loops, string APIs, tests, or warnings.
4. Preserve public API/ABI unless the user explicitly accepts a breaking
   change.
5. Run tests after each batch; use sanitizers for ownership/lifetime changes.

## Common upgrades

- `new`/`delete` ownership -> `std::unique_ptr`, `std::shared_ptr`, containers,
  or a custom RAII wrapper.
- `NULL` / `0` pointer constants -> `nullptr`.
- `typedef` -> `using` aliases.
- Raw arrays -> `std::array` for fixed size or `std::vector` for dynamic size.
- Raw C strings -> `std::string`; non-owning parameters may use
  `std::string_view` only when lifetime is safe.
- Plain `enum` -> `enum class` when API compatibility allows it.
- Magic constants -> named constants or scoped enums.
- Manual cleanup -> destructors, smart pointers, or scope guards.
- Hand-written loops -> `<algorithm>` / ranges only when clearer.
- Missing virtual overrides -> `override`.
- C-style casts -> named casts, or redesign if the cast hides type confusion.
- `auto_ptr` -> `unique_ptr`.
- `std::bind` -> lambdas when captures and lifetime are clearer.

## Before/after patterns

Prefer small, reviewable transformations:

```cpp
// Before
Widget* w = new Widget(config);
Use(w);
delete w;

// After
auto w = std::make_unique<Widget>(config);
Use(*w);
```

```cpp
// Before
typedef std::map<std::string, int> Counts;

// After
using Counts = std::map<std::string, int>;
```

```cpp
// Before
void SetName(const std::string& name);

// After, only if the function stores a copy
void SetName(std::string name) {
    name_ = std::move(name);
}
```

## Stop signs

- Stable ABI headers, virtual layout, default arguments, or serialized formats.
- Exception policy differs from the desired pattern.
- Custom in-house string/result/thread types at API boundaries.
- Performance-sensitive hot paths without measurements.
- Modernization that mixes style churn with behavior changes.

## Response expectations

For modernization work, name the behavior preserved, the API/ABI risk, tests
run, and any remaining manual review needed.
