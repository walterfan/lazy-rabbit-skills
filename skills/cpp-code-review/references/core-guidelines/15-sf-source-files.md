# SF: Source files

## Table of Contents

- [SF.1] Use `.cpp` suffix for code files and `.h` for interface files
- [SF.2] A header file must not contain object definitions or non-inline function definitions
- [SF.3] Use header files for all declarations used in multiple source files
- [SF.4] Include header files before other declarations in a file
- [SF.5] A `.cpp` file must include the header file(s) that defines its interface
- [SF.6] Use `using namespace` directives for transition or within a local scope (only)
- [SF.7] Don't write `using namespace` at global scope in a header file
- [SF.8] Use `#include` guards for all header files
- [SF.9] Avoid cyclic dependencies among source files
- [SF.10] Avoid dependencies on implicitly `#include`d names
- [SF.11] Header files should be self-contained
- [SF.12] Prefer quoted form of `#include` for relative files, angle bracket form elsewhere
- [SF.13] Use portable header identifiers in `#include` statements
- [SF.20] Use `namespace`s to express logical structure
- [SF.21] Don't use an unnamed namespace in a header
- [SF.22] Use an unnamed namespace for all internal/non-exported entities

---

### [SF.1] Use a `.cpp` suffix for code files and `.h` for interface files if your project doesn't already follow another convention

**reason**
See NL.27.

**enforcement**
- See NL.27.

---

### [SF.2] A header file must not contain object definitions or non-inline function definitions

**reason**
Including entities subject to the one-definition rule leads to linkage errors.

**code example [bad]**
```cpp
// file.h:
namespace Foo {
    int x = 7;
    int xx() { return x+x; }
}

// file1.cpp:
#include <file.h>
// ... more ...

// file2.cpp:
#include <file.h>
// ... more ...
```
Linking `file1.cpp` and `file2.cpp` will give two linker errors.

**enforcement**
- A header file should contain only: `#include`s, templates, class definitions, function declarations, `extern` declarations, `inline` function definitions, `constexpr` definitions, `const` definitions, `using` alias definitions.

---

### [SF.3] Use header files for all declarations used in multiple source files

**reason**
Maintainability. Readability.

**code example [bad]**
```cpp
// bar.cpp:
void bar() { cout << "bar\n"; }

// foo.cpp:
extern void bar();
void foo() { bar(); }
```
A maintainer of `bar` cannot find all declarations of `bar` if its type needs changing.

**enforcement**
- Flag declarations of entities in other source files not placed in a `.h`.

---

### [SF.4] Include header files before other declarations in a file

**reason**
Minimize context dependencies and increase readability.

**code example [good]**
```cpp
#include <vector>
#include <algorithm>
#include <string>

// ... my code here ...
```

**code example [bad]**
```cpp
#include <vector>

// ... my code here ...

#include <algorithm>
#include <string>
```

**enforcement**
- Easy.

---

### [SF.5] A `.cpp` file must include the header file(s) that defines its interface

**reason**
This enables the compiler to do an early consistency check.

**code example [bad]**
```cpp
// foo.h:
void foo(int);
int bar(long);
int foobar(int);

// foo.cpp:
void foo(int) { /* ... */ }
int bar(double) { /* ... */ }
double foobar(int);
```
The errors will not be caught until link time.

**code example [good]**
```cpp
// foo.h:
void foo(int);
int bar(long);
int foobar(int);

// foo.cpp:
#include "foo.h"

void foo(int) { /* ... */ }
int bar(double) { /* ... */ }
double foobar(int);   // error: wrong return type
```
The return-type error for `foobar` is now caught immediately when `foo.cpp` is compiled.

**enforcement**
- Flag `.cpp` files that don't include their corresponding `.h`.

---

### [SF.6] Use `using namespace` directives for transition, for foundation libraries (such as `std`), or within a local scope (only)

**reason**
`using namespace` can lead to name clashes, so it should be used sparingly.

**code example [good]**
```cpp
#include <string>
#include <vector>
#include <iostream>
#include <memory>
#include <algorithm>

using namespace std;
// ... here it's OK: the standard library is used pervasively
```

**code sample**
```cpp
#include <cmath>
using namespace std;

int g(int x)
{
    int sqrt = 7;
    // ...
    return sqrt(x); // error: name clash
}
```

**enforcement**
- No simple enforcement.

---

### [SF.7] Don't write `using namespace` at global scope in a header file

**reason**
Doing so takes away an `#include`r's ability to effectively disambiguate and to use alternatives. It also makes `#include`d headers order-dependent.

**code example [bad]**
```cpp
// bad.h
#include <iostream>
using namespace std; // bad

// user.cpp
#include "bad.h"

bool copy(/*... some parameters ...*/);    // some function that happens to be named copy

int main()
{
    copy(/*...*/);    // now overloads local ::copy and std::copy, could be ambiguous
}
```

**enforcement**
- Flag `using namespace` at global scope in a header file.

---

### [SF.8] Use `#include` guards for all header files

**reason**
To avoid files being `#include`d several times.

**code example [bad]**
```cpp
// file foobar.h:
#ifndef LIBRARY_FOOBAR_H
#define LIBRARY_FOOBAR_H
// ... declarations ...
#endif // LIBRARY_FOOBAR_H
```

**enforcement**
- Flag `.h` files without `#include` guards.

---

### [SF.9] Avoid cyclic dependencies among source files

**reason**
Cycles complicate comprehension and slow down compilation.

**code example [bad]**
```cpp
// file1.h:
#include "file2.h"

// file2.h:
#include "file3.h"

// file3.h:
#include "file1.h"
```

**enforcement**
- Flag all cycles.

---

### [SF.10] Avoid dependencies on implicitly `#include`d names

**reason**
Avoid surprises. Avoid having to change `#include`s if an `#include`d header changes.

**code example [bad]**
```cpp
#include <iostream>
using namespace std;

void use()
{
    string s;
    cin >> s;               // fine
    getline(cin, s);        // error: getline() not defined
    if (s == "surprise") {  // error == not defined
        // ...
    }
}
```

**code example [good]**
```cpp
#include <iostream>
#include <string>
using namespace std;

void use()
{
    string s;
    cin >> s;               // fine
    getline(cin, s);        // fine
    if (s == "surprise") {  // fine
        // ...
    }
}
```

**enforcement**
- No really good solution until modules.

---

### [SF.11] Header files should be self-contained

**reason**
Usability, headers should be simple to use and work when included on their own. Headers should encapsulate the functionality they provide.

**code example [good]**
```cpp
#include "helpers.h"
// helpers.h depends on std::string and includes <string>
```

**enforcement**
- A test should verify that the header file itself compiles or that a cpp file which only includes the header file compiles.

---

### [SF.12] Prefer the quoted form of `#include` for files relative to the including file and the angle bracket form everywhere else

**reason**
The standard provides flexibility for compilers to implement the two forms differently. Use quoted form for local relative files, angle brackets elsewhere.

**code sample**
```cpp
// foo.cpp:
#include <string>                // From the standard library, requires the <> form
#include <some_library/common.h> // A file from another library; use the <> form
#include "foo.h"                 // A file locally relative to foo.cpp, use the "" form
#include "util/util.h"           // A file locally relative in the same project, use the "" form
```

**enforcement**
- A test should identify whether headers referenced via `""` could be referenced with `<>`.

---

### [SF.13] Use portable header identifiers in `#include` statements

**reason**
The standard does not specify how compilers uniquely locate headers. Use case-sensitivity matching the header definition, and forward-slash `/` for path delimiters.

**code sample**
```cpp
// good examples
#include <vector>
#include <string>
#include "util/util.h"

// bad examples
#include <VECTOR>        // bad: standard defines <vector>, not <VECTOR>
#include <String>        // bad: standard defines <string>, not <String>
#include "Util/Util.H"   // bad: file system has "util/util.h"
#include "util\util.h"   // bad: '\' may not work as path separator
```

**enforcement**
- Only enforceable on case-sensitive implementations supporting `/` as path delimiter.

---

### [SF.20] Use `namespace`s to express logical structure

**reason**
Logical grouping of related declarations.

**enforcement**
- No specific enforcement.

---

### [SF.21] Don't use an unnamed (anonymous) namespace in a header

**reason**
It is almost always a bug to mention an unnamed namespace in a header file.

**code sample**
```cpp
// file foo.h:
namespace
{
    const double x = 1.234;  // bad
    double foo(double y)     // bad
    {
        return y + x;
    }
}

namespace Foo
{
    const double x = 1.234; // good
    inline double foo(double y)        // good
    {
        return y + x;
    }
}
```

**enforcement**
- Flag any use of an anonymous namespace in a header file.

---

### [SF.22] Use an unnamed (anonymous) namespace for all internal/non-exported entities

**reason**
Nothing external can depend on an entity in a nested unnamed namespace. Consider putting every definition in an implementation source file in an unnamed namespace unless that is defining an "external/exported" entity.

**code example [bad]**
```cpp
static int f();
int g();
static bool h();
int k();
```

**code example [good]**
```cpp
namespace {
    int f();
    bool h();
}
int g();
int k();
```

**enforcement**
- No specific enforcement.

---
