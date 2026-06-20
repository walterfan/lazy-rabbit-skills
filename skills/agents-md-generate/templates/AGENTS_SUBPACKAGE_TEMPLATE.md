# AGENTS.md - {{PACKAGE_NAME}}

<!-- Nested AGENTS.md: package-specific overrides only. Target <60 lines. -->

Root guide: [`{{ROOT_AGENTS_RELATIVE_PATH}}`]({{ROOT_AGENTS_RELATIVE_PATH}})

{{PACKAGE_ONE_SENTENCE}}

## Package Map

- `{{PACKAGE_MAIN_PATH}}` - {{PACKAGE_MAIN_PURPOSE}}
- `{{PACKAGE_TEST_PATH}}` - {{PACKAGE_TEST_PURPOSE}}
- `{{PACKAGE_DOCS_PATH_OR_REMOVE}}` - {{PACKAGE_DOCS_PURPOSE_OR_REMOVE}}

## Commands

```bash
{{PACKAGE_TEST_COMMAND}}   # package-local confidence check
{{PACKAGE_BUILD_COMMAND}}  # package build / typecheck, if different from root
```

## Overrides

- Public surface: {{PACKAGE_PUBLIC_SURFACE}} - {{PACKAGE_PUBLIC_SURFACE_REASON}}
- Dependency boundary: {{PACKAGE_DEPENDENCIES}} - {{PACKAGE_DEPENDENCIES_REASON}}
- Do not edit without review: {{PACKAGE_DANGER_ZONES}} - {{PACKAGE_DANGER_REASON}}

Update this nested file only when package-local commands, boundaries, or
review rules change.

<!-- last_updated: {{DATE}} -->
