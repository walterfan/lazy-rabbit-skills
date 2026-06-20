# Project Knowledge Base

<!-- maintained-by: human+ai -->

This documentation is the Project Knowledge Base for the repository. It is designed to help both humans and AI locate code, understand architecture, execute workflows, and verify changes.

## Overview

```{admonition} Purpose
:class: tip

This PKB should help readers:
- **Locate** code, configs, scripts, and entry points
- **Understand** architecture, stack choices, and workflows
- **Execute** setup, build, release, and debugging tasks
- **Verify** behavior with tests, observability, and documentation checks
```

## Table of Contents

```{toctree}
:maxdepth: 2
:caption: Getting Started

00-overview
01-quick-start
```

```{toctree}
:maxdepth: 2
:caption: Design & Structure

02-architecture
03-tech-stack
04-repo-map
05-data-and-api
06-workflows
```

```{toctree}
:maxdepth: 2
:caption: Development

07-conventions
08-build
09-testing
```

```{toctree}
:maxdepth: 2
:caption: Operations

10-runbook
11-observability
12-document
```

```{toctree}
:maxdepth: 1
:caption: Appendix

appendix-01-faq
appendix-02-glossary
diagrams-guide
ai-guide
adr/index
changes/index
```

## Quick Start

### For New Developers

1. Read [Project Overview](00-overview.md) to understand purpose, users, and scope.
2. Follow [Quick Start](01-quick-start.md) to get the project running locally.
3. Study [Repository Map](04-repo-map.md) to locate entry points and major directories.
4. Review [Runbook](10-runbook.md) and [Conventions](07-conventions.md) before making changes.

### For AI Assistants

Use a layered reading order:

1. **Round 1**: read `00-overview`, `02-architecture`, and `04-repo-map`
2. **Round 2**: read `05-data-and-api` and `06-workflows`
3. **Round 3**: read `09-testing`, `10-runbook`, `11-observability`, and `12-document`

See [How to Use This Documentation for AI](ai-guide.md) for the detailed workflow.

## Key Concepts

:::::{grid} 2
:gutter: 3

::::{grid-item-card} Navigation
:link: 04-repo-map
:link-type: doc

Find the project structure, startup files, and major module boundaries.
::::

::::{grid-item-card} Architecture
:link: 02-architecture
:link-type: doc

Learn how the system is decomposed and how the main pieces interact.
::::

::::{grid-item-card} Workflows
:link: 06-workflows
:link-type: doc

Explore critical request, event, and business flows with code references.
::::

::::{grid-item-card} Testing
:link: 09-testing
:link-type: doc

Review the test layers, critical regressions, and validation commands.
::::

:::::

## Documentation Maintenance

```{admonition} Living Documentation
:class: important

Keep the PKB fresh without wasting tokens:
- run rule-based freshness checks before LLM-heavy doc work
- apply mechanical Level 1 updates first
- batch Level 2 refreshes by PR, sprint, or milestone
- keep ADRs and product rationale human-led
```

## Contributing

See [Conventions](07-conventions.md) for coding standards and [Documentation Process](12-document.md) for PKB maintenance rules.

## Indices and tables

- {ref}`genindex`
- {ref}`search`

---

**Version**: {sub-ref}`release`
**Last Updated**: {sub-ref}`today`
<!-- PKB-metadata
last_updated: [YYYY-MM-DD]
commit: [git rev-parse --short HEAD]
updated_by: human+ai
confidentiality: L1
-->
