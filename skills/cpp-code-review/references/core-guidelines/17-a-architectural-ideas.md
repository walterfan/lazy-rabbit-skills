# A: Architectural ideas

## Table of Contents

- [A.1] Separate stable code from less stable code
- [A.2] Express potentially reusable parts as a library
- [A.4] There should be no cycles among libraries

---

### [A.1] Separate stable code from less stable code

**reason**
Isolating less stable code facilitates its unit testing, interface improvement, refactoring, and eventual deprecation.

**enforcement**
- No specific enforcement.

---

### [A.2] Express potentially reusable parts as a library

**reason**
A library is a collection of declarations and definitions maintained, documented, and shipped together. A library could be a set of headers (a "header-only library") or a set of headers plus a set of object files.

**enforcement**
- No specific enforcement.

---

### [A.4] There should be no cycles among libraries

**reason**
A cycle complicates the build process. Cycles are hard to understand and might introduce indeterminism (unspecified behavior).

A library can contain cyclic references in the definition of its components. However, a library should not depend on another that depends on it.

**enforcement**
- No specific enforcement.

---
