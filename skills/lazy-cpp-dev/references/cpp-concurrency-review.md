# C++ Concurrency, Lifetime, and Review

Use this note when a task touches threads, atomics, locks, coroutines, async
work, callbacks, caches, public APIs, or code that could hide UB/lifetime bugs.

## Concurrency defaults

- Pair every mutex with the data it guards, ideally in the same type.
- Use named RAII locks: `std::scoped_lock`, `std::lock_guard`, or
  `std::unique_lock`; avoid raw `lock()` / `unlock()`.
- Acquire multiple mutexes with `std::scoped_lock` to avoid deadlock.
- Treat `volatile` as not synchronization; use `std::atomic` or locks.
- Every thread needs an owner, cancellation/stop condition, and join/wait path.
- Prefer `std::jthread`, thread pools, or joining wrappers over `detach()`.
- Avoid `detach()` unless all touched state has global or otherwise proven
  lifetime.
- Pass small data between threads by value; share ownership via `shared_ptr`
  only when ownership is genuinely shared.
- Do not hold locks across unknown callbacks, virtual calls, blocking I/O, or
  `co_await`.
- Coroutine parameters must not borrow caller-owned data across suspension.
- Capturing lambdas used as coroutines are a sharp edge; prefer named coroutine
  functions or explicit lifetime management.
- Avoid default lambda captures (`[=]`, `[&]`) for escaping callbacks; capture
  values explicitly or hold `weak_ptr`.
- Do not hand-roll double-checked locking; use function-local statics or
  `std::call_once`.

## Lifetime defaults

- Every owning resource belongs to a RAII handle: smart pointer, container,
  `fstream`, socket/file wrapper, lock wrapper, or custom owner type.
- Never return a pointer, reference, iterator, `span`, or `string_view` to local
  or soon-invalid storage.
- A `string_view` / `span` must not outlive its source, including after moves,
  vector reallocation, string mutation, or temporary destruction.
- Treat moved-from objects as valid but unspecified until reassigned.
- Re-acquire iterators and pointers after container mutation that may
  invalidate them (`push_back`, `insert`, `erase`, `resize`, rehash).
- Escaping lambdas must not capture stack locals by reference.
- For polymorphic types, avoid slicing, ensure safe destruction, and avoid
  virtual calls from constructors/destructors.

## Common pitfalls

- Fire-and-forget `std::thread::detach()` touches stack data.
- `this` captured implicitly by a callback that outlives the object.
- `string_view` returned from a function that built a local `std::string`.
- `span` over a vector that later reallocates.
- Iterator invalidation after insert/erase/realloc/rehash.
- Use-after-move on strings, containers, or smart pointers.
- Base-class pass-by-value slices derived state.
- Polymorphic delete through a base with non-virtual destructor.
- `volatile` used as a synchronization primitive.
- Naked lock/unlock, inconsistent lock order, or anonymous lock guards.
- Holding locks across `co_await`, blocking I/O, or user callbacks.
- `memset` / `memcpy` on non-trivially-copyable types.
- Signed/unsigned arithmetic bugs, narrowing, C-style casts, and unsafe
  `const_cast`.
- Throwing destructors or non-`noexcept` move operations that break exception
  safety.

## Review order

1. Behavior and correctness.
2. Undefined behavior and lifetime safety.
3. Security and data exposure.
4. Concurrency, leaks, ownership, and exception safety.
5. API/ABI compatibility and error flow.
6. Missing tests and sanitizer gaps.
7. Naming/style nits.

## Focused checklist

### Correctness and lifetime

- Returned pointer/reference/view to a local?
- `string_view`, `span`, iterator, or pointer outlives its source?
- Moved-from object read before reassignment?
- Container iterator/pointer used after invalidating mutation?
- Uninitialized value, narrowing, or signed/unsigned mix?

### Ownership and resources

- Every owning resource in RAII?
- Naked `new`/`delete` or mismatched `new[]`/`delete`?
- Smart pointer parameter implies ownership when a reference would do?
- Rule of Five / Rule of Zero respected?
- Self-assignment safe where assignment is custom?

### Polymorphism

- Polymorphic base with unsafe destructor?
- Slicing on copy/pass-by-value?
- Virtual call from constructor/destructor?
- `dynamic_cast` pointer dereferenced without null check?

### Concurrency

- Mutex clearly protects specific data?
- Locks named and scoped?
- Multiple mutexes acquired safely?
- Raw lock/unlock or volatile-as-sync?
- Detached thread touches non-global data?
- Lock held across callback/I/O/`co_await`?
- Double-checked locking written by hand?

### Boundaries

- Inputs validated at API/handler boundaries?
- Unsafe C string/buffer APIs avoided?
- Shell/SQL parameterized?
- Secrets/JWTs/PII absent from logs?
- Behavior change has tests or a stated coverage gap?
