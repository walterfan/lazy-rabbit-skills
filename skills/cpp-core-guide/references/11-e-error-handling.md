# E: Error handling

## Table of Contents

- [E.1] Develop an error-handling strategy early in a design
- [E.2] Throw an exception to signal that a function can't perform its assigned task
- [E.3] Use exceptions for error handling only
- [E.4] Design your error-handling strategy around invariants
- [E.5] Let a constructor establish an invariant, and throw if it cannot
- [E.6] Use RAII to prevent leaks
- [E.7] State your preconditions
- [E.8] State your postconditions
- [E.12] Use `noexcept` when exiting a function because of a `throw` is impossible or unacceptable
- [E.13] Never throw while being the direct owner of an object
- [E.14] Use purpose-designed user-defined types as exceptions
- [E.15] Throw by value, catch exceptions from a hierarchy by reference
- [E.16] Destructors, deallocation, `swap`, and exception type copy/move must never fail
- [E.17] Don't try to catch every exception in every function
- [E.18] Minimize the use of explicit `try`/`catch`
- [E.19] Use a `final_action` object for cleanup if no suitable resource handle is available
- [E.25] If you can't throw exceptions, simulate RAII for resource management
- [E.26] If you can't throw exceptions, consider failing fast
- [E.27] If you can't throw exceptions, use error codes systematically
- [E.28] Avoid error handling based on global state (e.g. `errno`)
- [E.30] Don't use exception specifications
- [E.31] Properly order your `catch`-clauses

---

### [E.1] Develop an error-handling strategy early in a design

**reason**
A consistent and complete strategy for handling errors and resource leaks is hard to retrofit into a system.

**enforcement**
- No specific enforcement.

---

### [E.2] Throw an exception to signal that a function can't perform its assigned task

**reason**
To make error handling systematic, robust, and non-repetitive.

**code sample**
```cpp
struct Foo {
    vector<Thing> v;
    File_handle f;
    string s;
};

void use()
{
    Foo bar { {Thing{1}, Thing{2}, Thing{monkey} }, {"my_file", "r"}, "Here we go!"};
    // ...
}
```
Here, `vector` and `string`s constructors might not be able to allocate sufficient memory, and `File_handle` might not be able to open the required file. In each case, they throw an exception for `use()`'s caller to handle.

**code example [bad]**
```cpp
File_handle::File_handle(const string& name, const string& mode)
    : f{fopen(name.c_str(), mode.c_str())}
{
    if (!f)
        throw runtime_error{"File_handle: could not open " + name + " as " + mode};
}
```

**enforcement**
- No specific enforcement.

---

### [E.3] Use exceptions for error handling only

**reason**
To keep error handling separated from "ordinary code." C++ implementations tend to be optimized based on the assumption that exceptions are rare.

**code example [bad]**
```cpp
// don't: exception not used for error handling
int find_index(vector<string>& vec, const string& x)
{
    try {
        for (gsl::index i = 0; i < vec.size(); ++i)
            if (vec[i] == x) throw i;  // found x
    }
    catch (int i) {
        return i;
    }
    return -1;   // not found
}
```
This is more complicated and most likely runs much slower than the obvious alternative. There is nothing exceptional about finding a value in a `vector`.

**enforcement**
- Would need to be heuristic. Look for exception values "leaked" out of `catch` clauses.

---

### [E.4] Design your error-handling strategy around invariants

**reason**
To use an object it must be in a valid state (defined by an invariant) and to recover from an error every object not destroyed must be in a valid state.

**enforcement**
- No specific enforcement.

---

### [E.5] Let a constructor establish an invariant, and throw if it cannot

**reason**
Leaving an object without its invariant established is asking for trouble. Not all member functions can be called.

**code sample**
```cpp
class Vector {  // very simplified vector of doubles
    // if elem != nullptr then elem points to sz doubles
public:
    Vector() : elem{nullptr}, sz{0}{}
    Vector(int s) : elem{new double[s]}, sz{s} { /* initialize elements */ }
    ~Vector() { delete [] elem; }
    double& operator[](int s) { return elem[s]; }
    // ...
private:
    owner<double*> elem;
    int sz;
};
```
The class invariant is established by the constructors. `new` throws if it cannot allocate the required memory.

**enforcement**
- Flag classes with `private` state without a constructor.

---

### [E.6] Use RAII to prevent leaks

**reason**
Leaks are typically unacceptable. Manual resource release is error-prone. RAII is the simplest, most systematic way of preventing leaks.

**code example [bad]**
```cpp
void f1(int i)   // Bad: possible leak
{
    int* p = new int[12];
    // ...
    if (i < 17) throw Bad{"in f()", i};
    // ...
}
```

**code example [bad]**
```cpp
void f2(int i)   // Clumsy and error-prone: explicit release
{
    int* p = new int[12];
    // ...
    if (i < 17) {
        delete[] p;
        throw Bad{"in f()", i};
    }
    // ...
}
```

**code example [good]**
```cpp
void f3(int i)   // OK: resource management done by a handle
{
    auto p = make_unique<int[]>(12);
    // ...
    if (i < 17) throw Bad{"in f()", i};
    // ...
}
```

**code example [good]**
```cpp
void f4(int i)   // OK: works even when throw is implicit
{
    auto p = make_unique<int[]>(12);
    // ...
    helper(i);   // might throw
    // ...
}

void f5(int i)   // OK: resource management done by local object
{
    vector<int> v(12);
    // ...
    helper(i);   // might throw
    // ...
}
```

**code example [good]**
```cpp
// When exceptions cannot be used, simulate RAII with valid()
void f()
{
    vector<string> vs(100);   // not std::vector: valid() added
    if (!vs.valid()) {
        // handle error or exit
    }

    ifstream fs("foo");   // not std::ifstream: valid() added
    if (!fs.valid()) {
        // handle error or exit
    }

    // ...
} // destructors clean up as usual
```

**enforcement**
- No specific enforcement.

---

### [E.7] State your preconditions

**reason**
To avoid interface errors.

**enforcement**
- See I.5 / I.6.

---

### [E.8] State your postconditions

**reason**
To avoid interface errors.

**enforcement**
- See I.7 / I.8.

---

### [E.12] Use `noexcept` when exiting a function because of a `throw` is impossible or unacceptable

**reason**
To make error handling systematic, robust, and efficient.

**code example [bad]**
```cpp
double compute(double d) noexcept
{
    return log(sqrt(d <= 0 ? 1 : d));
}
```
Here, we know that `compute` will not throw because it is composed out of operations that don't throw.

**code example [bad]**
```cpp
vector<double> munge(const vector<double>& v) noexcept
{
    vector<double> v2(v.size());
    // ... do something ...
}
```
The `noexcept` states: "I am not willing or able to handle the situation where I cannot construct the local `vector`."

**enforcement**
- No specific enforcement.

---

### [E.13] Never throw while being the direct owner of an object

**reason**
That would be a leak.

**code example [bad]**
```cpp
void leak(int x)   // don't: might leak
{
    auto p = new int{7};
    if (x < 0) throw Get_me_out_of_here{};  // might leak *p
    // ...
    delete p;   // we might never get here
}
```

**code example [good]**
```cpp
void no_leak(int x)
{
    auto p = make_unique<int>(7);
    if (x < 0) throw Get_me_out_of_here{};  // will delete *p if necessary
    // ...
    // no need for delete p
}
```

**code example [bad]**
```cpp
void no_leak_simplified(int x)
{
    vector<int> v(7);
    // ...
}
```

**enforcement**
- No specific enforcement.

---

### [E.14] Use purpose-designed user-defined types as exceptions (not built-in types)

**reason**
A user-defined type can better transmit information about an error to a handler. The type is unlikely to clash with other people's exceptions.

**code example [bad]**
```cpp
throw 7; // bad

throw "something bad";  // bad

throw std::exception{}; // bad - no info
```

**code example [good]**
```cpp
class MyException : public std::runtime_error
{
public:
    MyException(const string& msg) : std::runtime_error{msg} {}
    // ...
};

// ...
throw MyException{"something bad"};  // good
```

**code example [good]**
```cpp
class MyCustomError final {};  // not derived from std::exception
// ...
throw MyCustomError{};  // good - handlers must catch this type (or ...)
```

**code example [good]**
```cpp
throw std::runtime_error("something bad"); // good

throw std::invalid_argument("i is not even"); // good
```

**code example [good]**
```cpp
enum class alert {RED, YELLOW, GREEN};
throw alert::RED; // good
```

**enforcement**
- Catch `throw` of built-in types and `std::exception`.

---

### [E.15] Throw by value, catch exceptions from a hierarchy by reference

**reason**
Throwing by value (not by pointer) and catching by reference prevents copying, especially slicing base subobjects.

**code example [bad]**
```cpp
void f()
{
    try {
        // ...
        throw new widget{}; // don't: throw by value, not by raw pointer
        // ...
    }
    catch (base_class e) {  // don't: might slice
        // ...
    }
}
```

**code example [good]**
```cpp
catch (base_class& e) { /* ... */ }

// or typically better still - a const reference:
catch (const base_class& e) { /* ... */ }
```

To rethrow a caught exception use `throw;` not `throw e;`.

**enforcement**
- Flag catching by value of a type that has a virtual function.
- Flag throwing raw pointers.

---

### [E.16] Destructors, deallocation, `swap`, and exception type copy/move construction must never fail

**reason**
We don't know how to write reliable programs if a destructor, a swap, a memory deallocation, or attempting to copy/move-construct an exception object fails.

**code example [bad]**
```cpp
class Connection {
    // ...
public:
    ~Connection()   // Don't: very bad destructor
    {
        if (cannot_disconnect()) throw I_give_up{information};
        // ...
    }
};
```

**enforcement**
- Catch destructors, deallocation operations, and `swap`s that `throw`.
- Catch such operations that are not `noexcept`.

---

### [E.17] Don't try to catch every exception in every function

**reason**
Catching an exception in a function that cannot take a meaningful recovery action leads to complexity and waste. Let an exception propagate until it reaches a function that can handle it. Let cleanup actions on the unwinding path be handled by RAII.

**code example [bad]**
```cpp
void f()   // bad
{
    try {
        // ...
    }
    catch (...) {
        // no action
        throw;   // propagate exception
    }
}
```

**enforcement**
- Flag nested try-blocks.
- Flag source code files with a too high ratio of try-blocks to functions.

---

### [E.18] Minimize the use of explicit `try`/`catch`

**reason**
`try`/`catch` is verbose and non-trivial uses are error-prone. `try`/`catch` can be a sign of unsystematic and/or low-level resource management or error handling.

**code example [bad]**
```cpp
void f(zstring s)
{
    Gadget* p;
    try {
        p = new Gadget(s);
        // ...
        delete p;
    }
    catch (Gadget_construction_failure) {
        delete p;
        throw;
    }
}
```

**code example [good]**
```cpp
void f2(zstring s)
{
    Gadget g {s};
}
```

**enforcement**
- Hard, needs a heuristic.

---

### [E.19] Use a `final_action` object to express cleanup if no suitable resource handle is available

**reason**
`finally` from the GSL is less verbose and harder to get wrong than `try`/`catch`.

**code sample**
```cpp
void f(int n)
{
    void* p = malloc(n);
    auto _ = gsl::finally([p] { free(p); });
    // ...
}
```

**enforcement**
- Heuristic: Detect `goto exit;`.

---

### [E.25] If you can't throw exceptions, simulate RAII for resource management

**reason**
Even without exceptions, RAII is usually the best and most systematic way of dealing with resources.

**code example [good]**
```cpp
error_indicator func(zstring arg)
{
    Gadget g {arg};
    if (!g.valid()) return gadget_construction_error;
    // ...
    return 0;   // zero indicates "good"
}
```
The caller must remember to test the return value. Consider adding `[[nodiscard]]`.

**enforcement**
- Possible for specific versions: e.g., test for systematic test of `valid()` after resource handle construction.

---

### [E.26] If you can't throw exceptions, consider failing fast

**reason**
If you can't do a good job at recovering, at least you can get out before too much consequential damage is done.

**code example [good]**
```cpp
void f(int n)
{
    // ...
    p = static_cast<X*>(malloc(n * sizeof(X)));
    if (!p) abort();     // abort if memory is exhausted
    // ...
}

// roughly equivalent to:
void f(int n)
{
    // ...
    p = new X[n];    // throw if memory is exhausted (by default, terminate)
    // ...
}
```

**enforcement**
- Awkward.

---

### [E.27] If you can't throw exceptions, use error codes systematically

**reason**
Systematic use of any error-handling strategy minimizes the chance of forgetting to handle an error.

**code sample**
```cpp
Gadget make_gadget(int n)
{
    // ...
}

void user()
{
    Gadget g = make_gadget(17);
    if (!g.valid()) {
            // error handling
    }
    // ...
}
```

**code example [good]**
```cpp
std::pair<Gadget, error_indicator> make_gadget(int n)
{
    // ...
}

void user()
{
    auto r = make_gadget(17);
    if (!r.second) {
            // error handling
    }
    Gadget& g = r.first;
    // ...
}
```

**code example [good]**
```cpp
// Cleanup can be messy without RAII:
std::pair<int, error_indicator> user()
{
    Gadget g1 = make_gadget(17);
    if (!g1.valid()) {
        return {0, g1_error};
    }

    Gadget g2 = make_gadget(31);
    if (!g2.valid()) {
        cleanup(g1);
        return {0, g2_error};
    }

    // ...

    if (all_foobar(g1, g2)) {
        cleanup(g2);
        cleanup(g1);
        return {0, foobar_error};
    }

    // ...
    cleanup(g2);
    cleanup(g1);
    return {res, 0};
}
```

**enforcement**
- Awkward.

---

### [E.28] Avoid error handling based on global state (e.g. `errno`)

**reason**
Global state is hard to manage and it is easy to forget to check it.

**code example [bad]**
```cpp
int last_err;

void f(int n)
{
    // ...
    p = static_cast<X*>(malloc(n * sizeof(X)));
    if (!p) last_err = -1;     // error if memory is exhausted
    // ...
}
```

**enforcement**
- Awkward.

---

### [E.30] Don't use exception specifications

**reason**
Exception specifications make error handling brittle, impose a run-time cost, and have been removed from the C++ standard.

**code sample**
```cpp
int use(int arg)
    throw(X, Y)
{
    // ...
    auto x = f(arg);
    // ...
}
```
If `f()` throws an exception different from `X` and `Y` the unexpected handler is invoked, which by default terminates.

**enforcement**
- Flag every exception specification.

---

### [E.31] Properly order your `catch`-clauses

**reason**
`catch`-clauses are evaluated in the order they appear and one clause can hide another.

**code example [bad]**
```cpp
void f()
{
    // ...
    try {
            // ...
    }
    catch (Base& b) { /* ... */ }
    catch (Derived& d) { /* ... */ }
    catch (...) { /* ... */ }
    catch (std::exception& e) { /* ... */ }
}
```
If `Derived` is derived from `Base`, the `Derived`-handler will never be invoked. The "catch everything" handler ensures the `std::exception`-handler will never be invoked.

**enforcement**
- Flag all "hiding handlers".

---
