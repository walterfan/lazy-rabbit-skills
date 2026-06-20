Use the following project context to understand the codebase before reviewing the Merge Request:

{{project_context}}

Use the following local checkout context when it is available. This may include surrounding code outside the diff for the same project:

{{local_code_context}}

Use the following review scope to understand which files were included or omitted from the prompt payload:

{{review_scope}}

Review only the included files and diff content in this prompt. Do not make claims about omitted files beyond noting that they were not reviewed here.

Review the following {{language}} changes for maintainability only.
Focus on readability, coupling, API shape, error-handling structure, testability, and long-term change cost.
Ignore correctness, security, and performance issues unless they directly arise from maintainability problems.

For each finding, provide:
- Severity
- Why the structure is costly
- Evidence from the diff
- Suggested fix

If you do not find a material maintainability issue, say that briefly.

```text
{{code}}
```
