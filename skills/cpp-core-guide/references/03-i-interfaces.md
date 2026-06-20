# I: Interfaces

## Table of Contents

- [I.1] Make interfaces explicit
- [I.2] Avoid non-`const` global variables
- [I.3] Avoid singletons
- [I.4] Make interfaces precisely and strongly typed
- [I.5] State preconditions (if any)
- [I.6] Prefer `Expects()` for expressing preconditions
- [I.7] State postconditions
- [I.8] Prefer `Ensures()` for expressing postconditions
- [I.9] If an interface is a template, document its parameters using concepts
- [I.10] Use exceptions to signal a failure to perform a required task
- [I.11] Never transfer ownership by a raw pointer (`T*`) or reference (`T&`)
- [I.12] Declare a pointer that must not be null as `not_null`
- [I.13] Do not pass an array as a single pointer
- [I.22] Avoid complex initialization of global objects
- [I.23] Keep the number of function arguments low
- [I.24] Avoid adjacent parameters invoked by same arguments in either order with different meaning
- [I.25] Prefer empty abstract classes as interfaces to class hierarchies
- [I.26] If you want a cross-compiler ABI, use a C-style subset
- [I.27] For stable library ABI, consider the Pimpl idiom
- [I.30] Encapsulate rule violations

---

### [I.1] Make interfaces explicit

**reason**
Correctness. Assumptions not stated in an interface are easily overlooked and hard to test.

**code example [bad]**
```cpp
int round(double d)
{
    return (round_up) ? ceil(d) : d;    // don't: "invisible" dependency
}
```

**code example [good]**
```cpp
// Pass the mode as an explicit parameter instead of relying on a global variable
int round(double d, bool round_up);
```

**enforcement**
- (Simple) A function should not make control-flow decisions based on the values of variables declared at namespace scope
- (Simple) A function should not write to variables declared at namespace scope

---

### [I.2] Avoid non-`const` global variables

**reason**
Non-`const` global variables hide dependencies and make the dependencies subject to unpredictable changes.

**code example [bad]**
```cpp
struct Data {
    // ... lots of stuff ...
} data;            // non-const data

void compute()     // don't
{
    // ... use data ...
}

void output()     // don't
{
    // ... use data ...
}
```

**code example [good]**
```cpp
// Pass data as an object by reference to const,
// or define the data as the state of some object and the operations as member functions
void compute(const Data& d);
void output(const Data& d);
```

**enforcement**
- (Simple) Report all non-`const` variables declared at namespace scope and global pointers/references to non-const data

---

### [I.3] Avoid singletons

**reason**
Singletons are basically complicated global objects in disguise.

**code example [bad]**
```cpp
class Singleton {
    // ... lots of stuff to ensure that only one Singleton object is created,
    // that it is initialized properly, etc.
};
```

**code example [good]**
```cpp
X& myX()
{
    static X my_x {3};
    return my_x;
}
// Simplest form — initialization on first use, thread-safe in C++11+
```

**enforcement**
- Look for classes with names that include `singleton`
- Look for classes for which only a single object is created (by counting objects or by examining constructors)

---

### [I.4] Make interfaces precisely and strongly typed

**reason**
Types are the simplest and best documentation, improve legibility due to their well-defined meaning, and are checked at compile time.

**code example [bad]**
```cpp
void pass(void* data);    // weak and under-qualified type void* is suspicious

draw_rect(100, 200, 100, 500); // what do the numbers specify?

set_settings(true, false, 42); // what do the numbers specify?

void blink_led(int time_to_blink) // bad -- the unit is ambiguous
{
    // ...
    // do something with time_to_blink
    // ...
}

void use()
{
    blink_led(2);
}
```

**code example [good]**
```cpp
void draw_rectangle(Point top_left, Point bottom_right);
void draw_rectangle(Point top_left, Size height_width);

draw_rectangle(p, Point{10, 20});  // two corners
draw_rectangle(p, Size{10, 20});   // one corner and a (height, width) pair

alarm_settings s{};
s.enabled = true;
s.displayMode = alarm_settings::mode::spinning_light;
s.frequency = alarm_settings::every_10_seconds;
set_settings(s);

void blink_led(milliseconds time_to_blink) // good -- the unit is explicit
{
    // ...
    // do something with time_to_blink
    // ...
}

void use()
{
    blink_led(1500ms);
}

template<class rep, class period>
void blink_led(duration<rep, period> time_to_blink) // good -- accepts any unit
{
    auto milliseconds_to_blink = duration_cast<milliseconds>(time_to_blink);
    // ...
    // do something with milliseconds_to_blink
    // ...
}

void use()
{
    blink_led(2s);
    blink_led(1500ms);
}
```

**enforcement**
- (Simple) Report the use of `void*` as a parameter or return type
- (Simple) Report the use of more than one `bool` parameter
- (Hard to do well) Look for functions that use too many primitive type arguments

---

### [I.5] State preconditions (if any)

**reason**
Arguments have meaning that might constrain their proper use in the callee.

**code example [bad]**
```cpp
double sqrt(double x);  // x must be non-negative, but nothing states that
```

**code example [good]**
```cpp
double sqrt(double x) { Expects(x >= 0); /* ... */ }
```

**enforcement**
- (Not enforceable) Finding the variety of ways preconditions can be asserted is not feasible

---

### [I.6] Prefer `Expects()` for expressing preconditions

**reason**
To make it clear that the condition is a precondition and to enable tool use.

**code example [bad]**
```cpp
int area(int height, int width)
{
    if (height <= 0 || width <= 0) my_error();   // obscure
    // ...
}
```

**code example [good]**
```cpp
int area(int height, int width)
{
    Expects(height > 0 && width > 0);            // good
    // ...
}
```

**enforcement**
- (Not enforceable) Finding the variety of ways preconditions can be asserted is not feasible

---

### [I.7] State postconditions

**reason**
To detect misunderstandings about the result and possibly catch erroneous implementations.

**code example [bad]**
```cpp
int area(int height, int width) { return height * width; }  // bad: no postcondition
```

**code example [good]**
```cpp
int area(int height, int width)
{
    auto res = height * width;
    Ensures(res > 0);
    return res;
}
```

**enforcement**
- (Not enforceable) This is a philosophical guideline that is infeasible to check directly in the general case

---

### [I.8] Prefer `Ensures()` for expressing postconditions

**reason**
To make it clear that the condition is a postcondition and to enable tool use.

**code example [bad]**
```cpp
void f()
{
    char buffer[MAX];
    // ...
    memset(buffer, 0, MAX);
    // postcondition not stated — optimizer may eliminate the memset
}
```

**code example [good]**
```cpp
void f()
{
    char buffer[MAX];
    // ...
    memset(buffer, 0, MAX);
    Ensures(buffer[0] == 0);
}
```

**enforcement**
- (Not enforceable) Finding the variety of ways postconditions can be asserted is not feasible

---

### [I.9] If an interface is a template, document its parameters using concepts

**reason**
Make the interface precisely specified and compile-time checkable.

**code example [bad]**
```cpp
template<typename Iter, typename Val>
Iter find(Iter first, Iter last, Val v);  // unconstrained
```

**code example [good]**
```cpp
template<typename Iter, typename Val>
  requires input_iterator<Iter> && equality_comparable_with<iter_value_t<Iter>, Val>
Iter find(Iter first, Iter last, Val v);
```

**enforcement**
- Warn if any non-variadic template parameter is not constrained by a concept

---

### [I.10] Use exceptions to signal a failure to perform a required task

**reason**
It should not be possible to ignore an error because that could leave the system or a computation in an undefined (or unexpected) state.

**code example [bad]**
```cpp
int printf(const char* ...);    // bad: return negative number if output fails
```

**code example [good]**
```cpp
template<class F, class ...Args>
explicit thread(F&& f, Args&&... args);  // good: throw system_error if unable to start
```

**code sample**
If you can't use exceptions, consider using a style that returns a pair of values:

```cpp
int val;
int error_code;
tie(val, error_code) = do_something();
if (error_code) {
    // ... handle the error or exit ...
}
// ... use val ...
```

Since C++17 the "structured bindings" feature can be used:

```cpp
auto [val, error_code] = do_something();
if (error_code) {
    // ... handle the error or exit ...
}
// ... use val ...
```

**enforcement**
- (Not enforceable) This is a philosophical guideline
- Look for `errno`

---

### [I.11] Never transfer ownership by a raw pointer (`T*`) or reference (`T&`)

**reason**
If there is any doubt whether the caller or the callee owns an object, leaks or premature destruction will occur.

**code example [bad]**
```cpp
X* compute(args)    // don't
{
    X* res = new X{};
    // ...
    return res;
}
```

**code example [good]**
```cpp
vector<double> compute(args)  // good
{
    vector<double> res(10000);
    // ...
    return res;
}
```

**enforcement**
- (Simple) Warn on `delete` of a raw pointer that is not an `owner<T>`
- (Simple) Warn on failure to either `reset` or explicitly `delete` an `owner` pointer on every code path
- (Simple) Warn if the return value of `new` is assigned to a raw pointer or non-`owner` reference

---

### [I.12] Declare a pointer that must not be null as `not_null`

**reason**
To help avoid dereferencing `nullptr` errors. To improve performance by avoiding redundant checks for `nullptr`.

**code example [bad]**
```cpp
int length(const char* p);            // it is not clear whether length(nullptr) is valid
length(nullptr);                      // OK?
```

**code example [good]**
```cpp
int length(not_null<const char*> p);  // better: we can assume that p cannot be nullptr

int length(not_null<czstring> p);     // we can assume p cannot be nullptr
                                      // we can assume p points to a zero-terminated array of characters
```

**enforcement**
- (Simple) If a function checks a pointer parameter against `nullptr` before access on all control-flow paths, warn it should be declared `not_null`
- (Complex) If a function with pointer return value ensures it is not `nullptr` on all return paths, warn the return type should be declared `not_null`

---

### [I.13] Do not pass an array as a single pointer

**reason**
(pointer, size)-style interfaces are error-prone. A plain pointer (to array) must rely on some convention to allow the callee to determine the size.

**code example [bad]**
```cpp
void copy_n(const T* p, T* q, int n); // copy from [p:p+n) to [q:q+n)

void draw(Shape* p, int n);  // poor interface; poor code
Circle arr[10];
draw(arr, 10);
```

**code example [good]**
```cpp
void copy(span<const T> r, span<T> r2); // copy r to r2

void draw2(span<Circle>);
Circle arr[10];
draw2(arr);    // deduce the element type and array size
```

**enforcement**
- (Simple)(Bounds) Warn for any expression that would rely on implicit conversion of an array type to a pointer type
- (Simple)(Bounds) Warn for any arithmetic operation on an expression of pointer type that results in a value of pointer type

---

### [I.22] Avoid complex initialization of global objects

**reason**
Complex initialization can lead to undefined order of execution.

**code example [bad]**
```cpp
// file1.c
extern const X x;
const Y y = f(x);   // read x; write y

// file2.c
extern const Y y;
const X x = g(y);   // read y; write x
// order of calls to f() and g() is undefined
```

**code example [good]**
```cpp
// Use constexpr initialization or avoid global objects with complex init altogether
constexpr X x{...};
```

**enforcement**
- Flag initializers of globals that call non-`constexpr` functions
- Flag initializers of globals that access `extern` objects

---

### [I.23] Keep the number of function arguments low

**reason**
Having many arguments opens opportunities for confusion. Passing lots of arguments is often costly compared to alternatives.

**code example [bad]**
```cpp
template<class InputIterator1, class InputIterator2, class OutputIterator, class Compare>
OutputIterator merge(InputIterator1 first1, InputIterator1 last1,
                     InputIterator2 first2, InputIterator2 last2,
                     OutputIterator result, Compare comp);
```

**code example [good]**
```cpp
template<class In1, class In2, class Out>
  requires mergeable<In1, In2, Out>
Out merge(In1 r1, In2 r2, Out result);
```

**enforcement**
- Warn when a function declares two iterators (including pointers) of the same type instead of a range or a view
- Try to use fewer than four (4) parameters

---

### [I.24] Avoid adjacent parameters that can be invoked by the same arguments in either order with different meaning

**reason**
Adjacent arguments of the same type are easily swapped by mistake.

**code example [bad]**
```cpp
void copy_n(T* p, T* q, int n);  // copy from [p:p + n) to [q:q + n)
```

**code example [good]**
```cpp
void copy_n(const T* p, T* q, int n);  // use const for the "from" argument
// or better:
void copy_n(span<const T> p, span<T> q);  // use span
```

**enforcement**
- (Simple) Warn if two consecutive parameters share the same type

---

### [I.25] Prefer empty abstract classes as interfaces to class hierarchies

**reason**
Abstract classes that are empty (have no non-static member data) are more likely to be stable than base classes with state.

**code example [bad]**
```cpp
class Shape {  // bad: interface class loaded with data
public:
    Point center() const { return c; }
    virtual void draw() const;
    virtual void rotate(int);
private:
    Point c;
    vector<Point> outline;
    Color col;
};
```

**code example [good]**
```cpp
class Shape {    // better: Shape is a pure interface
public:
    virtual Point center() const = 0;
    virtual void draw() const = 0;
    virtual void rotate(int) = 0;
    virtual ~Shape() = default;
    // ... no data members ...
};
```

**enforcement**
- (Simple) Warn if a pointer/reference to a class `C` is assigned to a pointer/reference to a base of `C` and the base class contains data members

---

### [I.26] If you want a cross-compiler ABI, use a C-style subset

**reason**
Different compilers implement different binary layouts for classes, exception handling, function names, and other implementation details.

**enforcement**
- (Not enforceable) It is difficult to reliably identify where an interface forms part of an ABI

---

### [I.27] For stable library ABI, consider the Pimpl idiom

**reason**
Private data members participate in class layout and private member functions participate in overload resolution. Changes to those implementation details require recompilation of all users. Pimpl can isolate users from changes at the cost of an indirection.

**code example [bad]**
```cpp
class widget {
public:
    void draw();
private:
    int n;  // changing this forces recompilation of all users
};
```

**code example [good]**
```cpp
// widget.h
class widget {
    class impl;
    std::unique_ptr<impl> pimpl;
public:
    void draw();
    widget(int);
    ~widget();
    widget(widget&&) noexcept;
    widget& operator=(widget&&) noexcept;
};

// widget.cpp
class widget::impl {
    int n;
public:
    void draw(const widget& w) { /* ... */ }
    impl(int n) : n(n) {}
};
void widget::draw() { pimpl->draw(*this); }
widget::widget(int n) : pimpl{std::make_unique<impl>(n)} {}
widget::~widget() = default;
```

**enforcement**
- (Not enforceable) It is difficult to reliably identify where an interface forms part of an ABI

---

### [I.30] Encapsulate rule violations

**reason**
To keep code simple and safe. Sometimes, ugly, unsafe, or error-prone techniques are necessary for logical or performance reasons. If so, keep them local rather than "infecting" interfaces.

**code example [bad]**
```cpp
bool owned;
owner<istream*> inp;
switch (source) {
case std_in:        owned = false; inp = &cin;                       break;
case command_line:  owned = true;  inp = new istringstream{argv[2]}; break;
case file:          owned = true;  inp = new ifstream{argv[2]};      break;
}
istream& in = *inp;
// ... someone has to remember: if (owned) delete inp;
```

**code example [good]**
```cpp
class Istream {
public:
    enum Opt { from_line = 1 };
    Istream() { }
    Istream(czstring p) : owned{true}, inp{new ifstream{p}} {}
    Istream(czstring p, Opt) : owned{true}, inp{new istringstream{p}} {}
    ~Istream() { if (owned) delete inp; }
    operator istream&() { return *inp; }
private:
    bool owned = false;
    istream* inp = &cin;
};
```

**enforcement**
- Hard to decide what rule-breaking code is essential
- Flag rule suppression that enable rule-violations to cross interfaces

---
