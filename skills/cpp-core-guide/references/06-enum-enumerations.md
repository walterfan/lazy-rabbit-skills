# Enum: Enumerations

## Table of Contents

- [Enum.1] Prefer enumerations over macros
- [Enum.2] Use enumerations to represent sets of related named constants
- [Enum.3] Prefer class enums over "plain" enums
- [Enum.4] Define operations on enumerations for safe and simple use
- [Enum.5] Don't use `ALL_CAPS` for enumerators
- [Enum.6] Avoid unnamed enumerations
- [Enum.7] Specify the underlying type of an enumeration only when necessary
- [Enum.8] Specify enumerator values only when necessary

---

### [Enum.1] Prefer enumerations over macros

**reason**
Macros do not obey scope and type rules. Also, macro names are removed during preprocessing and so usually don't appear in tools like debuggers.

**code example [bad]**
```cpp
// webcolors.h (third party header)
#define RED   0xFF0000
#define GREEN 0x00FF00
#define BLUE  0x0000FF

// productinfo.h
#define RED    0
#define PURPLE 1
#define BLUE   2

int webby = BLUE;   // webby == 2; probably not what was desired
```

**code example [good]**
```cpp
enum class Web_color { red = 0xFF0000, green = 0x00FF00, blue = 0x0000FF };
enum class Product_info { red = 0, purple = 1, blue = 2 };

int webby = blue;   // error: be specific
Web_color webby = Web_color::blue;
```

**enforcement**
- Flag macros that define integer values. Use `enum` or `const inline` or another non-macro alternative instead.

---

### [Enum.2] Use enumerations to represent sets of related named constants

**reason**
An enumeration shows the enumerators to be related and can be a named type.

**code example [good]**
```cpp
enum class Web_color { red = 0xFF0000, green = 0x00FF00, blue = 0x0000FF };
```

**enforcement**
- Flag `switch`-statements where the `case`s cover most but not all enumerators of an enumeration
- Flag `switch`-statements where the `case`s cover a few enumerators of an enumeration, but there is no `default`

---

### [Enum.3] Prefer class enums over "plain" enums

**reason**
To minimize surprises: traditional enums convert to int too readily.

**code example [bad]**
```cpp
void Print_color(int color);

enum Web_color { red = 0xFF0000, green = 0x00FF00, blue = 0x0000FF };
enum Product_info { red = 0, purple = 1, blue = 2 };

Web_color webby = Web_color::blue;
Print_color(webby);              // compiles, but semantically wrong
Print_color(Product_info::blue); // compiles, but semantically wrong
```

**code example [good]**
```cpp
void Print_color(int color);

enum class Web_color { red = 0xFF0000, green = 0x00FF00, blue = 0x0000FF };
enum class Product_info { red = 0, purple = 1, blue = 2 };

Web_color webby = Web_color::blue;
Print_color(webby);  // Error: cannot convert Web_color to int.
Print_color(Product_info::red);  // Error: cannot convert Product_info to int.
```

**enforcement**
- (Simple) Warn on any non-class `enum` definition

---

### [Enum.4] Define operations on enumerations for safe and simple use

**reason**
Convenience of use and avoidance of errors.

**code example [good]**
```cpp
enum class Day { mon, tue, wed, thu, fri, sat, sun };

Day& operator++(Day& d)
{
    return d = (d == Day::sun) ? Day::mon : static_cast<Day>(static_cast<int>(d)+1);
}

Day today = Day::sat;
Day tomorrow = ++today;
```

**enforcement**
- Flag repeated expressions cast back into an enumeration

---

### [Enum.5] Don't use `ALL_CAPS` for enumerators

**reason**
Avoid clashes with macros.

**code example [bad]**
```cpp
#define RED   0xFF0000
#define GREEN 0x00FF00
#define BLUE  0x0000FF

enum class Product_info { RED, PURPLE, BLUE };   // syntax error
```

**code example [good]**
```cpp
enum class Product_info { red, purple, blue };
```

**enforcement**
- Flag ALL_CAPS enumerators

---

### [Enum.6] Avoid unnamed enumerations

**reason**
If you can't name an enumeration, the values are not related.

**code example [bad]**
```cpp
enum { red = 0xFF0000, scale = 4, is_signed = 1 };
```

**code example [good]**
```cpp
constexpr int red = 0xFF0000;
constexpr short scale = 4;
constexpr bool is_signed = true;
```

**enforcement**
- Flag unnamed enumerations

---

### [Enum.7] Specify the underlying type of an enumeration only when necessary

**reason**
The default is the easiest to read and write. `int` is the default integer type and is compatible with C `enum`s.

**code example [bad]**
```cpp
enum class Web_color : int32_t { red = 0xFF0000,
                                 green = 0x00FF00,
                                 blue = 0x0000FF };  // underlying type is redundant
```

**code example [good]**
```cpp
enum class Direction : char { n, s, e, w,
                              ne, nw, se, sw };  // underlying type saves space

enum Flags : char;  // forward-declare requires underlying type
void f(Flags);
enum Flags : char { /* ... */ };
```

**enforcement**
- Flag redundant underlying type specifications

---

### [Enum.8] Specify enumerator values only when necessary

**reason**
It's the simplest. It avoids duplicate enumerator values. The default gives a consecutive set of values that is good for `switch`-statement implementations.

**code example [bad]**
```cpp
enum class Col2 { red = 1, yellow = 2, blue = 2 }; // typo
```

**code example [good]**
```cpp
enum class Col1 { red, yellow, blue };
enum class Month { jan = 1, feb, mar, apr, may, jun,
                   jul, august, sep, oct, nov, dec }; // starting with 1 is conventional
enum class Base_flag { dec = 1, oct = dec << 1, hex = dec << 2 }; // set of bits
```

**enforcement**
- Flag duplicate enumerator values
- Flag explicitly specified all-consecutive enumerator values

---
