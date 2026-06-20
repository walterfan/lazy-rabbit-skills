# 03. Tech Stack

<!-- maintained-by: human+ai -->

> **Template note**: Use real versions and real package names from manifests or lockfiles. Explain why each major technology exists in this repo.

## Purpose

Summarize the main technologies used in the project and how they fit together at runtime.

## System View

```{mermaid}
flowchart TD
    user["User or caller"] --> interface["UI / API / CLI layer"]
    interface --> runtime["Application runtime"]
    runtime --> storage["Primary storage"]
    runtime --> external["External dependencies"]
```

## Stack Summary

| Layer | Main technology | Why it exists in this repo |
|-------|-----------------|----------------------------|
| Interface | [framework or SDK] | [reason] |
| Runtime | [language or framework] | [reason] |
| Storage | [database or persistence] | [reason] |
| Build and packaging | [toolchain] | [reason] |
| Testing | [frameworks] | [reason] |

## Main Languages and Frameworks

- **Primary language**: [name and version]
- **Secondary languages**: [name and version]
- **Primary framework**: [name and role]
- **Build tool**: [name and role]

## Key Dependencies

| Package or crate | Area | Why it matters |
|------------------|------|----------------|
| [dependency 1] | [layer] | [reason] |
| [dependency 2] | [layer] | [reason] |
| [dependency 3] | [layer] | [reason] |

## Runtime Interaction Model

Describe how the major layers interact. For example:

1. [UI or caller] sends input
2. [runtime or service] validates and processes it
3. [storage or external system] persists or enriches it
4. [result path] returns the outcome

## Build and Packaging Notes

- **Local development**: [dev command or tool]
- **Production build**: [build command or tool]
- **Release packaging**: [bundler, CI, or release action]

## Common Misconceptions

| Misconception | Reality in this repo |
|---------------|----------------------|
| [Misconception 1] | [Correction] |
| [Misconception 2] | [Correction] |

## Related Documentation

- [Architecture](02-architecture.md)
- [Repository Map](04-repo-map.md)
- [Build](08-build.md)

---
<!-- PKB-metadata
last_updated: [YYYY-MM-DD]
commit: [git rev-parse --short HEAD]
updated_by: human+ai
confidentiality: L1
-->
