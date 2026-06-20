# 08. Build, Release, and Publish

<!-- maintained-by: human+ai -->

> **Template note**: Separate local build steps from CI/CD automation and from release/publish procedures.

## Scope

Describe what this page covers: local builds, CI pipelines, release packaging, and docs publishing.

## Local Build Paths

### Development

```bash
[install command]
[dev command]
```

### Production Build

```bash
[build command]
```

Expected outputs:

- `[output path 1]`
- `[output path 2]`

## CI/CD Pipelines

| Workflow | Trigger | Purpose | Key output |
|----------|---------|---------|------------|
| [workflow 1] | [trigger] | [purpose] | [artifact] |
| [workflow 2] | [trigger] | [purpose] | [artifact] |
| [workflow 3] | [trigger] | [purpose] | [artifact] |

## Release Process

1. [Update version fields]
2. [Run validation commands]
3. [Commit and push]
4. [Create or publish release artifact]
5. [Verify release outputs]

## Documentation Build and Publish

```bash
cd [doc root]
poetry install
make html
```

If bilingual docs exist, also document:

```bash
make gettext
make intl-update
```

## Common Failures

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| [Failure 1] | [Cause] | [Fix] |
| [Failure 2] | [Cause] | [Fix] |

## Related Documentation

- [Quick Start](01-quick-start.md)
- [Testing](09-testing.md)
- [Runbook](10-runbook.md)
- [Documentation Process](12-document.md)

---
<!-- PKB-metadata
last_updated: [YYYY-MM-DD]
commit: [git rev-parse --short HEAD]
updated_by: human+ai
confidentiality: L1
-->
