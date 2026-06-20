#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Memgraph helper for setup guidance, diagnostics, Cypher shortcuts, and Bolt execution."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import socket
from collections.abc import Iterable, Sequence


SETUP_COMMANDS = [
    ("Install on Linux/macOS", 'curl -sSf "https://install.memgraph.com" | sh'),
    ("Install on Windows PowerShell", "iwr https://windows.memgraph.com | iex"),
    (
        "Start Memgraph Platform with Docker",
        "docker run -it -p 7687:7687 -p 3000:3000 -p 7444:7444 -v mg_lib:/var/lib/memgraph memgraph/memgraph-platform",
    ),
    ("Open Memgraph Lab", "http://127.0.0.1:3000"),
    ("Install Python Bolt driver", "python3 -m pip install neo4j"),
]


SHORTCUTS = [
    (
        "List node labels with counts",
        "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS node_count ORDER BY node_count DESC, label;",
    ),
    (
        "List relationship types with counts",
        "MATCH ()-[r]->() RETURN type(r) AS relationship_type, count(r) AS relationship_count ORDER BY relationship_count DESC, relationship_type;",
    ),
    ("Count all nodes", "MATCH (n) RETURN count(n) AS node_count;"),
    ("Count all relationships", "MATCH ()-[r]->() RETURN count(r) AS relationship_count;"),
    ("Count nodes by label", "MATCH (n:User) RETURN count(n) AS node_count;"),
    ("Count relationships by type", "MATCH ()-[r:RATED]->() RETURN count(r) AS relationship_count;"),
    (
        "List properties for nodes of a label",
        "MATCH (n:User) UNWIND keys(n) AS property RETURN property, count(*) AS occurrences ORDER BY occurrences DESC, property;",
    ),
    (
        "List properties for relationships of a type",
        "MATCH ()-[r:RATED]->() UNWIND keys(r) AS property RETURN property, count(*) AS occurrences ORDER BY occurrences DESC, property;",
    ),
    ("Sample nodes", "MATCH (n:User) RETURN n LIMIT 10;"),
    ("Sample relationships", "MATCH ()-[r:RATED]->() RETURN r LIMIT 10;"),
    ("Explore a pattern", "MATCH (u:User)-[r:RATED]->(m:Movie) RETURN u, r, m LIMIT 20;"),
]


READ_STARTS = {
    "CALL",
    "EXPLAIN",
    "MATCH",
    "OPTIONAL",
    "PROFILE",
    "RETURN",
    "SHOW",
    "UNWIND",
    "WITH",
}
WRITE_TOKENS = {"CREATE", "DELETE", "DETACH", "DROP", "MERGE", "REMOVE", "SET"}


def add_connection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="127.0.0.1", help="Memgraph host")
    parser.add_argument("--port", type=int, default=7687, help="Memgraph Bolt port")
    parser.add_argument("--username", default="", help="Memgraph username, if auth is enabled")
    parser.add_argument("--password", default="", help="Memgraph password, if auth is enabled")
    parser.add_argument("--database", help="Optional database name")
    parser.add_argument("--lab-port", type=int, default=3000, help="Memgraph Lab HTTP port")
    parser.add_argument("--timeout", type=float, default=2.0, help="Socket timeout in seconds")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Memgraph helper for setup, diagnostics, and markdown-friendly Cypher execution."
    )
    add_connection_args(parser)

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("setup", help="Show setup commands for Memgraph")
    subparsers.add_parser("shortcuts", help="Show common Cypher shortcuts")
    add_connection_args(subparsers.add_parser("diagnose", help="Run simple local environment diagnostics"))
    add_connection_args(subparsers.add_parser("labels", help="List node labels with counts"))
    add_connection_args(subparsers.add_parser("relationship-types", help="List relationship types with counts"))
    add_connection_args(subparsers.add_parser("schema", help="Show labels and relationship types overview"))

    node_props = subparsers.add_parser("node-properties", help="List property keys for a node label")
    add_connection_args(node_props)
    node_props.add_argument("--label", required=True, help="Node label to inspect")

    rel_props = subparsers.add_parser("relationship-properties", help="List property keys for a relationship type")
    add_connection_args(rel_props)
    rel_props.add_argument("--type", required=True, dest="relationship_type", help="Relationship type to inspect")

    sample_nodes = subparsers.add_parser("sample-nodes", help="Preview nodes for a label")
    add_connection_args(sample_nodes)
    sample_nodes.add_argument("--label", help="Optional node label filter")
    sample_nodes.add_argument("--limit", type=int, default=10, help="Maximum rows to return")

    sample_rels = subparsers.add_parser("sample-relationships", help="Preview relationships for a type")
    add_connection_args(sample_rels)
    sample_rels.add_argument("--type", dest="relationship_type", help="Optional relationship type filter")
    sample_rels.add_argument("--limit", type=int, default=10, help="Maximum rows to return")

    query_parser = subparsers.add_parser("query", help="Run a read-only Cypher query")
    add_connection_args(query_parser)
    query_parser.add_argument("--cypher", "--sql", dest="cypher", required=True, help="Cypher statement to run")
    query_parser.add_argument("--max-rows", type=int, default=200, help="Maximum rows to render")

    exec_parser = subparsers.add_parser("exec", help="Run a write Cypher statement")
    add_connection_args(exec_parser)
    exec_parser.add_argument("--cypher", "--sql", dest="cypher", required=True, help="Cypher statement to run")
    exec_parser.add_argument(
        "--commit",
        action="store_true",
        help="Persist the mutation. Without this flag the transaction is rolled back.",
    )
    return parser.parse_args()


def tokenise_cypher(cypher: str) -> list[str]:
    cleaned = re.sub(r"/\*.*?\*/", " ", cypher, flags=re.S)
    cleaned = re.sub(r"//.*?$", " ", cleaned, flags=re.M)
    return re.findall(r"[A-Za-z_]+", cleaned.upper())


def classify_cypher(cypher: str) -> str:
    tokens = tokenise_cypher(cypher)
    if not tokens:
        return "empty"
    if any(token in WRITE_TOKENS for token in tokens):
        return "write"
    if tokens[0] in READ_STARTS:
        return "read"
    return "write"


def quote_identifier(identifier: str) -> str:
    safe = identifier.replace("`", "``")
    return f"`{safe}`"


def markdown_table(columns: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    rendered_rows = list(rows)
    if not rendered_rows:
        return "_No rows returned._"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(escape_cell(value) for value in row) + " |"
        for row in rendered_rows
    ]
    return "\n".join([header, separator, *body])


def escape_cell(value: object) -> str:
    if value is None:
        text = "NULL"
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def format_scalar(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, dict):
        items = ", ".join(
            f"{key}: {format_scalar(subvalue)}"
            for key, subvalue in sorted(value.items(), key=lambda item: item[0])
        )
        return "{%s}" % items
    if isinstance(value, (list, tuple, set)):
        items = ", ".join(format_scalar(item) for item in value)
        return "[%s]" % items
    return json.dumps(str(value), ensure_ascii=True)


def require_neo4j_driver():
    try:
        from neo4j import GraphDatabase
        from neo4j.graph import Node, Path, Relationship
    except ImportError as exc:
        raise SystemExit(
            "The Python package 'neo4j' is required for query/exec commands. "
            "Install it with: python3 -m pip install neo4j"
        ) from exc
    return GraphDatabase, Node, Relationship, Path


def format_value(value: object, node_cls: type, relationship_cls: type, path_cls: type) -> str:
    if isinstance(value, node_cls):
        labels = "".join(f":{label}" for label in sorted(value.labels))
        props = dict(value.items())
        if props:
            return f"({labels} {format_scalar(props)})"
        return f"({labels})" if labels else "()"
    if isinstance(value, relationship_cls):
        rel_type = value.type
        props = dict(value.items())
        if props:
            return f"[:{rel_type} {format_scalar(props)}]"
        return f"[:{rel_type}]"
    if isinstance(value, path_cls):
        parts: list[str] = []
        path_nodes = list(value.nodes)
        path_relationships = list(value.relationships)
        if not path_nodes:
            return "[]"
        parts.append(format_value(path_nodes[0], node_cls, relationship_cls, path_cls))
        for rel, node in zip(path_relationships, path_nodes[1:]):
            parts.append(format_value(rel, node_cls, relationship_cls, path_cls))
            parts.append(format_value(node, node_cls, relationship_cls, path_cls))
        return "".join(parts)
    return format_scalar(value)


def print_cypher(cypher: str) -> None:
    print("## Cypher")
    print("```cypher")
    print(cypher.strip())
    print("```")


def print_result(columns: Sequence[str], rows: Sequence[Sequence[object]], note: str | None = None) -> None:
    print("## Result")
    print(markdown_table(columns, rows))
    if note:
        print()
        print(note)


def make_driver(args: argparse.Namespace):
    GraphDatabase, node_cls, relationship_cls, path_cls = require_neo4j_driver()
    auth = None
    if args.username or args.password:
        auth = (args.username, args.password)
    driver = GraphDatabase.driver(f"bolt://{args.host}:{args.port}", auth=auth)
    return driver, node_cls, relationship_cls, path_cls


def run_read_query(args: argparse.Namespace, cypher: str, max_rows: int) -> None:
    if classify_cypher(cypher) != "read":
        raise SystemExit("The query command only accepts read-only Cypher. Use exec for mutations.")

    print_cypher(cypher)
    driver, node_cls, relationship_cls, path_cls = make_driver(args)
    try:
        session_kwargs = {"database": args.database} if args.database else {}
        with driver.session(**session_kwargs) as session:
            result = session.run(cypher)
            columns = list(result.keys())
            rows: list[tuple[object, ...]] = []
            truncated = False
            for index, record in enumerate(result):
                if index >= max_rows:
                    truncated = True
                    break
                rows.append(
                    tuple(
                        format_value(record[key], node_cls, relationship_cls, path_cls)
                        for key in columns
                    )
                )
        note = (
            f"_Rows shown: {len(rows)} (truncated to {max_rows})._"
            if truncated
            else f"_Rows shown: {len(rows)}._"
        )
        print_result(columns, rows, note=note)
    finally:
        driver.close()


def counters_to_rows(counters: object) -> list[tuple[object, object]]:
    items: list[tuple[object, object]] = []
    for key in (
        "nodes_created",
        "nodes_deleted",
        "relationships_created",
        "relationships_deleted",
        "properties_set",
        "labels_added",
        "labels_removed",
        "indexes_added",
        "indexes_removed",
        "constraints_added",
        "constraints_removed",
        "contains_updates",
    ):
        if hasattr(counters, key):
            items.append((key, getattr(counters, key)))
    return items


def run_write_query(args: argparse.Namespace, cypher: str, commit: bool) -> None:
    if classify_cypher(cypher) != "write":
        raise SystemExit("The exec command only accepts write Cypher. Use query for reads.")

    print_cypher(cypher)
    driver, _, _, _ = make_driver(args)
    try:
        session_kwargs = {"database": args.database} if args.database else {}
        with driver.session(**session_kwargs) as session:
            tx = session.begin_transaction()
            result = tx.run(cypher)
            summary = result.consume()
            rows = [("status", "committed" if commit else "dry-run"), *counters_to_rows(summary.counters)]
            if commit:
                tx.commit()
                note = "_Mutation committed to Memgraph._"
            else:
                tx.rollback()
                note = "_Mutation was rolled back because --commit was not provided._"
        print_result(["metric", "value"], rows, note=note)
    finally:
        driver.close()


def build_labels_query() -> str:
    return (
        "MATCH (n) "
        "UNWIND labels(n) AS label "
        "RETURN label, count(*) AS node_count "
        "ORDER BY node_count DESC, label;"
    )


def build_relationship_types_query() -> str:
    return (
        "MATCH ()-[r]->() "
        "RETURN type(r) AS relationship_type, count(r) AS relationship_count "
        "ORDER BY relationship_count DESC, relationship_type;"
    )


def build_node_properties_query(label: str) -> str:
    return (
        f"MATCH (n:{quote_identifier(label)}) "
        "UNWIND keys(n) AS property "
        "RETURN property, count(*) AS occurrences "
        "ORDER BY occurrences DESC, property;"
    )


def build_relationship_properties_query(relationship_type: str) -> str:
    return (
        f"MATCH ()-[r:{quote_identifier(relationship_type)}]->() "
        "UNWIND keys(r) AS property "
        "RETURN property, count(*) AS occurrences "
        "ORDER BY occurrences DESC, property;"
    )


def build_sample_nodes_query(label: str | None, limit: int) -> str:
    pattern = "(n)" if not label else f"(n:{quote_identifier(label)})"
    return f"MATCH {pattern} RETURN n LIMIT {limit};"


def build_sample_relationships_query(relationship_type: str | None, limit: int) -> str:
    rel = "r" if not relationship_type else f"r:{quote_identifier(relationship_type)}"
    return f"MATCH ()-[{rel}]->() RETURN r LIMIT {limit};"


def print_setup() -> None:
    print("## Result")
    print(markdown_table(["task", "command"], SETUP_COMMANDS))


def check_socket(host: str, port: int, timeout: float) -> tuple[bool, str]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True, "reachable"
    except PermissionError:
        return False, "connection blocked by local policy or sandbox"
    except OSError as exc:
        return False, str(exc)
    finally:
        sock.close()


def print_diagnose(args: argparse.Namespace) -> None:
    bolt_ok, bolt_detail = check_socket(args.host, args.port, args.timeout)
    lab_ok, lab_detail = check_socket(args.host, args.lab_port, args.timeout)
    driver_installed = bool(shutil.which("python3")) and module_exists("neo4j")
    rows = [
        ("docker", "found" if shutil.which("docker") else "missing", shutil.which("docker") or "not in PATH"),
        ("mgconsole", "found" if shutil.which("mgconsole") else "missing", shutil.which("mgconsole") or "not in PATH"),
        ("python neo4j driver", "found" if driver_installed else "missing", "python3 -m pip install neo4j"),
        (f"bolt {args.host}:{args.port}", "reachable" if bolt_ok else "unreachable", bolt_detail),
        (f"lab {args.host}:{args.lab_port}", "reachable" if lab_ok else "unreachable", lab_detail),
    ]
    print("## Result")
    print(markdown_table(["check", "status", "detail"], rows))
    print()
    print("## Notes")
    if not bolt_ok:
        print("- Start Memgraph or verify the published Bolt port.")
    if not lab_ok:
        print("- If you expect Memgraph Lab, verify port 3000 is published and open `http://127.0.0.1:3000`.")
    if not driver_installed:
        print("- Install the Python Bolt driver if you want this helper to execute Cypher directly.")
    if bolt_ok and lab_ok and driver_installed:
        print("- Local Memgraph connectivity looks healthy for the helper workflow.")


def module_exists(name: str) -> bool:
    try:
        __import__(name)
    except ImportError:
        return False
    return True


def run_schema(args: argparse.Namespace) -> None:
    print("# Labels")
    run_read_query(args, build_labels_query(), max_rows=500)
    print()
    print("# Relationship Types")
    run_read_query(args, build_relationship_types_query(), max_rows=500)


def main() -> None:
    args = parse_args()

    if args.command == "setup":
        print_setup()
        return
    if args.command == "shortcuts":
        print("## Result")
        print(markdown_table(["task", "cypher"], SHORTCUTS))
        return
    if args.command == "diagnose":
        print_diagnose(args)
        return

    if args.command == "labels":
        run_read_query(args, build_labels_query(), max_rows=500)
        return
    if args.command == "relationship-types":
        run_read_query(args, build_relationship_types_query(), max_rows=500)
        return
    if args.command == "schema":
        run_schema(args)
        return
    if args.command == "node-properties":
        run_read_query(args, build_node_properties_query(args.label), max_rows=500)
        return
    if args.command == "relationship-properties":
        run_read_query(args, build_relationship_properties_query(args.relationship_type), max_rows=500)
        return
    if args.command == "sample-nodes":
        run_read_query(args, build_sample_nodes_query(args.label, args.limit), max_rows=args.limit)
        return
    if args.command == "sample-relationships":
        run_read_query(args, build_sample_relationships_query(args.relationship_type, args.limit), max_rows=args.limit)
        return
    if args.command == "query":
        run_read_query(args, args.cypher, max_rows=args.max_rows)
        return
    if args.command == "exec":
        run_write_query(args, args.cypher, commit=args.commit)
        return

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
