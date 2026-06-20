---
name: lazy-sqlite-helper
description: >-
  Query and change local SQLite databases from natural-language requests. Use
  when the user mentions sqlite, `.db`, `.sqlite`, text2sql, SQL, table
  structure, table schema, records, rows, or wants to inspect or modify data in
  a SQLite file. This skill must show the SQL before execution, render query
  results as markdown tables, and use SQLite shortcuts for listing tables,
  describing schema, previewing records, and safely applying updates.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - sqlite
  - sql
  - text2sql
  - database
  - markdown-table
  - local-data
category: data-tools
use_cases:
  - "show me the tables in this sqlite db"
  - "generate SQL from this text and run it on the .db file"
  - "describe the schema of the orders table"
  - "preview rows before updating this sqlite table"
  - "change records in a sqlite database safely"
platforms:
  - codex
  - claude-code
  - cursor
visibility: public
---

# lazy-sqlite-helper

Turn user text into safe SQLite work: inspect first, generate SQL second, execute third, and always show both the SQL and the result.

## Contract

- **scope_in**: local SQLite files such as `.db`, `.sqlite`, `.sqlite3`; natural-language-to-SQL translation; schema inspection; record previews; `SELECT`, `INSERT`, `UPDATE`, `DELETE`, and light DDL for SQLite
- **scope_out**: MySQL/Postgres/remote databases; ORM-specific migrations; production database operations without an accessible local SQLite file; hidden writes when the user only asked to inspect
- **Preconditions**: the SQLite file path is known or can be located in the workspace; Python 3 is available; for writes, the target rows and intent are clear enough to avoid ambiguous changes
- **Postconditions**: the response includes the database path, exact SQL in a fenced `sql` block, results rendered as a markdown table when rows are returned, and an explicit note for dry-run vs committed writes

## Workflow

### Phase 0: Resolve the database and task

- Identify the SQLite file path before generating SQL.
- Classify the request into one of:
  - `inspect`: list tables, view schema, preview records
  - `query`: read data with `SELECT`
  - `change`: insert, update, delete, or DDL
- If the user describes intent in plain language, convert it into one concrete SQL statement at a time instead of generating a large script unless they explicitly asked for batch changes.

### Phase 1: Inspect first when schema is uncertain

Use the bundled helper script:

```bash
python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db tables
python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db schema --table users
python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db preview --table users --limit 20
```

Default inspection order:

1. List tables.
2. Inspect the relevant table schema.
3. Preview a few rows before writing SQL that changes data.

### Phase 2: Generate SQL from the user request

- Always show the SQL before execution in a fenced block:

```sql
SELECT id, email, created_at
FROM users
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 20;
```

- Prefer explicit column lists over `SELECT *` unless the user explicitly wants all columns or is doing a quick preview.
- Add `LIMIT` for exploration queries unless the user asked for a full export/count.
- For writes, generate a matching preview query first when practical so the affected rows are visible before commit.
- For ambiguous text requests, state the assumption that shaped the SQL.

### Phase 3: Execute with the helper

Read queries:

```bash
python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db query --sql "SELECT ..."
```

Writes default to dry-run unless `--commit` is provided:

```bash
python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db exec --sql "UPDATE users SET status = 'inactive' WHERE last_login_at < '2024-01-01'"
python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db exec --commit --sql "UPDATE users SET status = 'inactive' WHERE last_login_at < '2024-01-01'"
```

Rules:

- Use `query` only for read statements.
- Use `exec` only for data-changing statements.
- Do not commit destructive or broad writes until the user’s intent is explicit.
- Require explicit confirmation before `DELETE` without a narrow `WHERE`, `DROP`, `ALTER TABLE ... DROP`, or other clearly destructive changes.

### Phase 4: Response format

Use this shape for every non-trivial SQLite task:

1. `DB`: the SQLite path used
2. `SQL`: fenced `sql` block with the exact statement
3. `Result`: markdown table for rows, or a compact change summary for writes
4. `Notes`: assumptions, dry-run/commit status, and next useful shortcut if relevant

## Shortcuts

### Common helper commands

| Task | Command |
|------|---------|
| List tables | `python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db tables` |
| Show table schema | `python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db schema --table users` |
| Preview records | `python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db preview --table users --limit 20` |
| Run read query | `python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db query --sql "SELECT ..."` |
| Dry-run a change | `python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db exec --sql "UPDATE ..."` |
| Commit a change | `python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db exec --commit --sql "UPDATE ..."` |
| Show built-in SQL shortcuts | `python3 skills/lazy-sqlite-helper/scripts/sqlite_helper.py --db /path/to/app.db shortcuts` |

### SQLite SQL shortcuts

| Task | SQL |
|------|-----|
| List tables | `SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY type, name;` |
| Show create SQL | `SELECT sql FROM sqlite_master WHERE type IN ('table', 'view') AND name = 'users';` |
| Show columns | `PRAGMA table_info("users");` |
| Show foreign keys | `PRAGMA foreign_key_list("users");` |
| Show indexes | `PRAGMA index_list("users");` |
| Preview rows | `SELECT * FROM "users" LIMIT 20;` |
| Count rows | `SELECT COUNT(*) AS row_count FROM "users";` |

## Verification

### Hard gates

| Gate | Pass condition | On fail |
|------|----------------|---------|
| SQL shown first | Exact SQL appears before execution result | Stop and show the SQL |
| Correct execution mode | Read statements use `query`, writes use `exec` | Re-run with the correct command |
| Markdown result table | Returned rows are formatted as a markdown table | Reformat before answering |
| Safe write behavior | Writes are dry-run unless commit is explicit | Roll back and tell the user no commit happened |

### Soft gates

| Gate | Pass condition | On fail |
|------|----------------|---------|
| Schema-aware SQL | Table/column names were checked before complex SQL | Note the assumption or inspect schema first |
| Narrow write scope | `WHERE` clause or preview query makes affected rows clear | Warn the user and ask before commit |
| Query ergonomics | Exploration queries use explicit columns and `LIMIT` | Add them unless the user asked otherwise |

## Failure modes

| Symptom | Root cause | Fix |
|---------|------------|-----|
| Wrong column name in SQL | Schema was assumed instead of inspected | Run `schema` first |
| Huge markdown output | Query missed a `LIMIT` or export intent was unclear | Add `LIMIT` or ask whether a full dump is wanted |
| Accidental broad update | Write SQL was generated without a preview step | Show preview query and keep the write as dry-run |
| No rows returned | Filter does not match the data | Check preview rows or relax the predicate |
| User asked for text2sql only | Execution happened too early | Show SQL and wait unless execution was requested |

## Boundary examples

- **User**: "What tables are in this sqlite file?"  
  Run `tables`, then render the result as a markdown table.
- **User**: "Show the schema for `orders`."  
  Run `schema --table orders`, show the `CREATE TABLE` SQL and schema tables.
- **User**: "Find the latest 10 failed jobs."  
  Inspect schema if needed, generate `SELECT ... ORDER BY ... DESC LIMIT 10`, show SQL, then run `query`.
- **User**: "Set every row to inactive."  
  Treat this as destructive. Show the SQL, warn about broad impact, and do not commit without explicit confirmation.
