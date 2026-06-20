# 07. Conventions

<!-- maintained-by: human+ai -->

> **Template note**: Capture the project-specific rules that keep changes consistent. Prefer verified rules from config files, linters, or team practice.

## Style and Tooling

| Area | Rule | Source of truth |
|------|------|-----------------|
| Formatting | [formatter rule] | [config file] |
| Linting | [linter rule] | [config file] |
| Type checking | [tool or rule] | [config file] |
| Commit or review norms | [rule] | [team process] |

## Naming and Layout

- **Files and directories**: [naming expectations]
- **Modules or packages**: [layout expectations]
- **Public vs private APIs**: [boundary expectations]

## Error Handling

- **Error classification**: [how errors are grouped]
- **User-facing errors**: [how surfaced]
- **Retries or fallbacks**: [when allowed]

## Logging and Diagnostics

- **Required fields**: [trace id, request id, user id rules]
- **Sensitive data policy**: [what must never be logged]
- **Debug workflow**: [preferred approach]

## Configuration and Secrets

- **Config sources**: [env, files, flags, secret stores]
- **Override order**: [precedence]
- **Secrets handling**: [how secrets are loaded and rotated]

## Testing and Review Expectations

- **Tests expected for code changes**: [unit, integration, smoke]
- **Docs expected for changes**: [when to update PKB]
- **Review focus**: [safety, compatibility, performance, etc.]

## Anti-Patterns

- [Anti-pattern 1]
- [Anti-pattern 2]

## Related Documentation

- [Repository Map](04-repo-map.md)
- [Build](08-build.md)
- [Testing](09-testing.md)
- [Documentation Process](12-document.md)

---
<!-- PKB-metadata
last_updated: [YYYY-MM-DD]
commit: [git rev-parse --short HEAD]
updated_by: human+ai
confidentiality: L1
-->
