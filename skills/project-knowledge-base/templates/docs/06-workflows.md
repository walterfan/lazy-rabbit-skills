# 06. Workflows

<!-- maintained-by: human+ai -->

> **Template note**: Use one section per critical workflow. Prefer real code references and concrete failure branches over generic business prose.

## Workflow Index

1. [Workflow name 1](#workflow-1)
2. [Workflow name 2](#workflow-2)

---

## Workflow 1

### Trigger and Goal

- **Trigger**: [user action, scheduled task, event, or API call]
- **Goal**: [what successful completion means]

### Main Flow

```{mermaid}
sequenceDiagram
    participant Caller
    participant Entry
    participant Core
    participant Storage

    Caller->>Entry: [request or event]
    Entry->>Core: [validated input]
    Core->>Storage: [read or write]
    Storage-->>Core: [result]
    Core-->>Entry: [response]
    Entry-->>Caller: [outcome]
```

### Key Steps

1. [Step 1]
2. [Step 2]
3. [Step 3]

### Error and Edge Cases

| Case | Where handled | Expected outcome |
|------|---------------|------------------|
| [Case 1] | [module or symbol] | [result] |
| [Case 2] | [module or symbol] | [result] |

### Data and Contracts Involved

- [table, entity, event, API, or command]
- [table, entity, event, API, or command]

### Code References

- `[path-or-symbol-1]`
- `[path-or-symbol-2]`

---

## Workflow 2

Repeat the same structure for each additional critical workflow.

## Related Documentation

- [Architecture](02-architecture.md)
- [Data and API](05-data-and-api.md)
- [Testing](09-testing.md)
- [Runbook](10-runbook.md)

---
<!-- PKB-metadata
last_updated: [YYYY-MM-DD]
commit: [git rev-parse --short HEAD]
updated_by: human+ai
confidentiality: L1
-->
