#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Small SQLite helper for schema inspection, markdown-table output, and safe writes."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence


TABLES_SQL = """
SELECT name, type
FROM sqlite_master
WHERE type IN ('table', 'view')
  AND name NOT LIKE 'sqlite_%'
ORDER BY type, name;
""".strip()


SHORTCUTS = [
    (
        "List tables",
        "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') "
        "AND name NOT LIKE 'sqlite_%' ORDER BY type, name;",
    ),
    ("Show create SQL", "SELECT sql FROM sqlite_master WHERE type IN ('table', 'view') AND name = 'users';"),
    ("Show columns", 'PRAGMA table_info("users");'),
    ("Show foreign keys", 'PRAGMA foreign_key_list("users");'),
    ("Show indexes", 'PRAGMA index_list("users");'),
    ("Preview rows", 'SELECT * FROM "users" LIMIT 20;'),
    ("Count rows", 'SELECT COUNT(*) AS row_count FROM "users";'),
]


READ_ONLY_PREFIXES = {"SELECT", "PRAGMA", "EXPLAIN", "WITH"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect and query SQLite databases with markdown-friendly output."
    )
    parser.add_argument("--db", help="Path to the SQLite database file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("tables", help="List user tables and views")

    schema_parser = subparsers.add_parser("schema", help="Show schema details for a table or view")
    schema_parser.add_argument("--table", required=True, help="Table or view name")

    preview_parser = subparsers.add_parser("preview", help="Preview records from a table")
    preview_parser.add_argument("--table", required=True, help="Table or view name")
    preview_parser.add_argument("--limit", type=int, default=20, help="Maximum rows to show")

    query_parser = subparsers.add_parser("query", help="Run a read-only SQL query")
    query_parser.add_argument("--sql", required=True, help="Read-only SQL statement to run")
    query_parser.add_argument("--max-rows", type=int, default=200, help="Maximum rows to render")

    exec_parser = subparsers.add_parser("exec", help="Run a write statement")
    exec_parser.add_argument("--sql", required=True, help="Write SQL statement to run")
    exec_parser.add_argument(
        "--commit",
        action="store_true",
        help="Persist the change. Without this flag the statement is rolled back.",
    )

    subparsers.add_parser("shortcuts", help="Show common SQLite shortcut SQL")
    return parser.parse_args()


def connect_db(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.exists():
        raise SystemExit(f"Database file not found: {path}")
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def strip_sql_prefix(sql: str) -> str:
    text = sql.lstrip()
    while True:
        if text.startswith("--"):
            newline = text.find("\n")
            if newline == -1:
                return ""
            text = text[newline + 1 :].lstrip()
            continue
        if text.startswith("/*"):
            end = text.find("*/")
            if end == -1:
                return ""
            text = text[end + 2 :].lstrip()
            continue
        return text


def classify_sql(sql: str) -> str:
    stripped = strip_sql_prefix(sql)
    if not stripped:
        return "empty"
    keyword = stripped.split(None, 1)[0].upper()
    if keyword in READ_ONLY_PREFIXES:
        return "read"
    return "write"


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def escape_cell(value: object) -> str:
    if value is None:
        text = "NULL"
    elif isinstance(value, bytes):
        text = f"<{len(value)} bytes>"
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def markdown_table(columns: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    rows = list(rows)
    if not rows:
        return "_No rows returned._"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(escape_cell(value) for value in row) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def print_sql(sql: str) -> None:
    print("## SQL")
    print("```sql")
    print(sql.strip())
    print("```")


def print_result(columns: Sequence[str], rows: Sequence[Sequence[object]], note: str | None = None) -> None:
    print("## Result")
    print(markdown_table(columns, rows))
    if note:
        print()
        print(note)


def fetch_rows(conn: sqlite3.Connection, sql: str, max_rows: int = 200) -> tuple[list[str], list[tuple[object, ...]], bool]:
    cursor = conn.execute(sql)
    if cursor.description is None:
        raise SystemExit("Query did not return tabular rows. Use the exec command for writes.")
    columns = [column[0] for column in cursor.description]
    fetched = cursor.fetchmany(max_rows + 1)
    truncated = len(fetched) > max_rows
    rows = [tuple(row) for row in fetched[:max_rows]]
    return columns, rows, truncated


def run_tables(conn: sqlite3.Connection) -> None:
    print_sql(TABLES_SQL)
    columns, rows, _ = fetch_rows(conn, TABLES_SQL, max_rows=500)
    print_result(columns, rows)


def run_schema(conn: sqlite3.Connection, table: str) -> None:
    quoted = quote_identifier(table)
    escaped_name = table.replace("'", "''")
    ddl_sql = (
        "SELECT type, name, tbl_name, sql "
        "FROM sqlite_master "
        f"WHERE name = '{escaped_name}' "
        "ORDER BY type, name;"
    )
    columns_sql = f"PRAGMA table_info({quoted});"
    foreign_keys_sql = f"PRAGMA foreign_key_list({quoted});"
    indexes_sql = f"PRAGMA index_list({quoted});"

    print("## SQL")
    print("```sql")
    print(ddl_sql)
    print(columns_sql)
    print(foreign_keys_sql)
    print(indexes_sql)
    print("```")

    _, ddl_rows, _ = fetch_rows(conn, ddl_sql, max_rows=20)
    if ddl_rows:
        print("## Create SQL")
        create_sql = ddl_rows[0][3] or "-- no CREATE SQL recorded --"
        print("```sql")
        print(create_sql)
        print("```")
    else:
        print("## Create SQL")
        print("_Object not found in sqlite_master._")

    columns, rows, _ = fetch_rows(conn, columns_sql, max_rows=200)
    print_result(columns, rows)

    fk_columns, fk_rows, _ = fetch_rows(conn, foreign_keys_sql, max_rows=200)
    print()
    print("## Foreign Keys")
    print(markdown_table(fk_columns, fk_rows))

    index_columns, index_rows, _ = fetch_rows(conn, indexes_sql, max_rows=200)
    print()
    print("## Indexes")
    print(markdown_table(index_columns, index_rows))


def run_preview(conn: sqlite3.Connection, table: str, limit: int) -> None:
    sql = f"SELECT * FROM {quote_identifier(table)} LIMIT {limit};"
    print_sql(sql)
    columns, rows, _ = fetch_rows(conn, sql, max_rows=limit)
    print_result(columns, rows)


def run_query(conn: sqlite3.Connection, sql: str, max_rows: int) -> None:
    if classify_sql(sql) != "read":
        raise SystemExit("The query command only accepts read-only SQL. Use exec for writes.")
    print_sql(sql)
    columns, rows, truncated = fetch_rows(conn, sql, max_rows=max_rows)
    note = f"_Rows shown: {len(rows)} (truncated to {max_rows})._" if truncated else f"_Rows shown: {len(rows)}._"
    print_result(columns, rows, note=note)


def run_exec(conn: sqlite3.Connection, sql: str, commit: bool) -> None:
    if classify_sql(sql) != "write":
        raise SystemExit("The exec command only accepts write SQL. Use query for reads.")
    print_sql(sql)

    before = conn.total_changes
    cursor = conn.execute(sql)
    delta = conn.total_changes - before
    rowcount = cursor.rowcount

    if commit:
        conn.commit()
        status = "committed"
        note = "_Write committed to the database._"
    else:
        conn.rollback()
        status = "dry-run"
        note = "_Write was rolled back because --commit was not provided._"

    print_result(
        ["status", "rowcount", "total_changes"],
        [(status, rowcount, delta)],
        note=note,
    )


def run_shortcuts() -> None:
    print("## Result")
    print(markdown_table(["task", "sql"], SHORTCUTS))


def main() -> None:
    args = parse_args()
    if args.command == "shortcuts":
        run_shortcuts()
        return

    if not args.db:
        raise SystemExit("--db is required for this command.")

    conn = connect_db(args.db)
    try:
        if args.command == "tables":
            run_tables(conn)
        elif args.command == "schema":
            run_schema(conn, args.table)
        elif args.command == "preview":
            run_preview(conn, args.table, args.limit)
        elif args.command == "query":
            run_query(conn, args.sql, args.max_rows)
        elif args.command == "exec":
            run_exec(conn, args.sql, args.commit)
        else:
            raise SystemExit(f"Unsupported command: {args.command}")
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except sqlite3.Error as exc:
        raise SystemExit(f"SQLite error: {exc}") from exc
