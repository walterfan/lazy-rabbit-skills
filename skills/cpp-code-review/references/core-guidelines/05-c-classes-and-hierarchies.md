# C: Classes and class hierarchies

## Table of Contents

**Concrete types:** C.1-C.12 | **Default operations:** C.20-C.22
**Destructors:** C.30-C.37 | **Constructors:** C.40-C.52
**Copy and move:** C.60-C.67 | **Other defaults:** C.80-C.90
**Containers:** C.100-C.109 | **Hierarchy (OOP):** C.120-C.122
**Hierarchy design:** C.126-C.140 | **Hierarchy access:** C.145-C.153
**Overloading:** C.160-C.170 | **Unions:** C.180-C.183

---

### [C.1] Organize related data into structures (`struct`s or `class`es)

**reason**
Ease of comprehension. If data is related, that fact should be reflected in code.

**code sample**
```cpp
void draw(int x, int y, int x2, int y2);  // BAD: unnecessary implicit relationships
void draw(Point from, Point to);          // better
```

**enforcement**
- Probably impossible. Maybe a heuristic looking for data items used together.

---

### [C.2] Use `class` if the class has an invariant; use `struct` if the data members can vary independently

**reason**
Readability. The use of `class` alerts the programmer to the need for an invariant.

**code sample**
```cpp
struct Pair {  // the members can vary independently
    string name;
    int volume;
};

class Date {
public:
    Date(int yy, Month mm, char dd);
    // ...
private:
    int y;
    Month m;
    char d;
};
```

**enforcement**
- Look for `struct`s with all data private and `class`es with public members.

---

### [C.3] Represent the distinction between an interface and an implementation using a class

**reason**
An explicit distinction between interface and implementation improves readability and simplifies maintenance.

**code sample**
```cpp
class Date {
public:
    Date();
    // validate that {yy, mm, dd} is a valid date and initialize
    Date(int yy, Month mm, char dd);

    int day() const;
    Month month() const;
    // ...
private:
    // ... some representation ...
};
```

We can now change the representation of a `Date` without affecting its users (recompilation is likely, though).

**enforcement**
- ???

---

### [C.4] Make a function a member only if it needs direct access to the representation of a class

**reason**
Less coupling than with member functions, fewer functions that can cause trouble by modifying object state.

**code sample**
```cpp
class Date {
    // ... relatively small interface ...
};

// helper functions:
Date next_weekday(Date);
bool operator==(Date, Date);
```

The "helper functions" have no need for direct access to the representation of a `Date`.

```cpp
class Foobar {
public:
    void foo(long x) { /* manipulate private data */ }
    void foo(double x) { foo(std::lround(x)); }
    // ...
private:
    // ...
};
```

```cpp
x.scale(0.5).rotate(45).set_color(Color::red);
```

**enforcement**
- Look for non-`virtual` member functions that do not touch data members directly.
- Ignore `virtual` functions.
- Ignore functions that are part of an overload set out of which at least one function accesses `private` members.
- Ignore functions returning `this`.

---

### [C.5] Place helper functions in the same namespace as the class they support

**reason**
A helper function is a function that does not need direct access to the representation of the class, yet is seen as part of the useful interface to the class. Placing them in the same namespace makes their relationship obvious and allows ADL.

**code example [bad]**
```cpp
namespace Chrono { // here we keep time-related services

    class Time { /* ... */ };
    class Date { /* ... */ };

    // helper functions:
    bool operator==(Date, Date);
    Date next_weekday(Date);
    // ...
}
```

**enforcement**
- Flag global functions taking argument types from a single namespace.

---

### [C.7] Don't define a class or enum and declare a variable of its type in the same statement

**reason**
Mixing a type definition and the definition of another entity in the same declaration is confusing and unnecessary.

**code example [bad]**
```cpp
struct Data { /*...*/ } data{ /*...*/ };
```

**code example [good]**
```cpp
struct Data { /*...*/ };
Data data{ /*...*/ };
```

**enforcement**
- Flag if the `}` of a class or enumeration definition is not followed by a `;`.

---

### [C.8] Use `class` rather than `struct` if any member is non-public

**reason**
Readability. To make it clear that something is being hidden/abstracted.

**code example [bad]**
```cpp
struct Date {
    int d, m;

    Date(int i, Month m);
    // ... lots of functions ...
private:
    int y;  // year
};
```

There is nothing wrong with this code as far as the C++ language rules are concerned, but nearly everything is wrong from a design perspective. The private data is hidden far from the public data.

**enforcement**
- Flag classes declared with `struct` if there is a `private` or `protected` member.

---

### [C.9] Minimize exposure of members

**reason**
Encapsulation. Information hiding. Minimize the chance of unintended access.

**code sample**
```cpp
template<typename T, typename U>
struct pair {
    T a;
    U b;
    // ...
};
```

Whatever we do in the `//`-part, an arbitrary user of a `pair` can arbitrarily and independently change its `a` and `b`.

```cpp
class Distance {
public:
    // ...
    double meters() const { return magnitude*unit; }
    void set_unit(double u)
    {
            // ... check that u is a factor of 10 ...
            // ... change magnitude appropriately ...
            unit = u;
    }
    // ...
private:
    double magnitude;
    double unit;    // 1 is meters, 1000 is kilometers, 0.001 is millimeters, etc.
};
```

```cpp
class Foo {
public:
    int bar(int x) { check(x); return do_bar(x); }
    // ...
protected:
    int do_bar(int x); // do some operation on the data
    // ...
private:
    // ... data ...
};

class Dir : public Foo {
    //...
    int mem(int x, int y)
    {
        /* ... do something ... */
        return do_bar(x + y); // OK: derived class can bypass check
    }
};

void user(Foo& x)
{
    int r1 = x.bar(1);      // OK, will check
    int r2 = x.do_bar(2);   // error: would bypass check
    // ...
};
```

**enforcement**
- Flag protected data.
- Flag mixtures of `public` and `private` data.

---

### [C.10] Prefer concrete types over class hierarchies

**reason**
A concrete type is fundamentally simpler than a type in a class hierarchy: easier to design, easier to implement, easier to use, easier to reason about, smaller, and faster.

**code sample**
```cpp
class Point1 {
    int x, y;
    // ... operations ...
    // ... no virtual functions ...
};

class Point2 {
    int x, y;
    // ... operations, some virtual ...
    virtual ~Point2();
};

void use()
{
    Point1 p11 {1, 2};   // make an object on the stack
    Point1 p12 {p11};    // a copy

    auto p21 = make_unique<Point2>(1, 2);   // make an object on the free store
    auto p22 = p21->clone();                // make a copy
    // ...
}
```

If a class is part of a hierarchy, we (in real code) must manipulate its objects through pointers or references. That implies more memory overhead, more allocations and deallocations, and more run-time overhead.

**enforcement**
- ???

---

### [C.11] Make concrete types regular

**reason**
Regular types are easier to understand and reason about than types that are not regular.

**code sample**
```cpp
struct Bundle {
    string name;
    vector<Record> vr;
};

bool operator==(const Bundle& a, const Bundle& b)
{
    return a.name == b.name && a.vr == b.vr;
}

Bundle b1 { "my bundle", {r1, r2, r3}};
Bundle b2 = b1;
if (!(b1 == b2)) error("impossible!");
b2.name = "the other bundle";
if (b1 == b2) error("No!");
```

In particular, if a concrete type is copyable, prefer to also give it an equality comparison operator, and ensure that `a = b` implies `a == b`.

**enforcement**
- ???

---

### [C.12] Don't make data members `const` or references in a copyable or movable type

**reason**
`const` and reference data members are not useful in a copyable or movable type, and make such types at least partly uncopyable/unmovable for subtle reasons.

**code example [bad]**
```cpp
class bad {
    const int i;    // bad
    string& s;      // bad
    // ...
};
```

The `const` and `&` data members make this class "only-sort-of-copyable" -- copy-constructible but not copy-assignable.

**enforcement**
- Flag a data member that is `const`, `&`, or `&&` in a type that has any copy or move operation.

---

### [C.20] If you can avoid defining default operations, do

**reason**
It's the simplest and gives the cleanest semantics. This is known as "the rule of zero".

**code example [good]**
```cpp
struct Named_map {
public:
    explicit Named_map(const string& n) : name(n) {}
    // no copy/move constructors
    // no copy/move assignment operators
    // no destructor
private:
    string name;
    map<int, int> rep;
};

Named_map nm("map"); // construct
Named_map nm2 {nm};  // copy construct
```

Since `std::map` and `string` have all the special functions, no further work is needed.

**enforcement**
- (Not enforceable) While not enforceable, a good static analyzer can detect patterns that indicate a possible improvement.

---

### [C.21] If you define or `=delete` any copy, move, or destructor function, define or `=delete` them all

**reason**
The semantics of copy, move, and destruction are closely related, so if one needs to be declared, the odds are that others need consideration too. This is known as "the rule of five".

**code example [bad]**
```cpp
struct M2 {   // bad: incomplete set of copy/move/destructor operations
public:
    // ...
    // ... no copy or move operations ...
    ~M2() { delete[] rep; }
private:
    pair<int, int>* rep;  // zero-terminated set of pairs
};

void use()
{
    M2 x;
    M2 y;
    // ...
    x = y;   // the default assignment
    // ...
}
```

Given that "special attention" was needed for the destructor (here, to deallocate), the likelihood that the implicitly-defined copy and move assignment operators will be correct is low (here, we would get double deletion).

**code example [good]**
```cpp
class AbstractBase {
public:
    virtual void foo() = 0;
    virtual ~AbstractBase() = default;
    // ...
};

class CloneableBase {
public:
    virtual unique_ptr<CloneableBase> clone() const;
    virtual ~CloneableBase() = default;
    CloneableBase() = default;
    CloneableBase(const CloneableBase&) = delete;
    CloneableBase& operator=(const CloneableBase&) = delete;
    CloneableBase(CloneableBase&&) = delete;
    CloneableBase& operator=(CloneableBase&&) = delete;
    // ... other constructors and functions ...
};
```

**code example [good]**
```cpp
class X {
public:
    // ...
    virtual ~X() = default;               // destructor (virtual if X is meant to be a base class)
    X(const X&) = default;                // copy constructor
    X& operator=(const X&) = default;     // copy assignment
    X(X&&) noexcept = default;            // move constructor
    X& operator=(X&&) noexcept = default; // move assignment
};
```

A minor mistake (such as a misspelling, leaving out a `const`, using `&` instead of `&&`, or leaving out a special function) can lead to errors or warnings.

**enforcement**
- (Simple) A class should have a declaration (even a `=delete` one) for either all or none of the copy/move/destructor functions.

---

### [C.22] Make default operations consistent

**reason**
The default operations are conceptually a matched set. Users will be surprised if copy/move construction and copy/move assignment do logically different things.

**code example [bad]**
```cpp
class Silly {   // BAD: Inconsistent copy operations
    class Impl {
        // ...
    };
    shared_ptr<Impl> p;
public:
    Silly(const Silly& a) : p(make_shared<Impl>()) { *p = *a.p; }   // deep copy
    Silly& operator=(const Silly& a) { p = a.p; return *this; }   // shallow copy
    // ...
};
```

These operations disagree about copy semantics. This will lead to confusion and bugs.

**enforcement**
- (Complex) A copy/move constructor and the corresponding copy/move assignment operator should write to the same data members at the same level of dereference.
- (Complex) Any data members written in a copy/move constructor should also be initialized by all other constructors.
- (Complex) If a copy/move constructor performs a deep copy of a data member, then the destructor should modify the data member.
- (Complex) If a destructor is modifying a data member, that data member should be written in any copy/move constructors or assignment operators.

---

### [C.30] Define a destructor if a class needs an explicit action at object destruction

**reason**
A destructor is implicitly invoked at the end of an object's lifetime. If the default destructor is sufficient, use it.

**code example [good]**
```cpp
template<typename A>
struct final_action {   // slightly simplified
    A act;
    final_action(A a) : act{a} {}
    ~final_action() { act(); }
};

template<typename A>
final_action<A> finally(A act)   // deduce action type
{
    return final_action<A>{act};
}

void test()
{
    auto act = finally([] { cout << "Exit test\n"; });  // establish exit action
    // ...
    if (something) return;   // act done here
    // ...
} // act done here
```

**code example [bad]**
```cpp
class Foo {   // bad; use the default destructor
public:
    // ...
    ~Foo() { s = ""; i = 0; vi.clear(); }  // clean up
private:
    string s;
    int i;
    vector<int> vi;
};
```

The default destructor does it better, more efficiently, and can't get it wrong.

**enforcement**
- Look for likely "implicit resources", such as pointers and references. Look for classes with destructors even though all their data members have destructors.

---

### [C.31] All resources acquired by a class must be released by the class's destructor

**reason**
Prevention of resource leaks, especially in error cases.

**code example [bad]**
```cpp
class X {
    ifstream f;   // might own a file
    // ... no default operations defined or =deleted ...
};
```

`X`'s `ifstream` implicitly closes any file it might have open upon destruction of its `X`.

**code example [bad]**
```cpp
class X2 {     // bad
    FILE* f;   // might own a file
    // ... no default operations defined or =deleted ...
};
```

`X2` might leak a file handle.

```cpp
Preprocessor pp { /* ... */ };
Parser p { pp, /* ... */ };
Type_checker tc { p, /* ... */ };
```

Here `p` refers to `pp` but does not own it.

**enforcement**
- (Simple) If a class has pointer or reference members that are owners (e.g., deemed owners by using `gsl::owner`), then they should be referenced in its destructor.
- (Hard) Determine if pointer or reference members are owners when there is no explicit statement of ownership.

---

### [C.32] If a class has a raw pointer (`T*`) or reference (`T&`), consider whether it might be owning

**reason**
There is a lot of code that is non-specific about ownership.

**code sample**
```cpp
class legacy_class
{
    foo* m_owning;   // Bad: change to unique_ptr<T> or owner<T*>
    bar* m_observer; // OK: keep
};
```

**enforcement**
- Look at the initialization of raw member pointers and member references and see if an allocation is used.

---

### [C.33] If a class has an owning pointer member, define a destructor

**reason**
An owned object must be `delete`d upon destruction of the object that owns it.

**code example [bad]**
```cpp
template<typename T>
class Smart_ptr {
    T* p;   // BAD: vague about ownership of *p
    // ...
public:
    // ... no user-defined default operations ...
};

void use(Smart_ptr<int> p1)
{
    // error: p2.p leaked (if not nullptr and not owned by some other code)
    auto p2 = p1;
}
```

Note that if you define a destructor, you must define or delete all default operations:

```cpp
template<typename T>
class Smart_ptr2 {
    T* p;   // BAD: vague about ownership of *p
    // ...
public:
    // ... no user-defined copy operations ...
    ~Smart_ptr2() { delete p; }  // p is an owner!
};

void use(Smart_ptr2<int> p1)
{
    auto p2 = p1;   // error: double deletion
}
```

Be explicit about ownership:

```cpp
template<typename T>
class Smart_ptr3 {
    owner<T*> p;   // OK: explicit about ownership of *p
    // ...
public:
    // ...
    // ... copy and move operations ...
    ~Smart_ptr3() { delete p; }
};

void use(Smart_ptr3<int> p1)
{
    auto p2 = p1;   // OK: no double deletion
}
```

**enforcement**
- A class with a pointer data member is suspect.
- A class with an `owner<T>` should define its default operations.

---

### [C.35] A base class destructor should be either public and virtual, or protected and non-virtual

**reason**
To prevent undefined behavior. If the destructor is public, then calling code can attempt to destroy a derived class object through a base class pointer, and the result is undefined if the base class's destructor is non-virtual.

**code example [bad]**
```cpp
struct Base {  // BAD: implicitly has a public non-virtual destructor
    virtual void f();
};

struct D : Base {
    string s {"a resource needing cleanup"};
    ~D() { /* ... do some cleanup ... */ }
    // ...
};

void use()
{
    unique_ptr<Base> p = make_unique<D>();
    // ...
} // p's destruction calls ~Base(), not ~D(), which leaks D::s and possibly more
```

**code example [bad]**
```cpp
class X {
    ~X();   // private destructor
    // ...
};

void use()
{
    X a;                        // error: cannot destroy
    auto p = make_unique<X>();  // error: cannot destroy
}
```

**enforcement**
- A class with any virtual functions should have a destructor that is either public and virtual or else protected and non-virtual.
- If a class inherits publicly from a base class, the base class should have a destructor that is either public and virtual or else protected and non-virtual.

---

### [C.36] A destructor must not fail

**reason**
In general we do not know how to write error-free code if a destructor should fail. The standard library requires that all classes it deals with have destructors that do not exit by throwing.

**code sample**
```cpp
class X {
public:
    ~X() noexcept;
    // ...
};

X::~X() noexcept
{
    // ...
    if (cannot_release_a_resource) terminate();
    // ...
}
```

Declare a destructor `noexcept`. That will ensure that it either completes normally or terminates the program.

**enforcement**
- (Simple) A destructor should be declared `noexcept` if it could throw.

---

### [C.37] Make destructors `noexcept`

**reason**
A destructor must not fail. If a destructor tries to exit with an exception, it's a bad design error and the program had better terminate.

**code sample**
```cpp
struct X {
    Details x;  // happens to have a throwing destructor
    // ...
    ~X() { }    // implicitly noexcept(false); aka can throw
};
```

Not all destructors are noexcept by default; one throwing member poisons the whole class hierarchy. So, if in doubt, declare a destructor noexcept.

**enforcement**
- (Simple) A destructor should be declared `noexcept` if it could throw.

---

### [C.40] Define a constructor if a class has an invariant

**reason**
That's what constructors are for.

**code sample**
```cpp
class Date {  // a Date represents a valid date
              // in the January 1, 1900 to December 31, 2100 range
    Date(int dd, int mm, int yy)
        :d{dd}, m{mm}, y{yy}
    {
        if (!is_valid(d, m, y)) throw Bad_date{};  // enforce invariant
    }
    // ...
private:
    int d, m, y;
};
```

A constructor can be used for convenience even if a class does not have an invariant:

```cpp
struct Rec {
    string s;
    int i {0};
    Rec(const string& ss) : s{ss} {}
    Rec(int ii) :i{ii} {}
};

Rec r1 {7};
Rec r2 {"Foo bar"};
```

The C++11 initializer list rule eliminates the need for many constructors:

```cpp
struct Rec2{
    string s;
    int i;
    Rec2(const string& ss, int ii = 0) :s{ss}, i{ii} {}   // redundant
};

Rec2 r1 {"Foo", 7};
Rec2 r2 {"Bar"};
```

**enforcement**
- Flag classes with user-defined copy operations but no constructor.

---

### [C.41] A constructor should create a fully initialized object

**reason**
A constructor establishes the invariant for a class. A user should be able to assume that a constructed object is usable.

**code example [bad]**
```cpp
class X1 {
    FILE* f;   // call init() before any other function
    // ...
public:
    X1() {}
    void init();   // initialize f
    void read();   // read from f
    // ...
};

void f()
{
    X1 file;
    file.read();   // crash or bad read!
    // ...
    file.init();   // too late
    // ...
}
```

Compilers do not read comments.

**enforcement**
- (Simple) Every constructor should initialize every data member (either explicitly, via a delegating ctor call or via default construction).
- (Unknown) If a constructor has an `Ensures` contract, try to see if it holds as a postcondition.

---

### [C.42] If a constructor cannot construct a valid object, throw an exception

**reason**
Leaving behind an invalid object is asking for trouble.

**code example [good]**
```cpp
class X2 {
    FILE* f;
    // ...
public:
    X2(const string& name)
        :f{fopen(name.c_str(), "r")}
    {
        if (!f) throw runtime_error{"could not open" + name};
        // ...
    }

    void read();      // read from f
    // ...
};

void f()
{
    X2 file {"Zeno"}; // throws if file isn't open
    file.read();      // fine
    // ...
}
```

**code example [bad]**
```cpp
class X3 {     // bad: the constructor leaves a non-valid object behind
    FILE* f;   // call is_valid() before any other function
    bool valid;
    // ...
public:
    X3(const string& name)
        :f{fopen(name.c_str(), "r")}, valid{false}
    {
        if (f) valid = true;
        // ...
    }

    bool is_valid() { return valid; }
    void read();   // read from f
    // ...
};

void f()
{
    X3 file {"Heraclides"};
    file.read();   // crash or bad read!
    // ...
    if (file.is_valid()) {
        file.read();
        // ...
    }
    else {
        // ... handle error ...
    }
    // ...
}
```

**enforcement**
- ???

---

### [C.43] Ensure that a copyable class has a default constructor

**reason**
Many language and library facilities rely on default constructors to initialize their elements, e.g. `T a[10]` and `std::vector<T> v(10)`.

**code example [bad]**
```cpp
class Date { // BAD: no default constructor
public:
    Date(int dd, int mm, int yyyy);
    // ...
};

vector<Date> vd1(1000);   // default Date needed here
vector<Date> vd2(1000, Date{7, Month::October, 1885});   // alternative
```

Most realistic `Date` classes have a "first date" (e.g. January 1, 1970 is popular), so making that the default is usually trivial:

```cpp
class Date {
public:
    Date(int dd, int mm, int yyyy);
    Date() = default;
    // ...
private:
    int dd {1};
    int mm {1};
    int yyyy {1970};
    // ...
};

vector<Date> vd1(1000);
```

Beware that built-in types are not properly default constructed:

```cpp
struct X {
    string s;
    int i;
};

void f()
{
    X x;    // x.s is initialized to the empty string; x.i is uninitialized

    cout << x.s << ' ' << x.i << '\n';
    ++x.i;
}
```

An explicit default initialization can help:

```cpp
struct X {
    string s;
    int i {};   // default initialize (to 0)
};
```

**enforcement**
- Flag classes that are copyable by `=` without a default constructor.
- Flag classes that are comparable with `==` but not copyable.

---

### [C.44] Prefer default constructors to be simple and non-throwing

**reason**
Being able to set a value to "the default" without operations that might fail simplifies error handling and reasoning about move operations.

**code example [bad]**
```cpp
template<typename T>
class Vector0 {
public:
    Vector0() :Vector0{0} {}
    Vector0(int n) :elem{new T[n]}, space{elem + n}, last{elem} {}
    // ...
private:
    own<T*> elem;
    T* space;
    T* last;
};
```

Setting a `Vector0` to empty after an error involves an allocation, which might fail. Also, `Vector0<int> v[100]` costs 100 allocations.

**code example [good]**
```cpp
template<typename T>
class Vector1 {
public:
    Vector1() noexcept {}
    Vector1(int n) :elem{new T[n]}, space{elem + n}, last{elem} {}
    // ...
private:
    own<T*> elem {};
    T* space {};
    T* last {};
};
```

Using `{nullptr, nullptr, nullptr}` makes `Vector1{}` cheap. Setting a `Vector1` to empty after detecting an error is trivial.

**enforcement**
- Flag throwing default constructors.

---

### [C.45] Don't define a default constructor that only initializes data members; use default member initializers instead

**reason**
Using default member initializers lets the compiler generate the function for you. The compiler-generated function can be more efficient.

**code example [bad]**
```cpp
class X1 { // BAD: doesn't use member initializers
    string s;
    int i;
public:
    X1() :s{"default"}, i{1} { }
    // ...
};
```

**code example [good]**
```cpp
class X2 {
    string s {"default"};
    int i {1};
public:
    // use compiler-generated default constructor
    // ...
};
```

**enforcement**
- (Simple) Flag if a default constructor's explicit member initializer is a constant, and recommend that the constant should be written as a data member initializer instead.

---

### [C.46] By default, declare single-argument constructors `explicit`

**reason**
To avoid unintended conversions.

**code example [bad]**
```cpp
class String {
public:
    String(int);   // BAD
    // ...
};

String s = 10;   // surprise: string of size 10
```

**code example [good]**
```cpp
class Complex {
public:
    Complex(double d);   // OK: we want a conversion from d to {d, 0}
    // ...
};

Complex z = 10.7;   // unsurprising conversion
```

**enforcement**
- (Simple) Single-argument constructors should be declared `explicit`. Good single argument non-`explicit` constructors are rare in most code bases.

---

### [C.47] Define and initialize data members in the order of member declaration

**reason**
To minimize confusion and errors. That is the order in which the initialization happens (independent of the order of member initializers).

**code example [bad]**
```cpp
class Foo {
    int m1;
    int m2;
public:
    Foo(int x) :m2{x}, m1{++x} { }   // BAD: misleading initializer order
    // ...
};

Foo x(1); // surprise: x.m1 == x.m2 == 2
```

**enforcement**
- (Simple) A member initializer list should mention the members in the same order they are declared.

---

### [C.48] Prefer default member initializers to member initializers in constructors for constant initializers

**reason**
Makes it explicit that the same value is expected to be used in all constructors. Avoids repetition. Avoids maintenance problems.

**code example [bad]**
```cpp
class X {   // BAD
    int i;
    string s;
    int j;
public:
    X() :i{666}, s{"qqq"} { }   // j is uninitialized
    X(int ii) :i{ii} {}         // s is "" and j is uninitialized
    // ...
};
```

**code example [good]**
```cpp
class X2 {
    int i {666};
    string s {"qqq"};
    int j {0};
public:
    X2() = default;        // all members are initialized to their defaults
    X2(int ii) :i{ii} {}   // s and j initialized to their defaults
    // ...
};
```

**code example [bad]**
```cpp
class X3 {   // BAD: inexplicit, argument passing overhead
    int i;
    string s;
    int j;
public:
    X3(int ii = 666, const string& ss = "qqq", int jj = 0)
        :i{ii}, s{ss}, j{jj} { }   // all members are initialized to their defaults
    // ...
};
```

**enforcement**
- (Simple) Every constructor should initialize every data member (either explicitly, via a delegating ctor call or via default construction).
- (Simple) Default arguments to constructors suggest a default member initializer might be more appropriate.

---

### [C.49] Prefer initialization to assignment in constructors

**reason**
An initialization explicitly states that initialization, rather than assignment, is done and can be more elegant and efficient. Prevents "use before set" errors.

**code example [good]**
```cpp
class A {   // Good
    string s1;
public:
    A(czstring p) : s1{p} { }    // GOOD: directly construct
    // ...
};
```

**code example [bad]**
```cpp
class B {   // BAD
    string s1;
public:
    B(const char* p) { s1 = p; }   // BAD: default constructor followed by assignment
    // ...
};

class C {   // UGLY, aka very bad
    int* p;
public:
    C() { cout << *p; p = new int{10}; }   // accidental use before initialized
    // ...
};
```

**code example [good]**
```cpp
class D {   // Good
    string s1;
public:
    D(string_view v) : s1{v} { }    // GOOD: directly construct
    // ...
};
```

**enforcement**
- ???

---

### [C.50] Use a factory function if you need "virtual behavior" during initialization

**reason**
If the state of a base class object must depend on the state of a derived part of the object, we need to use a virtual function (or equivalent) while minimizing the window of opportunity to misuse an imperfectly constructed object.

**code example [bad]**
```cpp
class B {
public:
    B()
    {
        /* ... */
        f(); // BAD: C.82: Don't call virtual functions in constructors and destructors
        /* ... */
    }

    virtual void f() = 0;
};
```

**code example [good]**
```cpp
class B {
protected:
    class Token {};

public:
    explicit B(Token) { /* ... */ }  // create an imperfectly initialized object
    virtual void f() = 0;

    template<class T>
    static shared_ptr<T> create()    // interface for creating shared objects
    {
        auto p = make_shared<T>(typename T::Token{});
        p->post_initialize();
        return p;
    }

protected:
    virtual void post_initialize()   // called right after construction
        { /* ... */ f(); /* ... */ } // GOOD: virtual dispatch is safe
};

class D : public B {                 // some derived class
protected:
    class Token {};

public:
    explicit D(Token) : B{ B::Token{} } {}
    void f() override { /* ...  */ };

protected:
    template<class T>
    friend shared_ptr<T> B::create();
};

shared_ptr<D> p = D::create<D>();  // creating a D object
```

**enforcement**
- ???

---

### [C.51] Use delegating constructors to represent common actions for all constructors of a class

**reason**
To avoid repetition and accidental differences.

**code example [bad]**
```cpp
class Date {   // BAD: repetitive
    int d;
    Month m;
    int y;
public:
    Date(int dd, Month mm, year yy)
        :d{dd}, m{mm}, y{yy}
        { if (!valid(d, m, y)) throw Bad_date{}; }

    Date(int dd, Month mm)
        :d{dd}, m{mm} y{current_year()}
        { if (!valid(d, m, y)) throw Bad_date{}; }
    // ...
};
```

**code example [good]**
```cpp
class Date2 {
    int d;
    Month m;
    int y;
public:
    Date2(int dd, Month mm, year yy)
        :d{dd}, m{mm}, y{yy}
        { if (!valid(d, m, y)) throw Bad_date{}; }

    Date2(int dd, Month mm)
        :Date2{dd, mm, current_year()} {}
    // ...
};
```

**enforcement**
- (Moderate) Look for similar constructor bodies.

---

### [C.52] Use inheriting constructors to import constructors into a derived class that does not need further explicit initialization

**reason**
If you need those constructors for a derived class, re-implementing them is tedious and error-prone.

**code example [good]**
```cpp
class Rec {
    // ... data and lots of nice constructors ...
};

class Oper : public Rec {
    using Rec::Rec;
    // ... no data members ...
    // ... lots of nice utility functions ...
};
```

**code example [bad]**
```cpp
struct Rec2 : public Rec {
    int x;
    using Rec::Rec;
};

Rec2 r {"foo", 7};
int val = r.x;   // uninitialized
```

**enforcement**
- Make sure that every member of the derived class is initialized.

---

### [C.60] Make copy assignment non-`virtual`, take the parameter by `const&`, and return by non-`const&`

**reason**
It is simple and efficient. If you want to optimize for rvalues, provide an overload that takes an `&&`.

**code example [good]**
```cpp
class Foo {
public:
    Foo& operator=(const Foo& x)
    {
        // GOOD: no need to check for self-assignment (other than performance)
        auto tmp = x;
        swap(tmp); // see C.83
        return *this;
    }
    // ...
};

Foo a;
Foo b;
Foo f();

a = b;    // assign lvalue: copy
a = f();  // assign rvalue: potentially move
```

When assignment of large, equal-sized `Vector`s is common, the swap technique could cause an order of magnitude increase in cost:

```cpp
template<typename T>
class Vector {
public:
    Vector& operator=(const Vector&);
    // ...
private:
    T* elem;
    int sz;
};

Vector& Vector::operator=(const Vector& a)
{
    if (a.sz > sz) {
        // ... use the swap technique, it can't be bettered ...
        return *this;
    }
    // ... copy sz elements from *a.elem to elem ...
    if (a.sz < sz) {
        // ... destroy the surplus elements in *this and adjust size ...
    }
    return *this;
}
```

**enforcement**
- (Simple) An assignment operator should not be virtual. Here be dragons!
- (Simple) An assignment operator should return `T&` to enable chaining.
- (Moderate) An assignment operator should (implicitly or explicitly) invoke all base and member assignment operators.

---

### [C.61] A copy operation should copy

**reason**
That is the generally assumed semantics. After `x = y`, we should have `x == y`.

**code example [good]**
```cpp
class X {   // OK: value semantics
public:
    X();
    X(const X&);     // copy X
    void modify();   // change the value of X
    // ...
    ~X() { delete[] p; }
private:
    T* p;
    int sz;
};

bool operator==(const X& a, const X& b)
{
    return a.sz == b.sz && equal(a.p, a.p + a.sz, b.p, b.p + b.sz);
}

X::X(const X& a)
    :p{new T[a.sz]}, sz{a.sz}
{
    copy(a.p, a.p + sz, p);
}

X x;
X y = x;
if (x != y) throw Bad{};
x.modify();
if (x == y) throw Bad{};   // assume value semantics
```

```cpp
class X2 {  // OK: pointer semantics
public:
    X2();
    X2(const X2&) = default; // shallow copy
    ~X2() = default;
    void modify();          // change the pointed-to value
    // ...
private:
    T* p;
    int sz;
};

bool operator==(const X2& a, const X2& b)
{
    return a.sz == b.sz && a.p == b.p;
}

X2 x;
X2 y = x;
if (x != y) throw Bad{};
x.modify();
if (x != y) throw Bad{};  // assume pointer semantics
```

**enforcement**
- (Not enforceable)

---

### [C.62] Make copy assignment safe for self-assignment

**reason**
If `x = x` changes the value of `x`, people will be surprised and bad errors will occur (often including leaks).

**code sample**
```cpp
std::vector<int> v = {3, 1, 4, 1, 5, 9};
v = v;
// the value of v is still {3, 1, 4, 1, 5, 9}
```

```cpp
struct Bar {
    vector<pair<int, int>> v;
    map<string, int> m;
    string s;
};

Bar b;
// ...
b = b;   // correct and efficient
```

You can handle self-assignment by explicitly testing for self-assignment, but often it is faster and more elegant to cope without such a test (e.g., using `swap`):

```cpp
class Foo {
    string s;
    int i;
public:
    Foo& operator=(const Foo& a);
    // ...
};

Foo& Foo::operator=(const Foo& a)   // OK, but there is a cost
{
    if (this == &a) return *this;
    s = a.s;
    i = a.i;
    return *this;
}
```

```cpp
Foo& Foo::operator=(const Foo& a)   // simpler, and probably much better
{
    s = a.s;
    i = a.i;
    return *this;
}
```

**enforcement**
- (Simple) Assignment operators should not contain the pattern `if (this == &a) return *this;` ???

---

### [C.63] Make move assignment non-`virtual`, take the parameter by `&&`, and return by non-`const&`

**reason**
It is simple and efficient.

**enforcement**
- (Simple) An assignment operator should not be virtual.
- (Simple) An assignment operator should return `T&` to enable chaining.
- (Moderate) A move assignment operator should (implicitly or explicitly) invoke all base and member move assignment operators.

---

### [C.64] A move operation should move and leave its source in a valid state

**reason**
After `y = std::move(x)` the value of `y` should be the value `x` had and `x` should be in a valid state.

**code example [good]**
```cpp
class X {   // OK: value semantics
public:
    X();
    X(X&& a) noexcept;  // move X
    X& operator=(X&& a) noexcept; // move-assign X
    void modify();     // change the value of X
    // ...
    ~X() { delete[] p; }
private:
    T* p;
    int sz;
};

X::X(X&& a) noexcept
    :p{a.p}, sz{a.sz}  // steal representation
{
    a.p = nullptr;     // set to "empty"
    a.sz = 0;
}

void use()
{
    X x{};
    // ...
    X y = std::move(x);
    x = X{};   // OK
} // OK: x can be destroyed
```

**enforcement**
- (Not enforceable) Look for assignments to members in the move operation. If there is a default constructor, compare those assignments to the initializations in the default constructor.

---

### [C.65] Make move assignment safe for self-assignment

**reason**
If `x = x` changes the value of `x`, people will be surprised and bad errors can occur. `std::swap` is implemented using move operations so if you accidentally do `swap(a, b)` where `a` and `b` refer to the same object, failing to handle self-move could be a serious and subtle error.

**code example [good]**
```cpp
class Foo {
    string s;
    int i;
public:
    Foo& operator=(Foo&& a) noexcept;
    // ...
};

Foo& Foo::operator=(Foo&& a) noexcept  // OK, but there is a cost
{
    if (this == &a) return *this;  // this line is redundant
    s = std::move(a.s);
    i = a.i;
    return *this;
}
```

Move a pointer without a test:

```cpp
// move from other.ptr to this->ptr
T* temp = other.ptr;
other.ptr = nullptr;
delete ptr; // in self-move, this->ptr is also null; delete is a no-op
ptr = temp; // in self-move, the original ptr is restored
```

**enforcement**
- (Moderate) In the case of self-assignment, a move assignment operator should not leave the object holding pointer members that have been `delete`d or set to `nullptr`.
- (Not enforceable) Look at the use of standard-library container types (incl. `string`) and consider them safe for ordinary (not life-critical) uses.

---

### [C.66] Make move operations `noexcept`

**reason**
A throwing move violates most people's reasonable assumptions. A non-throwing move will be used more efficiently by standard-library and language facilities.

**code example [good]**
```cpp
template<typename T>
class Vector {
public:
    Vector(Vector&& a) noexcept :elem{a.elem}, sz{a.sz} { a.elem = nullptr; a.sz = 0; }
    Vector& operator=(Vector&& a) noexcept {
        if (&a != this) {
            delete elem;
            elem = a.elem; a.elem = nullptr;
            sz   = a.sz;   a.sz   = 0;
        }
        return *this;
    }
    // ...
private:
    T* elem;
    int sz;
};
```

**code example [bad]**
```cpp
template<typename T>
class Vector2 {
public:
    Vector2(Vector2&& a) noexcept { *this = a; }             // just use the copy
    Vector2& operator=(Vector2&& a) noexcept { *this = a; }  // just use the copy
    // ...
private:
    T* elem;
    int sz;
};
```

This `Vector2` is not just inefficient, but since a vector copy requires allocation, it can throw.

**enforcement**
- (Simple) A move operation should be marked `noexcept`.

---

### [C.67] A polymorphic class should suppress public copy/move

**reason**
A *polymorphic class* is a class that defines or inherits at least one virtual function. If it is accidentally passed by value, with the implicitly generated copy constructor and assignment, we risk slicing.

**code example [bad]**
```cpp
class B { // BAD: polymorphic base class doesn't suppress copying
public:
    virtual char m() { return 'B'; }
    // ... nothing about copy operations, so uses default ...
};

class D : public B {
public:
    char m() override { return 'D'; }
    // ...
};

void f(B& b)
{
    auto b2 = b; // oops, slices the object; b2.m() will return 'B'
}

D d;
f(d);
```

**code example [good]**
```cpp
class B { // GOOD: polymorphic class suppresses copying
public:
    B() = default;
    B(const B&) = delete;
    B& operator=(const B&) = delete;
    virtual char m() { return 'B'; }
    // ...
};

class D : public B {
public:
    char m() override { return 'D'; }
    // ...
};

void f(B& b)
{
    auto b2 = b; // ok, compiler will detect inadvertent copying, and protest
}

D d;
f(d);
```

If you need to create deep copies of polymorphic objects, use `clone()` functions: see C.130.

**enforcement**
- Flag a polymorphic class with a public copy operation.
- Flag an assignment of polymorphic class objects.

---

### [C.80] Use `=default` if you have to be explicit about using the default semantics

**reason**
The compiler is more likely to get the default semantics right and you cannot implement these functions better than the compiler.

**code example [good]**
```cpp
class Tracer {
    string message;
public:
    Tracer(const string& m) : message{m} { cerr << "entering " << message << '\n'; }
    ~Tracer() { cerr << "exiting " << message << '\n'; }

    Tracer(const Tracer&) = default;
    Tracer& operator=(const Tracer&) = default;
    Tracer(Tracer&&) noexcept = default;
    Tracer& operator=(Tracer&&) noexcept = default;
};
```

Because we defined the destructor, we must define the copy and move operations. The `= default` is the best and simplest way.

**code example [bad]**
```cpp
class Tracer2 {
    string message;
public:
    Tracer2(const string& m) : message{m} { cerr << "entering " << message << '\n'; }
    ~Tracer2() { cerr << "exiting " << message << '\n'; }

    Tracer2(const Tracer2& a) : message{a.message} {}
    Tracer2& operator=(const Tracer2& a) { message = a.message; return *this; }
    Tracer2(Tracer2&& a) noexcept :message{a.message} {}
    Tracer2& operator=(Tracer2&& a) noexcept { message = a.message; return *this; }
};
```

Writing out the bodies of the copy and move operations is verbose, tedious, and error-prone. A compiler does it better.

**enforcement**
- (Moderate) The body of a user-defined operation should not have the same semantics as the compiler-generated version.

---

### [C.81] Use `=delete` when you want to disable default behavior (without wanting an alternative)

**reason**
In a few cases, a default operation is not desirable.

**code sample**
```cpp
class Immortal {
public:
    ~Immortal() = delete;   // do not allow destruction
    // ...
};

void use()
{
    Immortal ugh;   // error: ugh cannot be destroyed
    Immortal* p = new Immortal{};
    delete p;       // error: cannot destroy *p
}
```

```cpp
template<class T, class D = default_delete<T>> class unique_ptr {
public:
    // ...
    constexpr unique_ptr() noexcept;
    explicit unique_ptr(pointer p) noexcept;
    // ...
    unique_ptr(unique_ptr&& u) noexcept;   // move constructor
    // ...
    unique_ptr(const unique_ptr&) = delete; // disable copy from lvalue
    // ...
};

unique_ptr<int> make();   // make "something" and return it by moving

void f()
{
    unique_ptr<int> pi {};
    auto pi2 {pi};      // error: no move constructor from lvalue
    auto pi3 {make()};  // OK, move: the result of make() is an rvalue
}
```

Note that deleted functions should be public.

**enforcement**
- The elimination of a default operation is (should be) based on the desired semantics of the class.

---

### [C.82] Don't call virtual functions in constructors and destructors

**reason**
The function called will be that of the object constructed so far, rather than a possibly overriding function in a derived class. Worse, a direct or indirect call to an unimplemented pure virtual function from a constructor or destructor results in undefined behavior.

**code example [bad]**
```cpp
class Base {
public:
    virtual void f() = 0;   // not implemented
    virtual void g();       // implemented with Base version
    virtual void h();       // implemented with Base version
    virtual ~Base();        // implemented with Base version
};

class Derived : public Base {
public:
    void g() override;   // provide Derived implementation
    void h() final;      // provide Derived implementation

    Derived()
    {
        // BAD: attempt to call an unimplemented virtual function
        f();

        // BAD: will call Derived::g, not dispatch further virtually
        g();

        // GOOD: explicitly state intent to call only the visible version
        Derived::g();

        // ok, no qualification needed, h is final
        h();
    }
};
```

Note that calling a specific explicitly qualified function is not a virtual call even if the function is `virtual`.

**enforcement**
- Flag calls of virtual functions from constructors and destructors.

---

### [C.83] For value-like types, consider providing a `noexcept` swap function

**reason**
A `swap` can be handy for implementing a number of idioms, from smoothly moving objects around to implementing assignment easily to providing a guaranteed commit function.

**code example [good]**
```cpp
class Foo {
public:
    void swap(Foo& rhs) noexcept
    {
        m1.swap(rhs.m1);
        std::swap(m2, rhs.m2);
    }
private:
    Bar m1;
    int m2;
};

void swap(Foo& a, Foo& b)
{
    a.swap(b);
}
```

**enforcement**
- Non-trivially copyable types should provide a member swap or a free swap overload.
- (Simple) When a class has a `swap` member function, it should be declared `noexcept`.

---

### [C.84] A `swap` function must not fail

**reason**
`swap` is widely used in ways that are assumed never to fail and programs cannot easily be written to work correctly in the presence of a failing `swap`.

**code example [bad]**
```cpp
void swap(My_vector& x, My_vector& y)
{
    auto tmp = x;   // copy elements
    x = y;
    y = tmp;
}
```

This is not just slow, but if a memory allocation occurs for the elements in `tmp`, this `swap` could throw and would make STL algorithms fail.

**enforcement**
- (Simple) When a class has a `swap` member function, it should be declared `noexcept`.

---

### [C.85] Make `swap` `noexcept`

**reason**
A `swap` must not fail. If a `swap` tries to exit with an exception, it's a bad design error and the program had better terminate.

**enforcement**
- (Simple) When a class has a `swap` member function, it should be declared `noexcept`.

---

### [C.86] Make `==` symmetric with respect to operand types and `noexcept`

**reason**
Asymmetric treatment of operands is surprising and a source of errors where conversions are possible.

**code example [good]**
```cpp
struct X {
    string name;
    int number;
};

bool operator==(const X& a, const X& b) noexcept {
    return a.name == b.name && a.number == b.number;
}
```

**code example [bad]**
```cpp
class B {
    string name;
    int number;
    bool operator==(const B& a) const {
        return name == a.name && number == a.number;
    }
    // ...
};
```

`B`'s comparison accepts conversions for its second operand, but not its first.

**enforcement**
- Flag an `operator==()` for which the argument types differ; same for other comparison operators.
- Flag member `operator==()`s; same for other comparison operators.

---

### [C.87] Beware of `==` on base classes

**reason**
It is really hard to write a foolproof and useful `==` for a hierarchy.

**code example [bad]**
```cpp
class B {
    string name;
    int number;
public:
    virtual bool operator==(const B& a) const
    {
         return name == a.name && number == a.number;
    }
    // ...
};

class D : public B {
    char character;
public:
    virtual bool operator==(const D& a) const
    {
        return B::operator==(a) && character == a.character;
    }
    // ...
};

B b = ...
D d = ...
b == d;    // compares name and number, ignores d's character
d == b;    // compares name and number, ignores d's character
D d2;
d == d2;   // compares name, number, and character
B& b2 = d2;
b2 == d;   // compares name and number, ignores d2's and d's character
```

**enforcement**
- Flag a virtual `operator==()`; same for other comparison operators.

---

### [C.89] Make a `hash` `noexcept`

**reason**
Users of hashed containers use hash indirectly and don't expect simple access to throw.

**code example [bad]**
```cpp
template<>
struct hash<My_type> {  // thoroughly bad hash specialization
    using result_type = size_t;
    using argument_type = My_type;

    size_t operator()(const My_type & x) const
    {
        size_t xs = x.s.size();
        if (xs < 4) throw Bad_My_type{};    // "Nobody expects the Spanish inquisition!"
        return hash<size_t>()(x.s.size()) ^ trim(x.s);
    }
};

int main()
{
    unordered_map<My_type, int> m;
    My_type mt{ "asdfg" };
    m[mt] = 7;
    cout << m[My_type{ "asdfg" }] << '\n';
}
```

**enforcement**
- Flag throwing `hash`es.

---

### [C.90] Rely on constructors and assignment operators, not `memset` and `memcpy`

**reason**
The standard C++ mechanism to construct an instance of a type is to call its constructor. Using memcpy to copy a non-trivially copyable type has undefined behavior. Frequently this results in slicing, or data corruption.

**code example [good]**
```cpp
struct base {
    virtual void update() = 0;
    std::shared_ptr<int> sp;
};

struct derived : public base {
    void update() override {}
};
```

**code example [bad]**
```cpp
void init(derived& a)
{
    memset(&a, 0, sizeof(derived));
}
```

This is type-unsafe and overwrites the vtable.

```cpp
void copy(derived& a, derived& b)
{
    memcpy(&a, &b, sizeof(derived));
}
```

This is also type-unsafe and overwrites the vtable.

**enforcement**
- Flag passing a non-trivially-copyable type to `memset` or `memcpy`.

---

### [C.100] Follow the STL when defining a container

**reason**
The STL containers are familiar to most C++ programmers and a fundamentally sound design.

**code sample**
```cpp
// simplified (e.g., no allocators):

template<typename T>
class Sorted_vector {
    using value_type = T;
    // ... iterator types ...

    Sorted_vector() = default;
    Sorted_vector(initializer_list<T>);    // initializer-list constructor: sort and store
    Sorted_vector(const Sorted_vector&) = default;
    Sorted_vector(Sorted_vector&&) noexcept = default;
    Sorted_vector& operator=(const Sorted_vector&) = default;     // copy assignment
    Sorted_vector& operator=(Sorted_vector&&) noexcept = default; // move assignment
    ~Sorted_vector() = default;

    Sorted_vector(const std::vector<T>& v);   // store and sort
    Sorted_vector(std::vector<T>&& v);        // sort and "steal representation"

    const T& operator[](int i) const { return rep[i]; }
    // no non-const direct access to preserve order

    void push_back(const T&);   // insert in the right place (not necessarily at back)
    void push_back(T&&);        // insert in the right place (not necessarily at back)

    // ... cbegin(), cend() ...
private:
    std::vector<T> rep;  // use a std::vector to hold elements
};

template<typename T> bool operator==(const Sorted_vector<T>&, const Sorted_vector<T>&);
template<typename T> bool operator!=(const Sorted_vector<T>&, const Sorted_vector<T>&);
// ...
```

**enforcement**
- ???

---

### [C.101] Give a container value semantics

**reason**
Regular objects are simpler to think and reason about than irregular ones.

**code sample**
```cpp
void f(const Sorted_vector<string>& v)
{
    Sorted_vector<string> v2 {v};
    if (v != v2)
        cout << "Behavior against reason and logic.\n";
    // ...
}
```

**enforcement**
- ???

---

### [C.102] Give a container move operations

**reason**
Containers tend to get large; without a move constructor and a copy constructor an object can be expensive to move around.

**code sample**
```cpp
Sorted_vector<int> read_sorted(istream& is)
{
    vector<int> v;
    cin >> v;   // assume we have a read operation for vectors
    Sorted_vector<int> sv = v;  // sorts
    return sv;
}
```

**enforcement**
- ???

---

### [C.103] Give a container an initializer list constructor

**reason**
People expect to be able to initialize a container with a set of values.

**code sample**
```cpp
Sorted_vector<int> sv {1, 3, -1, 7, 0, 0}; // Sorted_vector sorts elements as needed
```

**enforcement**
- ???

---

### [C.104] Give a container a default constructor that sets it to empty

**reason**
To make it `Regular`.

**code sample**
```cpp
vector<Sorted_sequence<string>> vs(100);    // 100 Sorted_sequences each with the value ""
```

**enforcement**
- ???

---

### [C.109] If a resource handle has pointer semantics, provide `*` and `->`

**reason**
That's what is expected from pointers. Familiarity.

**enforcement**
- ???

---

### [C.120] Use class hierarchies to represent concepts with inherent hierarchical structure (only)

**reason**
Direct representation of ideas in code eases comprehension and maintenance. Do *not* use inheritance when simply having a data member will do.

**code example [good]**
```cpp
class DrawableUIElement {
public:
    virtual void render() const = 0;
    // ...
};

class AbstractButton : public DrawableUIElement {
public:
    virtual void onClick() = 0;
    // ...
};

class PushButton : public AbstractButton {
    void render() const override;
    void onClick() override;
    // ...
};

class Checkbox : public AbstractButton {
// ...
};
```

**code example [bad]**
```cpp
template<typename T>
class Container {
public:
    // list operations:
    virtual T& get() = 0;
    virtual void put(T&) = 0;
    virtual void insert(Position) = 0;
    // ...
    // vector operations:
    virtual T& operator[](int) = 0;
    virtual void sort() = 0;
    // ...
    // tree operations:
    virtual void balance() = 0;
    // ...
};
```

Here most overriding classes cannot implement most of the functions required in the interface well. Thus the base class becomes an implementation burden.

**enforcement**
- Look for classes with lots of members that do nothing but throw.
- Flag every use of a non-public base class `B` where the derived class `D` does not override a virtual function or access a protected member in `B`.

---

### [C.121] If a base class is used as an interface, make it a pure abstract class

**reason**
A class is more stable (less brittle) if it does not contain data. Interfaces should normally be composed entirely of public pure virtual functions and a default/empty virtual destructor.

**code example [good]**
```cpp
class My_interface {
public:
    // ... only pure virtual functions here ...
    virtual ~My_interface() {}   // or =default
};
```

**code example [bad]**
```cpp
class Goof {
public:
    // ... only pure virtual functions here ...
    // no virtual destructor
};

class Derived : public Goof {
    string s;
    // ...
};

void use()
{
    unique_ptr<Goof> p {new Derived{"here we go"}};
    f(p.get()); // use Derived through the Goof interface
    g(p.get()); // use Derived through the Goof interface
} // leak
```

The `Derived` is `delete`d through its `Goof` interface, so its `string` is leaked.

**enforcement**
- Warn on any class that contains data members and also has an overridable (non-`final`) virtual function that wasn't inherited from a base class.

---

### [C.122] Use abstract classes as interfaces when complete separation of interface and implementation is needed

**reason**
Such as on an ABI (link) boundary.

**code sample**
```cpp
struct Device {
    virtual ~Device() = default;
    virtual void write(span<const char> outbuf) = 0;
    virtual void read(span<char> inbuf) = 0;
};

class D1 : public Device {
    // ... data ...

    void write(span<const char> outbuf) override;
    void read(span<char> inbuf) override;
};

class D2 : public Device {
    // ... different data ...

    void write(span<const char> outbuf) override;
    void read(span<char> inbuf) override;
};
```

A user can now use `D1`s and `D2`s interchangeably through the interface provided by `Device`.

**enforcement**
- ???

---

### [C.126] An abstract class typically doesn't need a user-written constructor

**reason**
An abstract class typically does not have any data for a constructor to initialize.

**code sample**
```cpp
class Shape {
public:
    // no user-written constructor needed in abstract base class
    virtual Point center() const = 0;    // pure virtual
    virtual void move(Point to) = 0;
    // ... more pure virtual functions ...
    virtual ~Shape() {}                 // destructor
};

class Circle : public Shape {
public:
    Circle(Point p, int rad);           // constructor in derived class
    Point center() const override { return x; }
};
```

**enforcement**
- Flag abstract classes with constructors.

---

### [C.127] A class with a virtual function should have a virtual or protected destructor

**reason**
A class with a virtual function is usually used via a pointer to base. Usually, the last user has to call delete on a pointer to base, so the destructor should be public and virtual.

**code example [bad]**
```cpp
struct B {
    virtual int f() = 0;
    // ... no user-written destructor, defaults to public non-virtual ...
};

// bad: derived from a class without a virtual destructor
struct D : B {
    string s {"default"};
    // ...
};

void use()
{
    unique_ptr<B> p = make_unique<D>();
    // ...
} // undefined behavior, might call B::~B only and leak the string
```

**enforcement**
- A class with any virtual functions should have a destructor that is either public and virtual or else protected and non-virtual.
- Flag `delete` of a class with a virtual function but no virtual destructor.

---

### [C.128] Virtual functions should specify exactly one of `virtual`, `override`, or `final`

**reason**
Readability. Detection of mistakes. Writing explicit `virtual`, `override`, or `final` is self-documenting and enables the compiler to catch mismatch of types and/or names.

**code example [bad]**
```cpp
struct B {
    void f1(int);
    virtual void f2(int) const;
    virtual void f3(int);
    // ...
};

struct D : B {
    void f1(int);        // bad (hope for a warning): D::f1() hides B::f1()
    void f2(int) const;  // bad (but conventional and valid): no explicit override
    void f3(double);     // bad (hope for a warning): D::f3() hides B::f3()
    // ...
};
```

**code example [good]**
```cpp
struct Better : B {
    void f1(int) override;        // error (caught): Better::f1() hides B::f1()
    void f2(int) const override;
    void f3(double) override;     // error (caught): Better::f3() hides B::f3()
    // ...
};
```

**enforcement**
- Compare virtual function names in base and derived classes and flag uses of the same name that do not override.
- Flag overrides with neither `override` nor `final`.
- Flag function declarations that use more than one of `virtual`, `override`, and `final`.

---

### [C.129] When designing a class hierarchy, distinguish between implementation inheritance and interface inheritance

**reason**
Implementation details in an interface make the interface brittle. Data in a base class increases the complexity of implementing the base and can lead to replication of code.

**code example [bad]**
```cpp
class Shape {   // BAD, mixed interface and implementation
public:
    Shape();
    Shape(Point ce = {0, 0}, Color co = none): cent{ce}, col {co} { /* ... */}

    Point center() const { return cent; }
    Color color() const { return col; }

    virtual void rotate(int) = 0;
    virtual void move(Point p) { cent = p; redraw(); }

    virtual void redraw();

    // ...
private:
    Point cent;
    Color col;
};

class Circle : public Shape {
public:
    Circle(Point c, int r) : Shape{c}, rad{r} { /* ... */ }

    // ...
private:
    int rad;
};

class Triangle : public Shape {
public:
    Triangle(Point p1, Point p2, Point p3); // calculate center
    // ...
};
```

Problems: As the hierarchy grows and more data is added to `Shape`, the constructors get harder to write and maintain.

**code example [good]**
```cpp
class Shape {  // pure interface
public:
    virtual Point center() const = 0;
    virtual Color color() const = 0;

    virtual void rotate(int) = 0;
    virtual void move(Point p) = 0;

    virtual void redraw() = 0;

    // ...
};
```

**code sample**

Dual hierarchy example:

```cpp
class Shape {   // pure interface
public:
    virtual Point center() const = 0;
    virtual Color color() const = 0;
    virtual void rotate(int) = 0;
    virtual void move(Point p) = 0;
    virtual void redraw() = 0;
    // ...
};

class Circle : public virtual Shape {   // pure interface
public:
    virtual int radius() = 0;
    // ...
};

class Impl::Shape : public virtual ::Shape { // implementation
public:
    // constructors, destructor
    // ...
    Point center() const override { /* ... */ }
    Color color() const override { /* ... */ }
    void rotate(int) override { /* ... */ }
    void move(Point p) override { /* ... */ }
    void redraw() override { /* ... */ }
    // ...
};

class Impl::Circle : public virtual ::Circle, public Impl::Shape {   // implementation
public:
    // constructors, destructor
    int radius() override { /* ... */ }
    // ...
};

// Smiley -> Circle -> Shape (interface)
// Impl::Smiley -> Impl::Circle -> Impl::Shape (implementation)

void work_with_shape(Shape&);

int user()
{
    Impl::Smiley my_smiley{ /* args */ };   // create concrete shape
    // ...
    my_smiley.some_member();        // use implementation class directly
    // ...
    work_with_shape(my_smiley);     // use implementation through abstract interface
    // ...
}
```

**enforcement**
- Flag a derived to base conversion to a base with both data and virtual functions.

---

### [C.130] For making deep copies of polymorphic classes prefer a virtual `clone` function instead of public copy construction/assignment

**reason**
Copying a polymorphic class is discouraged due to the slicing problem, see C.67. If you really need copy semantics, copy deeply.

**code example [bad]**
```cpp
class B {
public:
    B() = default;
    virtual ~B() = default;
    virtual gsl::owner<B*> clone() const = 0;
protected:
     B(const B&) = default;
     B& operator=(const B&) = default;
     B(B&&) noexcept = default;
     B& operator=(B&&) noexcept = default;
    // ...
};

class D : public B {
public:
    gsl::owner<D*> clone() const override
    {
        return new D{*this};
    };
};
```

**enforcement**
- ???

---

### [C.131] Avoid trivial getters and setters

**reason**
A trivial getter or setter adds no semantic value; the data item could just as well be `public`.

**code example [bad]**
```cpp
class Point {   // Bad: verbose
    int x;
    int y;
public:
    Point(int xx, int yy) : x{xx}, y{yy} { }
    int get_x() const { return x; }
    void set_x(int xx) { x = xx; }
    int get_y() const { return y; }
    void set_y(int yy) { y = yy; }
    // no behavioral member functions
};
```

Consider making such a class a `struct`:

```cpp
struct Point {
    int x {0};
    int y {0};
};
```

**enforcement**
- Flag multiple `get` and `set` member functions that simply access a member without additional semantics.

---

### [C.132] Don't make a function `virtual` without reason

**reason**
Redundant `virtual` increases run-time and object-code size. A virtual function can be overridden and is thus open to mistakes in a derived class.

**code example [bad]**
```cpp
template<class T>
class Vector {
public:
    // ...
    virtual int size() const { return sz; }   // bad: what good could a derived class do?
private:
    T* elem;   // the elements
    int sz;    // number of elements
};
```

**enforcement**
- Flag a class with virtual functions but no derived classes.
- Flag a class where all member functions are virtual and have implementations.

---

### [C.133] Avoid `protected` data

**reason**
`protected` data is a source of complexity and errors. `protected` data complicates the statement of invariants.

**code example [bad]**
```cpp
class Shape {
public:
    // ... interface functions ...
protected:
    // data for use in derived classes:
    Color fill_color;
    Color edge_color;
    Style st;
};
```

Now it is up to every derived `Shape` to manipulate the protected data correctly. This has been popular, but also a major source of maintenance problems.

**enforcement**
- Flag classes with `protected` data.

---

### [C.134] Ensure all non-`const` data members have the same access level

**reason**
Prevention of logical confusion leading to errors. If the non-`const` data members don't have the same access level, the type is confused about what it's trying to do.

**enforcement**
- Flag any class that has non-`const` data members with different access levels.

---

### [C.135] Use multiple inheritance to represent multiple distinct interfaces

**reason**
Not all classes will necessarily support all interfaces, and not all callers will necessarily want to deal with all operations.

**code sample**
```cpp
class iostream : public istream, public ostream {   // very simplified
    // ...
};
```

**enforcement**
- ???

---

### [C.136] Use multiple inheritance to represent the union of implementation attributes

**reason**
Some forms of mixins have state and often operations on that state.

**code sample**
```cpp
class iostream : public istream, public ostream {   // very simplified
    // ...
};
```

**enforcement**
- ???

---

### [C.137] Use `virtual` bases to avoid overly general base classes

**reason**
Allow separation of shared data and interface.

**code sample**
```cpp
struct Interface {
    virtual void f();
    virtual int g();
    // ... no data here ...
};

class Utility {  // with data
    void utility1();
    virtual void utility2();    // customization point
public:
    int x;
    int y;
};

class Derive1 : public Interface, virtual protected Utility {
    // override Interface functions
    // Maybe override Utility virtual functions
    // ...
};

class Derive2 : public Interface, virtual protected Utility {
    // override Interface functions
    // Maybe override Utility virtual functions
    // ...
};
```

**enforcement**
- Flag mixed interface and implementation hierarchies.

---

### [C.138] Create an overload set for a derived class and its bases with `using`

**reason**
Without a using declaration, member functions in the derived class hide the entire inherited overload sets.

**code example [bad]**
```cpp
#include <iostream>
class B {
public:
    virtual int f(int i) { std::cout << "f(int): "; return i; }
    virtual double f(double d) { std::cout << "f(double): "; return d; }
    virtual ~B() = default;
};
class D: public B {
public:
    int f(int i) override { std::cout << "f(int): "; return i + 1; }
};
int main()
{
    D d;
    std::cout << d.f(2) << '\n';   // prints "f(int): 3"
    std::cout << d.f(2.3) << '\n'; // prints "f(int): 3"
}
```

**code example [good]**
```cpp
class D: public B {
public:
    int f(int i) override { std::cout << "f(int): "; return i + 1; }
    using B::f; // exposes f(double)
};
```

For variadic bases, C++17 introduced a variadic form of the using-declaration:

```cpp
template<class... Ts>
struct Overloader : Ts... {
    using Ts::operator()...; // exposes operator() from every base
};
```

**enforcement**
- Diagnose name hiding.

---

### [C.139] Use `final` on classes sparingly

**reason**
Capping a hierarchy with `final` classes is rarely needed for logical reasons and can be damaging to the extensibility of a hierarchy.

**code example [bad]**
```cpp
class Widget { /* ... */ };

// nobody will ever want to improve My_widget (or so you thought)
class My_widget final : public Widget { /* ... */ };

class My_improved_widget : public My_widget { /* ... */ };  // error: can't do that
```

**enforcement**
- Flag uses of `final` on classes.

---

### [C.140] Do not provide different default arguments for a virtual function and an overrider

**reason**
That can cause confusion: An overrider does not inherit default arguments.

**code example [bad]**
```cpp
class Base {
public:
    virtual int multiply(int value, int factor = 2) = 0;
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    int multiply(int value, int factor = 10) override;
};

Derived d;
Base& b = d;

b.multiply(10);  // these two calls will call the same function but
d.multiply(10);  // with different arguments and so different results
```

**enforcement**
- Flag default arguments on virtual functions if they differ between base and derived declarations.

---

### [C.145] Access polymorphic objects through pointers and references

**reason**
If you have a class with a virtual function, you don't (in general) know which class provided the function to be used.

**code example [bad]**
```cpp
struct B { int a; virtual int f(); virtual ~B() = default };
struct D : B { int b; int f() override; };

void use(B b)
{
    D d;
    B b2 = d;   // slice
    B b3 = b;
}

void use2()
{
    D d;
    use(d);   // slice
}
```

Both `d`s are sliced. You can safely access a named polymorphic object in the scope of its definition:

```cpp
void use3()
{
    D d;
    d.f();   // OK
}
```

**enforcement**
- Flag all slicing.

---

### [C.146] Use `dynamic_cast` where class hierarchy navigation is unavoidable

**reason**
`dynamic_cast` is checked at run time.

**code sample**
```cpp
struct B {   // an interface
    virtual void f();
    virtual void g();
    virtual ~B();
};

struct D : B {   // a wider interface
    void f() override;
    virtual void h();
};

void user(B* pb)
{
    if (D* pd = dynamic_cast<D*>(pb)) {
        // ... use D's interface ...
    }
    else {
        // ... make do with B's interface ...
    }
}
```

Use of the other casts can violate type safety:

```cpp
void user2(B* pb)   // bad
{
    D* pd = static_cast<D*>(pb);    // I know that pb really points to a D; trust me
    // ... use D's interface ...
}

void user3(B* pb)    // unsafe
{
    if (some_condition) {
        D* pd = static_cast<D*>(pb);   // I know that pb really points to a D; trust me
        // ... use D's interface ...
    }
    else {
        // ... make do with B's interface ...
    }
}

void f()
{
    B b;
    user(&b);   // OK
    user2(&b);  // bad error
    user3(&b);  // OK *if* the programmer got the some_condition check right
}
```

Home-brew RTTI pitfall:

```cpp
struct B {
    const char* name {"B"};
    virtual const char* id() const { return name; }
    // ...
};

struct D : B {
    const char* name {"D"};
    const char* id() const override { return name; }
    // ...
};

void use()
{
    B* pb1 = new B;
    B* pb2 = new D;

    cout << pb1->id(); // "B"
    cout << pb2->id(); // "D"

    if (pb2->id() == "D") {         // looks innocent
        D* pd = static_cast<D*>(pb2);
        // ...
    }
    // ...
}
```

The result of `pb2->id() == "D"` is actually implementation defined.

**enforcement**
- Flag all uses of `static_cast` for downcasts, including C-style casts that perform a `static_cast`.

---

### [C.147] Use `dynamic_cast` to a reference type when failure to find the required class is considered an error

**reason**
Casting to a reference expresses that you intend to end up with a valid object, so the cast must succeed. `dynamic_cast` will then throw if it does not succeed.

**code sample**
```cpp
std::string f(Base& b)
{
    return dynamic_cast<Derived&>(b).to_string();
}
```

**enforcement**
- ???

---

### [C.148] Use `dynamic_cast` to a pointer type when failure to find the required class is considered a valid alternative

**reason**
The `dynamic_cast` conversion allows to test whether a pointer is pointing at a polymorphic object that has a given class in its hierarchy.

**code sample**
```cpp
void add(Shape* const item)
{
  // Ownership is always taken
  owned_shapes.emplace_back(item);

  // Check the Geometric_attributes and add the shape to none/one/some/all of the views

  if (auto even = dynamic_cast<Even_sided*>(item))
  {
    view_of_evens.emplace_back(even);
  }

  if (auto trisym = dynamic_cast<Trilaterally_symmetrical*>(item))
  {
    view_of_trisyms.emplace_back(trisym);
  }
}
```

**enforcement**
- (Complex) Unless there is a null test on the result of a `dynamic_cast` of a pointer type, warn upon dereference of the pointer.

---

### [C.149] Use `unique_ptr` or `shared_ptr` to avoid forgetting to `delete` objects created using `new`

**reason**
Avoid resource leaks.

**code sample**
```cpp
void use(int i)
{
    auto p = new int {7};           // bad: initialize local pointers with new
    auto q = make_unique<int>(9);   // ok: guarantee the release of the memory-allocated for 9
    if (0 < i) return;              // maybe return and leak
    delete p;                       // too late
}
```

**enforcement**
- Flag initialization of a naked pointer with the result of a `new`.
- Flag `delete` of local variable.

---

### [C.150] Use `make_unique()` to construct objects owned by `unique_ptr`s

See R.23.

**enforcement**
- See R.23.

---

### [C.151] Use `make_shared()` to construct objects owned by `shared_ptr`s

See R.22.

**enforcement**
- See R.22.

---

### [C.152] Never assign a pointer to an array of derived class objects to a pointer to its base

**reason**
Subscripting the resulting base pointer will lead to invalid object access and probably to memory corruption.

**code example [bad]**
```cpp
struct B { int x; };
struct D : B { int y; };

void use(B*);

D a[] = { {1, 2}, {3, 4}, {5, 6} };
B* p = a;     // bad: a decays to &a[0] which is converted to a B*
p[1].x = 7;   // overwrite a[0].y

use(a);       // bad: a decays to &a[0] which is converted to a B*
```

**enforcement**
- Flag all combinations of array decay and base to derived conversions.
- Pass an array as a `span` rather than as a pointer, and don't let the array name suffer a derived-to-base conversion before getting into the `span`.

---

### [C.153] Prefer virtual function to casting

**reason**
A virtual function call is safe, whereas casting is error-prone. A virtual function call reaches the most derived function, whereas a cast might reach an intermediate class and therefore give a wrong result.

**enforcement**
- See C.146.

---

### [C.160] Define operators primarily to mimic conventional usage

**reason**
Minimize surprises.

**code example [bad]**
```cpp
class X {
public:
    // ...
    X& operator=(const X&); // member function defining assignment
    friend bool operator==(const X&, const X&); // == needs access to representation
                                                // after a = b we have a == b
    // ...
};
```

**code example [bad]**
```cpp
X operator+(X a, X b) { return a.v - b.v; }   // bad: makes + subtract
```

**enforcement**
- Possibly impossible.

---

### [C.161] Use non-member functions for symmetric operators

**reason**
If you use member functions, you need two. Unless you use a non-member function for (say) `==`, `a == b` and `b == a` will be subtly different.

**code sample**
```cpp
bool operator==(Point a, Point b) { return a.x == b.x && a.y == b.y; }
```

**enforcement**
- Flag member operator functions.

---

### [C.162] Overload operations that are roughly equivalent

**reason**
Having different names for logically equivalent operations on different argument types is confusing, leads to encoding type information in function names, and inhibits generic programming.

**code sample**
```cpp
void print(int a);
void print(int a, int base);
void print(const string&);
```

These three functions all print their arguments (appropriately). Conversely:

```cpp
void print_int(int a);
void print_based(int a, int base);
void print_string(const string&);
```

Adding to the name just introduced verbosity and inhibits generic code.

**enforcement**
- ???

---

### [C.163] Overload only for operations that are roughly equivalent

**reason**
Having the same name for logically different functions is confusing and leads to errors when using generic programming.

**code example [good]**
```cpp
void open_gate(Gate& g);   // remove obstacle from garage exit lane
void fopen(const char* name, const char* mode);   // open file
```

The two operations are fundamentally different (and unrelated) so it is good that their names differ. Conversely:

```cpp
void open(Gate& g);   // remove obstacle from garage exit lane
void open(const char* name, const char* mode ="r");   // open file
```

The two operations are still fundamentally different but the names have been reduced to their (common) minimum, opening opportunities for confusion.

**enforcement**
- ???

---

### [C.164] Avoid implicit conversion operators

**reason**
Implicit conversions can be essential but often cause surprises.

**code example [bad]**
```cpp
struct S1 {
    string s;
    // ...
    operator char*() { return s.data(); }  // BAD, likely to cause surprises
};

struct S2 {
    string s;
    // ...
    explicit operator char*() { return s.data(); }
};

void f(S1 s1, S2 s2)
{
    char* x1 = s1;     // OK, but can cause surprises in many contexts
    char* x2 = s2;     // error (and that's usually a good thing)
    char* x3 = static_cast<char*>(s2); // we can be explicit (on your head be it)
}
```

The surprising and potentially damaging implicit conversion can occur in hard-to-spot contexts:

```cpp
S1 ff();

char* g()
{
    return ff();
}
```

The string returned by `ff()` is destroyed before the returned pointer into it can be used.

**enforcement**
- Flag all non-explicit conversion operators.

---

### [C.165] Use `using` for customization points

**reason**
To find function objects and functions defined in a separate namespace to "customize" a common function.

**code sample**
```cpp
namespace N {
    My_type X { /* ... */ };
    void swap(X&, X&);   // optimized swap for N::X
    // ...
}

void f1(N::X& a, N::X& b)
{
    std::swap(a, b);   // probably not what we wanted: calls std::swap()
}

void f2(N::X& a, N::X& b)
{
    swap(a, b);   // calls N::swap
}

void f3(N::X& a, N::X& b)
{
    using std::swap;  // make std::swap available
    swap(a, b);        // calls N::swap if it exists, otherwise std::swap
}
```

**enforcement**
- Unlikely, except for known customization points, such as `swap`.

---

### [C.166] Overload unary `&` only as part of a system of smart pointers and references

**reason**
The `&` operator is fundamental in C++. Many parts of the C++ semantics assume its default meaning.

**code sample**
```cpp
class Ptr { // a somewhat smart pointer
    Ptr(X* pp) : p(pp) { /* check */ }
    X* operator->() { /* check */ return p; }
    X operator[](int i);
    X operator*();
private:
    T* p;
};

class X {
    Ptr operator&() { return Ptr{this}; }
    // ...
};
```

**enforcement**
- Tricky. Warn if `&` is user-defined without also defining `->` for the result type.

---

### [C.167] Use an operator for an operation with its conventional meaning

**reason**
Readability. Convention. Reusability. Support for generic code.

**code example [good]**
```cpp
void cout_my_class(const My_class& c) // confusing, not conventional, not generic
{
    std::cout << /* class members here */;
}

std::ostream& operator<<(std::ostream& os, const my_class& c) // OK
{
    return os << /* class members here */;
}
```

By itself, `cout_my_class` would be OK, but it is not usable/composable with code that relies on the `<<` convention:

```cpp
My_class var { /* ... */ };
// ...
cout << "var = " << var << '\n';
```

**enforcement**
- Tricky. Requires semantic insight.

---

### [C.168] Define overloaded operators in the namespace of their operands

**reason**
Readability. Ability for find operators using ADL. Avoiding inconsistent definition in different namespaces.

**code example [good]**
```cpp
struct S { };
S operator+(S, S);   // OK: in the same namespace as S, and even next to S
S s;

S r = s + s;
```

```cpp
namespace N {
    struct S { };
    S operator+(S, S);   // OK: in the same namespace as S, and even next to S
}

N::S s;

S r = s + s;  // finds N::operator+() by ADL
```

**code example [bad]**
```cpp
struct S { };
S s;

namespace N {
    bool operator!(S a) { return true; }
    bool not_s = !s;
}

namespace M {
    bool operator!(S a) { return false; }
    bool not_s = !s;
}
```

Here, the meaning of `!s` differs in `N` and `M`.

**enforcement**
- Flag operator definitions that are not in the namespace of their operands.

---

### [C.170] If you feel like overloading a lambda, use a generic lambda

**reason**
You cannot overload by defining two different lambdas with the same name.

**code example [good]**
```cpp
void f(int);
void f(double);
auto f = [](char);   // error: cannot overload variable and function

auto g = [](int) { /* ... */ };
auto g = [](double) { /* ... */ };   // error: cannot overload variables

auto h = [](auto) { /* ... */ };   // OK
```

**enforcement**
- The compiler catches the attempt to overload a lambda.

---

### [C.180] Use `union`s to save memory

**reason**
A `union` allows a single piece of memory to be used for different types of objects at different times.

**code sample**
```cpp
union Value {
    int x;
    double d;
};

Value v = { 123 };  // now v holds an int
cout << v.x << '\n';    // write 123
v.d = 987.654;  // now v holds a double
cout << v.d << '\n';    // write 987.654
```

Short-string optimization:

```cpp
constexpr size_t buffer_size = 16; // Slightly larger than the size of a pointer

class Immutable_string {
public:
    Immutable_string(const char* str) :
        size(strlen(str))
    {
        if (size < buffer_size)
            strcpy_s(string_buffer, buffer_size, str);
        else {
            string_ptr = new char[size + 1];
            strcpy_s(string_ptr, size + 1, str);
        }
    }

    ~Immutable_string()
    {
        if (size >= buffer_size)
            delete[] string_ptr;
    }

    const char* get_str() const
    {
        return (size < buffer_size) ? string_buffer : string_ptr;
    }

private:
    // If the string is short enough, we store the string itself
    // instead of a pointer to the string.
    union {
        char* string_ptr;
        char string_buffer[buffer_size];
    };

    const size_t size;
};
```

**enforcement**
- ???

---

### [C.181] Avoid "naked" `union`s

**reason**
A *naked union* is a union without an associated indicator which member (if any) it holds, so that the programmer has to keep track. Naked unions are a source of type errors.

**code example [bad]**
```cpp
union Value {
    int x;
    double d;
};

Value v;
v.d = 987.654;  // v holds a double
```

So far, so good, but we can easily misuse the `union`:

```cpp
cout << v.x << '\n';    // BAD, undefined behavior: v holds a double, but we read it as an int
```

```cpp
v.x = 123;
cout << v.d << '\n';    // BAD: undefined behavior
```

The C++17 `variant` type does that for you:

```cpp
variant<int, double> v;
v = 123;        // v holds an int
int x = get<int>(v);
v = 123.456;    // v holds a double
double w = get<double>(v);
```

**enforcement**
- ???

---

### [C.182] Use anonymous `union`s to implement tagged unions

**reason**
A well-designed tagged union is type safe. An *anonymous* union simplifies the definition of a class with a (tag, union) pair.

**code example [good]**
```cpp
class Value { // two alternative representations represented as a union
private:
    enum class Tag { number, text };
    Tag type; // discriminant

    union { // representation (note: anonymous union)
        int i;
        string s; // string has default constructor, copy operations, and destructor
    };
public:
    struct Bad_entry { }; // used for exceptions

    ~Value();
    Value& operator=(const Value&);   // necessary because of the string variant
    Value(const Value&);
    // ...
    int number() const;
    string text() const;

    void set_number(int n);
    void set_text(const string&);
    // ...
};

int Value::number() const
{
    if (type != Tag::number) throw Bad_entry{};
    return i;
}

string Value::text() const
{
    if (type != Tag::text) throw Bad_entry{};
    return s;
}

void Value::set_number(int n)
{
    if (type == Tag::text) {
        s.~string();      // explicitly destroy string
        type = Tag::number;
    }
    i = n;
}

void Value::set_text(const string& ss)
{
    if (type == Tag::text)
        s = ss;
    else {
        new(&s) string{ss};   // placement new: explicitly construct string
        type = Tag::text;
    }
}

Value& Value::operator=(const Value& e)   // necessary because of the string variant
{
    if (type == Tag::text && e.type == Tag::text) {
        s = e.s;    // usual string assignment
        return *this;
    }

    if (type == Tag::text) s.~string(); // explicit destroy

    switch (e.type) {
    case Tag::number:
        i = e.i;
        break;
    case Tag::text:
        new(&s) string(e.s);   // placement new: explicit construct
    }

    type = e.type;
    return *this;
}

Value::~Value()
{
    if (type == Tag::text) s.~string(); // explicit destroy
}
```

**enforcement**
- ???

---

### [C.183] Don't use a `union` for type punning

**reason**
It is undefined behavior to read a `union` member with a different type from the one with which it was written. Such punning is invisible and a source of errors.

**code example [bad]**
```cpp
union Pun {
    int x;
    unsigned char c[sizeof(int)];
};

void bad(Pun& u)
{
    u.x = 'x';
    cout << u.c[0] << '\n';     // undefined behavior
}
```

If you wanted to see the bytes of an `int`, use a (named) cast:

```cpp
void if_you_must_pun(int& x)
{
    auto p = reinterpret_cast<std::byte*>(&x);
    cout << to_integer<unsigned>(p[0]) << '\n'; // OK; better
    // ...
}
```

Modern C++ introduced `std::byte` (C++17) and `std::bit_cast` (C++20) to facilitate operations on raw object representations.

**enforcement**
- ???
