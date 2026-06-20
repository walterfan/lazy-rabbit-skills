# 00. Project Overview

<!-- maintained-by: human+ai -->

> **Template note**: Replace placeholders with verified project facts. Remove sections that do not apply rather than filling them with guesses.

## Purpose

Describe what the project does, who it serves, and why it exists.

## Scope Boundaries

| In scope | Out of scope |
|----------|--------------|
| [Core capability 1] | [Explicit non-goal 1] |
| [Core capability 2] | [Explicit non-goal 2] |
| [Core capability 3] | [Explicit non-goal 3] |

## Key Users and Use Cases

- **[User role 1]**: [primary goal]
- **[User role 2]**: [primary goal]
- **[User role 3]**: [primary goal]

## System Snapshot

- **Deployment model**: [monolith / microservices / desktop app / CLI / library / mixed]
- **Core runtime shape**: [frontend + backend, worker fleet, local-only app, etc.]
- **Primary data path**: [request -> service -> storage summary]
- **Top risk or constraint**: [latency, consistency, offline support, compliance, etc.]

## Quality Targets

| Area | Target | Notes |
|------|--------|-------|
| Performance | [p95 latency / throughput target] | [Where it matters most] |
| Availability | [uptime or recovery target] | [RTO / RPO if relevant] |
| Correctness | [data or workflow guarantee] | [Consistency or validation expectation] |
| Security | [auth / secret / compliance expectation] | [Special constraints] |

## Key Project Facts

- **Code roots**: [for example: `src/`, `server/`, `cmd/`, `pkg/`]
- **Primary interfaces**: [HTTP API, message queue, CLI, local UI, SDK]
- **Source of truth docs**: [where design or product intent is documented]

## Related Documentation

- [Quick Start](01-quick-start.md)
- [Architecture](02-architecture.md)
- [Tech Stack](03-tech-stack.md)
- [Repository Map](04-repo-map.md)
- [Runbook](10-runbook.md)

---
<!-- PKB-metadata
last_updated: [YYYY-MM-DD]
commit: [git rev-parse --short HEAD]
updated_by: human+ai
confidentiality: L1
-->
