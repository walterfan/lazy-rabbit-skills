# ES: Expressions and statements

## Table of Contents

**General:** ES.1-ES.3 | **Declarations:** ES.5-ES.12, ES.20-ES.28, ES.30-ES.34
**Expressions:** ES.40-ES.50, ES.55-ES.56, ES.60-ES.65 | **Statements:** ES.70-ES.87
**Arithmetic:** ES.100-ES.107

---

### [ES.1] Prefer the standard library to other libraries and to "handcrafted code"

**reason**
Code using a library can be much easier to write, shorter, higher level of abstraction, and the library code is presumably already tested.

**code sample**
```cpp
auto sum = accumulate(begin(a), end(a), 0.0);   // good

auto sum = accumulate(v, 0.0); // better: a range version

// bad: verbose, purpose unstated
int max = v.size();
double sum = 0.0;
for (int i = 0; i < max; ++i)
    sum = sum + v[i];
```

**enforcement**
- Not easy. Look for messy loops, nested loops, long functions, absence of function calls, lack of use of built-in types.

---

### [ES.2] Prefer suitable abstractions to direct use of language features

**reason**
A "suitable abstraction" is closer to the application concepts, leads to shorter and clearer code, and is likely to be better tested.

**code example [good]**
```cpp
vector<string> read1(istream& is)   // good
{
    vector<string> res;
    for (string s; is >> s;)
        res.push_back(s);
    return res;
}
```

**code example [bad]**
```cpp
char** read2(istream& is, int maxelem, int maxstring, int* nread)   // bad: verbose and incomplete
{
    auto res = new char*[maxelem];
    int elemcount = 0;
    while (is && elemcount < maxelem) {
        auto s = new char[maxstring];
        is.read(s, maxstring);
        res[elemcount++] = s;
    }
    *nread = elemcount;
    return res;
}
```

Once the checking for overflow and error handling has been added that code gets quite messy, and there is the problem remembering to `delete` the returned pointer and the C-style strings that array contains.

**enforcement**
- Not easy. Look for messy loops, nested loops, long functions.

---

### [ES.3] Don't repeat yourself, avoid redundant code

**reason**
Duplicated code obscures intent, makes it harder to understand, and makes maintenance harder.

**code sample**
```cpp
void func(bool flag)    // Bad, duplicated code.
{
    if (flag) {
        x();
        y();
    }
    else {
        x();
        z();
    }
}

void func(bool flag)    // Better, no duplicated code.
{
    x();

    if (flag)
        y();
    else
        z();
}
```

**enforcement**
- Use a static analyzer. It will catch at least some redundant constructs.

---

### [ES.5] Keep scopes small

**reason**
Readability. Minimize resource retention. Avoid accidental misuse of value.

**code example [bad]**
```cpp
void use()
{
    int i;    // bad: i is needlessly accessible after loop
    for (i = 0; i < 20; ++i) { /* ... */ }
    // no intended use of i here
    for (int i = 0; i < 20; ++i) { /* ... */ }  // good: i is local to for-loop

    if (auto pc = dynamic_cast<Circle*>(ps)) {  // good: pc is local to if-statement
        // ... deal with Circle ...
    }
    else {
        // ... handle error ...
    }
}
```

**code example [bad]**
```cpp
void use(const string& name)
{
    string fn = name + ".txt";
    ifstream is {fn};
    Record r;
    is >> r;
    // ... 200 lines of code without intended use of fn or is ...
}
```

Factor out the read:

```cpp
Record load_record(const string& name)
{
    string fn = name + ".txt";
    ifstream is {fn};
    Record r;
    is >> r;
    return r;
}

void use(const string& name)
{
    Record r = load_record(name);
    // ... 200 lines of code ...
}
```

**enforcement**
- Flag loop variable declared outside a loop and not used after the loop.
- Flag when expensive resources, such as file handles and locks are not used for N-lines.

---

### [ES.6] Declare names in for-statement initializers and conditions to limit scope

**reason**
Readability. Limit the loop variable visibility to the scope of the loop. Minimize resource retention.

**code example [good]**
```cpp
void use()
{
    for (string s; cin >> s;)
        v.push_back(s);

    for (int i = 0; i < 20; ++i) {   // good: i is local to for-loop
        // ...
    }

    if (auto pc = dynamic_cast<Circle*>(ps)) {   // good: pc is local to if-statement
        // ... deal with Circle ...
    }
    else {
        // ... handle error ...
    }
}
```

**code example [bad]**
```cpp
int j;                            // BAD: j is visible outside the loop
for (j = 0; j < 100; ++j) {
    // ...
}
// j is still visible here and isn't needed
```

C++17/C++20 initializer statements:

```cpp
map<int, string> mymap;

if (auto result = mymap.insert(value); result.second) {
    // insert succeeded, and result is valid for this block
    use(result.first);  // ok
    // ...
} // result is destroyed here
```

**enforcement**
- Warn when a variable modified inside the `for`-statement is declared outside the loop and not being used outside the loop.
- (hard) Flag loop variables declared before the loop and used after the loop for an unrelated purpose.

---

### [ES.7] Keep common and local names short, and keep uncommon and non-local names longer

**reason**
Readability. Lowering the chance of clashes between unrelated non-local names.

**code example [good]**
```cpp
template<typename T>    // good
void print(ostream& os, const vector<T>& v)
{
    for (gsl::index i = 0; i < v.size(); ++i)
        os << v[i] << '\n';
}

template<typename Element_type>   // bad: verbose, hard to read
void print(ostream& target_stream, const vector<Element_type>& current_vector)
{
    for (gsl::index current_element_index = 0;
         current_element_index < current_vector.size();
         ++current_element_index
    )
    target_stream << current_vector[current_element_index] << '\n';
}
```

Unconventional and short non-local names obscure code:

```cpp
void use1(const string& s)
{
    // ...
    tt(s);   // bad: what is tt()?
    // ...
}

void use1(const string& s)
{
    // ...
    trim_tail(s);   // better
    // ...
}
```

**enforcement**
- Check length of local and non-local names. Also take function length into account.

---

### [ES.8] Avoid similar-looking names

**reason**
Code clarity and readability. Too-similar names slow down comprehension and increase the likelihood of error.

**code example [bad]**
```cpp
if (readable(i1 + l1 + ol + o1 + o0 + ol + o1 + I0 + l0)) surprise();
```

```cpp
struct foo { int n; };
struct foo foo();       // BAD, foo is a type already in scope
struct foo x = foo();   // requires disambiguation
```

**enforcement**
- Check names against a list of known confusing letter and digit combinations.
- Flag a declaration of a variable, function, or enumerator that hides a class or enumeration declared in the same scope.

---

### [ES.9] Avoid `ALL_CAPS` names

**reason**
Such names are commonly used for macros. Thus, `ALL_CAPS` names are vulnerable to unintended macro substitution.

**code example [bad]**
```cpp
// somewhere in some header:
#define NE !=

// somewhere else in some other header:
enum Coord { N, NE, NW, S, SE, SW, E, W };

// somewhere third in some poor programmer's .cpp:
switch (direction) {
case N:
    // ...
case NE:
    // ...
// ...
}
```

**enforcement**
- Flag all uses of ALL CAPS. For older code, accept ALL CAPS for macro names and flag all non-all-CAPS macro names.

---

### [ES.10] Declare one name (only) per declaration

**reason**
One declaration per line increases readability and avoids mistakes related to the C/C++ grammar.

**code example [bad]**
```cpp
char *p, c, a[7], *pp[7], **aa[10];   // yuck!
```

**code example [good]**
```cpp
auto [iter, inserted] = m.insert_or_assign(k, val);
if (inserted) { /* new entry was inserted */ }
```

```cpp
template<class InputIterator, class Predicate>
bool any_of(InputIterator first, InputIterator last, Predicate pred);
```

or better using concepts:

```cpp
bool any_of(input_iterator auto first, input_iterator auto last, predicate auto pred);
```

```cpp
int a = 10, b = 11, c = 12, d, e = 14, f = 15;
```

In a long list of declarators it is easy to overlook an uninitialized variable.

**enforcement**
- Flag variable and constant declarations with multiple declarators (e.g., `int* p, q;`).

---

### [ES.11] Use `auto` to avoid redundant repetition of type names

**reason**
Simple repetition is tedious and error-prone. When you use `auto`, the name of the declared entity is in a fixed position in the declaration, increasing readability.

**code example [bad]**
```cpp
auto p = v.begin();      // vector<DataRecord>::iterator
auto z1 = v[3];          // makes copy of DataRecord
auto& z2 = v[3];         // avoids copy
const auto& z3 = v[3];   // const and avoids copy
auto h = t.future();
auto q = make_unique<int[]>(s);
auto f = [](int x) { return x + 10; };
```

```cpp
template<class T>
auto Container<T>::first() -> Iterator;   // Container<T>::Iterator
```

Avoid `auto` for initializer lists:

```cpp
auto lst = { 1, 2, 3 };   // lst is an initializer list
auto x{1};   // x is an int (in C++17; initializer_list in C++11)
```

As of C++20, use concepts to be more specific:

```cpp
forward_iterator auto p = algo(x, y, z);
```

```cpp
std::set<int> values;
// ...
auto [ position, newly_inserted ] = values.insert(5);   // break out the members of the std::pair
```

**enforcement**
- Flag redundant repetition of type names in a declaration.

---

### [ES.12] Do not reuse names in nested scopes

**reason**
It is easy to get confused about which variable is used. Can cause maintenance problems.

**code example [bad]**
```cpp
int d = 0;
// ...
if (cond) {
    // ...
    d = 9;
    // ...
}
else {
    // ...
    int d = 7;
    // ...
    d = value_to_be_returned;
    // ...
}

return d;
```

If this is a large `if`-statement, it is easy to overlook that a new `d` has been introduced in the inner scope. This is known as "shadowing".

```cpp
void f(int x)
{
    int x = 4;  // error: reuse of function argument name

    if (x) {
        int x = 7;  // allowed, but bad
        // ...
    }
}
```

Reuse of a member name as a local variable:

```cpp
struct S {
    int m;
    void f(int x);
};

void S::f(int x)
{
    m = 7;    // assign to member
    if (x) {
        int m = 9;
        // ...
        m = 99; // assign to local variable
        // ...
    }
}
```

```cpp
struct B {
    void f(int);
};

struct D : B {
    void f(double);
    using B::f;
};
```

**enforcement**
- Flag reuse of a name in nested local scopes.
- Flag reuse of a member name as a local variable in a member function.
- Flag reuse of a global name as a local variable or a member name.
- Flag reuse of a base class member name in a derived class (except for function names).

---

### [ES.20] Always initialize an object

**reason**
Avoid used-before-set errors and their associated undefined behavior. Simplify refactoring.

**code sample**
```cpp
void use(int arg)
{
    int i;   // bad: uninitialized variable
    // ...
    i = 7;   // initialize i
}

void use(int arg)   // OK
{
    int i = 7;   // OK: initialized
    string s;    // OK: default initialized
    // ...
}
```

```cpp
widget i;    // "widget" a type that's expensive to initialize
widget j;

if (cond) {  // bad: i and j are initialized "late"
    i = f1();
    j = f2();
}
else {
    i = f3();
    j = f4();
}
```

Better, use structured bindings (C++17):

```cpp
pair<widget, widget> make_related_widgets(bool x)
{
    return (x) ? {f1(), f2()} : {f3(), f4()};
}

auto [i, j] = make_related_widgets(cond);    // C++17
```

Or use a lambda:

```cpp
auto [i, j] = [x] { return (x) ? pair{f1(), f2()} : pair{f3(), f4()} }();    // C++17
```

This rule covers data members:

```cpp
class X {
public:
    X(int i, int ci) : m2{i}, cm2{ci} {}
    // ...

private:
    int m1 = 7;
    int m2;
    int m3;

    const int cm1 = 7;
    const int cm2;
    const int cm3;
};
```

The compiler will flag the uninitialized `cm3` because it is a `const`, but it will not catch the lack of initialization of `m3`.

```cpp
constexpr int max = 8 * 1024;
int buf[max];         // OK, but suspicious: uninitialized
f.read(buf, max);

constexpr int max = 8 * 1024;
int buf[max] = {};   // zero all elements; better in some situations
f.read(buf, max);
```

Use a lambda as an initializer to avoid an uninitialized variable:

```cpp
error_code ec;
Value v = [&] {
    auto p = get_value();   // get_value() returns a pair<error_code, Value>
    ec = p.first;
    return p.second;
}();
```

**enforcement**
- Flag every uninitialized variable. Don't flag variables of user-defined types with default constructors.
- Check that an uninitialized buffer is written into *immediately* after declaration.

---

### [ES.21] Don't introduce a variable (or constant) before you need to use it

**reason**
Readability. To limit the scope in which the variable can be used.

**code example [bad]**
```cpp
int x = 7;
// ... no use of x here ...
++x;
```

**enforcement**
- Flag declarations that are distant from their first use.

---

### [ES.22] Don't declare a variable until you have a value to initialize it with

**reason**
Readability. Limit the scope in which a variable can be used. Don't risk used-before-set.

**code example [bad]**
```cpp
string s;
// ... no use of s here ...
s = "what a waste";
```

```cpp
SomeLargeType var;  // Hard-to-read CaMeLcAsEvArIaBlE

if (cond)   // some non-trivial condition
    Set(&var);
else if (cond2 || !cond3) {
    var = Set2(3.14);
}
else {
    var = 0;
    for (auto& e : something)
        var += e;
}

// use var; that this isn't done too early can be enforced statically with only control flow
```

**enforcement**
- Flag declarations with default initialization that are assigned to before they are first read.
- Flag any complicated computation after an uninitialized variable and before its use.

---

### [ES.23] Prefer the `{}`-initializer syntax

**reason**
Prefer `{}`. The rules for `{}` initialization are simpler, more general, less ambiguous, and safer than for other forms of initialization.

**code sample**
```cpp
int x {f(99)};
int y = x;
vector<int> v = {1, 2, 3, 4, 5, 6};
```

For containers, there is a tradition for using `{...}` for a list of elements and `(...)` for sizes:

```cpp
vector<int> v1(10);    // vector of 10 elements with the default value 0
vector<int> v2{10};    // vector of 1 element with the value 10

vector<int> v3(1, 2);  // vector of 1 element with the value 2
vector<int> v4{1, 2};  // vector of 2 elements with the values 1 and 2
```

`{}`-initializers do not allow narrowing conversions:

```cpp
int x {7.9};   // error: narrowing
int y = 7.9;   // OK: y becomes 7. Hope for a compiler warning
int z {gsl::narrow_cast<int>(7.9)};    // OK: you asked for it
```

`{}` initialization can be used for nearly all initialization:

```cpp
auto p = new vector<int> {1, 2, 3, 4, 5};   // initialized vector
D::D(int a, int b) :m{a, b} {   // member initializer (e.g., m might be a pair)
    // ...
};
X var {};   // initialize var to be empty
struct S {
    int m {7};   // default initializer for a member
    // ...
};
```

C++17 rules:

```cpp
auto x1 {7};        // x1 is an int with the value 7
auto x2 = {7};      // x2 is an initializer_list<int> with an element 7

auto x11 {7, 8};    // error: two initializers
auto x22 = {7, 8};  // x22 is an initializer_list<int> with elements 7 and 8
```

`={}` gives copy initialization whereas `{}` gives direct initialization:

```cpp
struct Z { explicit Z() {} };

Z z1{};     // OK: direct initialization, so we use explicit constructor
Z z2 = {};  // error: copy initialization, so we cannot use the explicit constructor
```

```cpp
template<typename T>
void f()
{
    T x1(1);    // T initialized with 1
    T x0();     // bad: function declaration (often a mistake)

    T y1 {1};   // T initialized with 1
    T y0 {};    // default initialized T
    // ...
}
```

**enforcement**
- Flag uses of `=` to initialize arithmetic types where narrowing occurs.
- Flag uses of `()` initialization syntax that are actually declarations.

---

### [ES.24] Use a `unique_ptr<T>` to hold pointers

**reason**
Using `std::unique_ptr` is the simplest way to avoid leaks. It is reliable, it makes the type system do much of the work to validate ownership safety.

**code sample**
```cpp
void use(bool leak)
{
    auto p1 = make_unique<int>(7);   // OK
    int* p2 = new int{7};            // bad: might leak
    // ... no assignment to p2 ...
    if (leak) return;
    // ... no assignment to p2 ...
    vector<int> v(7);
    v.at(7) = 0;                    // exception thrown
    delete p2;                      // too late to prevent leaks
    // ...
}
```

**enforcement**
- Look for raw pointers that are targets of `new`, `malloc()`, or functions that might return such pointers.

---

### [ES.25] Declare an object `const` or `constexpr` unless you want to modify its value later on

**reason**
That way you can't change the value by mistake. That way might offer the compiler optimization opportunities.

**code example [good]**
```cpp
void f(int n)
{
    const int bufmax = 2 * n + 2;  // good: we can't change bufmax by accident
    int xmax = n;                  // suspicious: is xmax intended to change?
    // ...
}
```

**enforcement**
- Look to see if a variable is actually mutated, and flag it if not.

---

### [ES.26] Don't use a variable for two unrelated purposes

**reason**
Readability and safety.

**code example [bad]**
```cpp
void use()
{
    int i;
    for (i = 0; i < 20; ++i) { /* ... */ }
    for (i = 0; i < 200; ++i) { /* ... */ } // bad: i recycled
}
```

**code sample**
```cpp
void write_to_file()
{
    std::string buffer;             // to avoid reallocations on every loop iteration
    for (auto& o : objects) {
        // First part of the work.
        generate_first_string(buffer, o);
        write_to_file(buffer);

        // Second part of the work.
        generate_second_string(buffer, o);
        write_to_file(buffer);

        // etc...
    }
}
```

**enforcement**
- Flag recycled variables.

---

### [ES.27] Use `std::array` or `stack_array` for arrays on the stack

**reason**
They are readable and don't implicitly convert to pointers. They are not confused with non-standard extensions of built-in arrays.

**code example [bad]**
```cpp
const int n = 7;
int m = 9;

void f()
{
    int a1[n];
    int a2[m];   // error: not ISO C++
    // ...
}
```

**code example [good]**
```cpp
const int n = 7;
int m = 9;

void f()
{
    array<int, n> a1;
    stack_array<int> a2(m);
    // ...
}
```

**enforcement**
- Flag arrays with non-constant bounds (C-style VLAs).
- Flag arrays with non-local constant bounds.

---

### [ES.28] Use lambdas for complex initialization, especially of `const` variables

**reason**
It nicely encapsulates local initialization, including cleaning up scratch variables needed only for the initialization, without needing to create a needless non-local yet non-reusable function.

**code example [bad]**
```cpp
widget x;   // should be const, but:
for (auto i = 2; i <= N; ++i) {          // this could be some
    x += some_obj.do_something_with(i);  // arbitrarily long code
}                                        // needed to initialize x
// from here, x should be const, but we can't say so in code in this style
```

**code example [good]**
```cpp
const widget x = [&] {
    widget val;                                // assume that widget has a default constructor
    for (auto i = 2; i <= N; ++i) {            // this could be some
        val += some_obj.do_something_with(i);  // arbitrarily long code
    }                                          // needed to initialize x
    return val;
}();
```

**enforcement**
- Hard. At best a heuristic. Look for an uninitialized variable followed by a loop assigning to it.

---

### [ES.30] Don't use macros for program text manipulation

**reason**
Macros are a major source of bugs. Macros don't obey the usual scope and type rules. Macros ensure that the human reader sees something different from what the compiler sees.

**code example [bad]**
```cpp
#define Case break; case   /* BAD */
```

```cpp
#define CAT(a, b) a ## b
#define STRINGIFY(a) #a

void f(int x, int y)
{
    string CAT(x, y) = "asdf";   // BAD: hard for tools to handle (and ugly)
    string sx2 = STRINGIFY(x);
    // ...
}
```

Workarounds for low-level string manipulation:

```cpp
enum E { a, b };

template<int x>
constexpr const char* stringify()
{
    switch (x) {
    case a: return "a";
    case b: return "b";
    }
}

void f()
{
    string s1 = stringify<a>();
    string s2 = stringify<b>();
    // ...
}
```

**enforcement**
- Scream when you see a macro that isn't just used for source control (e.g., `#ifdef`).

---

### [ES.31] Don't use macros for constants or "functions"

**reason**
Macros are a major source of bugs. Macros don't obey the usual scope and type rules.

**code example [bad]**
```cpp
#define PI 3.14
#define SQUARE(a, b) (a * b)
```

Better:

```cpp
constexpr double pi = 3.14;
template<typename T> T square(T a, T b) { return a * b; }
```

**enforcement**
- Scream when you see a macro that isn't just used for source control (e.g., `#ifdef`).

---

### [ES.32] Use `ALL_CAPS` for all macro names

**reason**
Convention. Readability. Distinguishing macros.

**code example [bad]**
```cpp
#define forever for (;;)   /* very BAD */

#define FOREVER for (;;)   /* Still evil, but at least visible to humans */
```

**enforcement**
- Scream when you see a lower case macro.

---

### [ES.33] If you must use macros, give them unique names

**reason**
Macros do not obey scope rules.

**code sample**
```cpp
#define MYCHAR        /* BAD, will eventually clash with someone else's MYCHAR*/

#define ZCORP_CHAR    /* Still evil, but less likely to clash */
```

**enforcement**
- Warn against short macro names.

---

### [ES.34] Don't define a (C-style) variadic function

**reason**
Not type safe. Requires messy cast-and-macro-laden code to get working right.

**code example [bad]**
```cpp
#include <cstdarg>

// "severity" followed by a zero-terminated list of char*s; write the C-style strings to cerr
void error(int severity ...)
{
    va_list ap;             // a magic type for holding arguments
    va_start(ap, severity); // arg startup: "severity" is the first argument of error()

    for (;;) {
        // treat the next var as a char*; no checking: a cast in disguise
        char* p = va_arg(ap, char*);
        if (!p) break;
        cerr << p << ' ';
    }

    va_end(ap);             // arg cleanup (don't forget this)

    cerr << '\n';
    if (severity) exit(severity);
}

void use()
{
    error(7, "this", "is", "an", "error", nullptr);
    error(7); // crash
    error(7, "this", "is", "an", "error");  // crash
    const char* is = "is";
    string an = "an";
    error(7, "this", is, an, "error"); // crash
}
```

**code example [good]**
```cpp
#include <iostream>

void error(int severity)
{
    std::cerr << '\n';
    std::exit(severity);
}

template<typename T, typename... Ts>
constexpr void error(int severity, T head, Ts... tail)
{
    std::cerr << head;
    error(severity, tail...);
}

void use()
{
    error(7); // No crash!
    error(5, "this", "is", "not", "an", "error"); // No crash!

    std::string an = "an";
    error(7, "this", "is", "not", an, "error"); // No crash!

    error(5, "oh", "no", nullptr); // Compile error! No need for nullptr.
}
```

**enforcement**
- Flag definitions of C-style variadic functions.
- Flag `#include <cstdarg>` and `#include <stdarg.h>`.

---

### [ES.40] Avoid complicated expressions

**reason**
Complicated expressions are error-prone.

**code sample**
```cpp
// bad: assignment hidden in subexpression
while ((c = getc()) != -1)

// bad: two non-local variables assigned in sub-expressions
while ((cin >> c1, cin >> c2), c1 == c2)

// better, but possibly still too complicated
for (char c1, c2; cin >> c1 >> c2 && c1 == c2;)

// OK: if i and j are not aliased
int x = ++i + ++j;

// OK: if i != j and i != k
v[i] = v[j] + v[k];

// bad: multiple assignments "hidden" in subexpressions
x = a + (b = f()) + (c = g()) * 7;

// bad: relies on commonly misunderstood precedence rules
x = a & b + c * d && e ^ f == 7;

// bad: undefined behavior
x = x++ + x++ + ++x;
```

A programmer should know and use the basic rules for expressions:

```cpp
x = k * y + z;             // OK

auto t1 = k * y;           // bad: unnecessarily verbose
x = t1 + z;

if (0 <= x && x < max)   // OK

auto t1 = 0 <= x;        // bad: unnecessarily verbose
auto t2 = x < max;
if (t1 && t2)            // ...
```

**enforcement**
- Tricky. Things to consider: side effects on multiple non-local variables, writes to aliased variables, more than N operators, reliance of subtle precedence rules, uses undefined behavior.

---

### [ES.41] If in doubt about operator precedence, parenthesize

**reason**
Avoid errors. Readability. Not everyone has the operator table memorized.

**code sample**
```cpp
const unsigned int flag = 2;
unsigned int a = flag;

if (a & flag != 0)  // bad: means a&(flag != 0)

if ((a & flag) != 0)  // OK: works as intended
```

You should know enough not to need parentheses for:

```cpp
if (a < 0 || a <= max) {
    // ...
}
```

**enforcement**
- Flag combinations of bitwise-logical operators and other operators.
- Flag assignment operators not as the leftmost operator.

---

### [ES.42] Keep use of pointers simple and straightforward

**reason**
Complicated pointer manipulation is a major source of errors. Use `gsl::span` instead. Pointer arithmetic is fragile and easy to get wrong.

**code example [bad]**
```cpp
void f(int* p, int count)
{
    if (count < 2) return;

    int* q = p + 1;    // BAD

    ptrdiff_t d;
    int n;
    d = (p - &n);      // OK
    d = (q - p);       // OK

    int n = *p++;      // BAD

    if (count < 6) return;

    p[4] = 1;          // BAD

    p[count - 1] = 2;  // BAD

    use(&p[0], 3);     // BAD
}
```

**code example [good]**
```cpp
void f(span<int> a) // BETTER: use span in the function declaration
{
    if (a.size() < 2) return;

    int n = a[0];      // OK

    span<int> q = a.subspan(1); // OK

    if (a.size() < 6) return;

    a[4] = 1;          // OK

    a[a.size() - 1] = 2;  // OK

    use(a.data(), 3);  // OK
}
```

```cpp
void f(array<int, 10> a, int pos)
{
    a[pos / 2] = 1; // BAD
    a[pos - 1] = 2; // BAD
    a[-1] = 3;    // BAD -- no replacement, just don't do this
    a[10] = 4;    // BAD -- no replacement, just don't do this
}
```

Use a `span`:

```cpp
void f1(span<int, 10> a, int pos) // A1: Change parameter type to use span
{
    a[pos / 2] = 1; // OK
    a[pos - 1] = 2; // OK
}

void f2(array<int, 10> arr, int pos) // A2: Add local span and use that
{
    span<int> a = {arr.data(), pos};
    a[pos / 2] = 1; // OK
    a[pos - 1] = 2; // OK
}
```

Use `at()`:

```cpp
void f3(array<int, 10> a, int pos) // ALTERNATIVE B: Use at() for access
{
    at(a, pos / 2) = 1; // OK
    at(a, pos - 1) = 2; // OK
}
```

```cpp
void f()
{
    int arr[COUNT];
    for (int i = 0; i < COUNT; ++i)
        arr[i] = i; // BAD, cannot use non-constant indexer
}
```

Use `span` and range-`for`:

```cpp
void f1a()
{
     int arr[COUNT];
     span<int, COUNT> av = arr;
     int i = 0;
     for (auto& e : av)
         e = i++;
}
```

Tooling can offer rewrites:

```cpp
static int a[10];

void f(int i, int j)
{
    a[i + j] = 12;      // BAD, could be rewritten as ...
    at(a, i + j) = 12;  // OK -- bounds-checked
}
```

Turning an array into a pointer removes opportunities for checking:

```cpp
void g(int* p);

void f()
{
    int a[5];
    g(a);        // BAD: are we trying to pass an array?
    g(&a[0]);    // OK: passing one object
}

void g1(span<int> av); // BETTER: get g() changed.

void f2()
{
    int a[5];
    span<int> av = a;

    g(av.data(), av.size());   // OK, if you have no choice
    g1(a);                     // OK -- no decay here, instead use implicit span ctor
}
```

**enforcement**
- Flag any arithmetic operation on an expression of pointer type that results in a value of pointer type.
- Flag any indexing expression on an expression or variable of array type where the indexer is not a compile-time constant expression.
- Flag any expression that would rely on implicit conversion of an array type to a pointer type.

---

### [ES.43] Avoid expressions with undefined order of evaluation

**reason**
You have no idea what such code does. Portability.

**code sample**
```cpp
v[i] = ++i;   //  the result is undefined
```

A good rule of thumb is that you should not read a value twice in an expression where you write to it.

**enforcement**
- Can be detected by a good analyzer.

---

### [ES.44] Don't depend on order of evaluation of function arguments

**reason**
Because that order is unspecified.

**code sample**
```cpp
int i = 0;
f(++i, ++i);
```

Before C++17, the behavior is undefined. Since C++17, this code does not have undefined behavior, but it is still not specified which argument is evaluated first.

```cpp
f1()->m(f2());          // m(f1(), f2())
cout << f1() << f2();   // operator<<(operator<<(cout, f1()), f2())
```

In C++17, these examples work as expected (left to right).

```cpp
f1() = f2();    // undefined behavior in C++14; in C++17, f2() is evaluated before f1()
```

**enforcement**
- Can be detected by a good analyzer.

---

### [ES.45] Avoid "magic constants"; use symbolic constants

**reason**
Unnamed constants embedded in expressions are easily overlooked and often hard to understand.

**code sample**
```cpp
for (int m = 1; m <= 12; ++m)   // don't: magic constant 12
    cout << month[m] << '\n';
```

Better:

```cpp
// months are indexed 1..12
constexpr int first_month = 1;
constexpr int last_month = 12;

for (int m = first_month; m <= last_month; ++m)   // better
    cout << month[m] << '\n';
```

Better still:

```cpp
for (auto m : month)
    cout << m << '\n';
```

**enforcement**
- Flag literals in code. Give a pass to `0`, `1`, `nullptr`, `\n`, `""`, and others on a positive list.

---

### [ES.46] Avoid lossy (narrowing, truncating) arithmetic conversions

**reason**
A narrowing conversion destroys information, often unexpectedly so.

**code example [bad]**
```cpp
double d = 7.9;
int i = d;    // bad: narrowing: i becomes 7
i = (int) d;  // bad: we're going to claim this is still not explicit enough

void f(int x, long y, double d)
{
    char c1 = x;   // bad: narrowing
    char c2 = y;   // bad: narrowing
    char c3 = d;   // bad: narrowing
}
```

**code example [good]**
```cpp
i = gsl::narrow_cast<int>(d);   // OK (you asked for it): narrowing: i becomes 7
i = gsl::narrow<int>(d);        // OK: throws narrowing_error
```

Lossy arithmetic casts:

```cpp
double d = -7.9;
unsigned u = 0;

u = d;                               // bad: narrowing
u = gsl::narrow_cast<unsigned>(d);   // OK (you asked for it): u becomes 4294967289
u = gsl::narrow<unsigned>(d);        // OK: throws narrowing_error
```

Contextual conversions to bool are not narrowing:

```cpp
if (ptr) do_something(*ptr);   // OK: ptr is used as a condition
bool b = ptr;                  // bad: narrowing
```

**enforcement**
- Flag all floating-point to integer conversions.
- Flag all `long`->`char`.
- Consider narrowing conversions for function arguments especially suspect.

---

### [ES.47] Use `nullptr` rather than `0` or `NULL`

**reason**
Readability. Minimize surprises: `nullptr` cannot be confused with an `int`.

**code example [bad]**
```cpp
void f(int);
void f(char*);
f(0);         // call f(int)
f(nullptr);   // call f(char*)
```

**enforcement**
- Flag uses of `0` and `NULL` for pointers.

---

### [ES.48] Avoid casts

**reason**
Casts are a well-known source of errors and make some optimizations unreliable.

**code example [bad]**
```cpp
double d = 2;
auto p = (long*)&d;
auto q = (long long*)&d;
cout << d << ' ' << *p << ' ' << *q << '\n';
```

What would you think this fragment prints? The result is at best implementation defined. I got:

`2 0 4611686018427387904`

Adding `*q = 666;` I got:

`3.29048e-321 666 666`

Surprised? It is actually undefined behavior.

**code sample**
Alternatives: Use templates, Use `std::variant`, Rely on well-defined safe implicit conversions, Use `std::ignore =` to ignore `[[nodiscard]]` values.

**enforcement**
- Flag all C-style casts, including to `void`.
- Flag functional style casts using `Type(value)`. Use `Type{value}` instead which is not narrowing.
- Flag identity casts between pointer types, where the source and target types are the same.
- Flag an explicit pointer cast that could be implicit.

---

### [ES.49] If you must use a cast, use a named cast

**reason**
Readability. Error avoidance. Named casts are more specific than a C-style or functional cast, allowing the compiler to catch some errors.

The named casts are: `static_cast`, `const_cast`, `reinterpret_cast`, `dynamic_cast`, `std::move`, `std::forward`, `gsl::narrow_cast`, `gsl::narrow`.

**code example [good]**
```cpp
class B { /* ... */ };
class D { /* ... */ };

template<typename D> D* upcast(B* pb)
{
    D* pd0 = pb;                        // error: no implicit conversion from B* to D*
    D* pd1 = (D*)pb;                    // legal, but what is done?
    D* pd2 = static_cast<D*>(pb);       // error: D is not derived from B
    D* pd3 = reinterpret_cast<D*>(pb);  // OK: on your head be it!
    D* pd4 = dynamic_cast<D*>(pb);      // OK: return nullptr
    // ...
}
```

When converting between types with no information loss, brace initialization might be used instead:

```cpp
double d {some_float};
int64_t i {some_int32};
```

`reinterpret_cast` can be essential, but the essential uses are not type safe:

```cpp
auto p = reinterpret_cast<Device_register>(0x800);  // inherently dangerous
```

**enforcement**
- Flag all C-style casts, including to `void`.
- Flag functional style casts using `Type(value)`.
- The type profile bans `reinterpret_cast`.
- The type profile warns when using `static_cast` between arithmetic types.

---

### [ES.50] Don't cast away `const`

**reason**
It makes a lie out of `const`. If the variable is actually declared `const`, modifying it results in undefined behavior.

**code example [bad]**
```cpp
void f(const int& x)
{
    const_cast<int&>(x) = 42;   // BAD
}

static int i = 0;
static const int j = 0;

f(i); // silent side effect
f(j); // undefined behavior
```

**code example [bad]**

Avoiding code duplication between const and non-const accessors:

```cpp
class Foo {
public:
    // BAD, duplicates logic
    Bar& get_bar()
    {
        /* complex logic around getting a non-const reference to my_bar */
    }

    const Bar& get_bar() const
    {
        /* same complex logic around getting a const reference to my_bar */
    }
private:
    Bar my_bar;
};
```

Instead, prefer a template helper that deduces `const`:

```cpp
class Foo {
public:                         // good
          Bar& get_bar()       { return get_bar_impl(*this); }
    const Bar& get_bar() const { return get_bar_impl(*this); }
private:
    Bar my_bar;

    template<class T>           // good, deduces whether T is const or non-const
    static auto& get_bar_impl(T& t)
        { /* the complex logic around getting a possibly-const reference to my_bar */ }
};
```

Caching/memoization â€” prefer `mutable`:

```cpp
class X {   // better solution
public:
    int get_val(int x) const
    {
        auto p = cache.find(x);
        if (p.first) return p.second;
        int val = compute(x);
        cache.set(x, val);
        return val;
    }
    // ...
private:
    mutable Cache cache;
};
```

**enforcement**
- Flag `const_cast`s.
- This rule is part of the type-safety profile.

---

### [ES.55] Avoid the need for range checking

**reason**
Constructs that cannot overflow do not overflow (and usually run faster).

**code sample**
```cpp
for (auto& x : v)      // print all elements of v
    cout << x << '\n';

auto p = find(v, x);   // find x in v
```

**enforcement**
- Look for explicit range checks and heuristically suggest alternatives.

---

### [ES.56] Write `std::move()` only when you need to explicitly move an object to another scope

**reason**
We move, rather than copy, to avoid duplication and for improved performance. A move typically leaves behind an empty object, which can be surprising or even dangerous.

**code example [good]**
```cpp
void sink(X&& x);   // sink takes ownership of x

void user()
{
    X x;
    // error: cannot bind an lvalue to a rvalue reference
    sink(x);
    // OK: sink takes the contents of x, x must now be assumed to be empty
    sink(std::move(x));

    // ...

    // probably a mistake
    use(x);
}
```

```cpp
void f()
{
    string s1 = "supercalifragilisticexpialidocious";

    string s2 = s1;             // ok, takes a copy
    assert(s1 == "supercalifragilisticexpialidocious");  // ok

    // bad, if you want to keep using s1's value
    string s3 = move(s1);

    // bad, assert will likely fail, s1 likely changed
    assert(s1 == "supercalifragilisticexpialidocious");
}
```

```cpp
void sink(unique_ptr<widget> p);  // pass ownership of p to sink()

void f()
{
    auto w = make_unique<widget>();
    // ...
    sink(std::move(w));               // ok, give to sink()
    // ...
    sink(w);    // Error: unique_ptr is carefully designed so that you cannot copy it
}
```

Never write `return move(local_variable);`:

```cpp
vector<int> make_vector()
{
    vector<int> result;
    // ... load result with data
    return std::move(result);       // bad; just write "return result;"
}
```

Never write `move` on a returned value:

```cpp
vector<int> v = std::move(make_vector());   // bad; the std::move is entirely redundant
```

Forwarding references vs rvalue references:

```cpp
void mover(X&& x)
{
    call_something(std::move(x));         // ok
    call_something(std::forward<X>(x));   // bad, don't std::forward an rvalue reference
    call_something(x);                    // suspicious, why not std::move?
}

template<class T>
void forwarder(T&& t)
{
    call_something(std::move(t));         // bad, don't std::move a forwarding reference
    call_something(std::forward<T>(t));   // ok
    call_something(t);                    // suspicious, why not std::forward?
}
```

**enforcement**
- Flag use of `std::move(x)` where `x` is an rvalue or the language will already treat it as an rvalue.
- Flag functions taking an `S&&` parameter if there is no `const S&` overload.
- Flag a `std::move`d argument passed to a parameter, except when the parameter type is an `X&&` rvalue reference or the type is move-only and the parameter is passed by value.
- Flag when `std::move` is applied to a forwarding reference. Use `std::forward` instead.
- Flag when `std::forward` is applied to an rvalue reference. Use `std::move` instead.
- Flag when an object is potentially moved from and the next operation is a `const` operation.

---

### [ES.60] Avoid `new` and `delete` outside resource management functions

**reason**
Direct resource management in application code is error-prone and tedious. This is also known as the rule of "No naked `new`!"

**code example [bad]**
```cpp
void f(int n)
{
    auto p = new X[n];   // n default constructed Xs
    // ...
    delete[] p;
}
```

There can be code in the `...` part that causes the `delete` never to happen.

**enforcement**
- Flag naked `new`s and naked `delete`s.

---

### [ES.61] Delete arrays using `delete[]` and non-arrays using `delete`

**reason**
That's what the language requires, and mismatches can lead to resource release errors and/or memory corruption.

**code example [bad]**
```cpp
void f(int n)
{
    auto p = new X[n];   // n default constructed Xs
    // ...
    delete p;   // error: just delete the object p, rather than delete the array p[]
}
```

**enforcement**
- Flag mismatched `new` and `delete` if they are in the same scope.
- Flag mismatched `new` and `delete` if they are in a constructor/destructor pair.

---

### [ES.62] Don't compare pointers into different arrays

**reason**
The result of doing so is undefined.

**code example [bad]**
```cpp
void f()
{
    int a1[7];
    int a2[9];
    if (&a1[5] < &a2[7]) {}       // bad: undefined
    if (0 < &a1[5] - &a2[7]) {}   // bad: undefined
}
```

**enforcement**
- ???

---

### [ES.63] Don't slice

**reason**
Slicing -- copying only part of an object using assignment or initialization -- most often leads to errors because the object was meant to be considered as a whole.

**code example [bad]**
```cpp
class Shape { /* ... */ };
class Circle : public Shape { /* ... */ Point c; int r; };

Circle c { {0, 0}, 42 };
Shape s {c};    // copy construct only the Shape part of Circle
s = c;          // or copy assign only the Shape part of Circle

void assign(const Shape& src, Shape& dest)
{
    dest = src;
}
Circle c2 { {1, 1}, 43 };
assign(c, c2);   // oops, not the whole state is transferred
assert(c == c2); // if we supply copying, we should also provide comparison,
                 // but this will likely return false
```

If you mean to slice, define an explicit operation:

```cpp
class Smiley : public Circle {
    public:
    Circle copy_circle();
    // ...
};

Smiley sm { /* ... */ };
Circle c1 {sm};  // ideally prevented by the definition of Circle
Circle c2 {sm.copy_circle()};
```

**enforcement**
- Warn against slicing.

---

### [ES.64] Use the `T{e}` notation for construction

**reason**
The `T{e}` construction syntax makes it explicit that construction is desired. The `T{e}` construction syntax doesn't allow narrowing. `T{e}` is the only safe and general expression for constructing a value of type `T` from an expression `e`.

**code sample**
```cpp
void use(char ch, int i, double d, char* p, long long lng)
{
    int x1 = int{ch};     // OK, but redundant
    int x2 = int{d};      // error: double->int narrowing; use a cast if you need to
    int x3 = int{p};      // error: pointer to->int; use a reinterpret_cast if you really need to
    int x4 = int{lng};    // error: long long->int narrowing; use a cast if you need to

    int y1 = int(ch);     // OK, but redundant
    int y2 = int(d);      // bad: double->int narrowing; use a cast if you need to
    int y3 = int(p);      // bad: pointer to->int; use a reinterpret_cast if you really need to
    int y4 = int(lng);    // bad: long long->int narrowing; use a cast if you need to

    int z1 = (int)ch;     // OK, but redundant
    int z2 = (int)d;      // bad: double->int narrowing; use a cast if you need to
    int z3 = (int)p;      // bad: pointer to->int; use a reinterpret_cast if you really need to
    int z4 = (int)lng;    // bad: long long->int narrowing; use a cast if you need to
}
```

When unambiguous, the `T` can be left out:

```cpp
complex<double> f(complex<double>);

auto z = f({2*pi, 1});
```

`std::vector` exception:

```cpp
vector<string> vs {10};                           // ten empty strings
vector<int> vi1 {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};  // ten elements 1..10
vector<int> vi2 {10};                             // one element with the value 10

vector<int> v3(10); // ten elements with value 0
```

We can define a type to represent the number of elements:

```cpp
struct Count { int n; };

template<typename T>
class Vector {
public:
    Vector(Count n);                     // n default-initialized elements
    Vector(initializer_list<T> init);    // init.size() elements
    // ...
};

Vector<int> v1{10};
Vector<int> v2{Count{10}};
Vector<Count> v3{Count{10}};    // yes, there is still a very minor problem
```

**enforcement**
- Flag the C-style `(T)e` and functional-style `T(e)` casts.

---

### [ES.65] Don't dereference an invalid pointer

**reason**
Dereferencing an invalid pointer, such as `nullptr`, is undefined behavior, typically leading to immediate crashes, wrong results, or memory corruption. By pointer here we mean any indirection to an object, including equivalently an iterator or view.

**code example [bad]**
```cpp
void f()
{
    int x = 0;
    int* p = &x;

    if (condition()) {
        int y = 0;
        p = &y;
    } // invalidates p

    *p = 42;            // BAD, p might be invalid if the branch was taken
}
```

```cpp
void f1()
{
    int x = 0;
    int* p = &x;

    int y = 0;
    if (condition()) {
        p = &y;
    }

    *p = 42;            // OK, p points to x or y and both are still in scope
}
```

Dealing with nullptr:

```cpp
void f(int* p)
{
    int x = *p; // BAD: how do we know that p is valid?
}

void f1(int* p) // deal with nullptr
{
    if (!p) {
        // deal with nullptr (allocate, return, throw, make p point to something, whatever)
    }
    int x = *p;
}

void f2(int* p) // state that p is not supposed to be nullptr
{
    assert(p);
    int x = *p;
}

void f3(int* p) // state that p is not supposed to be nullptr
    [[expects: p]]
{
    int x = *p;
}

void f(not_null<int*> p)
{
    int x = *p;
}
```

Use-after-delete:

```cpp
void f(int* p)  // old code, doesn't use owner
{
    delete p;
}

void g()        // old code: uses naked new
{
    auto q = new int{7};
    f(q);
    int x = *q; // BAD: dereferences invalid pointer
}
```

Iterator/pointer invalidation after container mutation:

```cpp
void f()
{
    vector<int> v(10);
    int* p = &v[5];
    v.push_back(99); // could reallocate v's elements
    int x = *p; // BAD: dereferences potentially invalid pointer
}
```

**enforcement**
- Flag a dereference of a pointer that points to an object that has gone out of scope.
- Flag a dereference of a pointer that might have been invalidated by assigning a `nullptr`.
- Flag a dereference of a pointer that might have been invalidated by a `delete`.
- Flag a dereference to a pointer to a container element that might have been invalidated by dereference.

---

### [ES.70] Prefer a `switch`-statement to an `if`-statement when there is a choice

**reason**
Readability. Efficiency: A `switch` compares against constants and is usually better optimized. A `switch` enables some heuristic consistency checking.

**code example [good]**
```cpp
void use(int n)
{
    switch (n) {   // good
    case 0:
        // ...
        break;
    case 7:
        // ...
        break;
    default:
        // ...
        break;
    }
}
```

rather than:

```cpp
void use2(int n)
{
    if (n == 0)   // bad: if-then-else chain comparing against a set of constants
        // ...
    else if (n == 7)
        // ...
}
```

**enforcement**
- Flag `if`-`then`-`else` chains that check against constants (only).

---

### [ES.71] Prefer a range-`for`-statement to a `for`-statement when there is a choice

**reason**
Readability. Error prevention. Efficiency.

**code sample**
```cpp
for (gsl::index i = 0; i < v.size(); ++i)   // bad
    cout << v[i] << '\n';

for (auto p = v.begin(); p != v.end(); ++p)   // bad
    cout << *p << '\n';

for (auto& x : v)    // OK
    cout << x << '\n';

for (gsl::index i = 1; i < v.size(); ++i) // touches two elements: can't be a range-for
    cout << v[i] + v[i - 1] << '\n';

for (gsl::index i = 0; i < v.size(); ++i) // possible side effect: can't be a range-for
    cout << f(v, &v[i]) << '\n';

for (gsl::index i = 0; i < v.size(); ++i) { // body messes with loop variable: can't be a range-for
    if (i % 2 != 0)
        cout << v[i] << '\n'; // output odd elements
}
```

Don't use expensive copies of the loop variable:

```cpp
for (string s : vs) // ...   // copies each element

for (string& s : vs) // ...  // better

for (const string& s : vs) // ...  // better still, if the loop variable isn't modified
```

**enforcement**
- Look at loops, if a traditional loop just looks at each element of a sequence, and there are no side effects, rewrite the loop to a ranged-`for` loop.

---

### [ES.72] Prefer a `for`-statement to a `while`-statement when there is an obvious loop variable

**reason**
Readability: the complete logic of the loop is visible "up front". The scope of the loop variable can be limited.

**code example [good]**
```cpp
for (gsl::index i = 0; i < vec.size(); i++) {
    // do work
}
```

**code example [bad]**
```cpp
int i = 0;
while (i < vec.size()) {
    // do work
    i++;
}
```

**enforcement**
- ???

---

### [ES.73] Prefer a `while`-statement to a `for`-statement when there is no obvious loop variable

**reason**
Readability.

**code sample**
```cpp
int events = 0;
for (; wait_for_event(); ++events) {  // bad, confusing
    // ...
}
```

Better:

```cpp
int events = 0;
while (wait_for_event()) {      // better
    ++events;
    // ...
}
```

**enforcement**
- Flag actions in `for`-initializers and `for`-increments that do not relate to the `for`-condition.

---

### [ES.74] Prefer to declare a loop variable in the initializer part of a `for`-statement

See ES.6.

**enforcement**
- See ES.6.

---

### [ES.75] Avoid `do`-statements

**reason**
Readability, avoidance of errors. The termination condition is at the end (where it can be overlooked) and the condition is not checked the first time through.

**code example [good]**
```cpp
int x;
do {
    cin >> x;
    // ...
} while (x < 0);
```

**enforcement**
- Flag `do`-statements.

---

### [ES.76] Avoid `goto`

**reason**
Readability, avoidance of errors. There are better control structures for humans; `goto` is for machine generated code.

**code sample**

Breaking out of a nested loop (exception to the rule):

```cpp
for (int i = 0; i < imax; ++i)
    for (int j = 0; j < jmax; ++j) {
        if (a[i][j] > elem_max) goto finished;
        // ...
    }
finished:
// ...
```

**code example [bad]**
```cpp
void f()
{
    // ...
        goto exit;
    // ...
        goto exit;
    // ...
exit:
    // ... common cleanup code ...
}
```

This is an ad-hoc simulation of destructors. Declare your resources with handles with destructors that clean up. Consider `gsl::finally()` as a cleaner and more reliable alternative to `goto exit`.

**enforcement**
- Flag `goto`. Better still flag all `goto`s that do not jump from a nested loop to the statement immediately after a nest of loops.

---

### [ES.77] Minimize the use of `break` and `continue` in loops

**reason**
In a non-trivial loop body, it is easy to overlook a `break` or a `continue`. A `break` in a loop has a dramatically different meaning than a `break` in a `switch`-statement.

**code example [good]**
```cpp
switch(x) {
case 1 :
    while (/* some condition */) {
        // ...
    break;
    } // Oops! break switch or break while intended?
case 2 :
    // ...
    break;
}
```

A loop that requires a `break` is a good candidate for a function, in which case the `break` becomes a `return`:

```cpp
//Original code: break inside loop
void use1()
{
    std::vector<T> vec = {/* initialized with some values */};
    T value;
    for (const T item : vec) {
        if (/* some condition*/) {
            value = item;
            break;
        }
    }
    /* then do something with value */
}

//BETTER: create a function and return inside loop
T search(const std::vector<T> &vec)
{
    for (const T &item : vec) {
        if (/* some condition*/) return item;
    }
    return T(); //default value
}

void use2()
{
    std::vector<T> vec = {/* initialized with some values */};
    T value = search(vec);
    /* then do something with value */
}
```

A loop that uses `continue` can equivalently be expressed by an `if`-statement:

```cpp
for (int item : vec) {  // BAD
    if (item%2 == 0) continue;
    if (item == 5) continue;
    if (item > 10) continue;
    /* do something with item */
}

for (int item : vec) {  // GOOD
    if (item%2 != 0 && item != 5 && item <= 10) {
        /* do something with item */
    }
}
```

**enforcement**
- ???

---

### [ES.78] Don't rely on implicit fallthrough in `switch` statements

**reason**
Always end a non-empty `case` with a `break`. Accidentally leaving out a `break` is a fairly common bug.

**code example [bad]**
```cpp
switch (eventType) {
case Information:
    update_status_bar();
    break;
case Warning:
    write_event_log();
    // Bad - implicit fallthrough
case Error:
    display_error_window();
    break;
}
```

Multiple case labels of a single statement is OK:

```cpp
switch (x) {
case 'a':
case 'b':
case 'f':
    do_something(x);
    break;
}
```

Use `[[fallthrough]]` for deliberate fallthrough:

```cpp
switch (eventType) {
case Information:
    update_status_bar();
    break;
case Warning:
    write_event_log();
    [[fallthrough]];
case Error:
    display_error_window();
    break;
}
```

**enforcement**
- Flag all implicit fallthroughs from non-empty `case`s.

---

### [ES.79] Use `default` to handle common cases (only)

**reason**
Code clarity. Improved opportunities for error detection.

**code example [good]**
```cpp
enum E { a, b, c, d };

void f1(E x)
{
    switch (x) {
    case a:
        do_something();
        break;
    case b:
        do_something_else();
        break;
    default:
        take_the_default_action();
        break;
    }
}
```

If you leave out the `default`, a maintainer might assume you intended to handle all cases:

```cpp
void f2(E x)
{
    switch (x) {
    case a:
        do_something();
        break;
    case b:
    case c:
        do_something_else();
        break;
    }
}
```

Did you forget case `d` or deliberately leave it out?

**enforcement**
- Flag `switch`-statements over an enumeration that don't handle all enumerators and do not have a `default`.

---

### [ES.84] Don't try to declare a local variable with no name

**reason**
There is no such thing. What looks like a variable without a name is to the compiler a statement consisting of a temporary that immediately goes out of scope.

**code example [bad]**
```cpp
void f()
{
    lock_guard<mutex>{mx};   // Bad
    // ...
}
```

This declares an unnamed `lock_guard` object that immediately goes out of scope at the point of the semicolon. This can lead to hard-to-find race conditions.

**enforcement**
- Flag statements that are just a temporary.

---

### [ES.85] Make empty statements visible

**reason**
Readability.

**code sample**
```cpp
for (i = 0; i < max; ++i);   // BAD: the empty statement is easily overlooked
v[i] = f(v[i]);

for (auto x : v) {           // better
    // nothing
}
v[i] = f(v[i]);
```

**enforcement**
- Flag empty statements that are not blocks and don't contain comments.

---

### [ES.86] Avoid modifying loop control variables inside the body of raw for-loops

**reason**
The loop control up front should enable correct reasoning about what is happening inside the loop. Modifying loop counters in both the iteration-expression and inside the body of the loop is a perennial source of surprises and bugs.

**code example [bad]**
```cpp
for (int i = 0; i < 10; ++i) {
    // no updates to i -- ok
}

for (int i = 0; i < 10; ++i) {
    //
    if (/* something */) ++i; // BAD
    //
}

bool skip = false;
for (int i = 0; i < 10; ++i) {
    if (skip) { skip = false; continue; }
    //
    if (/* something */) skip = true;  // Better: using two variables for two concepts.
    //
}
```

**enforcement**
- Flag variables that are potentially updated (have a non-`const` use) in both the loop control iteration-expression and the loop body.

---

### [ES.87] Don't add redundant `==` or `!=` to conditions

**reason**
Doing so avoids verbosity and eliminates some opportunities for mistakes.

**code sample**
```cpp
// These all mean "if p is not nullptr"
if (p) { ... }            // good
if (p != 0) { ... }       // redundant !=0, bad: don't use 0 for pointers
if (p != nullptr) { ... } // redundant !=nullptr, not recommended
```

Especially useful when a declaration is used as a condition:

```cpp
if (auto pc = dynamic_cast<Circle*>(ps)) { ... } // execute if ps points to a kind of Circle, good

if (auto pc = dynamic_cast<Circle*>(ps); pc != nullptr) { ... } // not recommended
```

Implicit conversions to bool:

```cpp
for (string s; cin >> s; ) v.push_back(s);
```

Explicit comparison of an integer to `0` is in general not redundant:

```cpp
void f(int i)
{
    if (i)            // suspect
    // ...
    if (i == success) // possibly better
    // ...
}
```

Common beginners error with `strcmp`:

```cpp
if(strcmp(p1, p2)) { ... }   // are the two C-style strings equal? (mistake!)
```

The opposite condition:

```cpp
// These all mean "if p is nullptr"
if (!p) { ... }           // good
if (p == 0) { ... }       // redundant == 0, bad: don't use 0 for pointers
if (p == nullptr) { ... } // redundant == nullptr, not recommended
```

**enforcement**
- Easy, just check for redundant use of `!=` and `==` in conditions.

---

### [ES.100] Don't mix signed and unsigned arithmetic

**reason**
Avoid wrong results.

**code example [bad]**
```cpp
int x = -3;
unsigned int y = 7;

cout << x - y << '\n';  // unsigned result, possibly 4294967286
cout << x + y << '\n';  // unsigned result: 4
cout << x * y << '\n';  // unsigned result, possibly 4294967275
```

**enforcement**
- Compilers already know and sometimes warn.
- (To avoid noise) Do not flag on a mixed signed/unsigned comparison where one of the arguments is `sizeof` or a call to container `.size()` and the other is `ptrdiff_t`.

---

### [ES.101] Use unsigned types for bit manipulation

**reason**
Unsigned types support bit manipulation without surprises from sign bits.

**code sample**
```cpp
unsigned char x = 0b1010'1010;
unsigned char y = ~x;   // y == 0b0101'0101;
```

**enforcement**
- Just about impossible in general because of the use of unsigned subscripts in the standard library.

---

### [ES.102] Use signed types for arithmetic

**reason**
Because most arithmetic is assumed to be signed; `x - y` yields a negative number when `y > x` except in the rare cases where you really want modular arithmetic.

**code sample**
```cpp
template<typename T, typename T2>
T subtract(T x, T2 y)
{
    return x - y;
}

void test()
{
    int s = 5;
    unsigned int us = 5;
    cout << subtract(s, 7) << '\n';       // -2
    cout << subtract(us, 7u) << '\n';     // 4294967294
    cout << subtract(s, 7u) << '\n';      // -2
    cout << subtract(us, 7) << '\n';      // 4294967294
    cout << subtract(s, us + 2) << '\n';  // -2
    cout << subtract(us, s + 2) << '\n';  // 4294967294
}
```

The standard library uses unsigned types for subscripts. The built-in array uses signed types:

```cpp
int a[10];
for (int i = 0; i < 10; ++i) a[i] = i;
vector<int> v(10);
// compares signed to unsigned; some compilers warn, but we should not
for (gsl::index i = 0; i < v.size(); ++i) v[i] = i;

int a2[-2];         // error: negative size

// OK, but the number of ints (4294967294) is so large that we should get an exception
vector<int> v2(-2);
```

**enforcement**
- Flag mixed signed and unsigned arithmetic.
- Flag results of unsigned arithmetic assigned to or printed as signed.
- Flag negative literals (e.g. `-2`) used as container subscripts.

---

### [ES.103] Don't overflow

**reason**
Overflow usually makes your numeric algorithm meaningless. Incrementing a value beyond a maximum value can lead to memory corruption and undefined behavior.

**code example [bad]**
```cpp
int a[10];
a[10] = 7;   // bad, array bounds overflow

for (int n = 0; n <= 10; ++n)
    a[n] = 9;   // bad, array bounds overflow
```

```cpp
int n = numeric_limits<int>::max();
int m = n + 1;   // bad, numeric overflow
```

```cpp
int area(int h, int w) { return h * w; }

auto a = area(10'000'000, 100'000'000);   // bad, numeric overflow
```

**enforcement**
- ???

---

### [ES.104] Don't underflow

**reason**
Decrementing a value beyond a minimum value can lead to memory corruption and undefined behavior.

**code example [bad]**
```cpp
int a[10];
a[-2] = 7;   // bad

int n = 101;
while (n--)
    a[n - 1] = 9;   // bad (twice)
```

**enforcement**
- ???

---

### [ES.105] Don't divide by integer zero

**reason**
The result is undefined and probably a crash.

**code example [bad]**
```cpp
int divide(int a, int b)
{
    // BAD, should be checked (e.g., in a precondition)
    return a / b;
}
```

**code example [good]**
```cpp
int divide(int a, int b)
{
    // good, address via precondition (and replace with contracts once C++ gets them)
    Expects(b != 0);
    return a / b;
}

double divide(double a, double b)
{
    // good, address via using double instead
    return a / b;
}
```

**enforcement**
- Flag division by an integral value that could be zero.

---

### [ES.106] Don't try to avoid negative values by using `unsigned`

**reason**
Choosing `unsigned` implies many changes to the usual behavior of integers, including modular arithmetic, can suppress warnings related to overflow, and opens the door for errors related to signed/unsigned mixes. Using `unsigned` doesn't actually eliminate the possibility of negative values.

**code sample**
```cpp
unsigned int u1 = -2;   // Valid: the value of u1 is 4294967294
int i1 = -2;
unsigned int u2 = i1;   // Valid: the value of u2 is 4294967294
int i2 = u2;            // Valid: the value of i2 is -2
```

```cpp
unsigned area(unsigned height, unsigned width) { return height*width; }
// ...
int height;
cin >> height;
auto a = area(height, 2);   // if the input is -2 a becomes 4294967292
```

```cpp
unsigned max = 100000;    // "accidental typo", I mean to say 10'000
unsigned short x = 100;
while (x < max) x += 100; // infinite loop
```

Alternatives:

```cpp
struct Positive {
    int val;
    Positive(int x) :val{x} { Assert(0 < x); }
    operator int() { return val; }
};

int f(Positive arg) { return arg; }

int r1 = f(2);
int r2 = f(-2);  // throws
```

**enforcement**
- See ES.100 Enforcements.

---

### [ES.107] Don't use `unsigned` for subscripts, prefer `gsl::index`

**reason**
To avoid signed/unsigned confusion. To enable better optimization. To enable better error detection. To avoid the pitfalls with `auto` and `int`.

**code example [bad]**
```cpp
vector<int> vec = /*...*/;

for (int i = 0; i < vec.size(); i += 2)                    // might not be big enough
    cout << vec[i] << '\n';
for (unsigned i = 0; i < vec.size(); i += 2)               // risk wraparound
    cout << vec[i] << '\n';
for (auto i = 0; i < vec.size(); i += 2)                   // might not be big enough
    cout << vec[i] << '\n';
for (vector<int>::size_type i = 0; i < vec.size(); i += 2) // verbose
    cout << vec[i] << '\n';
for (auto i = vec.size()-1; i >= 0; i -= 2)                // bug
    cout << vec[i] << '\n';
for (int i = vec.size()-1; i >= 0; i -= 2)                 // might not be big enough
    cout << vec[i] << '\n';
```

**code example [good]**
```cpp
vector<int> vec = /*...*/;

for (gsl::index i = 0; i < vec.size(); i += 2)             // ok
    cout << vec[i] << '\n';
for (gsl::index i = vec.size()-1; i >= 0; i -= 2)          // ok
    cout << vec[i] << '\n';
```

```cpp
template<typename T>
struct My_container {
public:
    // ...
    T& operator[](gsl::index i);    // not unsigned
    // ...
};
```

**enforcement**
- Very tricky as long as the standard-library containers get it wrong.
- (To avoid noise) Do not flag on a mixed signed/unsigned comparison where one of the arguments is `sizeof` or a call to container `.size()` and the other is `ptrdiff_t`.
