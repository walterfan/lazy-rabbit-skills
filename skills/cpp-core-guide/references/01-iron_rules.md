# Iron Rules — Violations That Cause Crashes, UB, OOB, or Leaks

Rules whose violation directly leads to **system crashes**, **memory read/write out-of-bounds**, **undefined behavior**, or **memory/resource leaks**. Extracted from all C++ Core Guidelines chapters.

When reviewing or writing C++ code, **check these rules first** — they represent the highest-severity defects.

## Table of Contents

- [1. Data Races — CP.2](#1-data-races--cp2)
- [2. Use RAII, Never Plain lock/unlock — CP.20](#2-use-raii-never-plain-lockunlock--cp20)
- [3. Don't Leak Any Resources — P.8, R.1](#3-dont-leak-any-resources--p8-r1)
- [4. Use unique_ptr/shared_ptr — R.11, R.20, R.21, ES.24, ES.60, ES.61](#4-use-unique_ptrshared_ptr--r11-r20-r21-es24-es60-es61)
- [5. Destructor Must Release All Resources — C.31, C.33](#5-destructor-must-release-all-resources--c31-c33)
- [6. Virtual Destructor in Polymorphic Base — C.35, C.127](#6-virtual-destructor-in-polymorphic-base--c35-c127)
- [7. Destructor Must Not Fail — C.36, C.37, E.16](#7-destructor-must-not-fail--c36-c37-e16)
- [8. No Virtual Calls in Constructors/Destructors — C.82](#8-no-virtual-calls-in-constructorsdestructors--c82)
- [9. Rule of Five — C.21](#9-rule-of-five--c21)
- [10. Copy/Move Self-Assignment Safety — C.62, C.65](#10-copymove-self-assignment-safety--c62-c65)
- [11. Don't Slice Polymorphic Objects — C.67, C.145, ES.63](#11-dont-slice-polymorphic-objects--c67-c145-es63)
- [12. Never Mix Hierarchies and Arrays — C.152, T.81](#12-never-mix-hierarchies-and-arrays--c152-t81)
- [13. Don't Dereference Invalid/Null Pointers — ES.65, I.12](#13-dont-dereference-invalidnull-pointers--es65-i12)
- [14. Undefined Order of Evaluation — ES.43, ES.44](#14-undefined-order-of-evaluation--es43-es44)
- [15. Don't Overflow / Don't Divide by Zero — ES.103, ES.104, ES.105](#15-dont-overflow--dont-divide-by-zero--es103-es104-es105)
- [16. Don't Mix Signed and Unsigned — ES.100, ES.106](#16-dont-mix-signed-and-unsigned--es100-es106)
- [17. Always Initialize Objects — ES.20](#17-always-initialize-objects--es20)
- [18. No Naked new/delete — R.11, R.12](#18-no-naked-newdelete--r11-r12)
- [19. No Union Type Punning — C.183](#19-no-union-type-punning--c183)
- [20. volatile Is Not Synchronization — CP.8, CP.200](#20-volatile-is-not-synchronization--cp8-cp200)
- [21. Don't Hold Locks Across Coroutine Suspension — CP.52](#21-dont-hold-locks-across-coroutine-suspension--cp52)
- [22. Coroutine Parameters Must Not Be References — CP.53](#22-coroutine-parameters-must-not-be-references--cp53)
- [23. Don't detach() Threads — CP.26](#23-dont-detach-threads--cp26)
- [24. Use scoped_lock for Multiple Mutexes — CP.21](#24-use-scoped_lock-for-multiple-mutexes--cp21)
- [25. No Capturing Lambda Coroutines — CP.51](#25-no-capturing-lambda-coroutines--cp51)
- [26. Avoid C-style Casts — ES.48, ES.49](#26-avoid-c-style-casts--es48-es49)
- [27. Don't Cast Away const — ES.50](#27-dont-cast-away-const--es50)
- [28. Avoid C-style Variadic Functions — ES.34](#28-avoid-c-style-variadic-functions--es34)
- [29. Match new/delete Forms — ES.61](#29-match-newdelete-forms--es61)
- [30. Don't Compare Pointers into Different Arrays — ES.62](#30-dont-compare-pointers-into-different-arrays--es62)
- [31. Never Return Pointer/Reference to a Local Object — F.43](#31-never-return-pointerreference-to-a-local-object--f43)
- [32. Don't memset/memcpy Non-Trivially-Copyable Types — C.90, SL.con.4](#32-dont-memsetmemcpy-non-trivially-copyable-types--c90-slcon4)
- [33. Avoid Container/Array Bounds Errors — SL.con.3](#33-avoid-containerarray-bounds-errors--slcon3)
- [34. Don't Pass an Array as a Single Pointer — I.13](#34-dont-pass-an-array-as-a-single-pointer--i13)
- [35. Don't Pass Pointer/Reference from Aliased Smart Pointer — R.37](#35-dont-pass-pointerreference-from-aliased-smart-pointer--r37)
- [36. Never Throw While Being Direct Owner of a Resource — E.13](#36-never-throw-while-being-direct-owner-of-a-resource--e13)
- [37. Don't Use setjmp/longjmp — SL.C.1](#37-dont-use-setjmplongjmp--slc1)
- [38. Don't Capture by Reference in Non-Local Lambdas — F.53](#38-dont-capture-by-reference-in-non-local-lambdas--f53)
- [39. Don't Dereference Invalidated Iterators/Pointers — ES.65](#39-dont-dereference-invalidated-iteratorspointers--es65)
- [40. Don't Read from a Moved-From Object — ES.56, C.64](#40-dont-read-from-a-moved-from-object--es56-c64)
- [41. Don't Let a string_view Outlive Its Source — ES.65 (lifetime)](#41-dont-let-a-string_view-outlive-its-source--es65-lifetime)

---

## 1. Data Races — CP.2

**severity:** Undefined behavior, crash, data corruption

If two threads can access the same object concurrently without synchronization, and at least one is a writer, you have a data race.

```cpp
// BAD — data race on static variable
int get_id()
{
    static int id = 1;
    return id++;  // UB: two threads may get same ID or corrupt id
}

// GOOD — use atomic
std::atomic<int> get_id()
{
    static std::atomic<int> id{1};
    return id++;
}
```

---

## 2. Use RAII, Never Plain lock/unlock — CP.20

**severity:** Deadlock, crash, resource leak

Sooner or later, someone will forget `unlock()`, place a `return`, or throw an exception.

```cpp
// BAD
mutex mtx;
void do_stuff()
{
    mtx.lock();
    // ... if exception thrown here, mtx never unlocked → deadlock
    mtx.unlock();
}

// GOOD
mutex mtx;
void do_stuff()
{
    unique_lock<mutex> lck{mtx};
    // automatically released on scope exit
}
```

---

## 3. Don't Leak Any Resources — P.8, R.1

**severity:** Resource leak, eventual system exhaustion

Even a slow growth in resources will, over time, exhaust their availability.

```cpp
// BAD — file handle leak on early return
void f(const char* name)
{
    FILE* input = fopen(name, "r");
    if (something) return;   // leaked!
    fclose(input);
}

// GOOD — RAII
void f(const char* name)
{
    ifstream input{name};
    if (something) return;   // no leak
}
```

---

## 4. Use unique_ptr/shared_ptr — R.11, R.20, R.21, ES.24, ES.60, ES.61

**severity:** Memory leak, double-free, use-after-free

Naked `new` and `delete` are the root of all resource-management evil.

```cpp
// BAD — leak on exception or early return
void use(bool leak)
{
    int* p2 = new int{7};
    if (leak) return;         // leaked!
    vector<int> v(7);
    v.at(7) = 0;              // throws → p2 leaked
    delete p2;
}

// GOOD
void use(bool leak)
{
    auto p1 = make_unique<int>(7);
    if (leak) return;         // p1 auto-deleted
}
```

---

## 5. Destructor Must Release All Resources — C.31, C.33

**severity:** Memory leak, resource leak

All resources acquired by a class must be released by the class's destructor.

```cpp
// BAD — owning pointer without destructor
class Foo {
    int* data;
public:
    Foo() : data(new int[100]) {}
    // no destructor → leak!
};

// GOOD
class Foo {
    unique_ptr<int[]> data;
public:
    Foo() : data(make_unique<int[]>(100)) {}
};
```

---

## 6. Virtual Destructor in Polymorphic Base — C.35, C.127

**severity:** Undefined behavior, memory leak, partial destruction

Deleting a derived object through a base pointer with a non-virtual destructor is UB.

```cpp
// BAD
struct Base {
    virtual void f();
    // non-virtual destructor!
};
struct D : Base {
    string s{"resource"};
    ~D() { /* cleanup */ }
};
void use()
{
    unique_ptr<Base> p = make_unique<D>();
}  // calls ~Base(), not ~D() → UB, leaks D::s

// GOOD
struct Base {
    virtual void f();
    virtual ~Base() = default;
};
```

---

## 7. Destructor Must Not Fail — C.36, C.37, E.16

**severity:** Crash (std::terminate), undefined behavior

If a destructor throws during stack unwinding, `std::terminate` is called.

```cpp
// BAD
class X {
public:
    ~X() noexcept(false) {
        throw runtime_error("cleanup failed");  // may call terminate!
    }
};

// GOOD
class X {
public:
    ~X() noexcept {
        try { cleanup(); }
        catch (...) { /* swallow or log */ }
    }
};
```

---

## 8. No Virtual Calls in Constructors/Destructors — C.82

**severity:** Unexpected behavior (calls base version, not derived override)

The function called will be that of the currently constructed object, not a possibly overriding function in a derived class.

```cpp
// BAD
class Base {
public:
    Base() { init(); }          // calls Base::init, NOT Derived::init
    virtual void init() { /* base init */ }
};
class Derived : public Base {
    int x;
public:
    void init() override { x = 42; }  // never called from Base ctor!
};
```

---

## 9. Rule of Five — C.21

**severity:** Double-free, use-after-free, memory corruption

If you define or `=delete` any copy, move, or destructor function, define or `=delete` them all.

```cpp
// BAD — destructor defined, but no copy/move ops
struct M2 {
    pair<int, int>* rep;
    ~M2() { delete[] rep; }
    // implicit copy → double delete!
};
void use()
{
    M2 x;
    M2 y;
    x = y;  // shallow copy → both delete same pointer
}

// GOOD
class M2 {
    unique_ptr<pair<int, int>[]> rep;
public:
    M2() = default;
    ~M2() = default;
    M2(const M2&) = delete;
    M2& operator=(const M2&) = delete;
    M2(M2&&) noexcept = default;
    M2& operator=(M2&&) noexcept = default;
};
```

---

## 10. Copy/Move Self-Assignment Safety — C.62, C.65

**severity:** Use-after-free, crash

If `x = x` destroys the resource before copying, undefined behavior.

```cpp
// BAD
class Foo {
    int* data;
public:
    Foo& operator=(const Foo& a) {
        delete data;           // destroys own data first!
        data = new int(*a.data);  // a.data is already deleted if self-assign
        return *this;
    }
};

// GOOD — copy-and-swap idiom
class Foo {
    int* data;
public:
    Foo& operator=(Foo a) {  // by value → copy made first
        swap(data, a.data);
        return *this;
    }
};
```

---

## 11. Don't Slice Polymorphic Objects — C.67, C.145, ES.63

**severity:** Silent data loss, incorrect behavior

Copying only part of an object using assignment or initialization loses derived data.

```cpp
// BAD — slicing
class Shape { /* ... */ };
class Circle : public Shape { Point c; int r; };

Circle c{{0,0}, 42};
Shape s{c};      // sliced! Circle data lost
s = c;           // sliced!
void f(Shape s); // slices on call
f(c);

// GOOD — use pointers/references for polymorphic types
void f(const Shape& s);
f(c);  // no slicing
```

---

## 12. Never Mix Hierarchies and Arrays — C.152, T.81

**severity:** Memory corruption, undefined behavior

Subscripting a base pointer to an array of derived objects misaligns access when sizes differ.

```cpp
// BAD
void maul(Fruit* p)
{
    *p = Pear{};
    p[1] = Pear{};  // UB: wrong offset if sizeof(Apple) != sizeof(Pear)
}
Apple aa[] = {an_apple, another_apple};
maul(aa);  // memory corruption
```

---

## 13. Don't Dereference Invalid/Null Pointers — ES.65, I.12

**severity:** Crash, undefined behavior

Dereferencing `nullptr` or dangling pointer is immediate UB, typically a crash.

```cpp
// GOOD — use gsl::not_null
int length(not_null<const char*> p);  // contract: p cannot be null

// GOOD — check before use
void f(int* p) {
    if (!p) return;
    *p = 42;
}
```

---

## 14. Undefined Order of Evaluation — ES.43, ES.44

**severity:** Undefined behavior

You have no idea what such code does. It may differ across compilers.

```cpp
// BAD — UB
v[i] = ++i;

// BAD — unspecified order of function arguments
int i = 0;
f(++i, ++i);
```

---

## 15. Don't Overflow / Don't Divide by Zero — ES.103, ES.104, ES.105

**severity:** Undefined behavior, crash

Signed integer overflow is UB. Division by zero is UB.

```cpp
// BAD
int x = INT_MAX;
x++;  // signed overflow → UB

int y = 10 / 0;  // UB → crash
```

---

## 16. Don't Mix Signed and Unsigned — ES.100, ES.106

**severity:** Wrong results, silent bugs

Implicit conversions between signed and unsigned produce surprising results.

```cpp
// BAD
int x = -3;
unsigned int y = 7;
cout << x - y << '\n';  // unsigned result: 4294967286, not -10
```

---

## 17. Always Initialize Objects — ES.20

**severity:** Undefined behavior, reading uninitialized memory

Using an uninitialized variable is UB.

```cpp
// BAD
int i;
if (i > 0) do_something();  // UB: i is uninitialized

// GOOD
int i = 0;
```

---

## 18. No Naked new/delete — R.11, R.12

**severity:** Memory leak, double-free

Naked `new`/`delete` is error-prone. Use smart pointers or containers.

```cpp
// BAD
void f()
{
    int* p = new int{7};
    // ... code that might throw or return early ...
    delete p;  // might never be reached
}

// GOOD
void f()
{
    auto p = make_unique<int>(7);
    // automatic cleanup
}
```

---

## 19. No Union Type Punning — C.183

**severity:** Undefined behavior

Reading a union member that was not the last one written is UB.

```cpp
// BAD
union Pun {
    int x;
    float f;
};
Pun p;
p.x = 42;
float val = p.f;  // UB: reading inactive member

// GOOD — use memcpy or std::bit_cast (C++20)
float val;
memcpy(&val, &p.x, sizeof(val));
```

---

## 20. volatile Is Not Synchronization — CP.8, CP.200

**severity:** Data race (undefined behavior)

In C++, `volatile` does not provide atomicity, does not synchronize between threads.

```cpp
// BAD
volatile int free_slots = max_slots;
Pool* use() {
    if (int n = free_slots--) return &pool[n];  // data race!
}

// GOOD
atomic<int> free_slots = max_slots;
Pool* use() {
    if (int n = free_slots--) return &pool[n];
}
```

---

## 21. Don't Hold Locks Across Coroutine Suspension — CP.52

**severity:** Deadlock, undefined behavior

If the coroutine resumes on a different thread, the lock is held by the wrong thread — that is UB.

```cpp
// BAD
std::future<void> do_something()
{
    std::lock_guard<std::mutex> guard(g_lock);
    co_await something();  // DANGER: suspended while holding lock
}

// GOOD
std::future<void> do_something()
{
    {
        std::lock_guard<std::mutex> guard(g_lock);
        // modify data
    }  // lock released
    co_await something();  // safe
}
```

---

## 22. Coroutine Parameters Must Not Be References — CP.53

**severity:** Use-after-free, dangling reference

After the first suspension point, reference parameters are dangling.

```cpp
// BAD
std::future<int> do_something(const std::shared_ptr<int>& input)
{
    co_await something();
    co_return *input + 1;  // DANGER: input may be dangling
}

// GOOD — take by value
std::future<int> do_something(std::shared_ptr<int> input)
{
    co_await something();
    co_return *input + 1;  // safe: input is a copy
}
```

---

## 23. Don't detach() Threads — CP.26

**severity:** Use-after-free, dangling pointer

Detached threads accessing local or stack variables after the creating scope exits leads to UB.

```cpp
// BAD
void some_fct()
{
    int x = 77;
    std::thread t([&x] { use(x); });
    t.detach();  // x destroyed when some_fct returns → dangling
}

// GOOD — use joining_thread or jthread
void some_fct()
{
    int x = 77;
    std::jthread t([&x] { use(x); });
    // automatically joins before x is destroyed
}
```

---

## 24. Use scoped_lock for Multiple Mutexes — CP.21

**severity:** Deadlock

Locking multiple mutexes in different orders causes deadlock.

```cpp
// BAD — deadlock prone
// thread 1                    // thread 2
lock_guard<mutex> lck1(m1);   lock_guard<mutex> lck2(m2);
lock_guard<mutex> lck2(m2);   lock_guard<mutex> lck1(m1);

// GOOD — C++17 scoped_lock
scoped_lock lck(m1, m2);  // order no longer matters
```

---

## 25. No Capturing Lambda Coroutines — CP.51

**severity:** Use-after-free

Captured variables are destroyed when the lambda closure goes out of scope, but the coroutine may still be running.

```cpp
// BAD
int value = get_value();
{
    const auto lambda = [value]() -> std::future<void> {
        co_await something();
        // value has already been destroyed!
    };
    lambda();
}  // lambda closure destroyed, coroutine still running

// GOOD — pass as parameter
const auto lambda = [](auto value) -> std::future<void> {
    co_await something();
    // value is still valid
};
lambda(get_value());
```

---

## 26. Avoid C-style Casts — ES.48, ES.49

**severity:** Undefined behavior, type confusion

C-style casts can silently perform `reinterpret_cast` and bypass the type system.

```cpp
// BAD
double d = 3.14;
int* p = (int*)&d;  // type punning → UB

// GOOD — use named casts (compiler checks apply)
auto x = static_cast<int>(d);
```

---

## 27. Don't Cast Away const — ES.50

**severity:** Undefined behavior

If the variable is actually declared `const`, modifying it through a casted pointer is UB.

```cpp
// BAD
const int x = 42;
int* p = const_cast<int*>(&x);
*p = 0;  // UB: x is truly const
```

---

## 28. Avoid C-style Variadic Functions — ES.34

**severity:** Undefined behavior, crash

Not type safe. Wrong `va_arg` type causes UB.

```cpp
// BAD
int sum(int count, ...) {
    va_list ap;
    va_start(ap, count);
    int s = 0;
    for (int i = 0; i < count; ++i)
        s += va_arg(ap, int);  // UB if caller passes non-int
    va_end(ap);
    return s;
}

// GOOD — variadic template
template<class ...Args>
auto sum(Args... args) { return (... + args); }
```

---

## 29. Match new/delete Forms — ES.61

**severity:** Undefined behavior, heap corruption

Using `delete` on an array or `delete[]` on a non-array is UB.

```cpp
// BAD
auto p = new X[n];
delete p;    // UB: should be delete[] p

// GOOD
auto p = new X[n];
delete[] p;

// BEST — avoid manual memory management
auto v = vector<X>(n);
```

---

## 30. Don't Compare Pointers into Different Arrays — ES.62

**severity:** Undefined behavior

The result of comparing pointers to elements of different arrays is undefined.

```cpp
// BAD
int a1[7];
int a2[9];
if (&a1[5] < &a2[7]) {}       // UB
if (0 < &a1[5] - &a2[7]) {}   // UB
```

---

## 31. Never Return Pointer/Reference to a Local Object — F.43

**severity:** Use-after-free, crash, data corruption

The local object is destroyed when the function returns; any pointer or reference to it is dangling.

```cpp
// BAD — dangling pointer to stack frame
int* f()
{
    int fx = 9;
    return &fx;  // BAD: returns address of local
}

// BAD — dangling reference
int& g()
{
    int x = 7;
    return x;  // BAD: reference to object about to be destroyed
}

// BAD — dangling via lambda capture
int* glob;
void h()
{
    int i = 99;
    auto lam = [&] { return &i; };
    glob = lam();  // BAD: i destroyed when h returns
}
```

---

## 32. Don't memset/memcpy Non-Trivially-Copyable Types — C.90, SL.con.4

**severity:** Memory corruption, vtable corruption, undefined behavior

`memset` and `memcpy` overwrite the raw bytes of an object, destroying vptrs, internal pointers, and invariants maintained by constructors.

```cpp
// BAD — corrupts vtable
struct Base {
    virtual void update() = 0;
};
struct Derived : public Base {
    void update() override {}
};

void f(Derived& a, Derived& b)
{
    memset(&a, 0, sizeof(Derived));   // destroys vptr → crash on next virtual call
    memcpy(&a, &b, sizeof(Derived));  // copies raw bytes including vptr → UB
}

// GOOD — use constructors and assignment operators
void g(Derived& a, Derived& b)
{
    a = {};     // default initialize
    b = a;      // proper copy
}
```

---

## 33. Avoid Container/Array Bounds Errors — SL.con.3

**severity:** Out-of-bounds read/write, crash, security vulnerability

Read or write beyond an allocated range typically leads to bad errors, wrong results, crashes, and security violations.

```cpp
// BAD — length error, memset operates on bytes not elements
void f()
{
    array<int, 10> a, b;
    memset(a.data(), 0, 10);         // BAD: should be 10 * sizeof(int)
    memcmp(a.data(), b.data(), 10);  // BAD: same error
}

// GOOD — use type-aware operations
void f()
{
    array<int, 10> a{}, b{};   // zero-initialized
    a.fill(0);
    fill(b.begin(), b.end(), 0);
}

// GOOD — use bounds-checked access
void g(vector<int>& v, array<int, 12> a, int i)
{
    v.at(0) = a.at(i);  // throws std::out_of_range if out of bounds
}
```

---

## 34. Don't Pass an Array as a Single Pointer — I.13

**severity:** Out-of-bounds access, memory corruption

Array-to-pointer decay loses size information. The callee has no way to determine the number of elements, leading to buffer overruns.

```cpp
// BAD — array decays to pointer, size lost
void draw(Shape* p, int n);  // poor interface
Circle arr[10];
draw(arr, 10);  // easy to get n wrong

// GOOD — use span
void draw(span<Circle>);
Circle arr[10];
draw(arr);  // size deduced, bounds safe
```

---

## 35. Don't Pass Pointer/Reference from Aliased Smart Pointer — R.37

**severity:** Use-after-free, dangling pointer, crash

If the smart pointer is the last owner and gets reset during the call, the raw pointer/reference becomes dangling.

```cpp
// BAD — g_p might be reset inside f() or its callees
shared_ptr<widget> g_p = ...;

void f(widget& w)
{
    g();
    use(w);  // w may be dangling if g() reset g_p
}
void g() { g_p = ...; }  // might destroy the widget

void my_code()
{
    f(*g_p);      // BAD: raw reference from aliased shared_ptr
    g_p->func();  // BAD: same risk
}

// GOOD — pin the smart pointer locally
void my_code()
{
    auto pin = g_p;    // increment ref count
    f(*pin);           // safe: pin keeps object alive
    pin->func();       // safe
}
```

---

## 36. Never Throw While Being Direct Owner of a Resource — E.13

**severity:** Resource leak

If you throw while holding a raw owning pointer (not wrapped in RAII), the resource is never released.

```cpp
// BAD — leak on throw
void leak(int x)
{
    auto p = new int{7};
    if (x < 0) throw Get_me_out_of_here{};  // *p leaked
    delete p;
}

// GOOD — RAII wrapper
void no_leak(int x)
{
    auto p = make_unique<int>(7);
    if (x < 0) throw Get_me_out_of_here{};  // *p auto-deleted
}
```

---

## 37. Don't Use setjmp/longjmp — SL.C.1

**severity:** Resource leak, undefined behavior

`longjmp` bypasses stack unwinding — destructors are not called, RAII is defeated, and resources leak.

```cpp
// BAD — longjmp skips destructors
jmp_buf env;

void f()
{
    unique_ptr<int> p = make_unique<int>(42);
    longjmp(env, 1);  // destructor of p is NOT called → leak
}

void g()
{
    if (setjmp(env) == 0) {
        f();
    }
    // p was never cleaned up
}

// GOOD — use exceptions or error codes
void f()
{
    auto p = make_unique<int>(42);
    throw runtime_error("fail");  // p properly destroyed during stack unwinding
}
```

---

## 38. Don't Capture by Reference in Non-Local Lambdas — F.53

**severity:** Use-after-free, dangling reference, crash

A lambda that outlives the scope of its captured references will access destroyed objects.

```cpp
// BAD — lambda escapes, captures become dangling
string f(string& s)
{
    return accumulate(
        istream_iterator<string>(istringstream(s)),
        istream_iterator<string>(),
        s,  // intermediate result in s
        [&](const string& a, const string& b) { return a + b; }
    );  // s might be moved from → dangling
}

// BAD — lambda stored, captures become dangling
void setup(vector<function<void()>>& work)
{
    string msg = "hello";
    work.push_back([&msg] { cout << msg; });  // msg destroyed when setup returns
}

// GOOD — capture by value for non-local use
void setup(vector<function<void()>>& work)
{
    string msg = "hello";
    work.push_back([msg] { cout << msg; });  // copy, safe
}
```

---

## 39. Don't Dereference Invalidated Iterators/Pointers — ES.65

**severity:** Use-after-free, crash, undefined behavior

Container mutations (`push_back`, `insert`, `erase`, `resize`, `clear`, `reserve`) may reallocate internal storage, invalidating all iterators, pointers, and references to elements. Using them after mutation is UB.

```cpp
// BAD — push_back may reallocate, invalidating p
void f()
{
    vector<int> v(10);
    int* p = &v[5];
    v.push_back(99);  // reallocation possible → p is dangling
    int x = *p;       // UB: dereferences invalidated pointer
}

// BAD — erase invalidates iterator at and after the erased position
void remove_evens(vector<int>& v)
{
    for (auto it = v.begin(); it != v.end(); ++it) {
        if (*it % 2 == 0)
            v.erase(it);  // UB: it is invalidated, then ++it on next iteration
    }
}

// GOOD — use erase-remove idiom
void remove_evens(vector<int>& v)
{
    v.erase(remove_if(v.begin(), v.end(),
                       [](int x) { return x % 2 == 0; }),
            v.end());
}

// GOOD — re-obtain iterator after mutation
void remove_evens(vector<int>& v)
{
    for (auto it = v.begin(); it != v.end(); ) {
        if (*it % 2 == 0)
            it = v.erase(it);  // erase returns valid next iterator
        else
            ++it;
    }
}

// BAD — range-for while modifying container
void f(vector<int>& v)
{
    for (auto& x : v) {
        if (x == 0)
            v.push_back(42);  // UB: invalidates the range-for's hidden iterators
    }
}
```

---

## 40. Don't Read from a Moved-From Object — ES.56, C.64

**severity:** Undefined / unspecified value, logic errors, potential crash

After `std::move`, the source object is in a valid-but-unspecified state. Reading its value (other than to destroy or reassign) leads to unpredictable behavior.

```cpp
// BAD — use after move
void f()
{
    string s = "hello";
    vector<string> v;
    v.push_back(std::move(s));
    cout << s << endl;           // BAD: s is moved-from, value is unspecified
    cout << s.size() << endl;    // BAD: unspecified
}

// BAD — conditional move then use
void g(bool cond, string s)
{
    vector<string> v;
    if (cond) v.push_back(std::move(s));
    cout << s;  // BAD: s may or may not be moved-from depending on cond
}

// GOOD — don't read after move, or reassign first
void f()
{
    string s = "hello";
    vector<string> v;
    v.push_back(std::move(s));
    s = "world";          // OK: reassign to a known state
    cout << s << endl;    // OK: "world"
}

// GOOD — use the moved-to value
void f()
{
    string s = "hello";
    vector<string> v;
    v.push_back(std::move(s));
    cout << v.back() << endl;  // OK: use the moved-to value
}
```

---

## 41. Don't Let a string_view Outlive Its Source — ES.65 (lifetime)

**severity:** Dangling reference, use-after-free, crash

`string_view` (and `span`) are non-owning views. If the underlying string/buffer is destroyed or reallocated, the view becomes dangling.

```cpp
// BAD — view outlives temporary
string_view sv = "hello"s;  // temporary string destroyed at end of statement
cout << sv;                 // UB: dangling view

// BAD — return view to local
string_view bad()
{
    string s = "hello";
    return s;  // BAD: s destroyed, view dangles
}

// BAD — view invalidated by container mutation
string_view get_first(vector<string>& v)
{
    string_view sv = v[0];
    v.push_back("new");  // may reallocate → v[0] moves → sv dangles
    return sv;           // UB
}

// BAD — view into a string that gets modified
string s = "hello world";
string_view sv = s;
s += " and more";  // may reallocate → sv dangles
cout << sv;        // UB

// GOOD — ensure source outlives view
const string s = "hello";   // const, won't be modified
string_view sv = s;          // safe: s outlives sv
cout << sv;

// GOOD — return string, not view, when function creates the data
string good()
{
    string s = "hello";
    return s;  // return by value, caller owns it
}

// GOOD — take string_view as parameter (caller manages lifetime)
void process(string_view sv)
{
    cout << sv;  // OK: caller guarantees sv is valid during call
}
```

---
