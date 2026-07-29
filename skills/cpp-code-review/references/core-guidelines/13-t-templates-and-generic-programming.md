# T: Templates and generic programming

## Table of Contents

**Generic programming:** T.1-T.5 | **Concept use:** T.10-T.13
**Concept definition:** T.20-T.26 | **Template interfaces:** T.40-T.49
**Template definitions:** T.60-T.69 | **Template hierarchies:** T.80-T.84
**Variadic templates:** T.100-T.103 | **Metaprogramming:** T.120-T.125
**Other:** T.140-T.150

## T.gp: Generic programming

---

### [T.1] Use templates to raise the level of abstraction of code

**reason**
Generality. Reuse. Efficiency. Encourages consistent definition of user types.

**code example [bad]**
```cpp
template<typename T>
    requires Incrementable<T>
T sum1(vector<T>& v, T s)
{
    for (auto x : v) s += x;
    return s;
}

template<typename T>
    requires Simple_number<T>
T sum2(vector<T>& v, T s)
{
    for (auto x : v) s = s + x;
    return s;
}
```
Overconstrained implementers of `sum1` and `sum2`.

**code example [good]**
```cpp
template<typename T>
    requires Arithmetic<T>
T sum(vector<T>& v, T s)
{
    for (auto x : v) s += x;
    return s;
}
```

**enforcement**
- Flag algorithms with "overly simple" requirements, such as direct use of specific operators without a concept.

---

### [T.2] Use templates to express algorithms that apply to many argument types

**reason**
Generality. Minimizing the amount of source code. Interoperability. Reuse.

**code example [good]**
```cpp
template<typename Iter, typename Val>
    // requires Input_iterator<Iter>
    //       && Equality_comparable<Value_type<Iter>, Val>
Iter find(Iter b, Iter e, Val v)
{
    // ...
}
```

**enforcement**
- Hard, probably needs a human.

---

### [T.3] Use templates to express containers and ranges

**reason**
Containers need an element type. Expressing that as a template argument is general, reusable, and type safe.

**code example [good]**
```cpp
template<typename T>
    // requires Regular<T>
class Vector {
    // ...
    T* elem;   // points to sz Ts
    int sz;
};

Vector<double> v(10);
v[7] = 9.9;
```

**code example [bad]**
```cpp
class Container {
    // ...
    void* elem;   // points to size elements of some type
    int sz;
};

Container c(10, sizeof(double));
((double*) c.elem)[7] = 9.9;
```

**enforcement**
- Flag uses of `void*`s and casts outside low-level implementation code.

---

### [T.4] Use templates to express syntax tree manipulation

**reason**
Expression templates, AST manipulation at compile time.

**enforcement**
- No specific enforcement.

---

### [T.5] Combine generic and OO techniques to amplify their strengths, not their costs

**reason**
Generic and OO techniques are complementary.

**code sample**
```cpp
// Static helps dynamic: Use static polymorphism to implement dynamically polymorphic interfaces.
class Command {
    // pure virtual functions
};

template</*...*/>
class ConcreteCommand : public Command {
    // implement virtuals
};
```

**code sample**
```cpp
// Dynamic helps static: type erasure
class Object {
public:
    template<typename T>
    Object(T&& obj)
        : concept_(std::make_shared<ConcreteCommand<T>>(std::forward<T>(obj))) {}

    int get_id() const { return concept_->get_id(); }

private:
    struct Command {
        virtual ~Command() {}
        virtual int get_id() const = 0;
    };

    template<typename T>
    struct ConcreteCommand final : Command {
        ConcreteCommand(T&& obj) noexcept : object_(std::forward<T>(obj)) {}
        int get_id() const final { return object_.get_id(); }
    private:
        T object_;
    };

    std::shared_ptr<Command> concept_;
};

Object o(Bar{});
Object o2(Foo{});
```

**enforcement**
- See the reference to more specific rules.

---

## T.con-use: Concept use

---

### [T.10] Specify concepts for all template arguments

**reason**
Correctness and readability. A concept dramatically improves documentation and error handling for the template.

**code sample**
```cpp
template<typename Iter, typename Val>
    requires input_iterator<Iter>
             && equality_comparable_with<iter_value_t<Iter>, Val>
Iter find(Iter b, Iter e, Val v)
{
    // ...
}

// or equivalently and more succinctly:
template<input_iterator Iter, typename Val>
    requires equality_comparable_with<iter_value_t<Iter>, Val>
Iter find(Iter b, Iter e, Val v)
{
    // ...
}
```

**enforcement**
- Flag template type arguments without concepts.

---

### [T.11] Whenever possible use standard concepts

**reason**
"Standard" concepts save work, are better thought out, and improve interoperability.

**code sample**
```cpp
// don't define this: sortable is in <iterator>
template<typename T>
concept Ordered_container = Sequence<T> && Random_access<Iterator<T>> && Ordered<Value_type<T>>;

void sort(Ordered_container auto& s);

// better: just use sortable
void sort(sortable auto& s);
```

**enforcement**
- Hard. Look for unconstrained arguments and "homebrew" concepts without axioms.

---

### [T.12] Prefer concept names over `auto` for local variables

**reason**
`auto` is the weakest concept. Concept names convey more meaning.

**code sample**
```cpp
vector<string> v{ "abc", "xyz" };
auto& x = v.front();        // bad
String auto& s = v.front(); // good (String is a GSL concept)
```

**enforcement**
- No specific enforcement.

---

### [T.13] Prefer the shorthand notation for simple, single-type argument concepts

**reason**
Readability. Direct expression of an idea.

**code example [good]**
```cpp
template<typename T>       // Correct but verbose
    requires sortable<T>
void sort(T&);

template<sortable T>       // Better
void sort(T&);

void sort(sortable auto&); // Best
```

**enforcement**
- Later, flag declarations that first introduce a typename and then constrain it with a simple concept.

---

## T.concepts.def: Concept definition rules

---

### [T.20] Avoid "concepts" without meaningful semantics

**reason**
Concepts are meant to express semantic notions. Simple constraints like "has a `+` operator" should only be building blocks.

**code example [bad]**
```cpp
template<typename T>
concept Addable = requires(T a, T b) { a + b; };

template<Addable N>
auto algo(const N& a, const N& b)
{
    return a + b;
}

int x = 7;
int y = 9;
auto z = algo(x, y);   // z = 16

string xx = "7";
string yy = "9";
auto zz = algo(xx, yy);   // zz = "79" -- probably not intended
```

**code example [good]**
```cpp
template<typename T>
concept Number = requires(T a, T b) { a + b; a - b; a * b; a / b; };

template<Number N>
auto algo(const N& a, const N& b)
{
    return a + b;
}

string xx = "7";
string yy = "9";
auto zz = algo(xx, yy);   // error: string is not a Number
```

**enforcement**
- Flag single-operation `concepts` when used outside the definition of other `concepts`.

---

### [T.21] Require a complete set of operations for a concept

**reason**
Ease of comprehension. Improved interoperability.

**code example [bad]**
```cpp
template<typename T> concept Subtractable = requires(T a, T b) { a - b; };
// Makes no semantic sense. You need at least + to make - meaningful.
```

**code example [good]**
```cpp
class Minimal {
    // ...
};

bool operator==(const Minimal&, const Minimal&);
bool operator<(const Minimal&, const Minimal&);
Minimal operator+(const Minimal&, const Minimal&);
// no other operators

void f(Minimal x, Minimal y)
{
    if (!(x == y)) { /* ... */ }    // OK
    if (x != y) { /* ... */ }       // surprise! error

    while (!(x < y)) { /* ... */ }  // OK
    while (x >= y) { /* ... */ }    // surprise! error

    x = x + y;          // OK
    x += y;             // surprise! error
}
```

**enforcement**
- Flag classes that support "odd" subsets of a set of operators.

---

### [T.22] Specify axioms for concepts

**reason**
A meaningful/useful concept has a semantic meaning. Expressing these semantics can catch conceptual errors.

**code sample**
```cpp
template<typename T>
    // axiom(T a, T b) { a + b == b + a; a - a == 0; a * (b + c) == a * b + a * c; }
    concept Number = requires(T a, T b) {
        { a + b } -> convertible_to<T>;
        { a - b } -> convertible_to<T>;
        { a * b } -> convertible_to<T>;
        { a / b } -> convertible_to<T>;
    };
```

**enforcement**
- Look for the word "axiom" in concept definition comments.

---

### [T.23] Differentiate a refined concept from its more general case by adding new use patterns

**reason**
Otherwise they cannot be distinguished automatically by the compiler.

**code sample**
```cpp
template<typename I>
concept Input_iter = requires(I iter) { ++iter; };

template<typename I>
concept Fwd_iter = Input_iter<I> && requires(I iter) { iter++; };
```

**enforcement**
- Flag a concept that has exactly the same requirements as another already-seen concept.

---

### [T.24] Use tag classes or traits to differentiate concepts that differ only in semantics

**reason**
Two concepts requiring the same syntax but having different semantics lead to ambiguity unless differentiated.

**code sample**
```cpp
template<typename I>    // iterator providing random access
concept RA_iter = ...;

template<typename I>    // iterator providing random access to contiguous data
concept Contiguous_iter =
    RA_iter<I> && is_contiguous_v<I>;  // using is_contiguous trait
```

**enforcement**
- The compiler flags ambiguous use of identical concepts.

---

### [T.25] Avoid complementary constraints

**reason**
Functions with complementary requirements expressed using negation are brittle.

**code sample**
```cpp
// bad:
template<typename T>
    requires !C<T>
void f();

template<typename T>
    requires C<T>
void f();

// better:
template<typename T>   // general template
    void f();

template<typename T>   // specialization by concept
    requires C<T>
void f();
```

**enforcement**
- Flag pairs of functions with `C<T>` and `!C<T>` constraints.

---

### [T.26] Prefer to define concepts in terms of use-patterns rather than simple syntax

**reason**
The definition is more readable and corresponds directly to what a user has to write.

**code sample**
```cpp
template<typename T> concept Equality = requires(T a, T b) {
    { a == b } -> std::convertible_to<bool>;
    { a != b } -> std::convertible_to<bool>;
    // axiom { !(a == b) == (a != b) }
};
```

**enforcement**
- No specific enforcement.

---

## Template interfaces

---

### [T.40] Use function objects to pass operations to algorithms

**reason**
Function objects can carry more information through an interface. In general, better performance than pointers to functions.

**code example [good]**
```cpp
bool greater(double x, double y) { return x > y; }
sort(v, greater);                                    // pointer to function: potentially slow
sort(v, [](double x, double y) { return x > y; });   // function object
sort(v, std::greater{});                             // function object

bool greater_than_7(double x) { return x > 7; }
auto x = find_if(v, greater_than_7);                 // pointer to function: inflexible
auto y = find_if(v, [](double x) { return x > 7; }); // function object: carries the needed data
auto z = find_if(v, Greater_than<double>(7));        // function object: carries the needed data
```

**enforcement**
- Flag pointer to function template arguments.

---

### [T.41] Require only essential properties in a template's concepts

**reason**
Keep interfaces simple and stable.

**code sample**
```cpp
void sort(sortable auto& s)  // sort sequence s
{
    if (debug) cerr << "enter sort( " << s <<  ")\n";
    // ...
}

// Should NOT be rewritten to require Streamable:
template<sortable S>
    requires Streamable<S>
void sort(S& s)  // sort sequence s
{
    if (debug) cerr << "enter sort( " << s <<  ")\n";
    // ...
}
```

**enforcement**
- No specific enforcement.

---

### [T.42] Use template aliases to simplify notation and hide implementation details

**reason**
Improved readability. Implementation hiding.

**code example [good]**
```cpp
template<typename T, size_t N>
class Matrix {
    // ...
    using Iterator = typename std::vector<T>::iterator;
    // ...
};

template<typename T>
using Value_type = typename container_traits<T>::value_type;
```

**enforcement**
- Flag use of `typename` as a disambiguator outside `using` declarations.

---

### [T.43] Prefer `using` over `typedef` for defining aliases

**reason**
Improved readability. `using` can be used for template aliases, `typedef` can't.

**code example [good]**
```cpp
typedef int (*PFI)(int);   // OK, but convoluted

using PFI2 = int (*)(int);   // OK, preferred

template<typename T>
typedef int (*PFT)(T);      // error

template<typename T>
using PFT2 = int (*)(T);   // OK
```

**enforcement**
- Flag uses of `typedef`.

---

### [T.44] Use function templates to deduce class template argument types (where feasible)

**reason**
Writing the template argument types explicitly can be tedious and unnecessarily verbose.

**code example [good]**
```cpp
tuple<int, string, double> t1 = {1, "Hamlet", 3.14};   // explicit type
auto t2 = make_tuple(1, "Ophelia"s, 3.14);         // better; deduced type

// C++17: Template parameter deduction for constructors
tuple t1 = {1, "Hamlet"s, 3.14}; // deduced: tuple<int, string, double>
```

**enforcement**
- Flag uses where an explicitly specialized type exactly matches the types of the arguments used.

---

### [T.46] Require template arguments to be at least semiregular

**reason**
Readability. Preventing surprises and errors.

**code sample**
```cpp
class X {
public:
    explicit X(int);
    X(const X&);
    X operator=(const X&);
    X(X&&) noexcept;
    X& operator=(X&&) noexcept;
    ~X();
    // ... no more constructors ...
};

X x {1};              // fine
X y = x;              // fine
std::vector<X> v(10); // error: no default constructor
```

**enforcement**
- Flag types used as template arguments that are not at least semiregular.

---

### [T.47] Avoid highly visible unconstrained templates with common names

**reason**
An unconstrained template argument is a perfect match for anything, so it can be preferred over more specific types that require minor conversions. Particularly dangerous with ADL.

**code example [bad]**
```cpp
namespace Bad {
    struct S { int m; };
    template<typename T1, typename T2>
    bool operator==(T1, T2) { cout << "Bad\n"; return true; }
}

namespace T0 {
    bool operator==(int, Bad::S) { cout << "T0\n"; return true; }

    void test()
    {
        Bad::S bad{ 1 };
        vector<int> v(10);
        bool b = 1 == bad;            // prints "T0"
        bool b2 = v.size() == bad;    // prints "Bad" -- v.size() is unsigned, needs conversion
    }
}
```

**enforcement**
- Flag templates defined in a namespace where concrete types are also defined.

---

### [T.48] If your compiler does not support concepts, fake them with `enable_if`

**reason**
`enable_if` can be used to conditionally define functions and to select among a set of functions.

**code sample**
```cpp
template<typename T>
enable_if_t<is_integral_v<T>>
f(T v)
{
    // ...
}

// Equivalent to:
template<Integral T>
void f(T v)
{
    // ...
}
```

**enforcement**
- No specific enforcement.

---

### [T.49] Where possible, avoid type-erasure

**reason**
Type erasure incurs an extra level of indirection by hiding type information behind a separate compilation boundary.

**enforcement**
- No specific enforcement.

---

## T.def: Template definitions

---

### [T.60] Minimize a template's context dependencies

**reason**
Eases understanding. Minimizes errors from unexpected dependencies.

**code sample**
```cpp
template<typename C>
void sort(C& c)
{
    std::sort(begin(c), end(c)); // necessary and useful dependency
}

template<typename Iter>
Iter algo(Iter first, Iter last)
{
    for (; first != last; ++first) {
        auto x = sqrt(*first); // potentially surprising dependency: which sqrt()?
        helper(first, x);      // potentially surprising dependency
        TT var = 7;            // potentially surprising dependency: which TT?
    }
}
```

**enforcement**
- Tricky.

---

### [T.61] Do not over-parameterize members (SCARY)

**reason**
A member that does not depend on a template parameter limits use and typically increases code size.

**code example [bad]**
```cpp
template<typename T, typename A = std::allocator<T>>
class List {
public:
    struct Link {   // does not depend on A
        T elem;
        Link* pre;
        Link* suc;
    };
    using iterator = Link*;
    // ...
};
```

**code example [good]**
```cpp
template<typename T>
struct Link {
    T elem;
    Link* pre;
    Link* suc;
};

template<typename T, typename A = std::allocator<T>>
class List2 {
public:
    using iterator = Link<T>*;
    // ...
};
```

**enforcement**
- Flag member types that do not depend on every template parameter.

---

### [T.62] Place non-dependent class template members in a non-templated base class

**reason**
Allow the base class members to be used without specifying template arguments and without template instantiation.

**code sample**
```cpp
struct Foo_base {
    enum { v1, v2 };
    // ...
};

template<typename T>
class Foo : public Foo_base {
public:
    // ...
};
```

**enforcement**
- No specific enforcement.

---

### [T.64] Use specialization to provide alternative implementations of class templates

**reason**
A template defines a general interface. Specialization provides alternative implementations.

**enforcement**
- No specific enforcement.

---

### [T.65] Use tag dispatch to provide alternative implementations of a function

**reason**
Tag dispatch allows selecting implementations based on specific properties of an argument type. Performance.

**code sample**
```cpp
struct trivially_copyable_tag {};
struct non_trivially_copyable_tag {};

template<class T> struct copy_trait { using tag = non_trivially_copyable_tag; };
template<> struct copy_trait<int> { using tag = trivially_copyable_tag; };

template<class Iter>
Out copy_helper(Iter first, Iter last, Iter out, trivially_copyable_tag)
{
    // use memmove
}

template<class Iter>
Out copy_helper(Iter first, Iter last, Iter out, non_trivially_copyable_tag)
{
    // use loop calling copy constructors
}

template<class Iter>
Out copy(Iter first, Iter last, Iter out)
{
    using tag_type = typename copy_trait<std::iter_value_t<Iter>>::tag;
    return copy_helper(first, last, out, tag_type{})
}
```

**enforcement**
- No specific enforcement.

---

### [T.67] Use specialization to provide alternative implementations for irregular types

**reason**
Specialization handles types with special properties differently.

**enforcement**
- No specific enforcement.

---

### [T.68] Use `{}` rather than `()` within templates to avoid ambiguities

**reason**
`()` is vulnerable to grammar ambiguities.

**code example [bad]**
```cpp
template<typename T, typename U>
void f(T t, U u)
{
    T v1(T(u));    // mistake: oops, v1 is a function, not a variable
    T v2{u};       // clear:   obviously a variable
    auto x = T(u); // unclear: construction or cast?
}

f(1, "asdf"); // bad: cast from const char* to int
```

**enforcement**
- Flag `()` initializers and function-style casts.

---

### [T.69] Inside a template, don't make an unqualified non-member function call unless you intend it to be a customization point

**reason**
Provide only intended flexibility. Avoid vulnerability to accidental environmental changes.

**code sample**
```cpp
template<class T>
void test1(T t)
{
    t.f();    // require T to provide f()
}

template<class T>
void test2(T t)
{
    f(t);     // require f(/*T*/) be available via ADL -- customization point
}

template<class T>
void test3(T t)
{
    test_traits<T>::f(t); // require customizing test_traits<>
}
```

**enforcement**
- Flag unqualified calls to non-member functions that pass dependent-type variables.

---

## T.temp-hier: Template and hierarchy rules

---

### [T.80] Do not naively templatize a class hierarchy

**reason**
Templating a class hierarchy with many virtual functions can lead to code bloat.

**code example [bad]**
```cpp
template<typename T>
struct Container {         // an interface
    virtual T* get(int i);
    virtual T* first();
    virtual T* next();
    virtual void sort();
};

template<typename T>
class Vector : public Container<T> {
public:
    // ...
};
```

**enforcement**
- Flag virtual functions that depend on a template argument.

---

### [T.81] Do not mix hierarchies and arrays

**reason**
An array of derived classes can implicitly "decay" to a pointer to a base class with disastrous results.

**code sample**
```cpp
void maul(Fruit* p)
{
    *p = Pear{};     // put a Pear into *p
    p[1] = Pear{};   // put a Pear into p[1]
}

Apple aa [] = { an_apple, another_apple };
maul(aa);
Apple& a0 = &aa[0];   // a Pear?
Apple& a1 = &aa[1];   // a Pear?
```
If `sizeof(Apple) != sizeof(Pear)` the access to `aa[1]` will not be aligned properly. Type violation and memory corruption.

**enforcement**
- Detect this horror!

---

### [T.82] Linearize a hierarchy when virtual functions are undesirable

**reason**
Avoid vtable overhead when not needed.

**enforcement**
- No specific enforcement.

---

### [T.83] Do not declare a member function template virtual

**reason**
C++ does not support that. vtbls could not be generated until link time.

**code example [bad]**
```cpp
class Shape {
    // ...
    template<class T>
    virtual bool intersect(T* p);   // error: template cannot be virtual
};
```

**enforcement**
- The compiler handles that.

---

### [T.84] Use a non-template core implementation to provide an ABI-stable interface

**reason**
Improve stability of code. Avoid code bloat.

**code sample**
```cpp
struct Link_base {   // stable
    Link_base* suc;
    Link_base* pre;
};

template<typename T>   // templated wrapper to add type safety
struct Link : Link_base {
    T val;
};

struct List_base {
    Link_base* first;
    int sz;
    void add_front(Link_base* p);
    // ...
};

template<typename T>
class List : List_base {
public:
    void put_front(const T& e) { add_front(new Link<T>{e}); }
    T& front() { return static_cast<Link<T>*>(first)->val; }
    // ...
};
```

**enforcement**
- No specific enforcement.

---

## T.var: Variadic template rules

---

### [T.100] Use variadic templates when you need a function that takes a variable number of arguments of a variety of types

**reason**
Most general mechanism, efficient and type-safe. Don't use C varargs.

**enforcement**
- Flag uses of `va_arg` in user code.

---

### [T.101] How to pass arguments to a variadic template

**reason**
Beware of move-only and reference arguments.

**enforcement**
- No specific enforcement.

---

### [T.102] How to process arguments to a variadic template

**reason**
Forwarding, type checking, references.

**enforcement**
- No specific enforcement.

---

### [T.103] Don't use variadic templates for homogeneous argument lists

**reason**
There are more precise ways of specifying a homogeneous sequence, such as `initializer_list`.

**enforcement**
- No specific enforcement.

---

## T.meta: Template metaprogramming (TMP)

---

### [T.120] Use template metaprogramming only when you really need to

**reason**
TMP is hard to get right, slows down compilation, and is often very hard to maintain. However, there are real-world cases where TMP provides better performance than any alternative.

**enforcement**
- No specific enforcement.

---

### [T.121] Use template metaprogramming primarily to emulate concepts

**reason**
Where C++20 is not available, we need to emulate concepts using TMP.

**code sample**
```cpp
template<typename Iter>
    /*requires*/ enable_if<random_access_iterator<Iter>, void>
advance(Iter p, int n) { p += n; }

template<typename Iter>
    /*requires*/ enable_if<forward_iterator<Iter>, void>
advance(Iter p, int n) { assert(n >= 0); while (n--) ++p;}

// Much simpler using concepts:
void advance(random_access_iterator auto p, int n) { p += n; }
void advance(forward_iterator auto p, int n) { assert(n >= 0); while (n--) ++p;}
```

**enforcement**
- No specific enforcement.

---

### [T.122] Use templates (usually template aliases) to compute types at compile time

**reason**
Template metaprogramming is the only directly supported way of generating types at compile time. "Traits" techniques are mostly replaced by template aliases.

**enforcement**
- No specific enforcement.

---

### [T.123] Use `constexpr` functions to compute values at compile time

**reason**
A function is the most obvious way of expressing a computation of a value. Often less compile-time overhead than alternatives.

**code sample**
```cpp
template<typename T>
    // requires Number<T>
constexpr T pow(T v, int n)   // power/exponential
{
    T res = 1;
    while (n--) res *= v;
    return res;
}

constexpr auto f7 = pow(pi, 7);
```

**enforcement**
- Flag template metaprograms yielding a value. Replace with `constexpr` functions.

---

### [T.124] Prefer to use standard-library TMP facilities

**reason**
Facilities defined in the standard, such as `conditional`, `enable_if`, and `tuple`, are portable and can be assumed to be known.

**enforcement**
- No specific enforcement.

---

### [T.125] If you need to go beyond the standard-library TMP facilities, use an existing library

**reason**
Getting advanced TMP facilities is not easy and using a library makes you part of a (hopefully supportive) community.

**enforcement**
- No specific enforcement.

---

## Other template rules

---

### [T.140] If an operation can be reused, give it a name

See F.10.

---

### [T.141] Use an unnamed lambda if you need a simple function object in one place only

See F.11.

---

### [T.143] Don't write unintentionally non-generic code

**reason**
Generality. Reusability. Don't gratuitously commit to details.

**code sample**
```cpp
for (auto i = first; i < last; ++i) {   // less generic
    // ...
}

for (auto i = first; i != last; ++i) {   // good; more generic
    // ...
}
```

**code sample**
```cpp
// bad, unless there is a specific reason for limiting to Derived1
void my_func(Derived1& param)
{
    use(param.f());
    use(param.g());
}

// good, uses only Base interface
void my_func(Base& param)
{
    use(param.f());
    use(param.g());
}
```

**enforcement**
- Flag comparison of iterators using `<` instead of `!=`.
- Flag `x.size() == 0` when `x.empty()` is available.

---

### [T.144] Don't specialize function templates

**reason**
You can't partially specialize a function template per language rules. Function template specializations don't participate in overloading, they don't act as you probably wanted. Overload instead.

**enforcement**
- Flag all specializations of a function template.

---

### [T.150] Check that a class matches a concept using `static_assert`

**reason**
If you intend for a class to match a concept, verifying that early saves users' pain.

**code sample**
```cpp
class X {
public:
    X() = delete;
    X(const X&) = default;
    X(X&&) = default;
    X& operator=(const X&) = default;
    // ...
};

static_assert(Default_constructible<X>);    // error: X has no default constructor
static_assert(Copyable<X>);                 // error: we forgot to define X's move constructor
```

**enforcement**
- Not feasible.

---
