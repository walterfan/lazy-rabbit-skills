---
name: lazy-memgraph-helper
description: >-
  Query, change, set up, and diagnose Memgraph from natural-language requests.
  Use when the user mentions Memgraph, Cypher, graph SQL, Bolt, graph query,
  node labels, relationship types, properties, Memgraph Lab, mgconsole, Docker,
  or wants help inspecting or modifying Memgraph data. This skill must show the
  Cypher before execution, render query results as markdown tables, provide
  shortcuts for labels, relationships, counts, properties, and samples, and
  guide Memgraph environment setup and troubleshooting.
version: 0.1.0
author: walterfan@ustc.edu
tags:
  - memgraph
  - cypher
  - graph-database
  - text2sql
  - bolt
  - docker
  - markdown-table
  - diagnostics
category: data-tools
use_cases:
  - "set up Memgraph locally with Docker or the install script"
  - "generate Cypher from plain English and run it against Memgraph"
  - "show node labels, relationship types, counts, and properties"
  - "preview graph data before updating or deleting it"
  - "diagnose why Memgraph Lab or the Bolt endpoint is not reachable"
platforms:
  - codex
  - claude-code
  - cursor
visibility: public
---

# lazy-memgraph-helper

Turn user text into safe Memgraph work: set up the instance, inspect the graph, generate Cypher, then execute it with clear visibility into what happened.

## Contract

- **scope_in**: Memgraph setup on local machines or Docker; Bolt connectivity; Memgraph Lab reachability; natural-language-to-Cypher translation; schema-ish graph inspection through labels, relationship types, properties, counts, and samples; read/write Cypher against a running Memgraph instance
- **scope_out**: Neo4j-specific admin procedures that Memgraph does not support; hidden writes when the user only asked to inspect; remote production changes without a reachable Memgraph endpoint; full data-model design for unrelated graph engines
- **Preconditions**: for setup tasks, Docker or shell access is available; for query tasks, the Memgraph host and Bolt port are known or can be inferred; for writes, the target pattern is concrete enough to avoid ambiguous mutations
- **Postconditions**: the response includes the Memgraph endpoint, exact Cypher in a fenced `cypher` block, results rendered as markdown tables when rows are returned, and an explicit note for dry-run vs committed writes

## Workflow

### Phase 0: Classify the request

- Pick one primary mode:
  - `setup`: install or start Memgraph
  - `diagnose`: check why Memgraph or Lab is not reachable
  - `inspect`: discover labels, relationship types, counts, properties, and sample graph data
  - `query`: generate and run read-only Cypher
  - `change`: generate and run mutations such as `CREATE`, `MERGE`, `SET`, `DELETE`
  - `teach`: explain how Memgraph and Cypher work
- Treat the user’s “graph SQL” wording as Cypher terminology and say so once when helpful.

### Phase 1: Set up or diagnose first when the instance is uncertain

Use the bundled helper:

```bash
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py setup
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py diagnose --host 127.0.0.1 --port 7687 --lab-port 3000
```

Preferred setup paths:

1. Docker quick start for local experimentation.
2. The bundled [docker-compose.yml](docker-compose.yml) when the user wants a reusable local stack.
3. Memgraph install script for Linux/macOS.
4. Optional Memgraph Lab access on `http://127.0.0.1:3000`.

Diagnosis order:

1. Check whether `docker` is installed.
2. Check whether the Bolt port is reachable.
3. Check whether the Lab HTTP port is reachable.
4. Check whether the Python Bolt driver is installed if programmatic execution is needed.

### Phase 2: Inspect the graph before generating non-trivial Cypher

Use inspection shortcuts first:

```bash
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 labels
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 relationship-types
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 schema
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 node-properties --label User
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 relationship-properties --type RATED
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 sample-nodes --label User --limit 10
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 sample-relationships --type RATED --limit 10
```

Default inspection order:

1. Node labels and counts.
2. Relationship types and counts.
3. Property keys for the relevant label or relationship type.
4. Sample rows before generating write queries.

### Phase 3: Generate Cypher from the user request

- Always show the generated statement before execution:

```cypher
MATCH (u:User)-[r:RATED]->(m:Movie)
WHERE r.rating >= 4
RETURN u.id AS user_id, m.title AS movie_title, r.rating AS rating
ORDER BY rating DESC, movie_title
LIMIT 20;
```

- Prefer `MATCH ... RETURN` for exploration, `MERGE` over duplicate-prone `CREATE` when the user implies idempotent upserts, and `LIMIT` for browsing queries.
- For destructive or broad writes, show a preview query first, then keep the mutation as dry-run unless the user explicitly asks to commit it.
- State assumptions when turning vague text into Cypher, especially around labels, relationship types, direction, or property names.

### Phase 4: Execute safely

Read queries:

```bash
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 query --cypher "MATCH (n) RETURN n LIMIT 10"
```

Writes default to dry-run unless `--commit` is present:

```bash
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 exec --cypher "MATCH (u:User {id: 1}) SET u.status = 'inactive'"
python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 exec --commit --cypher "MATCH (u:User {id: 1}) SET u.status = 'inactive'"
```

Rules:

- Use `query` only for read-only Cypher.
- Use `exec` only for mutations.
- Do not commit broad deletes, label removals, or schema-level changes without explicit confirmation.
- If the Python driver is missing, use the helper’s setup guidance to install it or fall back to Memgraph Lab / `mgconsole`.

### Phase 5: Response format

Use this shape for every non-trivial task:

1. `Endpoint`: host, port, and Lab URL when relevant
2. `Cypher`: fenced `cypher` block with the exact statement
3. `Result`: markdown table for returned rows, or a compact mutation summary for writes
4. `Notes`: assumptions, dry-run/commit status, setup or diagnosis findings, and the next useful shortcut

## Shortcuts

### Helper commands

| Task | Command |
|------|---------|
| Show setup commands | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py setup` |
| Diagnose local environment | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py diagnose --host 127.0.0.1 --port 7687 --lab-port 3000` |
| Show built-in Cypher shortcuts | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py shortcuts` |
| List node labels | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 labels` |
| List relationship types | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 relationship-types` |
| Quick schema overview | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 schema` |
| Show node properties for a label | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 node-properties --label User` |
| Show relationship properties for a type | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 relationship-properties --type RATED` |
| Sample nodes | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 sample-nodes --label User --limit 10` |
| Sample relationships | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 sample-relationships --type RATED --limit 10` |
| Run read query | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 query --cypher "MATCH (n) RETURN n LIMIT 10"` |
| Dry-run mutation | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 exec --cypher "MATCH (n) DELETE n"` |
| Commit mutation | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py --host 127.0.0.1 exec --commit --cypher "MATCH (n) DELETE n"` |

### Cypher shortcuts

| Task | Cypher |
|------|--------|
| List node labels with counts | `MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS node_count ORDER BY node_count DESC, label;` |
| List relationship types with counts | `MATCH ()-[r]->() RETURN type(r) AS relationship_type, count(r) AS relationship_count ORDER BY relationship_count DESC, relationship_type;` |
| Count all nodes | `MATCH (n) RETURN count(n) AS node_count;` |
| Count all relationships | `MATCH ()-[r]->() RETURN count(r) AS relationship_count;` |
| Count nodes by label | `MATCH (n:User) RETURN count(n) AS node_count;` |
| Count relationships by type | `MATCH ()-[r:RATED]->() RETURN count(r) AS relationship_count;` |
| List properties for nodes of a label | `MATCH (n:User) UNWIND keys(n) AS property RETURN property, count(*) AS occurrences ORDER BY occurrences DESC, property;` |
| List properties for relationships of a type | `MATCH ()-[r:RATED]->() UNWIND keys(r) AS property RETURN property, count(*) AS occurrences ORDER BY occurrences DESC, property;` |
| Sample nodes | `MATCH (n:User) RETURN n LIMIT 10;` |
| Sample relationships | `MATCH ()-[r:RATED]->() RETURN r LIMIT 10;` |
| Explore a pattern | `MATCH (u:User)-[r:RATED]->(m:Movie) RETURN u, r, m LIMIT 20;` |

## Setup and diagnosis

### Official quick-start commands

| Task | Command |
|------|---------|
| Install on Linux/macOS | `curl -sSf "https://install.memgraph.com" \| sh` |
| Install on Windows PowerShell | `iwr https://windows.memgraph.com \| iex` |
| Start Docker platform image | `docker run -it -p 7687:7687 -p 3000:3000 -p 7444:7444 -v mg_lib:/var/lib/memgraph memgraph/memgraph-platform` |
| Start the bundled compose stack | `docker compose -f skills/lazy-memgraph-helper/docker-compose.yml up -d` |
| Open Memgraph Lab | `http://127.0.0.1:3000` |
| Install Python Bolt driver for the helper | `python3 -m pip install neo4j` |

### Quick diagnosis checklist

| Symptom | Check | Expected |
|---------|-------|----------|
| Bolt connection refused | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py diagnose --host 127.0.0.1 --port 7687` | Bolt port reachable |
| Lab not loading | `python3 skills/lazy-memgraph-helper/scripts/memgraph_helper.py diagnose --host 127.0.0.1 --lab-port 3000` | Lab HTTP port reachable |
| Helper cannot query Memgraph | `python3 -m pip show neo4j` | `neo4j` installed |
| Docker image not running | `docker ps` | Memgraph container present |

## Verification

### Hard gates

| Gate | Pass condition | On fail |
|------|----------------|---------|
| Cypher shown first | Exact Cypher appears before execution result | Stop and show the Cypher |
| Correct execution mode | Reads use `query`, writes use `exec` | Re-run with the correct command |
| Markdown result table | Returned rows are formatted as a markdown table | Reformat before answering |
| Safe write behavior | Mutations are dry-run unless `--commit` is explicit | Roll back and say no commit happened |

### Soft gates

| Gate | Pass condition | On fail |
|------|----------------|---------|
| Graph-aware Cypher | Labels, relationship types, and properties were inspected before complex queries | Note the assumption or inspect first |
| Query ergonomics | Exploration queries include a useful `LIMIT` and explicit aliases when needed | Add them unless the user asked otherwise |
| Setup evidence | Startup or diagnosis commands match the current environment facts | State the gap and what still needs checking |

## Failure modes

| Symptom | Root cause | Fix |
|---------|------------|-----|
| “SQL” query does not work | The graph engine expects Cypher, not relational SQL | Translate the request into Cypher |
| Wrong label or property name | The graph was not inspected first | Run `labels`, `relationship-types`, or property shortcuts |
| Broad mutation risk | The generated Cypher lacks a narrow match pattern | Add a preview query and keep the write as dry-run |
| Helper cannot connect | Memgraph is not running or Bolt is not reachable | Run `setup` or `diagnose` |
| Helper cannot execute | Python driver missing | Install `neo4j` or use Lab / `mgconsole` |

## Boundary examples

- **User**: "Teach me how to use Memgraph."  
  Explain the setup paths, Bolt/Lab ports, and Cypher basics with a few small examples.
- **User**: "Show me all node labels and relationship types."  
  Run `schema` or the separate label/type shortcuts and return markdown tables.
- **User**: "Find users who rated Comedy movies above 4."  
  Inspect labels and types if needed, generate Cypher, show it, then run `query`.
- **User**: "Delete all test data."  
  Treat this as destructive, show the preview and mutation Cypher, and do not commit without explicit confirmation.

## Additional resources

- AuthN/AuthZ overview: [references/authn-authz.md](references/authn-authz.md)
- Reusable local stack: [docker-compose.yml](docker-compose.yml)
