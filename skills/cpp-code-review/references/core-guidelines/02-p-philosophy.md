# P: Philosophy

## Table of Contents

- [P.1] Express ideas directly in code
- [P.2] Write in ISO Standard C++
- [P.3] Express intent
- [P.4] Ideally, a program should be statically type safe
- [P.5] Prefer compile-time checking to run-time checking
- [P.6] What cannot be checked at compile time should be checkable at run time
- [P.7] Catch run-time errors early
- [P.8] Don't leak any resources
- [P.9] Don't waste time or space
- [P.10] Prefer immutable data to mutable data
- [P.11] Encapsulate messy constructs, rather than spreading through the code
- [P.12] Use supporting tools as appropriate
- [P.13] Use support libraries as appropriate

---

### [P.1] Express ideas directly in code

**reason**
Compilers don't read comments (or design documents) and neither do many programmers consistently. What is expressed in code has defined semantics and can be checked by compilers and other tools.

**code example [bad]**
```cpp
class Date {
public:
    Month month() const;  // do
    int month();          // don't
};
```
The first declaration of `month` is explicit about returning a `Month` and about not modifying the state of the `Date` object.

**code example [bad]**
```cpp
void f(vector<string>& v)
{
    string val;
    cin >> val;
    int index = -1;                    // bad, plus should use gsl::index
    for (int i = 0; i < v.size(); ++i) {
        if (v[i] == val) {
            index = i;
            break;
        }
    }
}
```

**code example [good]**
```cpp
void f(vector<string>& v)
{
    string val;
    cin >> val;
    auto p = find(begin(v), end(v), val);  // better
}
```

**enforcement**
- Use `const` consistently (check if member functions modify their object; check if functions modify arguments passed by pointer or reference)
- Flag uses of casts (casts neuter the type system)
- Detect code that mimics the standard library (hard)

---

### [P.2] Write in ISO Standard C++

**reason**
This is a set of guidelines for writing ISO Standard C++. Extensions often do not have rigorously defined semantics and may impact portability.

**code example [bad]**
```cpp
// Using non-standard extensions or relying on undefined behavior
// e.g. implementation-defined meaning of sizeof(int)
```

**code example [good]**
```cpp
// Use standard C++ features, avoid dependence on undefined behavior
// Use an up-to-date C++ compiler (C++20 or C++17) with options that reject extensions
```

**enforcement**
- Use an up-to-date C++ compiler (currently C++20 or C++17) with a set of options that do not accept extensions

---

### [P.3] Express intent

**reason**
Unless the intent of some code is stated (e.g., in names or comments), it is impossible to tell whether the code does what it is supposed to do.

**code example [bad]**
```cpp
gsl::index i = 0;
while (i < v.size()) {
    // ... do something with v[i] ...
}
```

**code example [good]**
```cpp
for (const auto& x : v) { /* do something with the value of x */ }
```

**enforcement**
- Simple `for` loops vs. range-`for` loops
- `f(T*, int)` interfaces vs. `f(span<T>)` interfaces
- Loop variables in too large a scope
- Naked `new` and `delete`
- Functions with many parameters of built-in types

---

### [P.4] Ideally, a program should be statically type safe

**reason**
Ideally, a program would be completely statically (compile-time) type safe. Unfortunately, that is not possible. Problem areas: unions, casts, array decay, range errors, narrowing conversions.

**code example [bad]**
```cpp
// Using union, C-style casts, array decay, etc. that break type safety
```

**code example [good]**
```cpp
// unions â†’ use variant (C++17)
// casts â†’ minimize their use; templates can help
// array decay â†’ use span (GSL)
// range errors â†’ use span
// narrowing conversions â†’ minimize use, use narrow or narrow_cast (GSL)
```

**enforcement**
- Ban, restrain, or detect each problem category separately as required
- Always suggest an alternative

---

### [P.5] Prefer compile-time checking to run-time checking

**reason**
Code clarity and performance. You don't need to write error handlers for errors caught at compile time.

**code example [bad]**
```cpp
int bits = 0;
for (Int i = 1; i; i <<= 1)
    ++bits;
if (bits < 32)
    cerr << "Int too small\n";
```

**code example [good]**
```cpp
static_assert(sizeof(Int) >= 4);    // do: compile-time check
```

**enforcement**
- Look for pointer arguments
- Look for run-time checks for range violations

---

### [P.6] What cannot be checked at compile time should be checkable at run time

**reason**
Leaving hard-to-detect errors in a program is asking for crashes and bad results.

**code example [bad]**
```cpp
extern void f(int* p);

void g(int n)
{
    f(new int[n]);  // bad: the number of elements is not passed to f()
}
```

**code example [good]**
```cpp
extern void f4(vector<int>&);
extern void f4(span<int>);

void g3(int n)
{
    vector<int> v(n);
    f4(v);                     // pass a reference, retain ownership
    f4(span<int>{v});          // pass a view, retain ownership
}
```

**enforcement**
- Flag (pointer, count)-style interfaces

---

### [P.7] Catch run-time errors early

**reason**
Avoid "mysterious" crashes. Avoid errors leading to (possibly unrecognized) wrong results.

**code example [bad]**
```cpp
void increment1(int* p, int n)    // bad: error-prone
{
    for (int i = 0; i < n; ++i) ++p[i];
}

void use1(int m)
{
    const int n = 10;
    int a[n] = {};
    increment1(a, m);   // maybe typo, maybe m <= n is supposed
}
```

**code example [good]**
```cpp
void increment2(span<int> p)
{
    for (int& x : p) ++x;
}

void use3(int m)
{
    const int n = 10;
    int a[n] = {};
    increment2(a);   // the number of elements of a need not be repeated
}
```

**enforcement**
- Look at pointers and arrays: do range-checking early and not repeatedly
- Look at conversions: eliminate or mark narrowing conversions
- Look for unchecked values coming from input
- Look for structured data (objects of classes with invariants) being converted into strings

---

### [P.8] Don't leak any resources

**reason**
Even a slow growth in resources will, over time, exhaust the availability of those resources. This is particularly important for long-running programs.

**code example [bad]**
```cpp
void f(const char* name)
{
    FILE* input = fopen(name, "r");
    // ...
    if (something) return;   // bad: if something == true, a file handle is leaked
    // ...
    fclose(input);
}
```

**code example [good]**
```cpp
void f(const char* name)
{
    ifstream input {name};
    // ...
    if (something) return;   // OK: no leak
    // ...
}
```

**enforcement**
- Look at pointers: classify them into non-owners (the default) and owners
- Look for naked `new` and `delete`
- Look for known resource allocating functions returning raw pointers (such as `fopen`, `malloc`, and `strdup`)

---

### [P.9] Don't waste time or space

**reason**
This is C++. Time and space spent well to achieve a goal is not wasted.

**code example [bad]**
```cpp
struct X {
    char ch;
    int i;
    string s;
    char ch2;

    X& operator=(const X& a);
    X(const X&);
};

X waste(const char* p)
{
    if (!p) throw Nullptr_error{};
    int n = strlen(p);
    auto buf = new char[n];
    if (!buf) throw Allocation_error{};
    for (int i = 0; i < n; ++i) buf[i] = p[i];
    X x;
    x.ch = 'a';
    x.s = string(n);
    for (gsl::index i = 0; i < x.s.size(); ++i) x.s[i] = buf[i];
    delete[] buf;
    return x;
}
```

**code example [good]**
```cpp
// Use proper layout (avoid padding waste)
// Don't define redundant copy operations (let move semantics work)
// Use string instead of manual new/delete
// Leverage RVO
```

**enforcement**
- Flag an unused return value from a user-defined non-defaulted postfix `operator++` or `operator--`. Prefer using the prefix form instead.

---

### [P.10] Prefer immutable data to mutable data

**reason**
It is easier to reason about constants than about variables. Something immutable cannot change unexpectedly. Sometimes immutability enables better optimization. You can't have a data race on a constant.

**enforcement**
See Con: Constants and immutability section.

---

### [P.11] Encapsulate messy constructs, rather than spreading through the code

**reason**
Messy code is more likely to hide bugs and harder to write. A good interface is easier and safer to use.

**code example [bad]**
```cpp
int sz = 100;
int* p = (int*) malloc(sizeof(int) * sz);
int count = 0;
for (;;) {
    // ... read an int into x, exit loop if end of file is reached ...
    if (count == sz)
        p = (int*) realloc(p, sizeof(int) * sz * 2);
    p[count++] = x;
}
```

**code example [good]**
```cpp
vector<int> v;
v.reserve(100);
for (int x; cin >> x; ) {
    // ... check that x is valid ...
    v.push_back(x);
}
```

**enforcement**
- Look for "messy code" such as complex pointer manipulation and casting outside the implementation of abstractions

---

### [P.12] Use supporting tools as appropriate

**reason**
There are many things that are done better "by machine." Computers don't tire or get bored by repetitive tasks.

**enforcement**
- Run a static analyzer to verify that your code follows the guidelines you want it to follow

---

### [P.13] Use support libraries as appropriate

**reason**
Using a well-designed, well-documented, and well-supported library saves time and effort. A widely used library is more likely to be kept up-to-date and ported to new systems.

**code example [good]**
```cpp
std::sort(begin(v), end(v), std::greater<>());
```

**enforcement**
No specific enforcement. By default use the ISO C++ Standard Library and the Guidelines Support Library.

---
