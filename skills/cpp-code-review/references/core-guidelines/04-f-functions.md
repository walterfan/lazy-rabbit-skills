# F: Functions

## Table of Contents

- [F.1] "Package" meaningful operations as carefully named functions
- [F.2] A function should perform a single logical operation
- [F.3] Keep functions short and simple
- [F.4] If a function might have to be evaluated at compile time, declare it `constexpr`
- [F.5] If a function is very small and time-critical, declare it `inline`
- [F.6] If your function must not throw, declare it `noexcept`
- [F.7] For general use, take `T*` or `T&` arguments rather than smart pointers
- [F.8] Prefer pure functions
- [F.9] Unused parameters should be unnamed
- [F.10] If an operation can be reused, give it a name
- [F.11] Use an unnamed lambda if you need a simple function object in one place only
- [F.15] Prefer simple and conventional ways of passing information
- [F.16] For "in" parameters, pass cheaply-copied types by value and others by reference to `const`
- [F.17] For "in-out" parameters, pass by reference to non-`const`
- [F.18] For "will-move-from" parameters, pass by `X&&` and `std::move` the parameter
- [F.19] For "forward" parameters, pass by `TP&&` and only `std::forward` the parameter
- [F.20] For "out" output values, prefer return values to output parameters
- [F.21] To return multiple "out" values, prefer returning a struct
- [F.60] Prefer `T*` over `T&` when "no argument" is a valid option
- [F.22] Use `T*` or `owner<T*>` to designate a single object
- [F.23] Use a `not_null<T>` to indicate that "null" is not a valid value
- [F.24] Use a `span<T>` or a `span_p<T>` to designate a half-open sequence
- [F.25] Use a `zstring` or a `not_null<zstring>` to designate a C-style string
- [F.26] Use a `unique_ptr<T>` to transfer ownership where a pointer is needed
- [F.27] Use a `shared_ptr<T>` to share ownership
- [F.42] Return a `T*` to indicate a position (only)
- [F.43] Never return a pointer or a reference to a local object
- [F.44] Return a `T&` when copy is undesirable and "returning no object" isn't needed
- [F.45] Don't return a `T&&`
- [F.46] `int` is the return type for `main()`
- [F.47] Return `T&` from assignment operators
- [F.48] Don't `return std::move(local)`
- [F.49] Don't return `const T`
- [F.50] Use a lambda when a function won't do
- [F.51] Where there is a choice, prefer default arguments over overloading
- [F.52] Prefer capturing by reference in lambdas used locally
- [F.53] Avoid capturing by reference in lambdas used non-locally
- [F.54] Don't use `[=]` default capture when capturing `this`
- [F.55] Don't use `va_arg` arguments
- [F.56] Avoid unnecessary condition nesting

## F.def: Function definitions

---

### [F.1] "Package" meaningful operations as carefully named functions

**reason**
Factoring out common code makes code more readable, more likely to be reused, and limits errors from complex code.

**code example [bad]**
```cpp
void read_and_print(istream& is)    // read and print an int
{
    int x;
    if (is >> x)
        cout << "the int is " << x << '\n';
    else
        cerr << "no int on input\n";
}
```
It reads, writes (to a fixed ostream), writes error messages, and handles only ints. Nothing to reuse.

**code example [good]**
```cpp
sort(a, b, [](T x, T y) { return x.rank() < y.rank() && x.value() < y.value(); });

// Better: name the lambda
auto lessT = [](T x, T y) { return x.rank() < y.rank() && x.value() < y.value(); };
sort(a, b, lessT);
```

**enforcement**
- See "Keep functions short and simple"
- Flag identical and very similar lambdas used in different places

---

### [F.2] A function should perform a single logical operation

**reason**
A function that performs a single operation is simpler to understand, test, and reuse.

**code example [bad]**
```cpp
void read_and_print()    // bad
{
    int x;
    cin >> x;
    // check for errors
    cout << x << "\n";
}
```

**code example [good]**
```cpp
int read(istream& is)    // better
{
    int x;
    is >> x;
    // check for errors
    return x;
}

void print(ostream& os, int x)
{
    os << x << "\n";
}
```

**enforcement**
- Consider functions with more than one "out" parameter suspicious
- Consider "large" functions that don't fit on one editor screen suspicious
- Consider functions with 7 or more parameters suspicious

---

### [F.3] Keep functions short and simple

**reason**
Large functions are hard to read, more likely to contain complex code, and more likely to have variables in larger than minimal scopes.

**code example [bad]**
```cpp
double simple_func(double val, int flag1, int flag2)
{
    double intermediate;
    if (flag1 > 0) {
        intermediate = func1(val);
        if (flag2 % 2)
             intermediate = sqrt(intermediate);
    }
    else if (flag1 == -1) {
        intermediate = func1(-val);
        if (flag2 % 2)
             intermediate = sqrt(-intermediate);
        flag1 = -flag1;
    }
    if (abs(flag2) > 10) {
        intermediate = func2(intermediate);
    }
    switch (flag2 / 10) {
    case 1: if (flag1 == -1) return finalize(intermediate, 1.171);
            break;
    case 2: return finalize(intermediate, 13.1);
    default: break;
    }
    return finalize(intermediate, 0.);
}
```

**code example [good]**
```cpp
double func1_muon(double val, int flag)
{
    // ...
}

double func1_tau(double val, int flag1, int flag2)
{
    // ...
}

double simple_func(double val, int flag1, int flag2)
{
    if (flag1 > 0)
        return func1_muon(val, flag2);
    if (flag1 == -1)
        return func1_tau(-val, flag1, flag2);
    return 0.;
}
```

**enforcement**
- Flag functions that do not "fit on a screen." Try 60 lines by 140 characters.
- Flag functions that are too complex. Try cyclomatic complexity "more than 10 logical paths through."

---

### [F.4] If a function might have to be evaluated at compile time, declare it `constexpr`

**reason**
`constexpr` is needed to tell the compiler to allow compile-time evaluation.

**code sample**
```cpp
constexpr int fac(int n)
{
    constexpr int max_exp = 17;      // constexpr enables max_exp to be used in Expects
    Expects(0 <= n && n < max_exp);  // prevent silliness and overflow
    int x = 1;
    for (int i = 2; i <= n; ++i) x *= i;
    return x;
}
```

**code sample**
```cpp
constexpr int min(int x, int y) { return x < y ? x : y; }

void test(int v)
{
    int m1 = min(-1, 2);            // probably compile-time evaluation
    constexpr int m2 = min(-1, 2);  // compile-time evaluation
    int m3 = min(-1, v);            // run-time evaluation
    constexpr int m4 = min(-1, v);  // error: cannot evaluate at compile time
}
```

**enforcement**
- Impossible and unnecessary. The compiler gives an error if a non-`constexpr` function is called where a constant is required.

---

### [F.5] If a function is very small and time-critical, declare it `inline`

**reason**
Some optimizers are good at inlining without hints from the programmer, but don't rely on it. Specifying `inline` encourages the compiler to do a better job.

**code sample**
```cpp
inline string cat(const string& s, const string& s2) { return s + s2; }
```

Note: `constexpr` implies `inline`. Member functions defined in-class are `inline` by default.

**enforcement**
- No specific enforcement.

---

### [F.6] If your function must not throw, declare it `noexcept`

**reason**
If an exception is not supposed to be thrown, the program cannot be assumed to cope with the error and should be terminated as soon as possible. Declaring a function `noexcept` helps optimizers by reducing the number of alternative execution paths.

**code sample**
```cpp
vector<string> collect(istream& is) noexcept
{
    vector<string> res;
    for (string s; is >> s;)
        res.push_back(s);
    return res;
}
```
If `collect()` runs out of memory, the program crashes. Unless the program is crafted to survive memory exhaustion, that might be the right thing to do.

**enforcement**
- (Hard) Flag low-level functions that are not `noexcept`, yet cannot throw
- Flag throwing `swap`, `move`, destructors, and default constructors

---

### [F.7] For general use, take `T*` or `T&` arguments rather than smart pointers

**reason**
Passing a smart pointer transfers or shares ownership and should only be used when ownership semantics are intended. Passing by smart pointer restricts the use of a function to callers that use smart pointers.

**code example [bad]**
```cpp
void f(shared_ptr<widget>& w)
{
    // ...
    use(*w); // only use of w -- the lifetime is not used at all
    // ...
};

shared_ptr<widget> my_widget = /* ... */;
f(my_widget);

widget stack_widget;
f(stack_widget); // error
```

**code example [good]**
```cpp
void f(widget& w)
{
    // ...
    use(w);
    // ...
};

shared_ptr<widget> my_widget = /* ... */;
f(*my_widget);

widget stack_widget;
f(stack_widget); // ok -- now this works
```

**enforcement**
- (Simple) Warn if a function takes a parameter of a smart pointer type that is copyable but the function only calls `operator*`, `operator->` or `get()`. Suggest using a `T*` or `T&` instead.
- Flag a parameter of a smart pointer type that is copyable/movable but never copied/moved from in the function body and that is not passed along to another function that could do so.

---

### [F.8] Prefer pure functions

**reason**
Pure functions are easier to reason about, sometimes easier to optimize (and even parallelize), and sometimes can be memoized.

**code sample**
```cpp
template<class T>
auto square(T t) { return t * t; }
```

**enforcement**
- Not possible.

---

### [F.9] Unused parameters should be unnamed

**reason**
Readability. Suppression of unused parameter warnings.

**code sample**
```cpp
widget* find(const set<widget>& s, const widget& w, Hint);   // once upon a time, a hint was used
```

**code sample**
```cpp
template <typename Value>
Value* find(const set<Value>& s, const Value& v, [[maybe_unused]] Hint h)
{
    if constexpr (sizeof(Value) > CacheSize)
    {
        // a hint is used only if Value is of a certain size
    }
}
```

**enforcement**
- Flag named unused parameters.

---

### [F.10] If an operation can be reused, give it a name

**reason**
Documentation, readability, opportunity for reuse.

**code example [bad]**
```cpp
auto x = find_if(vr.begin(), vr.end(),
    [&](Rec& r) {
        if (r.name.size() != n.size()) return false;
        for (int i = 0; i < r.name.size(); ++i)
            if (tolower(r.name[i]) != tolower(n[i])) return false;
        return true;
    }
);
```

**code example [good]**
```cpp
bool compare_insensitive(const string& a, const string& b)
{
    if (a.size() != b.size()) return false;
    for (int i = 0; i < a.size(); ++i) if (tolower(a[i]) != tolower(b[i])) return false;
    return true;
}

auto x = find_if(vr.begin(), vr.end(),
    [&](Rec& r) { return compare_insensitive(r.name, n); }
);
```

**enforcement**
- (Hard) flag similar lambdas

---

### [F.11] Use an unnamed lambda if you need a simple function object in one place only

**reason**
That makes the code concise and gives better locality than alternatives.

**code example [good]**
```cpp
auto earlyUsersEnd = std::remove_if(users.begin(), users.end(),
                                    [](const User &a) { return a.id > 100; });
```

**enforcement**
- Look for identical and near identical lambdas (to be replaced with named functions or named lambdas).

---

## F.call: Parameter passing

---

### [F.15] Prefer simple and conventional ways of passing information

**reason**
Using "unusual and clever" techniques causes surprises, slows understanding by other programmers, and encourages bugs.

**enforcement**
- Use the advanced techniques only after demonstrating need, and document that need in a comment.

---

### [F.16] For "in" parameters, pass cheaply-copied types by value and others by reference to `const`

**reason**
Both let the caller know that a function will not modify the argument, and both allow initialization by rvalues. What is "cheap to copy" depends on the machine architecture, but two or three words (doubles, pointers, references) are usually best passed by value.

**code sample**
```cpp
void f1(const string& s);  // OK: pass by reference to const; always cheap
void f2(string s);         // bad: potentially expensive
void f3(int x);            // OK: Unbeatable
void f4(const int& x);     // bad: overhead on access in f4()
```

**code example [bad]**
```cpp
int multiply(int, int); // just input ints, pass by value

// suffix is input-only but not as cheap as an int, pass by const&
string& concatenate(string&, const string& suffix);

void sink(unique_ptr<widget>);  // input only, and moves ownership of the widget
```

**enforcement**
- (Simple) Warn when a parameter being passed by value has a size greater than `2 * sizeof(void*)`. Suggest using a reference to `const` instead.
- (Simple) Warn when a parameter passed by reference to `const` has a size less or equal than `2 * sizeof(void*)`. Suggest passing by value instead.
- (Simple) Warn when a parameter passed by reference to `const` is `move`d.

---

### [F.17] For "in-out" parameters, pass by reference to non-`const`

**reason**
This makes it clear to callers that the object is assumed to be modified.

**code example [bad]**
```cpp
void update(Record& r);  // assume that update writes to r
```

**code example [bad]**
```cpp
void increment_all(span<int> a)
{
  for (auto&& e : a)
    ++e;
}
```

**code example [bad]**
```cpp
void f(string& s)
{
    s = "New York";  // non-obvious error
}

void g()
{
    string buffer = ".................................";
    f(buffer);
    // ...
}
```
Here, the writer of `g()` is supplying a buffer for `f()` to fill, but `f()` simply replaces it.

**enforcement**
- (Moderate) Warn about functions regarding reference to non-`const` parameters that do *not* write to them.
- (Simple) Warn when a non-`const` parameter being passed by reference is `move`d.

---

### [F.18] For "will-move-from" parameters, pass by `X&&` and `std::move` the parameter

**reason**
It's efficient and eliminates bugs at the call site: `X&&` binds to rvalues, which requires an explicit `std::move` at the call site if passing an lvalue.

**code sample**
```cpp
void sink(vector<int>&& v)  // sink takes ownership of whatever the argument owned
{
    // usually there might be const accesses of v here
    store_somewhere(std::move(v));
    // usually no more use of v here; it is moved-from
}
```

**code example [bad]**
```cpp
// Unique owner types that are move-only and cheap-to-move can also be passed by value
template<class T>
void sink(std::unique_ptr<T> p)
{
    // use p ... possibly std::move(p) onward somewhere else
}   // p gets destroyed
```

**enforcement**
- Flag all `X&&` parameters (where `X` is not a template type parameter name) where the function body uses them without `std::move`
- Flag access to moved-from objects
- Don't conditionally move from objects

---

### [F.19] For "forward" parameters, pass by `TP&&` and only `std::forward` the parameter

**reason**
If the object is to be passed onward to other code and not directly used by this function, we want to make this function agnostic to the argument `const`-ness and rvalue-ness.

**code sample**
```cpp
template<class F, class... Args>
inline decltype(auto) invoke(F&& f, Args&&... args)
{
    return forward<F>(f)(forward<Args>(args)...);
}
```

**code sample**
```cpp
template<class PairLike>
inline auto test(PairLike&& pairlike)
{
    // ...
    f1(some, args, and, forward<PairLike>(pairlike).first);           // forward .first
    f2(and, forward<PairLike>(pairlike).second, in, another, call);   // forward .second
}
```

**enforcement**
- Flag a function that takes a `TP&&` parameter and does anything with it other than `std::forward`ing it exactly once on every static path.

---

### [F.20] For "out" output values, prefer return values to output parameters

**reason**
A return value is self-documenting, whereas an `&` could be either in-out or out-only and is liable to be misused.

**code sample**
```cpp
// OK: return pointers to elements with the value x
vector<const int*> find_all(const vector<int>&, int x);

// Bad: place pointers to elements with value x in-out
void find_all(const vector<int>&, vector<const int*>& out, int x);
```

**code example [bad]**
```cpp
Matrix operator+(const Matrix& a, const Matrix& b)
{
    Matrix res;
    // ... fill res with the sum ...
    return res;
}

Matrix x = m1 + m2;  // move constructor
y = m3 + m3;         // move assignment
```

**code sample**
```cpp
struct Package {      // exceptional case: expensive-to-move object
    char header[16];
    char load[2024 - 16];
};

Package fill();       // Bad: large return value
void fill(Package&);  // OK

int val();            // OK
void val(int&);       // Bad: Is val reading its argument
```

**enforcement**
- Flag reference to non-`const` parameters that are not read before being written to and are a type that could be cheaply returned.

---

### [F.21] To return multiple "out" values, prefer returning a struct

**reason**
A return value is self-documenting as an "output-only" value. Prefer using a named `struct` if possible. Otherwise, a `tuple` is useful in variadic templates.

**code example [bad]**
```cpp
int f(const string& input, /*output only*/ string& output_data)
{
    // ...
    output_data = something();
    return status;
}
```

**code example [good]**
```cpp
struct f_result { int status; string data; };

f_result f(const string& input)
{
    // ...
    return {status, something()};
}
```

**code sample**
```cpp
// C++98
pair<set::iterator, bool> result = my_set.insert("Hello");
if (result.second)
    do_something_with(result.first);    // workaround

// C++17 structured bindings
if (auto [ iter, success ] = my_set.insert("Hello"); success)
    do_something_with(iter);
```

**enforcement**
- Output parameters should be replaced by return values
- `pair` or `tuple` return types should be replaced by `struct`, if possible

---

### [F.60] Prefer `T*` over `T&` when "no argument" is a valid option

**reason**
A pointer (`T*`) can be a `nullptr` and a reference (`T&`) cannot. Sometimes having `nullptr` as an alternative to indicate "no object" is useful.

**code sample**
```cpp
string zstring_to_string(zstring p) // zstring is a char*; that is a C-style string
{
    if (!p) return string{};    // p might be nullptr; remember to check
    return string{p};
}

void print(const vector<int>& r)
{
    // r refers to a vector<int>; no check needed
}
```

**enforcement**
- Flag ???

---

### [F.22] Use `T*` or `owner<T*>` to designate a single object

**reason**
Readability: it makes the meaning of a plain pointer clear. Enables significant tool support.

**code example [bad]**
```cpp
void use(int* p, int n, char* s, int* q)
{
    p[n - 1] = 666; // Bad: we don't know if p points to n elements
    cout << s;      // Bad: we don't know if s points to a zero-terminated array
    delete q;       // Bad: we don't know if *q is allocated on the free store
}
```

**code example [good]**
```cpp
void use2(span<int> p, zstring s, owner<int*> q)
{
    p[p.size() - 1] = 666; // OK, a range error can be caught
    cout << s; // OK
    delete q;  // OK
}
```

**enforcement**
- (Simple)(Bounds) Warn for any arithmetic operation on an expression of pointer type that results in a value of pointer type.

---

### [F.23] Use a `not_null<T>` to indicate that "null" is not a valid value

**reason**
Clarity. A function with a `not_null<T>` parameter makes it clear that the caller is responsible for any `nullptr` checks that might be necessary.

**code sample**
```cpp
int length(Record* p);
// When I call length(p) should I check if p is nullptr first?

// it is the caller's job to make sure p != nullptr
int length(not_null<Record*> p);

// the implementor of length() must assume that p == nullptr is possible
int length(Record* p);
```

**enforcement**
- (Simple) Warn if a raw pointer is dereferenced without being tested against `nullptr` within a function, suggest it is declared `not_null` instead.
- (Simple) Error if a raw pointer is sometimes dereferenced after first being tested against `nullptr` and sometimes is not.
- (Simple) Warn if a `not_null` pointer is tested against `nullptr` within a function.

---

### [F.24] Use a `span<T>` or a `span_p<T>` to designate a half-open sequence

**reason**
Informal/non-explicit ranges are a source of errors.

**code example [good]**
```cpp
X* find(span<X> r, const X& v);    // find v in r

vector<X> vec;
// ...
auto p = find({vec.begin(), vec.end()}, X{});  // find X{} in vec
```

**code example [good]**
```cpp
void f(span<int> s)
{
    // range traversal (guaranteed correct)
    for (int x : s) cout << x << '\n';

    // C-style traversal (potentially checked)
    for (gsl::index i = 0; i < s.size(); ++i) cout << s[i] << '\n';

    // random access (potentially checked)
    s[7] = 9;

    // extract pointers (potentially checked)
    std::sort(&s[0], &s[s.size() / 2]);
}
```

**enforcement**
- (Complex) Warn where accesses to pointer parameters are bounded by other parameters that are integral types and suggest they could use `span` instead.

---

### [F.25] Use a `zstring` or a `not_null<zstring>` to designate a C-style string

**reason**
C-style strings are ubiquitous. We must distinguish C-style strings from a pointer to a single character or an old-fashioned pointer to an array of characters. If you don't need null termination, use `string_view`.

**code example [bad]**
```cpp
// the implementor of length() must assume that p == nullptr is possible
int length(zstring p);

// it is the caller's job to make sure p != nullptr
int length(not_null<zstring> p);
```

**enforcement**
- No specific enforcement.

---

### [F.26] Use a `unique_ptr<T>` to transfer ownership where a pointer is needed

**reason**
Using `unique_ptr` is the cheapest way to pass a pointer safely.

**code sample**
```cpp
unique_ptr<Shape> get_shape(istream& is)  // assemble shape from input stream
{
    auto kind = read_header(is);
    switch (kind) {
    case kCircle:
        return make_unique<Circle>(is);
    case kTriangle:
        return make_unique<Triangle>(is);
    // ...
    }
}
```

**enforcement**
- (Simple) Warn if a function returns a locally allocated raw pointer. Suggest using either `unique_ptr` or `shared_ptr` instead.

---

### [F.27] Use a `shared_ptr<T>` to share ownership

**reason**
Using `std::shared_ptr` is the standard way to represent shared ownership. The last owner deletes the object.

**code sample**
```cpp
{
    shared_ptr<const Image> im { read_image(somewhere) };

    std::thread t0 {shade, args0, top_left, im};
    std::thread t1 {shade, args1, top_right, im};
    std::thread t2 {shade, args2, bottom_left, im};
    std::thread t3 {shade, args3, bottom_right, im};

    // detaching threads requires extra care, but even if we detach ...
}
// ... shared_ptr ensures that eventually the last thread to finish safely deletes the image
```

**enforcement**
- (Not enforceable) This is a too complex pattern to reliably detect.

---

### [F.42] Return a `T*` to indicate a position (only)

**reason**
That's what pointers are good for. Returning a `T*` to transfer ownership is a misuse.

**code example [good]**
```cpp
Node* find(Node* t, const string& s)  // find s in a binary tree of Nodes
{
    if (!t || t->name == s) return t;
    if ((auto p = find(t->left, s))) return p;
    if ((auto p = find(t->right, s))) return p;
    return nullptr;
}
```
The pointer returned by `find` indicates a Node holding `s`. It does not imply a transfer of ownership.

**enforcement**
- Flag `delete`, `std::free()`, etc. applied to a plain `T*`. Only owners should be deleted.
- Flag `new`, `malloc()`, etc. assigned to a plain `T*`. Only owners should be responsible for deletion.

---

### [F.43] Never (directly or indirectly) return a pointer or a reference to a local object

**reason**
To avoid the crashes and data corruption that can result from the use of such a dangling pointer.

**code example [bad]**
```cpp
int* f()
{
    int fx = 9;
    return &fx;  // BAD
}

void g(int* p)
{
    int gx;
    cout << "*p == " << *p << '\n';
    *p = 999;
    cout << "gx == " << gx << '\n';
}

void h()
{
    int* p = f();
    int z = *p;  // read from abandoned stack frame (bad)
    g(p);        // pass pointer to abandoned stack frame to function (bad)
}
```

**code example [bad]**
```cpp
int& f()
{
    int x = 7;
    // ...
    return x;  // Bad: returns reference to object that is about to be destroyed
}
```

**code example [bad]**
```cpp
int* glob;       // global variables are bad in so many ways

template<class T>
void steal(T x)
{
    glob = x();  // BAD
}

void f()
{
    int i = 99;
    steal([&] { return &i; });
}

int main()
{
    f();
    cout << *glob << '\n';
}
```

**enforcement**
- Compilers tend to catch return of reference to locals and could in many cases catch return of pointers to locals
- Static analysis can catch many common patterns of the use of pointers indicating positions

---

### [F.44] Return a `T&` when copy is undesirable and "returning no object" isn't needed

**reason**
The language guarantees that a `T&` refers to an object, so that testing for `nullptr` isn't necessary.

**code sample**
```cpp
class Car
{
    array<wheel, 4> w;
    // ...
public:
    wheel& get_wheel(int i) { Expects(i < w.size()); return w[i]; }
    // ...
};

void use()
{
    Car c;
    wheel& w0 = c.get_wheel(0); // w0 has the same lifetime as c
}
```

**enforcement**
- Flag functions where no `return` expression could yield `nullptr`.

---

### [F.45] Don't return a `T&&`

**reason**
It's asking to return a reference to a destroyed temporary object. An `&&` is a magnet for temporary objects.

**code example [bad]**
```cpp
auto&& x = max(0, 1);   // OK, so far
foo(x);                 // Undefined behavior
```

**code sample**
```cpp
// BAD
template<class F>
auto&& wrapper(F f)
{
    log_call(typeid(f));
    return f();          // BAD: returns a reference to a temporary
}

// Better
template<class F>
auto wrapper(F f)
{
    log_call(typeid(f));
    return f();          // OK
}
```

**enforcement**
- Flag any use of `&&` as a return type, except in `std::move` and `std::forward`.

---

### [F.46] `int` is the return type for `main()`

**reason**
It's a language rule, but violated through "language extensions" so often that it is worth mentioning.

**code example [bad]**
```cpp
void main() { /* ... */ };  // bad, not C++

int main()
{
    std::cout << "This is the way to do it\n";
}
```

**enforcement**
- The compiler should do it. If the compiler doesn't do it, let tools flag it.

---

### [F.47] Return `T&` from assignment operators

**reason**
The convention for operator overloads is for `operator=(const T&)` to perform the assignment and then return (non-`const`) `*this`. This ensures consistency with standard-library types and follows the principle of "do as the ints do."

**code example [bad]**
```cpp
class Foo
{
 public:
    // ...
    Foo& operator=(const Foo& rhs)
    {
      // Copy members.
      // ...
      return *this;
    }
};
```

**enforcement**
- This should be enforced by tooling by checking the return type (and return value) of any assignment operator.

---

### [F.48] Don't `return std::move(local)`

**reason**
Returning a local variable implicitly moves it anyway. An explicit `std::move` is always a pessimization, because it prevents Return Value Optimization (RVO), which can eliminate the move completely.

**code example [bad]**
```cpp
S bad()
{
  S result;
  return std::move(result);
}
```

**code example [good]**
```cpp
S good()
{
  S result;
  // Named RVO: move elision at best, move construction at worst
  return result;
}
```

**enforcement**
- This should be enforced by tooling by checking the return expression.

---

### [F.49] Don't return `const T`

**reason**
It is not recommended to return a `const` value. Such older advice is now obsolete; it does not add value, and it interferes with move semantics.

**code example [bad]**
```cpp
const vector<int> fct();    // bad: that "const" is more trouble than it is worth

void g(vector<int>& vx)
{
    // ...
    fct() = vx;   // prevented by the "const"
    // ...
    vx = fct(); // expensive copy: move semantics suppressed by the "const"
    // ...
}
```

**enforcement**
- Flag returning a `const` value. To fix: Remove `const` to return a non-`const` value instead.

---

### [F.50] Use a lambda when a function won't do (to capture local variables, or to write a local function)

**reason**
Functions can't capture local variables or be defined at local scope; if you need those things, prefer a lambda. On the other hand, lambdas and function objects don't overload; if you need to overload, prefer a function.

**code example [bad]**
```cpp
// writing a function that should only take an int or a string -- overloading is natural
void f(int);
void f(const string&);

// writing a function object that needs to capture local state -- a lambda is natural
vector<work> v = lots_of_work();
for (int tasknum = 0; tasknum < max; ++tasknum) {
    pool.run([=, &v] {
        /*
        ...
        ... process (1/max)-th of v, the tasknum-th chunk
        ...
        */
    });
}
pool.join();
```

**enforcement**
- Warn on use of a named non-generic lambda that captures nothing and appears at global scope. Write an ordinary function instead.

---

### [F.51] Where there is a choice, prefer default arguments over overloading

**reason**
Default arguments simply provide alternative interfaces to a single implementation. There is no guarantee that a set of overloaded functions all implement the same semantics.

**code sample**
```cpp
void print(const string& s, format f = {});

// as opposed to:
void print(const string& s);  // use default format
void print(const string& s, format f);
```

**enforcement**
- Warn on an overload set where the overloads have a common prefix of parameters (e.g., `f(int)`, `f(int, const string&)`, `f(int, const string&, double)`).

---

### [F.52] Prefer capturing by reference in lambdas that will be used locally, including passed to algorithms

**reason**
For efficiency and correctness, you nearly always want to capture by reference when using the lambda locally.

**code sample**
```cpp
std::for_each(begin(sockets), end(sockets), [&message](auto& socket)
{
    socket.send(message);
});
```

**code sample**
```cpp
void send_packets(buffers& bufs)
{
    stage encryptor([](buffer& b) { encrypt(b); });
    stage compressor([&](buffer& b) { compress(b); encryptor.process(b); });
    stage decorator([&](buffer& b) { decorate(b); compressor.process(b); });
    for (auto& b : bufs) { decorator.process(b); }
}  // automatically blocks waiting for pipeline to finish
```

**enforcement**
- Flag a lambda that captures by reference, but is used other than locally within the function scope or passed to a function by reference.

---

### [F.53] Avoid capturing by reference in lambdas that will be used non-locally, including returned, stored on the heap, or passed to another thread

**reason**
Pointers and references to locals shouldn't outlive their scope. Lambdas that capture by reference are just another place to store a reference to a local object.

**code example [bad]**
```cpp
int local = 42;

// Note that after program exits this scope,
// local no longer exists, therefore
// process() call will have undefined behavior!
thread_pool.queue_work([&] { process(local); });
```

**code example [good]**
```cpp
int local = 42;
// Want a copy of local.
// Since a copy of local is made, it will always be available for the call.
thread_pool.queue_work([=] { process(local); });
```

**enforcement**
- (Simple) Warn when capture-list contains a reference to a locally declared variable
- (Complex) Flag when capture-list contains a reference to a locally declared variable and the lambda is passed to a non-`const` and non-local context

---

### [F.54] When writing a lambda that captures `this` or any class data member, don't use `[=]` default capture

**reason**
It's confusing. Writing `[=]` in a member function appears to capture by value, but actually captures data members by reference because it actually captures the invisible `this` pointer by value.

**code example [bad]**
```cpp
class My_class {
    int x = 0;
    // ...

    void f()
    {
        int i = 0;
        // ...

        auto lambda = [=] { use(i, x); };   // BAD: "looks like" copy/value capture
        // x is actually captured by reference via this

        x = 42;
        lambda(); // calls use(0, 42);
        x = 43;
        lambda(); // calls use(0, 43);

        // ...

        auto lambda2 = [i, this] { use(i, x); }; // ok, most explicit and least confusing

        // ...
    }
};
```

**enforcement**
- Flag any lambda capture-list that specifies a capture-default of `[=]` and also captures `this` (whether explicitly or via the default capture and a use of `this` in the body)

---

### [F.55] Don't use `va_arg` arguments

**reason**
Reading from a `va_arg` assumes that the correct type was actually passed. Passing to varargs assumes the correct type will be read. This is fragile because it cannot generally be enforced to be safe in the language.

**code sample**
```cpp
int sum(...)
{
    // ...
    while (/*...*/)
        result += va_arg(list, int); // BAD, assumes it will be passed ints
    // ...
}

sum(3, 2); // ok
sum(3.14159, 2.71828); // BAD, undefined

template<class ...Args>
auto sum(Args... args) // GOOD, and much more flexible
{
    return (... + args); // note: C++17 "fold expression"
}

sum(3, 2); // ok: 5
sum(3.14159, 2.71828); // ok: ~5.85987
```

**enforcement**
- Issue a diagnostic for using `va_list`, `va_start`, or `va_arg`
- Issue a diagnostic for passing an argument to a vararg parameter of a function that does not offer an overload for a more specific type in the position of the vararg

---

### [F.56] Avoid unnecessary condition nesting

**reason**
Shallow nesting of conditions makes the code easier to follow. It also makes the intent clearer.

**code example [bad]**
```cpp
// Bad: Deep nesting
void foo() {
    // ...
    if (x) {
        computeImportantThings(x);
    }
}

// Bad: Still a redundant else.
void foo() {
    // ...
    if (!x) {
        return;
    }
    else {
        computeImportantThings(x);
    }
}
```

**code example [good]**
```cpp
// Good: Early return, no redundant else
void foo() {
    // ...
    if (!x)
        return;

    computeImportantThings(x);
}
```

**code sample**
```cpp
// Bad: Unnecessary nesting of conditions
void foo() {
    // ...
    if (x) {
        if (y) {
            computeImportantThings(x);
        }
    }
}

// Good: Merge conditions + return early
void foo() {
    // ...
    if (!(x && y))
        return;

    computeImportantThings(x);
}
```

**enforcement**
- Flag a redundant `else`
- Flag a function whose body is simply a conditional statement enclosing a block

---
