# SL: The Standard Library

## Table of Contents

- [SL.1] Use libraries wherever possible
- [SL.2] Prefer the standard library to other libraries
- [SL.3] Do not add non-standard entities to namespace `std`
- [SL.4] Use the standard library in a type-safe manner
- [SL.con.1] Prefer STL `array` or `vector` instead of a C array
- [SL.con.2] Prefer STL `vector` by default
- [SL.con.3] Avoid bounds errors
- [SL.con.4] Don't use `memset`/`memcpy` for non-trivially-copyable arguments
- [SL.str.1] Use `std::string` to own character sequences
- [SL.str.2] Use `std::string_view` or `gsl::span<char>` to refer to character sequences
- [SL.str.3] Use `zstring`/`czstring` for C-style zero-terminated strings
- [SL.str.4] Use `char*` to refer to a single character
- [SL.str.5] Use `std::byte` to refer to byte values that are not characters
- [SL.str.10] Use `std::string` for locale-sensitive string operations
- [SL.str.11] Use `gsl::span<char>` rather than `string_view` to mutate a string
- [SL.str.12] Use the `s` suffix for string literals meant to be `std::string`
- [SL.io.1] Use character-level input only when you have to
- [SL.io.2] When reading, always consider ill-formed input
- [SL.io.3] Prefer `iostream`s for I/O
- [SL.io.10] Unless you use `printf`-family functions call `ios_base::sync_with_stdio(false)`
- [SL.io.50] Avoid `endl`
- [SL.C.1] Don't use `setjmp`/`longjmp`

---

### [SL.1] Use libraries wherever possible

**reason**
Save time. Don't re-invent the wheel. Benefit from other people's work when they make improvements.

**enforcement**
- No specific enforcement.

---

### [SL.2] Prefer the standard library to other libraries

**reason**
More people know the standard library. It is more likely to be stable, well-maintained, and widely available than your own code or most other libraries.

**enforcement**
- No specific enforcement.

---

### [SL.3] Do not add non-standard entities to namespace `std`

**reason**
Adding to `std` might change the meaning of otherwise standards conforming code. Additions to `std` might clash with future versions of the standard.

**code sample**
```cpp
namespace std { // BAD: violates standard
    class My_vector {
        //     . . .
    };
}

namespace Foo { // GOOD: user namespace is allowed
    class My_vector {
        //     . . .
    };
}
```

**enforcement**
- Possible, but messy and likely to cause problems with platforms.

---

### [SL.4] Use the standard library in a type-safe manner

**reason**
Breaking this rule can lead to undefined behavior, memory corruption, and all kinds of other bad errors. This is a semi-philosophical meta-rule needing many supporting concrete rules.

**enforcement**
- See specific sub-rules below.

---

## SL.con: Containers

---

### [SL.con.1] Prefer using STL `array` or `vector` instead of a C array

**reason**
C arrays are less safe, and have no advantages over `array` and `vector`. For a fixed-length array, use `std::array`. For a variable-length array, use `std::vector`.

**code sample**
```cpp
int v[SIZE];                        // BAD
std::array<int, SIZE> w;            // ok
```

**code sample**
```cpp
int* v = new int[initial_size];     // BAD, owning raw pointer
delete[] v;                         // BAD, manual delete

std::vector<int> w(initial_size);   // ok
```

**enforcement**
- Flag declaration of a C array inside a function or class that also declares an STL container.

---

### [SL.con.2] Prefer using STL `vector` by default unless you have a reason to use a different container

**reason**
`vector` and `array` offer the fastest general-purpose access (random access, vectorization-friendly), fastest default access pattern (prefetcher-friendly), and lowest space overhead (contiguous layout, zero per-element overhead, cache-friendly).

**code example [bad]**
```cpp
vector<int> v1(20);  // v1 has 20 elements with the value 0
vector<int> v2 {20}; // v2 has 1 element with the value 20
```

**enforcement**
- Flag a `vector` whose size never changes after construction. To fix: Use an `array` instead.

---

### [SL.con.3] Avoid bounds errors

**reason**
Read or write beyond an allocated range of elements typically leads to bad errors, wrong results, crashes, and security violations.

**code example [bad]**
```cpp
void f()
{
    array<int, 10> a, b;
    memset(a.data(), 0, 10);         // BAD, and contains a length error (length = 10 * sizeof(int))
    memcmp(a.data(), b.data(), 10);  // BAD, and contains a length error
}
```

**code example [good]**
```cpp
void f()
{
    array<int, 10> a, b, c{};       // c is initialized to zero
    a.fill(0);
    fill(b.begin(), b.end(), 0);    // std::fill()
    fill(b, 0);                     // std::ranges::fill()

    if ( a == b ) {
      // ...
    }
}
```

**code sample**
```cpp
void f(std::vector<int>& v, std::array<int, 12> a, int i)
{
    v[0] = a[0];        // BAD
    v.at(0) = a[0];     // OK (alternative 1)
    at(v, 0) = a[0];    // OK (alternative 2)

    v.at(0) = a[i];     // BAD
    v.at(0) = a.at(i);  // OK (alternative 1)
    v.at(0) = at(a, i); // OK (alternative 2)
}
```

**enforcement**
- Issue a diagnostic for any call to a standard-library function that is not bounds-checked.

---

### [SL.con.4] Don't use `memset` or `memcpy` for arguments that are not trivially-copyable

**reason**
Doing so messes the semantics of the objects (e.g., by overwriting a `vptr`).

**code example [good]**
```cpp
struct base {
    virtual void update() = 0;
};

struct derived : public base {
    void update() override {}
};

void f(derived& a, derived& b) // goodbye v-tables
{
    memset(&a, 0, sizeof(derived));
    memcpy(&a, &b, sizeof(derived));
    memcmp(&a, &b, sizeof(derived));
}

// Instead, define proper default initialization, copy, and comparison functions
void g(derived& a, derived& b)
{
    a = {};    // default initialize
    b = a;     // copy
    if (a == b) do_something(a, b);
}
```

**enforcement**
- Flag the use of those functions for types that are not trivially copyable.

---

## SL.str: String

---

### [SL.str.1] Use `std::string` to own character sequences

**reason**
`string` correctly handles allocation, ownership, copying, gradual expansion, and offers a variety of useful operations.

**code example [bad]**
```cpp
vector<string> read_until(const string& terminator)
{
    vector<string> res;
    for (string s; cin >> s && s != terminator; ) // read a word
        res.push_back(s);
    return res;
}
```

**code example [bad]**
```cpp
char* cat(const char* s1, const char* s2)   // beware!
{
    int l1 = strlen(s1);
    int l2 = strlen(s2);
    char* p = (char*) malloc(l1 + l2 + 2);
    strcpy(p, s1, l1);
    p[l1] = '.';
    strcpy(p + l1 + 1, s2, l2);
    p[l1 + l2 + 1] = 0;
    return p;
}
// Did we get that right? Will the caller remember to free() the returned pointer?
```

**enforcement**
- No specific enforcement.

---

### [SL.str.2] Use `std::string_view` or `gsl::span<char>` to refer to character sequences

**reason**
Provides simple and (potentially) safe access to character sequences independently of how those sequences are allocated and stored.

**code example [good]**
```cpp
vector<string> read_until(string_view terminator);

void user(zstring p, const string& s, string_view ss)
{
    auto v1 = read_until(p);
    auto v2 = read_until(s);
    auto v3 = read_until(ss);
}
```

**enforcement**
- No specific enforcement.

---

### [SL.str.3] Use `zstring` or `czstring` to refer to a C-style, zero-terminated, sequence of characters

**reason**
Readability. Statement of intent. A plain `char*` can be a pointer to a single character, a pointer to an array of characters, or a pointer to a C-style string. Distinguishing these alternatives prevents misunderstandings and bugs.

**code sample**
```cpp
void f1(const char* s); // s is probably a string

void f1(zstring s);     // s is a C-style string or the nullptr
void f1(czstring s);    // s is a C-style string constant or the nullptr
void f1(std::byte* s);  // s is a pointer to a byte (C++17)
```

**enforcement**
- Flag uses of `[]` on a `char*`
- Flag uses of `delete` on a `char*`
- Flag uses of `free()` on a `char*`

---

### [SL.str.4] Use `char*` to refer to a single character

**reason**
The variety of uses of `char*` in current code is a major source of errors.

**code example [bad]**
```cpp
char arr[] = {'a', 'b', 'c'};

void print(const char* p)
{
    cout << p << '\n';
}

void use()
{
    print(arr);   // run-time error; potentially very bad
}
```
The array `arr` is not a C-style string because it is not zero-terminated.

**enforcement**
- Flag uses of `[]` on a `char*`.

---

### [SL.str.5] Use `std::byte` to refer to byte values that do not necessarily represent characters

**reason**
Use of `char*` to represent a pointer to something that is not necessarily a character causes confusion and disables valuable optimizations.

**enforcement**
- No specific enforcement.

---

### [SL.str.10] Use `std::string` when you need to perform locale-sensitive string operations

**reason**
`std::string` supports standard-library locale facilities.

**enforcement**
- No specific enforcement.

---

### [SL.str.11] Use `gsl::span<char>` rather than `std::string_view` when you need to mutate a string

**reason**
`std::string_view` is read-only.

**enforcement**
- The compiler will flag attempts to write to a `string_view`.

---

### [SL.str.12] Use the `s` suffix for string literals meant to be standard-library `string`s

**reason**
Direct expression of an idea minimizes mistakes.

**code example [bad]**
```cpp
auto pp1 = make_pair("Tokyo", 9.00);         // {C-style string,double} intended?
pair<string, double> pp2 = {"Tokyo", 9.00};  // a bit verbose
auto pp3 = make_pair("Tokyo"s, 9.00);        // {std::string,double}    // C++14
pair pp4 = {"Tokyo"s, 9.00};                 // {std::string,double}    // C++17
```

**enforcement**
- No specific enforcement.

---

## SL.io: Iostream

---

### [SL.io.1] Use character-level input only when you have to

**reason**
Unless you genuinely just deal with individual characters, using character-level input leads to potentially error-prone and potentially inefficient composition of tokens out of characters.

**code sample**
```cpp
// bad: character-level
char c;
char buf[128];
int i = 0;
while (cin.get(c) && !isspace(c) && i < 128)
    buf[i++] = c;
if (i == 128) {
    // ... handle too long string ....
}

// better (much simpler and probably faster):
string s;
s.reserve(128);
cin >> s;
```

**enforcement**
- No specific enforcement.

---

### [SL.io.2] When reading, always consider ill-formed input

**reason**
Errors are typically best handled as soon as possible. If input isn't validated, every function must be written to cope with bad data.

**enforcement**
- No specific enforcement.

---

### [SL.io.3] Prefer `iostream`s for I/O

**reason**
`iostream`s are safe, flexible, and extensible.

**code example [good]**
```cpp
// write a complex number:
complex<double> z{ 3, 4 };
cout << z << '\n';

// read a file of complex numbers:
for (complex<double> z; cin >> z; )
    v.push_back(z);
```

**enforcement**
- Optionally flag `<cstdio>` and `<stdio.h>`.

---

### [SL.io.10] Unless you use `printf`-family functions call `ios_base::sync_with_stdio(false)`

**reason**
Synchronizing `iostreams` with `printf-style` I/O can be costly.

**code sample**
```cpp
int main()
{
    ios_base::sync_with_stdio(false);
    // ... use iostreams ...
}
```

**enforcement**
- No specific enforcement.

---

### [SL.io.50] Avoid `endl`

**reason**
The `endl` manipulator is mostly equivalent to `'\n'` and `"\n"`; as most commonly used it simply slows down output by doing redundant `flush()`s.

**code sample**
```cpp
cout << "Hello, World!" << endl;    // two output operations and a flush
cout << "Hello, World!\n";          // one output operation and no flush
```

**enforcement**
- No specific enforcement.

---

## SL.C: The C Standard Library

---

### [SL.C.1] Don't use setjmp/longjmp

**reason**
A `longjmp` ignores destructors, thus invalidating all resource-management strategies relying on RAII.

**enforcement**
- Flag all occurrences of `longjmp` and `setjmp`.

---
