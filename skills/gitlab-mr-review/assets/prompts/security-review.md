Use the following project context to understand the codebase before reviewing the Merge Request:

{{project_context}}

Use the following local checkout context when it is available. This may include surrounding code outside the diff for the same project:

{{local_code_context}}

Use the following review scope to understand which files were included or omitted from the prompt payload:

{{review_scope}}

Review only the included files and diff content in this prompt. Do not make claims about omitted files beyond noting that they were not reviewed here.

Review the following {{language}} changes for security only.
Focus on trust boundaries, authorization, input handling, injection risks, secret handling, unsafe logging, insecure defaults, and exploitable data flows.
Ignore correctness, performance, and maintainability issues unless they directly create security risk.

For each finding, provide:
- Severity
- Attack or abuse path
- Evidence from the diff
- Suggested fix

If you do not find a material security issue, say that briefly.

```text
{{code}}
```
