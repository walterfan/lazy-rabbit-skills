# CPL: C-style programming

## Table of Contents

- [CPL.1] Prefer C++ to C
- [CPL.2] If you must use C, use the common subset of C and C++, and compile the C code as C++
- [CPL.3] If you must use C for interfaces, use C++ in the calling code

---

### [CPL.1] Prefer C++ to C

**reason**
C++ provides better type checking and more notational support. It provides better support for high-level programming and often generates faster code.

**code example [good]**
```cpp
char ch = 7;
void* pv = &ch;
int* pi = pv;   // not C++
*pi = 999;      // overwrite sizeof(int) bytes near &ch
```
The rules for implicit casting to and from `void*` in C are subtle and unenforced. This example violates a rule against converting to a type with stricter alignment.

**enforcement**
- Use a C++ compiler.

---

### [CPL.2] If you must use C, use the common subset of C and C++, and compile the C code as C++

**reason**
That subset can be compiled with both C and C++ compilers, and when compiled as C++ is better type checked than "pure C."

**code example [good]**
```cpp
int* p1 = malloc(10 * sizeof(int));                      // not C++
int* p2 = static_cast<int*>(malloc(10 * sizeof(int)));   // not C, C-style C++
int* p3 = new int[10];                                   // not C
int* p4 = (int*) malloc(10 * sizeof(int));               // both C and C++
```

**enforcement**
- Flag if using a build mode that compiles code as C. The C++ compiler will enforce that the code is valid C++ unless you use C extension options.

---

### [CPL.3] If you must use C for interfaces, use C++ in the calling code using such interfaces

**reason**
C++ is more expressive than C and offers better support for many types of programming.

**code example [good]**
```cpp
// in C:
double sqrt(double);

// in C++:
extern "C" double sqrt(double);
sqrt(2);
```

**code sample**
```cpp
// in C:
X call_f(struct Y*, int);

// in C++:
extern "C" X call_f(Y* p, int i)
{
    return p->f(i);   // possibly a virtual function call
}
```

**enforcement**
- None needed.

---
