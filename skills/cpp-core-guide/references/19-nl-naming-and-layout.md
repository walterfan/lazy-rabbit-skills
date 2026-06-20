# NL: Naming and layout suggestions

## Table of Contents

- [NL.1] Don't say in comments what can be clearly stated in code
- [NL.2] State intent in comments
- [NL.3] Keep comments crisp
- [NL.4] Maintain a consistent indentation style
- [NL.5] Avoid encoding type information in names
- [NL.7] Make the length of a name roughly proportional to the length of its scope
- [NL.8] Use a consistent naming style
- [NL.9] Use `ALL_CAPS` for macro names only
- [NL.10] Prefer `underscore_style` names
- [NL.11] Make literals readable
- [NL.15] Use spaces sparingly
- [NL.16] Use a conventional class member declaration order
- [NL.17] Use K&R-derived layout
- [NL.18] Use C++-style declarator layout
- [NL.19] Avoid names that are easily misread
- [NL.20] Don't place two statements on the same line
- [NL.21] Declare one name (only) per declaration
- [NL.25] Don't use `void` as an argument type
- [NL.26] Use conventional `const` notation
- [NL.27] Use a `.cpp` suffix for code files and `.h` for interface files

---

### [NL.1] Don't say in comments what can be clearly stated in code

**reason**
Compilers do not read comments. Comments are less precise than code. Comments are not updated as consistently as code.

**code example [bad]**
```cpp
auto x = m * v1 + vv;   // multiply m with v1 and add the result to vv
```

**enforcement**
- Not feasible.

---

### [NL.2] State intent in comments

**reason**
Code says what is done, not what is supposed to be done. Often intent can be stated more clearly and concisely than the implementation.

**code sample**
```cpp
void stable_sort(Sortable& c)
    // sort c in the order determined by <, keep equal elements (as defined by ==) in
    // their original relative order
{
    // ... quite a few lines of non-trivial code ...
}
```

**enforcement**
- Not possible.

---

### [NL.3] Keep comments crisp

**reason**
Verbosity slows down understanding and makes the code harder to read by spreading it around in the source file.

**enforcement**
- Not possible.

---

### [NL.4] Maintain a consistent indentation style

**reason**
Readability. Avoidance of "silly mistakes."

**code example [bad]**
```cpp
int i;
for (i = 0; i < max; ++i); // bug waiting to happen
if (i == j)
    return i;
```

**enforcement**
- Use a tool.

---

### [NL.5] Avoid encoding type information in names

**reason**
If names reflect types rather than functionality, it becomes hard to change the types used to provide that functionality.

**code example [bad]**
```cpp
void print_int(int i);
void print_string(const char*);

print_int(1);          // repetitive, manual type matching
print_string("xyzzy"); // repetitive, manual type matching
```

**code example [good]**
```cpp
void print(int i);
void print(string_view);    // also works on any string-like sequence

print(1);              // clear, automatic type matching
print("xyzzy");        // clear, automatic type matching
```

**enforcement**
- No specific enforcement.

---

### [NL.7] Make the length of a name roughly proportional to the length of its scope

**reason**
The larger the scope the greater the chance of confusion and of an unintended name clash.

**code example [bad]**
```cpp
double sqrt(double x);   // return the square root of x; x must be non-negative
int length(const char* p);  // return the number of characters in a zero-terminated C-style string

int length_of_string(const char zero_terminated_array_of_char[])    // bad: verbose
int g;      // bad: global variable with a cryptic name
int open;   // bad: global variable with a short, popular name
```

**enforcement**
- No specific enforcement.

---

### [NL.8] Use a consistent naming style

**reason**
Consistency in naming and naming style increases readability.

**code sample**
```cpp
// ISO Standard style: lower case only and digits, separate words with underscores
int my_map;

// Stroustrup: ISO Standard but with upper case for your own types and concepts
My_map

// CamelCase: capitalize each word in a multi-word identifier
MyMap
myMap
```

**enforcement**
- Would be possible except for the use of libraries with varying conventions.

---

### [NL.9] Use `ALL_CAPS` for macro names only

**reason**
To avoid confusing macros with names that obey scope and type rules.

**code example [bad]**
```cpp
void f()
{
    const int SIZE{1000};  // Bad, use 'size' instead
    int v[SIZE];
}

enum bad { BAD, WORSE, HORRIBLE }; // BAD
```

**enforcement**
- Flag macros with lower-case letters
- Flag `ALL_CAPS` non-macro names

---

### [NL.10] Prefer `underscore_style` names

**reason**
The use of underscores to separate parts of a name is the original C and C++ style and used in the C++ Standard Library.

**enforcement**
- Impossible.

---

### [NL.11] Make literals readable

**reason**
Readability.

**code sample**
```cpp
auto c = 299'792'458; // m/s2
auto q2 = 0b0000'1111'0000'0000;
auto ss_number = 123'456'7890;

auto hello = "Hello!"s; // a std::string
auto world = "world";   // a C-style string
auto interval = 100ms;  // using <chrono>
```

**enforcement**
- Flag long digit sequences. The trouble is to define "long"; maybe 7.

---

### [NL.15] Use spaces sparingly

**reason**
Too much space makes the text larger and distracts.

**code example [bad]**
```cpp
#include < map >

int main(int argc, char * argv [ ])
{
    // ...
}
```

**code example [good]**
```cpp
#include <map>

int main(int argc, char* argv[])
{
    // ...
}
```

**enforcement**
- No specific enforcement.

---

### [NL.16] Use a conventional class member declaration order

**reason**
A conventional order of members improves readability. Use: types, constructors/assignments/destructor, functions, data. Use `public` before `protected` before `private`.

**code example [bad]**
```cpp
class X {
public:
    // interface
protected:
    // unchecked function for use by derived class implementations
private:
    // implementation details
};
```

**code example [bad]**
```cpp
class X {   // bad: multiple blocks of same access
public:
    void f();
public:
    int g();
    // ...
};
```

**enforcement**
- Flag departures from the suggested order.

---

### [NL.17] Use K&R-derived layout

**reason**
This is the original C and C++ layout. It preserves vertical space well. It distinguishes different language constructs well. In the context of C++, this style is often called "Stroustrup."

**code sample**
```cpp
struct Cable {
    int x;
    // ...
};

double foo(int x)
{
    if (0 < x) {
        // ...
    }

    switch (x) {
    case 0:
        // ...
        break;
    case amazing:
        // ...
        break;
    default:
        // ...
        break;
    }

    if (0 < x)
        ++x;

    if (x < 0)
        something();
    else
        something_else();

    return some_value;
}
```
Note the space between `if` and `(`. The `{` for a `class` and a `struct` is *not* on a separate line, but the `{` for a function is.

**enforcement**
- If you want enforcement, use an IDE to reformat.

---

### [NL.18] Use C++-style declarator layout

**reason**
The C-style layout emphasizes use in expressions and grammar, whereas the C++-style emphasizes types.

**code example [good]**
```cpp
T& operator[](size_t);   // OK
T &operator[](size_t);   // just strange
T & operator[](size_t);   // undecided
```

**enforcement**
- Impossible in the face of history.

---

### [NL.19] Avoid names that are easily misread

**reason**
Readability. Not everyone has screens and printers that make it easy to distinguish all characters.

**code example [bad]**
```cpp
int oO01lL = 6; // bad

int splunk = 7;
int splonk = 8; // bad: splunk and splonk are easily confused
```

**enforcement**
- No specific enforcement.

---

### [NL.20] Don't place two statements on the same line

**reason**
Readability. It is really easy to overlook a statement when there is more on a line.

**code example [bad]**
```cpp
int x = 7; char* p = 29;    // don't
int x = 7; f(x);  ++x;      // don't
```

**enforcement**
- Easy.

---

### [NL.21] Declare one name (only) per declaration

**reason**
Readability. Minimizing confusion with the declarator syntax.

**enforcement**
- See ES.10.

---

### [NL.25] Don't use `void` as an argument type

**reason**
It's verbose and only needed where C compatibility matters.

**code sample**
```cpp
void f(void);   // bad
void g();       // better
```

**enforcement**
- No specific enforcement.

---

### [NL.26] Use conventional `const` notation

**reason**
Conventional notation is more familiar to more programmers. Consistency in large code bases.

**code sample**
```cpp
const int x = 7;    // OK
int const y = 9;    // bad

const int *const p = nullptr;   // OK, constant pointer to constant int
int const *const p = nullptr;   // bad, constant pointer to constant int
```

**enforcement**
- Flag `const` used as a suffix for a type.

---

### [NL.27] Use a `.cpp` suffix for code files and `.h` for interface files

**reason**
It's a longstanding convention. But consistency is more important, so if your project uses something else, follow that.

**code example [bad]**
```cpp
// foo.h:
extern int a;   // a declaration
extern void foo();

// foo.cpp:
int a;   // a definition
void foo() { ++a; }
```

**code example [bad]**
```cpp
// foo.h:
int a;   // a definition
void foo() { ++a; }
// #include <foo.h> twice and you get a linker error for two ODR violations.
```

**enforcement**
- Flag non-conventional file names
- Check that `.h` and `.cpp` follow the rules

---
