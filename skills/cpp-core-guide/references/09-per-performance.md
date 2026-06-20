# Per: Performance

## Table of Contents

- [Per.1] Don't optimize without reason
- [Per.2] Don't optimize prematurely
- [Per.3] Don't optimize something that's not performance critical
- [Per.4] Don't assume that complicated code is necessarily faster than simple code
- [Per.5] Don't assume that low-level code is necessarily faster than high-level code
- [Per.6] Don't make claims about performance without measurements
- [Per.7] Design to enable optimization
- [Per.10] Rely on the static type system
- [Per.11] Move computation from run time to compile time
- [Per.12] Eliminate redundant aliases
- [Per.13] Eliminate redundant indirections
- [Per.14] Minimize the number of allocations and deallocations
- [Per.15] Do not allocate on a critical branch
- [Per.16] Use compact data structures
- [Per.17] Declare the most used member of a time-critical struct first
- [Per.18] Space is time
- [Per.19] Access memory predictably
- [Per.30] Avoid context switches on the critical path

---

### [Per.1] Don't optimize without reason

**reason**
If there is no need for optimization, the main result of the effort will be more errors and higher maintenance costs.

**enforcement**
- No specific enforcement.

---

### [Per.2] Don't optimize prematurely

**reason**
Elaborately optimized code is usually larger and harder to change than unoptimized code.

**enforcement**
- No specific enforcement.

---

### [Per.3] Don't optimize something that's not performance critical

**reason**
Optimizing a non-performance-critical part of a program has no effect on system performance. If your program spends most of its time waiting for the web or for a human, optimization of in-memory computation is probably useless.

**enforcement**
- No specific enforcement.

---

### [Per.4] Don't assume that complicated code is necessarily faster than simple code

**reason**
Simple code can be very fast. Optimizers sometimes do marvels with simple code.

**code example [good]**
```cpp
// clear expression of intent, fast execution
vector<uint8_t> v(100000);

for (auto& c : v)
    c = ~c;
```

**code example [bad]**
```cpp
// intended to be faster, but is often slower
vector<uint8_t> v(100000);

for (size_t i = 0; i < v.size(); i += sizeof(uint64_t)) {
    uint64_t& quad_word = *reinterpret_cast<uint64_t*>(&v[i]);
    quad_word = ~quad_word;
}
```

**enforcement**
- No specific enforcement.

---

### [Per.5] Don't assume that low-level code is necessarily faster than high-level code

**reason**
Low-level code sometimes inhibits optimizations. Optimizers sometimes do marvels with high-level code.

**enforcement**
- No specific enforcement.

---

### [Per.6] Don't make claims about performance without measurements

**reason**
The field of performance is littered with myth and bogus folklore. Modern hardware and optimizers defy naive assumptions; even experts are regularly surprised.

**enforcement**
- No specific enforcement. Use `time` or `<chrono>` to measure.

---

### [Per.7] Design to enable optimization

**reason**
Because we often need to optimize the initial design. A design that ignores the possibility of later improvement is hard to change.

**code example [bad]**
```cpp
// C/C++ standard qsort: throws away type info, forces user to repeat info
void qsort (void* base, size_t num, size_t size, int (*compar)(const void*, const void*));

double data[100];
// ...
qsort(data, 100, sizeof(double), compare_doubles);
```

**code example [good]**
```cpp
template<typename Iter>
    void sort(Iter b, Iter e);  // sort [b:e)

sort(data, data + 100);
```

**code example [good]**
```cpp
// C++20: even better
void sort(sortable auto& c);
sort(c);

// With comparison criterion
template<random_access_range R, class C> requires sortable<R, C>
void sort(R&& r, C c);
```

**code sample**
```cpp
// binary_search returns only true/false
template<class ForwardIterator, class T>
bool binary_search(ForwardIterator first, ForwardIterator last, const T& val);

// lower_bound returns iterator to first match
template<class ForwardIterator, class T>
ForwardIterator lower_bound(ForwardIterator first, ForwardIterator last, const T& val);

// equal_range returns pair of iterators specifying first and one beyond last match
template<class ForwardIterator, class T>
pair<ForwardIterator, ForwardIterator>
equal_range(ForwardIterator first, ForwardIterator last, const T& val);

auto r = equal_range(begin(c), end(c), 7);
for (auto p = r.first; p != r.second; ++p)
    cout << *p << '\n';
```

**enforcement**
- Tricky. Maybe looking for `void*` function arguments will find examples of interfaces that hinder later optimization.

---

### [Per.10] Rely on the static type system

**reason**
Type violations, weak types (e.g. `void*`s), and low-level code (e.g., manipulation of sequences as individual bytes) make the job of the optimizer much harder.

**enforcement**
- No specific enforcement.

---

### [Per.11] Move computation from run time to compile time

**reason**
To decrease code size and run time. To avoid data races by using constants. To catch errors at compile time.

**code sample**
```cpp
double square(double d) { return d*d; }
static double s2 = square(2);    // old-style: dynamic initialization

constexpr double ntimes(double d, int n)   // assume 0 <= n
{
        double m = 1;
        while (n--) m *= d;
        return m;
}
constexpr double s3 {ntimes(2, 3)};  // modern-style: compile-time initialization
```

**code sample**
```cpp
constexpr int on_stack_max = 20;

template<typename T>
struct Scoped {     // store a T in Scoped
        // ...
    T obj;
};

template<typename T>
struct On_heap {    // store a T on the free store
        // ...
        T* objp;
};

template<typename T>
using Handle = typename std::conditional<(sizeof(T) <= on_stack_max),
                    Scoped<T>,      // first alternative
                    On_heap<T>      // second alternative
               >::type;

void f()
{
    Handle<double> v1;                   // the double goes on the stack
    Handle<std::array<double, 200>> v2;  // the array goes on the free store
    // ...
}
```

**enforcement**
- Look for simple functions that might be constexpr (but are not)
- Look for functions called with all constant-expression arguments
- Look for macros that could be constexpr

---

### [Per.12] Eliminate redundant aliases

**reason**
Redundant aliases can hinder optimization.

**enforcement**
- No specific enforcement.

---

### [Per.13] Eliminate redundant indirections

**reason**
Redundant indirections can hinder optimization.

**enforcement**
- No specific enforcement.

---

### [Per.14] Minimize the number of allocations and deallocations

**reason**
Allocation and deallocation are expensive operations.

**enforcement**
- No specific enforcement.

---

### [Per.15] Do not allocate on a critical branch

**reason**
Allocation can block or add unpredictable latency on a critical path.

**enforcement**
- No specific enforcement.

---

### [Per.16] Use compact data structures

**reason**
Performance is typically dominated by memory access times.

**enforcement**
- No specific enforcement.

---

### [Per.17] Declare the most used member of a time-critical struct first

**reason**
Layout can affect cache performance.

**enforcement**
- No specific enforcement.

---

### [Per.18] Space is time

**reason**
Performance is typically dominated by memory access times.

**enforcement**
- No specific enforcement.

---

### [Per.19] Access memory predictably

**reason**
Performance is very sensitive to cache performance, and cache algorithms favor simple (usually linear) access to adjacent data.

**code sample**
```cpp
int matrix[rows][cols];

// bad: column-major traversal â€” poor cache locality
for (int c = 0; c < cols; ++c)
    for (int r = 0; r < rows; ++r)
        sum += matrix[r][c];

// good: row-major traversal â€” good cache locality
for (int r = 0; r < rows; ++r)
    for (int c = 0; c < cols; ++c)
        sum += matrix[r][c];
```

**enforcement**
- No specific enforcement.

---

### [Per.30] Avoid context switches on the critical path

**reason**
Context switches are expensive.

**enforcement**
- No specific enforcement.

---
