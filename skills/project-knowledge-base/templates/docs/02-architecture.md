# 02. Architecture

<!-- maintained-by: human+ai -->

> **Template note**: Follow the C4 order: Context -> Container -> Component -> Code. Use diagrams only where they improve understanding.

## Context

Summarize the system boundary, key actors, and external systems.

```{mermaid}
flowchart TD
    user["Primary user or caller"] --> system["System under documentation"]
    system --> external["External system or dependency"]
```

## Container View

| Container | Responsibility | Technology | Depends on |
|-----------|----------------|------------|------------|
| [Container 1] | [What it owns] | [Runtime/framework] | [Main dependencies] |
| [Container 2] | [What it owns] | [Runtime/framework] | [Main dependencies] |
| [Container 3] | [What it owns] | [Runtime/framework] | [Main dependencies] |

## Component View

For each critical container, describe the major internal components and their boundaries.

### [Container or module name]

- **Responsibilities**: [What this part owns]
- **Key entry points**: [main files, handlers, commands, routes]
- **Important dependencies**: [storage, service, queue, external API]
- **Failure modes**: [what tends to break here]

## Code-Level View

Document only the code structures that matter for high-change or business-critical areas.

| Area | Important files or symbols | Why it matters |
|------|-----------------------------|----------------|
| [Critical path 1] | [file or symbol list] | [Reason] |
| [Critical path 2] | [file or symbol list] | [Reason] |

## Key Runtime Flows

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
    Core-->>Entry: [response or event]
    Entry-->>Caller: [output]
```

Describe:

- main success path
- validation boundaries
- transaction or consistency boundaries
- retry, idempotency, or compensation behavior

## Cross-Cutting Concerns

- **Authentication and authorization**: [where enforced]
- **Error handling**: [how errors are classified and surfaced]
- **Logging and tracing**: [correlation and debug strategy]
- **Caching**: [where used and invalidated]
- **Configuration and secrets**: [how loaded]

## Deployment and Scaling Notes

- **Environments**: [dev / staging / prod or desktop-only]
- **Scaling model**: [horizontal, vertical, local-only, queue workers, etc.]
- **Recovery considerations**: [backup, failover, rebuild, local reset]

## Related Documentation

- [Tech Stack](03-tech-stack.md)
- [Repository Map](04-repo-map.md)
- [Data and API](05-data-and-api.md)
- [Workflows](06-workflows.md)
- [ADRs](adr/index.md)

---
<!-- PKB-metadata
last_updated: [YYYY-MM-DD]
commit: [git rev-parse --short HEAD]
updated_by: human+ai
confidentiality: L1
-->
