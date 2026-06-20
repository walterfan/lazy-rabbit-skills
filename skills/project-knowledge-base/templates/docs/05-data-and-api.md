# 05. Data and API

<!-- maintained-by: human+ai -->

> **Template note**: Document only verified schemas, interfaces, commands, and events. Distinguish stable contracts from implementation details.

## Data Model Overview

| Entity or table | Purpose | Primary owner | Notes |
|-----------------|---------|---------------|-------|
| [Entity 1] | [purpose] | [module or service] | [notes] |
| [Entity 2] | [purpose] | [module or service] | [notes] |

## Storage and Persistence Rules

- **Primary storage**: [database, file, queue, or cache]
- **Schema or migration source**: [path or tool]
- **Consistency rule**: [transaction or synchronization notes]
- **Retention or cleanup rule**: [if applicable]

## External Interfaces

| Interface | Path or endpoint | Input | Output | Notes |
|-----------|------------------|-------|--------|-------|
| [HTTP / RPC / CLI / UI contract] | [path] | [shape] | [shape] | [notes] |
| [Event or webhook] | [topic or route] | [shape] | [shape] | [notes] |

## Internal Commands and Events

| Name | Trigger | Consumer or handler | Notes |
|------|---------|---------------------|-------|
| [Command or event 1] | [trigger] | [handler] | [notes] |
| [Command or event 2] | [trigger] | [handler] | [notes] |

## Validation and Compatibility

- **Validation rules**: [input or schema rules]
- **Backward compatibility expectations**: [API or event compatibility]
- **Versioning rules**: [if contracts evolve]

## Key Code References

- `[path-or-symbol-1]`
- `[path-or-symbol-2]`
- `[path-or-symbol-3]`

## Related Documentation

- [Architecture](02-architecture.md)
- [Workflows](06-workflows.md)
- [Testing](09-testing.md)

---
<!-- PKB-metadata
last_updated: [YYYY-MM-DD]
commit: [git rev-parse --short HEAD]
updated_by: human+ai
confidentiality: L1
-->
