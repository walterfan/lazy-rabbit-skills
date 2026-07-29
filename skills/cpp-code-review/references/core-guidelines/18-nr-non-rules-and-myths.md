# NR: Non-Rules and myths

## Table of Contents

- [NR.1] Don't insist that all declarations should be at the top of a function
- [NR.2] Don't insist on having only a single `return`-statement in a function
- [NR.3] Don't avoid exceptions
- [NR.4] Don't insist on placing each class definition in its own source file
- [NR.5] Don't use two-phase initialization
- [NR.6] Don't place all cleanup actions at the end of a function and `goto exit`
- [NR.7] Don't make data members `protected`

---

### [NR.1] Don't insist that all declarations should be at the top of a function

**reason**
The "all declarations on top" rule is a legacy of old programming languages that didn't allow initialization of variables and constants after a statement. This leads to longer programs and more errors caused by uninitialized and wrongly initialized variables.

**code example [bad]**
```cpp
int use(int x)
{
    int i;
    char c;
    double d;

    // ... some stuff ...

    if (x < i) {
        // ...
        i = f(x, d);
    }
    if (i < x) {
        // ...
        i = g(x, c);
    }
    return i;
}
```
The larger the distance between the uninitialized variable and its use, the larger the chance of a bug.

**enforcement**
- Always initialize an object
- ES.21: Don't introduce a variable (or constant) before you need to use it

---

### [NR.2] Don't insist on having only a single `return`-statement in a function

**reason**
The single-return rule can lead to unnecessarily convoluted code and the introduction of extra state variables. It makes it harder to concentrate error checking at the top of a function.

**code example [good]**
```cpp
template<class T>
string sign(T x)
{
    if (x < 0)
        return "negative";
    if (x > 0)
        return "positive";
    return "zero";
}
```

**code example [bad]**
```cpp
template<class T>
string sign(T x)        // bad
{
    string res;
    if (x < 0)
        res = "negative";
    else if (x > 0)
        res = "positive";
    else
        res = "zero";
    return res;
}
```

**code sample**
```cpp
int index(const char* p)
{
    if (!p) return -1;  // error indicator: alternatively "throw nullptr_error{}"
    // ... do a lookup to find the index for p
    return i;
}

// Applying single-return rule: worse
int index2(const char* p)
{
    int i;
    if (!p)
        i = -1;  // error indicator
    else {
        // ... do a lookup to find the index for p
    }
    return i;
}
```

**enforcement**
- Keep functions short and simple
- Feel free to use multiple `return` statements (and to throw exceptions)

---

### [NR.3] Don't avoid exceptions

**reason**
There seem to be four main reasons given for not using exceptions: they are inefficient; they lead to leaks and errors; exception performance is not predictable; the exception-handling run-time support takes up too much space. However, exceptions clearly differentiate between erroneous return and ordinary return, they cannot be forgotten or ignored, and they can be used systematically.

**enforcement**
- Use RAII
- Use Contracts/assertions: GSL's `Expects` and `Ensures`

---

### [NR.4] Don't insist on placing each class definition in its own source file

**reason**
The resulting number of files from placing each class in its own file are hard to manage and can slow down compilation. Individual classes are rarely a good logical unit of maintenance and distribution.

**enforcement**
- Use namespaces containing logically cohesive sets of classes and functions.

---

### [NR.5] Don't use two-phase initialization

**reason**
Splitting initialization into two leads to weaker invariants, more complicated code (having to deal with semi-constructed objects), and errors.

**code example [bad]**
```cpp
// Old conventional style: many problems
class Picture
{
    int mx;
    int my;
    int * data;
public:
    // main problem: constructor does not fully construct
    Picture(int x, int y)
    {
        mx = x;
        my = y;
        data = nullptr;
    }

    ~Picture()
    {
        Cleanup();
    }

    // bad: two-phase initialization
    bool Init()
    {
        if (mx <= 0 || my <= 0) {
            return false;
        }
        if (data) {
            return false;
        }
        data = (int*) malloc(mx*my*sizeof(int));   // also bad: owning raw * and malloc
        return data != nullptr;
    }

    void Cleanup()
    {
        if (data) free(data);
        data = nullptr;
    }
};

Picture picture(100, 0); // not ready-to-use picture here
if (!picture.Init()) {
    puts("Error, invalid picture");
}
// now have an invalid picture object instance.
```

**code example [good]**
```cpp
class Picture
{
    int mx;
    int my;
    vector<int> data;

    static int check_size(int size)
    {
        // invariant check
        Expects(size > 0);
        return size;
    }

public:
    Picture(int x, int y)
        : mx(check_size(x))
        , my(check_size(y))
        , data(mx * my) // will throw std::bad_alloc on error
    {
        // picture is ready-to-use
    }

    // compiler generated dtor does the job. (also see C.21)
};

Picture picture1(100, 100);
// picture1 is ready-to-use here...

// not a valid size for y,
// default contract violation behavior will call std::terminate then
Picture picture2(100, 0);
// not reach here...
```

**enforcement**
- Always establish a class invariant in a constructor
- Don't define an object before it is needed

---

### [NR.6] Don't place all cleanup actions at the end of a function and `goto exit`

**reason**
`goto` is error-prone. This technique is a pre-exception technique for RAII-like resource and error handling.

**code example [bad]**
```cpp
void do_something(int n)
{
    if (n < 100) goto exit;
    // ...
    int* p = (int*) malloc(n);
    // ...
    if (some_error) goto exit;
    // ...
exit:
    free(p);
}
```
And spot the bug.

**enforcement**
- Use exceptions and RAII
- For non-RAII resources, use `finally`

---

### [NR.7] Don't make data members `protected`

**reason**
`protected` data is a source of errors. `protected` data can be manipulated from an unbounded amount of code in various places. `protected` data is the class hierarchy equivalent to global data.

**enforcement**
- Avoid `protected` data

---
