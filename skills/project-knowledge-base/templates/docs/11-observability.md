# 11. Observability

<!-- maintained-by: human+ai -->

> **Template note**: Explain how developers or operators can see what is happening, not just which tools exist.

## Philosophy

Summarize the observability goals for this project: what must be visible, how fast issues should be diagnosable, and what signals matter most.

## Logging

| Aspect | Approach |
|--------|----------|
| Library or framework | [tool] |
| Levels | [debug, info, warn, error] |
| Format | [JSON, text, structured fields] |
| Output location | [stdout, file path, external sink] |

## Metrics

| Metric | Type | Why it matters |
|--------|------|----------------|
| [Metric 1] | [counter, gauge, histogram] | [reason] |
| [Metric 2] | [counter, gauge, histogram] | [reason] |

## Tracing or Correlation

- **Trace or request identifier**: [how generated and propagated]
- **Cross-service visibility**: [how linked]
- **Diagnostic value**: [what problems this helps explain]

## Alerts and Health Signals

| Condition | Signal | Expected action |
|-----------|--------|-----------------|
| [Condition 1] | [alert, dialog, page, log] | [action] |
| [Condition 2] | [alert, dialog, page, log] | [action] |

## Diagnostic Tools

- [Tool 1 and what it is used for]
- [Tool 2 and what it is used for]
- [Tool 3 and what it is used for]

## Operational Checklist

- [ ] Key logs are easy to locate
- [ ] Critical metrics are named and described
- [ ] Health checks or equivalent diagnostics exist
- [ ] The runbook references the right signals first

## Related Documentation

- [Architecture](02-architecture.md)
- [Build](08-build.md)
- [Runbook](10-runbook.md)
- [Testing](09-testing.md)

---
<!-- PKB-metadata
last_updated: [YYYY-MM-DD]
commit: [git rev-parse --short HEAD]
updated_by: human+ai
confidentiality: L1
-->
