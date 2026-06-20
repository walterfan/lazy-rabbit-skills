# 09. Testing Strategy

<!-- maintained-by: human+ai -->

> **Template note**: This page should describe how to validate the project in practice, not just list test tools.

## Test Layers

| Layer | Primary checks | Notes |
|-------|----------------|------|
| [Layer 1] | `[command]` | [what it validates] |
| [Layer 2] | `[command]` | [what it validates] |
| [Layer 3] | [manual or automated check] | [what it validates] |

## Core Regression Areas

- [Critical area 1]
- [Critical area 2]
- [Critical area 3]

## Test Data and Environments

- **Fixtures or seeds**: [where they live]
- **State isolation**: [how tests avoid leaking state]
- **External dependency strategy**: [mock, fake, sandbox, or real]

## Validation Commands

```bash
[unit test command]
[integration test command]
[type or lint validation command]
```

## Manual Smoke Checks

1. [Smoke check 1]
2. [Smoke check 2]
3. [Smoke check 3]

## Documentation Verification

If the PKB is published docs, include the verification steps here:

```bash
cd [doc root]
make html
```

## Regression Additions

When a bug is fixed, add a regression scenario here covering:

- the original failure
- the expected behavior after the fix
- the smallest useful automated or manual check

## Related Documentation

- [Workflows](06-workflows.md)
- [Runbook](10-runbook.md)
- [Observability](11-observability.md)

---
<!-- PKB-metadata
last_updated: [YYYY-MM-DD]
commit: [git rev-parse --short HEAD]
updated_by: human+ai
confidentiality: L1
-->
