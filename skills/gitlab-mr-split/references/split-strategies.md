# Split Strategies Reference

## Overview

When splitting a large MR, the key decision is how to group files. Each strategy
produces a different set of sub-MRs optimized for different codebases and change patterns.

## Strategy: by-directory

Groups files by their top-level (or second-level) directory path.

**Best for**: monorepos, multi-module projects where each directory is a semi-independent unit.

**Example**:
```
src/auth/login.py        -> group "auth"
src/auth/token.py        -> group "auth"
src/billing/invoice.py   -> group "billing"
src/billing/payment.py   -> group "billing"
tests/test_login.py      -> group "tests"
```

**Option**: `--group-depth N` controls how many directory levels to use for grouping.
With `--group-depth 2`, `src/auth/login.py` groups as `src/auth` instead of `src`.

## Strategy: by-layer

Groups files by their architectural role, inferred from path patterns and file naming.

**Best for**: layered architectures (MVC, clean architecture, hexagonal).

**Layer detection rules**:
| Layer | Path/name patterns |
|-------|--------------------|
| model | `model/`, `entity/`, `domain/`, `*Model.*`, `*Entity.*` |
| service | `service/`, `usecase/`, `*Service.*`, `*UseCase.*` |
| controller | `controller/`, `handler/`, `api/`, `*Controller.*`, `*Handler.*` |
| repository | `repository/`, `dao/`, `*Repository.*`, `*Dao.*` |
| config | `config/`, `*.yml`, `*.yaml`, `*.properties`, `*.toml`, `*.json` (non-source) |
| test | `test/`, `tests/`, `*Test.*`, `*_test.*`, `test_*.*`, `*Spec.*` |
| migration | `migration/`, `db/migrate/`, `*.sql` |
| other | everything else |

**Option**: `--colocate-tests` (default: true) moves test files into the same group as
the source files they test, rather than grouping all tests together.

## Strategy: by-dependency

Analyzes import/include statements to build a dependency graph, then splits into
topological layers so that each sub-MR only depends on files in previous sub-MRs.

**Best for**: tightly coupled changes where import order matters.

**How it works**:
1. Parse imports/includes from each changed file.
2. Build a directed graph of dependencies between changed files.
3. Compute topological layers (files with no dependencies on other changed files go first).
4. Each layer becomes a sub-MR group.

**Supported languages**: Python (`import`, `from X import`), Java/Kotlin (`import`),
JavaScript/TypeScript (`import`, `require`), Go (`import`), C/C++ (`#include`).

## Strategy: custom

User provides an explicit mapping of files to groups via a JSON file.

**Format**:
```json
{
  "groups": [
    {
      "name": "database-schema",
      "files": ["db/migrate/001_add_users.sql", "db/migrate/002_add_roles.sql"]
    },
    {
      "name": "user-model",
      "files": ["src/models/user.py", "src/models/role.py", "tests/test_user.py"]
    },
    {
      "name": "auth-api",
      "files": ["src/controllers/auth.py", "src/services/auth_service.py", "tests/test_auth.py"]
    }
  ]
}
```

**Validation**: the script checks that every changed file appears in exactly one group
and that no file is listed that isn't in the original MR.

## Choosing a Strategy

```
Is the MR spread across multiple top-level directories?
  YES -> by-directory
  NO  -> Is the code layered (model/service/controller)?
           YES -> by-layer
           NO  -> Are there complex cross-file dependencies?
                    YES -> by-dependency
                    NO  -> custom (or by-directory with --group-depth 2)
```

## Dependency Chain

Sub-MRs form a chain:

```
target-branch <-- split-1 <-- split-2 <-- split-3
                   (MR 1/3)    (MR 2/3)    (MR 3/3)
```

- MR 1/3 targets `target-branch` (e.g., `main`)
- MR 2/3 targets `split-1`
- MR 3/3 targets `split-2`

Merge in order: 1/3 first, then 2/3 (retarget to `main` after 1/3 merges), then 3/3.

Some teams prefer all sub-MRs to target `main` directly (parallel strategy). Use
`--target-mode parallel` to create independent sub-MRs that all target the original
target branch. This works when the file groups are truly independent with no
cross-group dependencies.
