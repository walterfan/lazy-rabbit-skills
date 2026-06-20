Use the following project context to understand the codebase before reviewing the Merge Request:

{{project_context}}

Use the following local checkout context when it is available. This may include surrounding code outside the diff for the same project:

{{local_code_context}}

Use the following review scope to understand which files were included or omitted from the prompt payload:

{{review_scope}}

Review only the included files and diff content in this prompt. Do not make claims about omitted files beyond noting that they were not reviewed here.

Review the following {{language}} changes for correctness only.
Focus on logic errors, invalid assumptions, missing validation, state transitions, boundary conditions, null or undefined handling, and behavior regressions.
Ignore security, performance, and maintainability issues unless they directly cause incorrect behavior.

Focus on finding potential bugs:
1. Logic errors
2. Edge cases not handled
3. Null pointer exceptions
4. Race conditions
5. Off-by-one errors
6. Memory leak
7. Thread or goroutine leak
8. Infinite loop among modules or libraries
9. Dead lock

For each finding, provide:
- Severity
- Why it can fail
- Evidence from the diff
- Suggested fix

If you do not find a material correctness issue, say that briefly.

```text
{{code}}
```
