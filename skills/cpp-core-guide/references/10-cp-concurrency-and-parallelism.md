# CP: Concurrency and parallelism

## Table of Contents

**General:** CP.1-CP.9 | **Concurrency:** CP.20-CP.44, CP.50
**Coroutines:** CP.51-CP.53 | **Message passing:** CP.60-CP.61
**Lock-free:** CP.100-CP.111 | **Etc.:** CP.200-CP.201

---

### [CP.1] Assume that your code will run as part of a multi-threaded program

**reason**
It's hard to be certain that concurrency isn't used now or won't be used sometime in the future. Code gets reused. Libraries not using threads might be used from some other part of a program that does use threads.

**code example [bad]**
```cpp
double cached_computation(int x)
{
    // bad: these statics cause data races in multi-threaded usage
    static int cached_x = 0.0;
    static double cached_result = COMPUTATION_OF_ZERO;

    if (cached_x != x) {
        cached_x = x;
        cached_result = computation(x);
    }
    return cached_result;
}
```

**code example [good]**
```cpp
struct ComputationCache {
    int cached_x = 0;
    double cached_result = COMPUTATION_OF_ZERO;

    double compute(int x) {
        if (cached_x != x) {
            cached_x = x;
            cached_result = computation(x);
        }
        return cached_result;
    }
};
```
Here the cache is stored as member data rather than as shared static state.

**enforcement**
- No specific enforcement.

---

### [CP.2] Avoid data races

**reason**
Unless you do, nothing is guaranteed to work and subtle errors will persist. If two threads can access the same object concurrently (without synchronization), and at least one is a writer, you have a data race.

**code example [bad]**
```cpp
int get_id()
{
  static int id = 1;
  return id++;
}
```
The increment is a data race. Two threads might get the same ID.

**code example [bad]**
```cpp
void f(fstream& fs, regex pattern)
{
    array<double, max> buf;
    int sz = read_vec(fs, buf, max);
    gsl::span<double> s {buf};
    // ...
    auto h1 = async([&] { sort(std::execution::par, s); });     // spawn a task to sort
    auto h2 = async([&] { return find_all(buf, sz, pattern); });   // spawn a task to find matches
    // ...
}
```
Data race on the elements of `buf` (`sort` will both read and write).

**code example [bad]**
```cpp
// code not controlled by a lock
unsigned val;

if (val < 5) {
    // ... other thread can change val here ...
    switch (val) {
    case 0: // ...
    case 1: // ...
    case 2: // ...
    case 3: // ...
    case 4: // ...
    }
}
```
A `val` outside `[0..4]` will cause a jump to an address that could be anywhere in the program.

**enforcement**
- Some is possible, do at least something. Use static and dynamic enforcement tools (e.g., Clang Thread Sanitizer).

---

### [CP.3] Minimize explicit sharing of writable data

**reason**
If you don't share writable data, you can't have a data race. The less sharing, the less chance to forget to synchronize access.

**code example [bad]**
```cpp
bool validate(const vector<Reading>&);
Graph<Temp_node> temperature_gradients(const vector<Reading>&);
Image altitude_map(const vector<Reading>&);

void process_readings(const vector<Reading>& surface_readings)
{
    auto h1 = async([&] { if (!validate(surface_readings)) throw Invalid_data{}; });
    auto h2 = async([&] { return temperature_gradients(surface_readings); });
    auto h3 = async([&] { return altitude_map(surface_readings); });
    // ...
    h1.get();
    auto v2 = h2.get();
    auto v3 = h3.get();
    // ...
}
```
Without `const`, we would have to review every asynchronously invoked function for potential data races on `surface_readings`.

**enforcement**
- No specific enforcement.

---

### [CP.4] Think in terms of tasks, rather than threads

**reason**
A `thread` is an implementation concept. A task is an application notion, something you'd like to do, preferably concurrently. Application concepts are easier to reason about.

**code sample**
```cpp
void some_fun(const std::string& msg)
{
    std::thread publisher([=] { std::cout << msg; });      // bad: less expressive
                                                           //      and more error-prone
    auto pubtask = std::async([=] { std::cout << msg; });  // OK
    // ...
    publisher.join();
}
```

**enforcement**
- No specific enforcement.

---

### [CP.8] Don't try to use `volatile` for synchronization

**reason**
In C++, unlike some other languages, `volatile` does not provide atomicity, does not synchronize between threads, and does not prevent instruction reordering. It simply has nothing to do with concurrency.

**code example [bad]**
```cpp
int free_slots = max_slots;

Pool* use()
{
    if (int n = free_slots--) return &pool[n];
}

// BAD: volatile doesn't fix the race
volatile int free_slots = max_slots;

Pool* use()
{
    if (int n = free_slots--) return &pool[n];
}

// GOOD: use atomic
atomic<int> free_slots = max_slots;

Pool* use()
{
    if (int n = free_slots--) return &pool[n];
}
```

**enforcement**
- No specific enforcement.

---

### [CP.9] Whenever feasible use tools to validate your concurrent code

**reason**
Experience shows that concurrent code is exceptionally hard to get right and that compile-time checking, run-time checks, and testing are less effective at finding concurrency errors than they are at finding errors in sequential code.

**enforcement**
- Use static enforcement tools (e.g., Clang Thread Safety Analysis) and dynamic tools (e.g., Thread Sanitizer / TSAN).

---

## CP.con: Concurrency

---

### [CP.20] Use RAII, never plain `lock()`/`unlock()`

**reason**
Avoids nasty errors from unreleased locks.

**code example [bad]**
```cpp
mutex mtx;

void do_stuff()
{
    mtx.lock();
    // ... do stuff ...
    mtx.unlock();
}
```
Sooner or later, someone will forget `mtx.unlock()`, place a `return`, or throw an exception.

**code example [good]**
```cpp
mutex mtx;

void do_stuff()
{
    unique_lock<mutex> lck {mtx};
    // ... do stuff ...
}
```

**enforcement**
- Flag calls of member `lock()` and `unlock()`.

---

### [CP.21] Use `std::lock()` or `std::scoped_lock` to acquire multiple `mutex`es

**reason**
To avoid deadlocks on multiple `mutex`es.

**code example [bad]**
```cpp
// thread 1
lock_guard<mutex> lck1(m1);
lock_guard<mutex> lck2(m2);

// thread 2
lock_guard<mutex> lck2(m2);
lock_guard<mutex> lck1(m1);
```
This is asking for deadlock.

**code example [good]**
```cpp
// thread 1
lock(m1, m2);
lock_guard<mutex> lck1(m1, adopt_lock);
lock_guard<mutex> lck2(m2, adopt_lock);

// thread 2
lock(m2, m1);
lock_guard<mutex> lck2(m2, adopt_lock);
lock_guard<mutex> lck1(m1, adopt_lock);
```

**code example [good]**
```cpp
// Better (C++17 only):
// thread 1
scoped_lock<mutex, mutex> lck1(m1, m2);

// thread 2
scoped_lock<mutex, mutex> lck2(m2, m1);
```
Order no longer matters.

**enforcement**
- Detect the acquisition of multiple `mutex`es.

---

### [CP.22] Never call unknown code while holding a lock (e.g., a callback)

**reason**
If you don't know what a piece of code does, you are risking deadlock.

**code example [bad]**
```cpp
void do_this(Foo* p)
{
    lock_guard<mutex> lck {my_mutex};
    // ... do something ...
    p->act(my_data);
    // ...
}
```
If `Foo::act` is a virtual function, it might call `do_this` recursively and cause a deadlock on `my_mutex`.

**code sample**
```cpp
recursive_mutex my_mutex;

template<typename Action>
void do_something(Action f)
{
    unique_lock<recursive_mutex> lck {my_mutex};
    // ... do something ...
    f(this);    // f will do something to *this
    // ...
}
```

**enforcement**
- Flag calling a virtual function with a non-recursive `mutex` held
- Flag calling a callback with a non-recursive `mutex` held

---

### [CP.23] Think of a joining `thread` as a scoped container

**reason**
To maintain pointer safety and avoid leaks. If a `thread` joins, we can safely pass pointers to objects in the scope of the `thread` and its enclosing scopes.

**code example [good]**
```cpp
void f(int* p)
{
    // ...
    *p = 99;
    // ...
}
int glob = 33;

void some_fct(int* p)
{
    int x = 77;
    joining_thread t0(f, &x);           // OK
    joining_thread t1(f, p);            // OK
    joining_thread t2(f, &glob);        // OK
    auto q = make_unique<int>(99);
    joining_thread t3(f, q.get());      // OK
    // ...
}
```

**enforcement**
- Ensure that `joining_thread`s don't `detach()`.

---

### [CP.24] Think of a `thread` as a global container

**reason**
If a `thread` is detached, we can safely pass pointers to static and free store objects (only).

**code example [bad]**
```cpp
void f(int* p)
{
    // ...
    *p = 99;
    // ...
}

int glob = 33;

void some_fct(int* p)
{
    int x = 77;
    std::thread t0(f, &x);           // bad
    std::thread t1(f, p);            // bad
    std::thread t2(f, &glob);        // OK
    auto q = make_unique<int>(99);
    std::thread t3(f, q.get());      // bad
    // ...
    t0.detach();
    t1.detach();
    t2.detach();
    t3.detach();
    // ...
}
```

**enforcement**
- Flag attempts to pass local variables to a thread that might `detach()`.

---

### [CP.25] Prefer `gsl::joining_thread` over `std::thread`

**reason**
A `joining_thread` is a thread that joins at the end of its scope. Detached threads are hard to monitor.

**code example [bad]**
```cpp
void f() { std::cout << "Hello "; }

struct F {
    void operator()() const { std::cout << "parallel world "; }
};

int main()
{
    std::thread t1{f};
    std::thread t2{F()};
}  // spot the bugs
```

**code example [good]**
```cpp
void f() { std::cout << "Hello "; }

struct F {
    void operator()() const { std::cout << "parallel world "; }
};

int main()
{
    std::thread t1{f};
    std::thread t2{F()};

    t1.join();
    t2.join();
}  // one bad bug left
```

**enforcement**
- Flag uses of `std::thread`. Suggest `gsl::joining_thread` or C++20 `std::jthread`.

---

### [CP.26] Don't `detach()` a thread

**reason**
The need to outlive the scope of its creation is inherent in the thread's task, but implementing that idea by `detach` makes it harder to monitor and communicate with the detached thread.

**code example [good]**
```cpp
void heartbeat();

void use()
{
    std::thread t(heartbeat);
    t.detach();
    // ...
}

// Better:
gsl::joining_thread t(heartbeat);  // heartbeat runs "forever"
```

**code sample**
```cpp
// Separate point of creation from point of ownership:
void heartbeat();

unique_ptr<gsl::joining_thread> tick_tock {nullptr};

void use()
{
    tick_tock = make_unique<gsl::joining_thread>(heartbeat);
    // ...
}
```

**enforcement**
- Flag `detach()`.

---

### [CP.31] Pass small amounts of data between threads by value, rather than by reference or pointer

**reason**
A small amount of data is cheaper to copy and access than to share it using some locking mechanism. Copying naturally gives unique ownership and eliminates the possibility of data races.

**code sample**
```cpp
string modify1(string);
void modify2(string&);

void fct(string& s)
{
    auto res = async(modify1, s);
    async(modify2, s);
}
```
The call of `modify1` involves copying two `string` values; `modify2` will need some form of locking to avoid data races.

**enforcement**
- No specific enforcement.

---

### [CP.32] To share ownership between unrelated `thread`s use `shared_ptr`

**reason**
If threads are unrelated and they need to share free store memory that needs to be deleted, a `shared_ptr` is the only safe way to ensure proper deletion.

**enforcement**
- No specific enforcement.

---

### [CP.40] Minimize context switching

**reason**
Context switches are expensive.

**enforcement**
- No specific enforcement.

---

### [CP.41] Minimize thread creation and destruction

**reason**
Thread creation is expensive.

**code example [bad]**
```cpp
void worker(Message m)
{
    // process
}

void dispatcher(istream& is)
{
    for (Message m; is >> m; )
        run_list.push_back(new thread(worker, m));
}
```

**code example [good]**
```cpp
Sync_queue<Message> work;

void dispatcher(istream& is)
{
    for (Message m; is >> m; )
        work.put(m);
}

void worker()
{
    for (Message m; m = work.get(); ) {
        // process
    }
}

void workers()  // set up worker threads (specifically 4 worker threads)
{
    joining_thread w1 {worker};
    joining_thread w2 {worker};
    joining_thread w3 {worker};
    joining_thread w4 {worker};
}
```

**enforcement**
- No specific enforcement.

---

### [CP.42] Don't `wait` without a condition

**reason**
A `wait` without a condition can miss a wakeup or wake up simply to find that there is no work to do.

**code example [bad]**
```cpp
std::condition_variable cv;
std::mutex mx;

void thread1()
{
    while (true) {
        // do some work ...
        std::unique_lock<std::mutex> lock(mx);
        cv.notify_one();    // wake other thread
    }
}

void thread2()
{
    while (true) {
        std::unique_lock<std::mutex> lock(mx);
        cv.wait(lock);    // might block forever
        // do work ...
    }
}
```

**code example [good]**
```cpp
template<typename T>
class Sync_queue {
public:
    void put(const T& val);
    void put(T&& val);
    void get(T& val);
private:
    mutex mtx;
    condition_variable cond;
    list<T> q;
};

template<typename T>
void Sync_queue<T>::put(const T& val)
{
    lock_guard<mutex> lck(mtx);
    q.push_back(val);
    cond.notify_one();
}

template<typename T>
void Sync_queue<T>::get(T& val)
{
    unique_lock<mutex> lck(mtx);
    cond.wait(lck, [this] { return !q.empty(); });    // prevent spurious wakeup
    val = q.front();
    q.pop_front();
}
```

**enforcement**
- Flag all `wait`s without conditions.

---

### [CP.43] Minimize time spent in a critical section

**reason**
The less time spent with a `mutex` taken, the less chance that another `thread` has to wait, and `thread` suspension and resumption are expensive.

**code example [bad]**
```cpp
void do_something() // bad
{
    unique_lock<mutex> lck(my_lock);
    do0();  // preparation: does not need lock
    do1();  // transaction: needs locking
    do2();  // cleanup: does not need locking
}
```

**code example [good]**
```cpp
void do_something() // OK
{
    do0();  // preparation: does not need lock
    {
        unique_lock<mutex> lck(my_lock);
        do1();  // transaction: needs locking
    }
    do2();  // cleanup: does not need locking
}
```

**enforcement**
- Flag "naked" `lock()` and `unlock()`.

---

### [CP.44] Remember to name your `lock_guard`s and `unique_lock`s

**reason**
An unnamed local object is a temporary that immediately goes out of scope.

**code example [bad]**
```cpp
mutex m1;
mutex m2;

void f()
{
    unique_lock<mutex>(m1); // (A) default-constructed local, shadows global m1!
    lock_guard<mutex> {m2}; // (B) unnamed temporary, locks then immediately unlocks m2
    // do work in critical section ... OOPS: neither mutex is locked!
}
```

**enforcement**
- Flag all unnamed `lock_guard`s and `unique_lock`s.

---

### [CP.50] Define a `mutex` together with the data it guards. Use `synchronized_value<T>` where possible

**reason**
It should be obvious to a reader that the data is to be guarded and how.

**code sample**
```cpp
struct Record {
    std::mutex m;   // take this mutex before accessing other members
    // ...
};

class MyClass {
    struct DataRecord {
       // ...
    };
    synchronized_value<DataRecord> data; // Protect the data with a mutex
};
```

**enforcement**
- No specific enforcement.

---

## CP.coro: Coroutines

---

### [CP.51] Do not use capturing lambdas that are coroutines

**reason**
Usage patterns correct with normal lambdas are hazardous with coroutine lambdas. The obvious pattern of capturing variables will result in accessing freed memory after the first suspension point.

**code example [bad]**
```cpp
int value = get_value();
std::shared_ptr<Foo> sharedFoo = get_foo();
{
  const auto lambda = [value, sharedFoo]() -> std::future<void>
  {
    co_await something();
    // "sharedFoo" and "value" have already been destroyed
    // the "shared" pointer didn't accomplish anything
  };
  lambda();
} // the lambda closure object has now gone out of scope
```

**code example [good]**
```cpp
int value = get_value();
std::shared_ptr<Foo> sharedFoo = get_foo();
{
  // take as by-value parameter instead of as a capture
  const auto lambda = [](auto sharedFoo, auto value) -> std::future<void>
  {
    co_await something();
    // sharedFoo and value are still valid at this point
  };
  lambda(sharedFoo, value);
} // the lambda closure object has now gone out of scope
```

**code example [good]**
```cpp
// Best: use a function for coroutines
std::future<void> Class::do_something(int value, std::shared_ptr<Foo> sharedFoo)
{
  co_await something();
  // sharedFoo and value are still valid at this point
}

void SomeOtherFunction()
{
  int value = get_value();
  std::shared_ptr<Foo> sharedFoo = get_foo();
  do_something(value, sharedFoo);
}
```

**enforcement**
- Flag a lambda that is a coroutine and has a non-empty capture list.

---

### [CP.52] Do not hold locks or other synchronization primitives across suspension points

**reason**
This pattern creates a significant risk of deadlocks. If the coroutine completes on a different thread, that is undefined behavior.

**code example [bad]**
```cpp
std::mutex g_lock;

std::future<void> Class::do_something()
{
    std::lock_guard<std::mutex> guard(g_lock);
    co_await something(); // DANGER: coroutine suspended while holding a lock
    co_await somethingElse();
}
```

**code example [good]**
```cpp
std::mutex g_lock;

std::future<void> Class::do_something()
{
    {
        std::lock_guard<std::mutex> guard(g_lock);
        // modify data protected by lock
    }
    co_await something(); // OK: lock released before coroutine suspends
    co_await somethingElse();
}
```

**enforcement**
- Flag all lock guards that are not destructed before a coroutine suspends.

---

### [CP.53] Parameters to coroutines should not be passed by reference

**reason**
Once a coroutine reaches the first suspension point, the synchronous portion returns. After that point any parameters passed by reference are dangling.

**code example [bad]**
```cpp
std::future<int> Class::do_something(const std::shared_ptr<int>& input)
{
    co_await something();
    // DANGER: the reference to input may no longer be valid
    co_return *input + 1;
}
```

**code example [good]**
```cpp
std::future<int> Class::do_something(std::shared_ptr<int> input)
{
    co_await something();
    co_return *input + 1; // input is a copy that is still valid here
}
```

**enforcement**
- Flag all reference parameters to a coroutine.

---

## CP.mess: Message passing

---

### [CP.60] Use a `future` to return a value from a concurrent task

**reason**
A `future` preserves the usual function call return semantics for asynchronous tasks. There is no explicit locking and both correct (value) return and error (exception) return are handled simply.

**enforcement**
- No specific enforcement.

---

### [CP.61] Use `async()` to spawn concurrent tasks

**reason**
Similar to R.12 (avoid raw owning pointers), you should also avoid raw threads and raw promises where possible. Use a factory function such as `std::async`.

**code example [good]**
```cpp
int read_value(const std::string& filename)
{
    std::ifstream in(filename);
    in.exceptions(std::ifstream::failbit);
    int value;
    in >> value;
    return value;
}

void async_example()
{
    try {
        std::future<int> f1 = std::async(read_value, "v1.txt");
        std::future<int> f2 = std::async(read_value, "v2.txt");
        std::cout << f1.get() + f2.get() << '\n';
    } catch (const std::ios_base::failure& fail) {
        // handle exception here
    }
}
```

**code example [bad]**
```cpp
void async_example()
{
    std::promise<int> p1;
    std::future<int> f1 = p1.get_future();
    std::thread t1([p1 = std::move(p1)]() mutable {
        p1.set_value(read_value("v1.txt"));
    });
    t1.detach(); // evil

    std::packaged_task<int()> pt2(read_value, "v2.txt");
    std::future<int> f2 = pt2.get_future();
    std::thread(std::move(pt2)).detach();

    std::cout << f1.get() + f2.get() << '\n';
}
```

**code example [good]**
```cpp
// Good: use a WorkQueue abstraction
void async_example(WorkQueue& wq)
{
    std::future<int> f1 = wq.enqueue([]() {
        return read_value("v1.txt");
    });
    std::future<int> f2 = wq.enqueue([]() {
        return read_value("v2.txt");
    });
    std::cout << f1.get() + f2.get() << '\n';
}
```

**enforcement**
- No specific enforcement.

---

## CP.free: Lock-free programming

---

### [CP.100] Don't use lock-free programming unless you absolutely have to

**reason**
It's error-prone and requires expert level knowledge of language features, machine architecture, and data structures.

**code example [bad]**
```cpp
extern atomic<Link*> head;        // the shared head of a linked list

Link* nh = new Link(data, nullptr);    // make a link ready for insertion
Link* h = head.load();                 // read the shared head of the list

do {
    if (h->data <= data) break;        // if so, insert elsewhere
    nh->next = h;                      // next element is the previous head
} while (!head.compare_exchange_weak(h, nh));    // write nh to head or to h
```
Spot the bug. Read up on the ABA problem.

**enforcement**
- No specific enforcement.

---

### [CP.101] Distrust your hardware/compiler combination

**reason**
The low-level hardware interfaces used by lock-free programming are among the hardest to implement well and among the areas where the most subtle portability problems occur.

**enforcement**
- Have strong rules for re-testing in place that covers any change in hardware, operating system, compiler, and libraries.

---

### [CP.102] Carefully study the literature

**reason**
With the exception of atomics and a few other standard patterns, lock-free programming is really an expert-only topic. Become an expert before shipping lock-free code.

**enforcement**
- No specific enforcement.

---

### [CP.110] Do not write your own double-checked locking for initialization

**reason**
Since C++11, static local variables are now initialized in a thread-safe way. Use either static local variables or `std::call_once` instead.

**code example [good]**
```cpp
// Example with std::call_once
void f()
{
    static std::once_flag my_once_flag;
    std::call_once(my_once_flag, []()
    {
        // do this only once
    });
    // ...
}

// Example with thread-safe static local variables of C++11
void f()
{
    static My_class my_object; // Constructor called only once
    // ...
}
```

**enforcement**
- No specific enforcement.

---

### [CP.111] Use a conventional pattern if you really need double-checked locking

**reason**
Double-checked locking is easy to mess up.

**code example [bad]**
```cpp
mutex action_mutex;
volatile bool action_needed;

if (action_needed) {
    std::lock_guard<std::mutex> lock(action_mutex);
    if (action_needed) {
        take_action();
        action_needed = false;
    }
}
```
The use of `volatile` does not make the first check thread-safe.

**code example [good]**
```cpp
mutex action_mutex;
atomic<bool> action_needed;

if (action_needed) {
    std::lock_guard<std::mutex> lock(action_mutex);
    if (action_needed) {
        take_action();
        action_needed = false;
    }
}
```

**code example [good]**
```cpp
// Fine-tuned memory order:
mutex action_mutex;
atomic<bool> action_needed;

if (action_needed.load(memory_order_acquire)) {
    lock_guard<std::mutex> lock(action_mutex);
    if (action_needed.load(memory_order_relaxed)) {
        take_action();
        action_needed.store(false, memory_order_release);
    }
}
```

**enforcement**
- No specific enforcement.

---

## CP.etc: Etc. concurrency rules

---

### [CP.200] Use `volatile` only to talk to non-C++ memory

**reason**
`volatile` is used to refer to objects that are shared with "non-C++" code or hardware that does not follow the C++ memory model.

**code example [bad]**
```cpp
const volatile long clock;
// This describes a register constantly updated by a clock circuit.
// clock is volatile because its value will change without any action from the C++ program.

long t1 = clock;
// ... no use of clock here ...
long t2 = clock;
```

**code example [bad]**
```cpp
int volatile* vi = get_hardware_memory_location();
    // note: we get a pointer to someone else's memory here
    // volatile says "treat this with extra respect"
```

**code example [bad]**
```cpp
void f()
{
    volatile int i = 0; // bad, volatile local variable
    // etc.
}

class My_type {
    volatile int i = 0; // suspicious, volatile data member
    // etc.
};
```

**enforcement**
- Flag `volatile T` local and data members; almost certainly you intended to use `atomic<T>` instead.

---

### [CP.201] Signals

**reason**
UNIX signal handling. Very little is async-signal-safe. Best to communicate with a signal handler minimally or not at all.

**enforcement**
- No specific enforcement.

---
