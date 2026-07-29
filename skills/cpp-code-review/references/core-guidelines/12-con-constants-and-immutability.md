# Con: Constants and immutability

## Table of Contents

- [Con.1] By default, make objects immutable
- [Con.2] By default, make member functions `const`
- [Con.3] By default, pass pointers and references to `const`s
- [Con.4] Use `const` to define objects with values that do not change after construction
- [Con.5] Use `constexpr` for values that can be computed at compile time

---

### [Con.1] By default, make objects immutable

**reason**
Immutable objects are easier to reason about, so make objects non-`const` only when there is a need to change their value. Prevents accidental or hard-to-notice change of value.

**code example [bad]**
```cpp
for (const int i : c) cout << i << '\n';    // just reading: const

for (int i : c) cout << i << '\n';          // BAD: just reading
```

**code example [bad]**
```cpp
// Exception: A local variable that is returned by value and is cheaper to move
// than copy should not be declared const because it can force an unnecessary copy.
std::vector<int> f(int i)
{
    std::vector<int> v{ i, i, i };  // const not needed
    return v;
}
```

**code sample**
```cpp
void g(const int i) { ... }  // pedantic
// Function parameters passed by value are rarely mutated, but also rarely declared const.
```

**enforcement**
- Flag non-`const` variables that are not modified (except for parameters to avoid many false positives and returned local variables)

---

### [Con.2] By default, make member functions `const`

**reason**
A member function should be marked `const` unless it changes the object's observable state. This gives a more precise statement of design intent, better readability, more errors caught by the compiler, and sometimes more optimization opportunities.

**code example [bad]**
```cpp
class Point {
    int x, y;
public:
    int getx() { return x; }    // BAD, should be const as it doesn't modify the object's state
    // ...
};

void f(const Point& pt)
{
    int x = pt.getx();          // ERROR, doesn't compile because getx was not marked const
}
```

**code sample**
```cpp
// A const member function can modify the value of an object that is mutable
class Date {
public:
    // ...
    const string& string_ref() const
    {
        if (string_val == "") compute_string_rep();
        return string_val;
    }
    // ...
private:
    void compute_string_rep() const;    // compute string representation and place it in string_val
    mutable string string_val;
    // ...
};
```

**enforcement**
- Flag a member function that is not marked `const`, but that does not perform a non-`const` operation on any data member.

---

### [Con.3] By default, pass pointers and references to `const`s

**reason**
To avoid a called function unexpectedly changing the value. It's far easier to reason about programs when called functions don't modify state.

**code example [bad]**
```cpp
void f(char* p);        // does f modify *p? (assume it does)
void g(const char* p);  // g does not modify *p
```

**enforcement**
- Flag a function that does not modify an object passed by pointer or reference to non-`const`
- Flag a function that (using a cast) modifies an object passed by pointer or reference to `const`

---

### [Con.4] Use `const` to define objects with values that do not change after construction

**reason**
Prevent surprises from unexpectedly changed object values.

**code sample**
```cpp
void f()
{
    int x = 7;
    const int y = 9;

    for (;;) {
        // ...
    }
    // ...
}
// As x is not const, we must assume that it is modified somewhere in the loop.
```

**enforcement**
- Flag unmodified non-`const` variables.

---

### [Con.5] Use `constexpr` for values that can be computed at compile time

**reason**
Better performance, better compile-time checking, guaranteed compile-time evaluation, no possibility of race conditions.

**code example [good]**
```cpp
double x = f(2);            // possible run-time evaluation
const double y = f(2);      // possible run-time evaluation
constexpr double z = f(2);  // error unless f(2) can be evaluated at compile time
```

**enforcement**
- Flag `const` definitions with constant expression initializers.

---
