# R: Resource management

## Table of Contents

- [R.1] Manage resources automatically using RAII
- [R.2] In interfaces, use raw pointers to denote individual objects (only)
- [R.3] A raw pointer (`T*`) is non-owning
- [R.4] A raw reference (`T&`) is non-owning
- [R.5] Prefer scoped objects, don't heap-allocate unnecessarily
- [R.6] Avoid non-`const` global variables
- [R.10] Avoid `malloc()` and `free()`
- [R.11] Avoid calling `new` and `delete` explicitly
- [R.12] Immediately give explicit resource allocation to a manager object
- [R.13] Perform at most one explicit resource allocation in a single expression
- [R.14] Avoid `[]` parameters, prefer `span`
- [R.15] Always overload matched allocation/deallocation pairs
- [R.20] Use `unique_ptr` or `shared_ptr` to represent ownership
- [R.21] Prefer `unique_ptr` over `shared_ptr` unless you need to share ownership
- [R.22] Use `make_shared()` to make `shared_ptr`s
- [R.23] Use `make_unique()` to make `unique_ptr`s
- [R.24] Use `std::weak_ptr` to break cycles of `shared_ptr`s
- [R.30] Take smart pointers as parameters only to explicitly express lifetime semantics
- [R.31] If you have non-`std` smart pointers, follow the basic pattern from `std`
- [R.32] Take a `unique_ptr<widget>` parameter to express ownership assumption
- [R.33] Take a `unique_ptr<widget>&` parameter to express reseat
- [R.34] Take a `shared_ptr<widget>` parameter to express shared ownership
- [R.35] Take a `shared_ptr<widget>&` parameter to express possible reseat
- [R.36] Take a `const shared_ptr<widget>&` to express possible reference count retention
- [R.37] Do not pass a pointer or reference obtained from an aliased smart pointer

---

### [R.1] Manage resources automatically using resource handles and RAII (Resource Acquisition Is Initialization)

**reason**
To avoid leaks and the complexity of manual resource management. C++'s language-enforced constructor/destructor symmetry mirrors the symmetry inherent in resource acquire/release function pairs such as `fopen`/`fclose`, `lock`/`unlock`, and `new`/`delete`.

**code example [bad]**
```cpp
void send(X* x, string_view destination)
{
    auto port = open_port(destination);
    my_mutex.lock();
    // ...
    send(port, x);
    // ...
    my_mutex.unlock();
    close_port(port);
    delete x;
}
```
You have to remember to `unlock`, `close_port`, and `delete` on all paths, and do each exactly once. If any code marked `...` throws, `x` is leaked and `my_mutex` remains locked.

**code example [good]**
```cpp
void send(unique_ptr<X> x, string_view destination)  // x owns the X
{
    Port port{destination};            // port owns the PortHandle
    lock_guard<mutex> guard{my_mutex}; // guard owns the lock
    // ...
    send(port, x);
    // ...
} // automatically unlocks my_mutex and deletes the pointer in x
```

**code example [good]**
```cpp
class Port {
    PortHandle port;
public:
    Port(string_view destination) : port{open_port(destination)} { }
    ~Port() { close_port(port); }
    operator PortHandle() { return port; }

    Port(const Port&) = delete;
    Port& operator=(const Port&) = delete;
};
```

**enforcement**
- No specific enforcement. See RAII.

---

### [R.2] In interfaces, use raw pointers to denote individual objects (only)

**reason**
Arrays are best represented by a container type (e.g., `vector`) or a `span` (non-owning). Such containers and views hold sufficient information to do range checking.

**code example [bad]**
```cpp
void f(int* p, int n)   // n is the number of elements in p[]
{
    // ...
    p[2] = 7;   // bad: subscript raw pointer
    // ...
}
```

**code example [good]**
```cpp
void g(int* p, int fmt)   // print *p using format #fmt
{
    // ... uses *p and p[0] only ...
}
```

**enforcement**
- Flag pointer arithmetic (including `++`) on a pointer that is not part of a container, view, or iterator
- Flag array names passed as simple pointers

---

### [R.3] A raw pointer (a `T*`) is non-owning

**reason**
There is nothing (in the C++ standard or in most code) to say otherwise and most raw pointers are non-owning. We want owning pointers identified so that we can reliably and efficiently delete the objects pointed to by owning pointers.

**code example [bad]**
```cpp
void f()
{
    int* p1 = new int{7};           // bad: raw owning pointer
    auto p2 = make_unique<int>(7);  // OK: the int is owned by a unique pointer
    // ...
}
```

**code example [bad]**
```cpp
template<typename T>
class X {
public:
    T* p;   // bad: it is unclear whether p is owning or not
    T* q;   // bad: it is unclear whether q is owning or not
};

template<typename T>
class X2 {
public:
    owner<T*> p;  // OK: p is owning
    T* q;         // OK: q is not owning
};
```

**code example [bad]**
```cpp
Gadget* make_gadget(int n)
{
    auto p = new Gadget{n};
    // ...
    return p;
}

void caller(int n)
{
    auto p = make_gadget(n);   // remember to delete p
    // ...
    delete p;
}
```

**code example [good]**
```cpp
Gadget make_gadget(int n)
{
    Gadget g{n};
    // ...
    return g;
}
```

**enforcement**
- (Simple) Warn on `delete` of a raw pointer that is not an `owner<T>`
- (Moderate) Warn on failure to either `reset` or explicitly `delete` an `owner<T>` pointer on every code path
- (Simple) Warn if the return value of `new` is assigned to a raw pointer
- (Simple) Warn if a function returns an object that was allocated within the function but has a move constructor. Suggest returning it by value instead.

---

### [R.4] A raw reference (a `T&`) is non-owning

**reason**
There is nothing (in the C++ standard or in most code) to say otherwise and most raw references are non-owning.

**code example [bad]**
```cpp
void f()
{
    int& r = *new int{7};  // bad: raw owning reference
    // ...
    delete &r;             // bad: violated the rule against deleting raw pointers
}
```

**enforcement**
- See the raw pointer rule

---

### [R.5] Prefer scoped objects, don't heap-allocate unnecessarily

**reason**
A scoped object is a local object, a global object, or a member. This implies that there is no separate allocation and deallocation cost in excess of that already used for the containing scope or object.

**code sample**
```cpp
// bad: unnecessary heap allocation
void f(int n)
{
    auto p = new Gadget{n};
    // ...
    delete p;
}

// good: use a local variable
void f(int n)
{
    Gadget g{n};
    // ...
}
```

**enforcement**
- (Moderate) Warn if an object is allocated and then deallocated on all paths within a function. Suggest it should be a local stack object instead.
- (Simple) Warn if a local `Unique_pointer` or `Shared_pointer` that is not moved, copied, reassigned or `reset` before its lifetime ends is not declared `const`.

---

### [R.6] Avoid non-`const` global variables

**reason**
See I.2.

**enforcement**
- See I.2.

---

## R.alloc: Allocation and deallocation

---

### [R.10] Avoid `malloc()` and `free()`

**reason**
`malloc()` and `free()` do not support construction and destruction, and do not mix well with `new` and `delete`.

**code sample**
```cpp
class Record {
    int id;
    string name;
    // ...
};

void use()
{
    // p1 might be nullptr
    // *p1 is not initialized; in particular,
    // that string isn't a string, but a string-sized bag of bits
    Record* p1 = static_cast<Record*>(malloc(sizeof(Record)));

    auto p2 = new Record;

    // unless an exception is thrown, *p2 is default initialized
    auto p3 = new(nothrow) Record;
    // p3 might be nullptr; if not, *p3 is default initialized

    // ...

    delete p1;    // error: cannot delete object allocated by malloc()
    free(p2);    // error: cannot free() object allocated by new
}
```

**enforcement**
- Flag explicit use of `malloc` and `free`.

---

### [R.11] Avoid calling `new` and `delete` explicitly

**reason**
The pointer returned by `new` should belong to a resource handle (that can call `delete`). If the pointer returned by `new` is assigned to a plain/naked pointer, the object can be leaked.

**enforcement**
- (Simple) Warn on any explicit use of `new` and `delete`. Suggest using `make_unique` instead.

---

### [R.12] Immediately give the result of an explicit resource allocation to a manager object

**reason**
If you don't, an exception or a return might lead to a leak.

**code example [bad]**
```cpp
void func(const string& name)
{
    FILE* f = fopen(name, "r");            // open the file
    vector<char> buf(1024);
    auto _ = finally([f] { fclose(f); });  // remember to close the file
    // ...
}
// The allocation of buf might fail and leak the file handle.
```

**code example [good]**
```cpp
void func(const string& name)
{
    ifstream f{name};   // open the file
    vector<char> buf(1024);
    // ...
}
```

**enforcement**
- Flag explicit allocations used to initialize pointers

---

### [R.13] Perform at most one explicit resource allocation in a single expression statement

**reason**
If you perform two explicit resource allocations in one statement, you could leak resources because the order of evaluation of many subexpressions, including function arguments, is unspecified.

**code example [bad]**
```cpp
void fun(shared_ptr<Widget> sp1, shared_ptr<Widget> sp2);

// BAD: potential leak
fun(shared_ptr<Widget>(new Widget(a, b)), shared_ptr<Widget>(new Widget(c, d)));
```

**code example [good]**
```cpp
fun(make_shared<Widget>(a, b), make_shared<Widget>(c, d)); // Best
```

**code example [good]**
```cpp
// Better, but messy
shared_ptr<Widget> sp1(new Widget(a, b));
fun(sp1, new Widget(c, d));
```

**enforcement**
- Flag expressions with multiple explicit resource allocations

---

### [R.14] Avoid `[]` parameters, prefer `span`

**reason**
An array decays to a pointer, thereby losing its size, opening the opportunity for range errors.

**code example [good]**
```cpp
void f(int[]);          // not recommended

void f(int*);           // not recommended for multiple objects
                        // (a pointer should point to a single object, do not subscript)

void f(gsl::span<int>); // good, recommended
```

**enforcement**
- Flag `[]` parameters. Use `span` instead.

---

### [R.15] Always overload matched allocation/deallocation pairs

**reason**
Otherwise you get mismatched operations and chaos.

**code sample**
```cpp
class X {
    // ...
    void* operator new(size_t s);
    void operator delete(void*);
    // ...
};
```

**enforcement**
- Flag incomplete pairs.

---

## R.smart: Smart pointers

---

### [R.20] Use `unique_ptr` or `shared_ptr` to represent ownership

**reason**
They can prevent resource leaks.

**code sample**
```cpp
void f()
{
    X* p1 { new X };              // bad, p1 will leak
    auto p2 = make_unique<X>();   // good, unique ownership
    auto p3 = make_shared<X>();   // good, shared ownership
}
```

**enforcement**
- (Simple) Warn if the return value of `new` is assigned to a raw pointer
- (Simple) Warn if the result of a function returning a raw owning pointer is assigned to a raw pointer

---

### [R.21] Prefer `unique_ptr` over `shared_ptr` unless you need to share ownership

**reason**
A `unique_ptr` is conceptually simpler and more predictable (you know when destruction happens) and faster (you don't implicitly maintain a use count).

**code example [bad]**
```cpp
void f()
{
    shared_ptr<Base> base = make_shared<Derived>();
    // use base locally, without copying it -- refcount never exceeds 1
} // destroy base
```

**code example [good]**
```cpp
void f()
{
    unique_ptr<Base> base = make_unique<Derived>();
    // use base locally
} // destroy base
```

**enforcement**
- (Simple) Warn if a function uses a `Shared_pointer` with an object allocated within the function, but never returns or passes the `Shared_pointer`. Suggest using `unique_ptr` instead.

---

### [R.22] Use `make_shared()` to make `shared_ptr`s

**reason**
`make_shared` gives a more concise statement of the construction. It also gives an opportunity to eliminate a separate allocation for the reference counts. It also ensures exception safety in complex expressions (in pre-C++17 code).

**code sample**
```cpp
shared_ptr<X> p1 { new X{2} }; // bad
auto p = make_shared<X>(2);    // good
```

**enforcement**
- (Simple) Warn if a `shared_ptr` is constructed from the result of `new` rather than `make_shared`.

---

### [R.23] Use `make_unique()` to make `unique_ptr`s

**reason**
`make_unique` gives a more concise statement of the construction. It also ensures exception safety in complex expressions (in pre-C++17 code).

**code example [good]**
```cpp
unique_ptr<Foo> p {new Foo{7}};    // OK: but repetitive
auto q = make_unique<Foo>(7);      // Better: no repetition of Foo
```

**enforcement**
- (Simple) Warn if a `unique_ptr` is constructed from the result of `new` rather than `make_unique`.

---

### [R.24] Use `std::weak_ptr` to break cycles of `shared_ptr`s

**reason**
`shared_ptr`s rely on use counting and the use count for a cyclic structure never goes to zero, so we need a mechanism to be able to destroy a cyclic structure.

**code sample**
```cpp
#include <memory>

class bar;

class foo {
public:
  explicit foo(const std::shared_ptr<bar>& forward_reference)
    : forward_reference_(forward_reference)
  { }
private:
  std::shared_ptr<bar> forward_reference_;
};

class bar {
public:
  explicit bar(const std::weak_ptr<foo>& back_reference)
    : back_reference_(back_reference)
  { }
  void do_something()
  {
    if (auto shared_back_reference = back_reference_.lock()) {
      // Use *shared_back_reference
    }
  }
private:
  std::weak_ptr<foo> back_reference_;
};
```

**enforcement**
- Probably impossible. If we could statically detect cycles, we wouldn't need `weak_ptr`.

---

### [R.30] Take smart pointers as parameters only to explicitly express lifetime semantics

**reason**
See F.7.

**enforcement**
- See F.7.

---

### [R.31] If you have non-`std` smart pointers, follow the basic pattern from `std`

**reason**
The rules in the following section also work for other kinds of third-party and custom smart pointers and are very useful for diagnosing common smart pointer errors.

**code example [bad]**
```cpp
// use Boost's intrusive_ptr
#include <boost/intrusive_ptr.hpp>
void f(boost::intrusive_ptr<widget> p)  // error under rule 'sharedptrparam'
{
    p->foo();
}

// use Microsoft's CComPtr
#include <atlbase.h>
void f(CComPtr<widget> p)               // error under rule 'sharedptrparam'
{
    p->foo();
}
```
Both cases: `p` is a `Shared_pointer`, but nothing about its sharedness is used here. These functions should accept a `widget*`, `widget&`, or a smart pointer only if they need to participate in lifetime management.

**enforcement**
- No specific enforcement.

---

### [R.32] Take a `unique_ptr<widget>` parameter to express that a function assumes ownership of a `widget`

**reason**
Using `unique_ptr` in this way both documents and enforces the function call's ownership transfer.

**code sample**
```cpp
void sink(unique_ptr<widget>); // takes ownership of the widget
void uses(widget*);            // just uses the widget
```

**enforcement**
- (Simple) Warn if a function takes a `Unique_pointer<T>` parameter by lvalue reference and does not either assign to it or call `reset()` on it on at least one code path. Suggest taking a `T*` or `T&` instead.

---

### [R.33] Take a `unique_ptr<widget>&` parameter to express that a function reseats the `widget`

**reason**
Using `unique_ptr` in this way both documents and enforces the function call's reseating semantics. "Reseat" means "making a pointer or a smart pointer refer to a different object."

**code example [good]**
```cpp
void reseat(unique_ptr<widget>&); // "will" or "might" reseat pointer
```

**enforcement**
- (Simple) Warn if a function takes a `Unique_pointer<T>` parameter by lvalue reference and does not either assign to it or call `reset()` on it on at least one code path.

---

### [R.34] Take a `shared_ptr<widget>` parameter to express shared ownership

**reason**
This makes the function's ownership sharing explicit.

**code example [good]**
```cpp
class WidgetUser
{
public:
    // WidgetUser will share ownership of the widget
    explicit WidgetUser(std::shared_ptr<widget> w) noexcept:
        m_widget{std::move(w)} {}
    // ...
private:
    std::shared_ptr<widget> m_widget;
};
```

**enforcement**
- (Simple) Warn if a function takes a `Shared_pointer<T>` by value or by reference to `const` and does not copy or move it to another `Shared_pointer` on at least one code path
- (Simple) Warn if a function takes a `Shared_pointer<T>` by rvalue reference. Suggest taking it by value instead.

---

### [R.35] Take a `shared_ptr<widget>&` parameter to express that a function might reseat the shared pointer

**reason**
This makes the function's reseating explicit. "Reseat" means "making a reference or a smart pointer refer to a different object."

**code example [good]**
```cpp
void ChangeWidget(std::shared_ptr<widget>& w)
{
    // This will change the callers widget
    w = std::make_shared<widget>(widget{});
}
```

**enforcement**
- (Simple) Warn if a function takes a `Shared_pointer<T>` parameter by lvalue reference and does not either assign to it or call `reset()` on it on at least one code path.

---

### [R.36] Take a `const shared_ptr<widget>&` parameter to express that it might retain a reference count to the object

**reason**
This makes the function's intent explicit.

**code example [bad]**
```cpp
void share(shared_ptr<widget>);            // share -- "will" retain refcount
void reseat(shared_ptr<widget>&);          // "might" reseat ptr
void may_share(const shared_ptr<widget>&); // "might" retain refcount
```

**enforcement**
- (Simple) Warn if a function takes a `Shared_pointer<T>` by value or by reference to `const` and does not copy or move it to another `Shared_pointer` on at least one code path.

---

### [R.37] Do not pass a pointer or reference obtained from an aliased smart pointer

**reason**
Violating this rule is the number one cause of losing reference counts and finding yourself with a dangling pointer. Functions should prefer to pass raw pointers and references down call chains. At the top of the call tree, obtain the raw pointer or reference from a smart pointer that keeps the object alive.

**code example [bad]**
```cpp
// global (static or heap), or aliased local ...
shared_ptr<widget> g_p = ...;

void f(widget& w)
{
    g();
    use(w);  // A
}

void g()
{
    g_p = ...; // oops, if this was the last shared_ptr to that widget, destroys the widget
}

void my_code()
{
    // BAD: passing pointer or reference obtained from a non-local smart pointer
    //      that could be inadvertently reset somewhere inside f or its callees
    f(*g_p);

    // BAD: same reason, just passing it as a "this" pointer
    g_p->func();
}
```

**code example [good]**
```cpp
void my_code()
{
    // cheap: 1 increment covers this entire function and all the call trees below us
    auto pin = g_p;

    // GOOD: passing pointer or reference obtained from a local unaliased smart pointer
    f(*pin);

    // GOOD: same reason
    pin->func();
}
```

**enforcement**
- (Simple) Warn if a pointer or reference obtained from a smart pointer variable that is non-local, or that is local but potentially aliased, is used in a function call. If the smart pointer is a `Shared_pointer` then suggest taking a local copy and obtain a pointer or reference from that instead.

---
