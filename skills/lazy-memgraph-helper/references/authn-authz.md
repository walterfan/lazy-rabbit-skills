# Memgraph AuthN and AuthZ

This note summarizes Memgraph's authentication and authorization model from official Memgraph sources. Use it when the user asks how Memgraph security works, how to think about users and roles, or what features exist before planning local setup.

## Authentication

Memgraph supports native username/password authentication over Bolt.

- Native auth is part of Memgraph's security feature set.
- Drivers usually pass auth as a Bolt username/password tuple.
- Memgraph also describes support for centralized external auth systems such as PAM, LDAP, and SSO providers including Entra ID and Okta.
- A custom external auth module is also part of the enterprise-oriented security story.

From the June 19, 2024 official security post, Memgraph describes password handling in terms of password hashes rather than storing raw passwords, and mentions multiple hashing options:

- `bcrypt`
- `sha256`
- repeated `sha256`

That same post also says Memgraph can enforce password-strength rules with a regex-based policy.

## Authorization

Memgraph describes authorization as role-based plus graph-aware fine-grained controls.

### 1. Clause-based authorization

This is query-level authorization. Roles can be granted or denied access to Cypher clauses such as:

- `MATCH`
- `CREATE`
- `MERGE`
- other query clauses

This is the coarse-grained RBAC layer and is the right mental model for roles like:

- admin
- read-write
- read-only

### 2. Label-based authorization

This is fine-grained graph authorization for node labels and relationship edge types.

- Access rules can be scoped to labels.
- Access rules can also be scoped to edge types.
- This is the feature Memgraph positions for more granular graph partitioning or even multi-tenant-style isolation patterns.

The older Memgraph label-based access-control article illustrates privileges such as:

- `READ`
- `UPDATE`
- `CREATE_DELETE`
- `NOTHING`

and shows grant syntax such as `GRANT READ ON LABELS * TO user` and `GRANT UPDATE ON EDGE_TYPES :my_edge_type TO user`.

### 3. Property-based authorization

As of Memgraph's official June 19, 2024 security article, property-based authorization was described as "coming soon".

Inference:
Do not assume property-level authorization is generally available unless a newer official Memgraph doc confirms it for the exact version you are deploying.

## Practical model

The simplest way to reason about Memgraph security is:

1. Authentication answers: who is connecting?
2. Role-based authorization answers: what Cypher operations can they run?
3. Label and edge-type authorization answers: which parts of the graph can they see or mutate?

## What this means for local setup

For local developer setups, keep these concerns separate:

1. Bring up Memgraph first with Docker or the install script.
2. Decide whether the environment is throwaway local dev or shared.
3. If shared, define named users and roles instead of relying on a single unrestricted account.
4. Use clause-level permissions for coarse access.
5. Use label/edge-type controls when you need graph partitioning or more granular data boundaries.

## Sources

- Memgraph homepage: https://memgraph.com/
- Security features blog, published June 19, 2024: https://memgraph.com/blog/graph-database-security-features-explained
- Capabilities page: https://memgraph.com/capabilities
- Memgraph DB product page: https://memgraph.com/memgraphdb
- Label-based access-control blog: https://memgraph.com/blog/label-based-access-control-in-memgraph-securing-first-class-graph-citizens
