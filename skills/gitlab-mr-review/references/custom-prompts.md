# Custom Prompt Files

The skill is designed for one review aspect per round. If the built-in focuses are not enough, swap in a custom prompt file with:

```bash
python3 skills/gitlab-mr-review/scripts/review_mr.py "<mr-ref>" \
  --prompt-file /absolute/path/to/review-focus.md
```

It also supports built-in prompt selection:

```bash
python3 skills/gitlab-mr-review/scripts/review_mr.py "<mr-ref>" \
  --review-focus security
```

If the review target is a different local repository, add:

```bash
python3 /absolute/path/to/skills/gitlab-mr-review/scripts/review_mr.py "<mr-ref>" \
  --project-root /absolute/path/to/target-project
```

For local pre-MR review, use:

```bash
python3 /absolute/path/to/skills/gitlab-mr-review/scripts/review_mr.py \
  --local-diff \
  --project-root /absolute/path/to/target-project
```

Current built-in review focuses:

- `correctness`
- `security`
- `performance`
- `maintainability`

## Supported Placeholders

- `{{language}}`
  The dominant language in the MR, or `mixed (Go, Python, ...)`.
- `{{code}}`
  Combined selected MR summary and selected diff markdown.
- `{{bundle}}`
  Combined project context, review scope, selected MR summary, and selected diff markdown.
- `{{review_focus}}`
  The normalized built-in focus name such as `correctness` or `security`.
- `{{review_scope}}`
  A compact markdown block describing prompt budgeting, selected files, and omitted files.
- `{{project_context}}`
  A compact markdown block with project identity, languages, repo stack markers, and README-derived background.
- `{{local_code_context}}`
  Optional local checkout snippets from the same project, used to provide surrounding code outside the diff when the target MR matches the local repository.
- `{{project_name}}`
  The GitLab project path or identifier being reviewed.
- `{{project_languages}}`
  Language summary inferred from the MR and repository manifests.
- `{{project_frameworks}}`
  Repo stack markers inferred from common manifests.
- `{{project_stack}}`
  Repo-wide framework and middleware markers inferred from manifests.
- `{{project_background}}`
  Short README-derived project background for architectural context.
- `{{mr_title}}`
  Merge Request title.
- `{{mr_description}}`
  Merge Request description.
- `{{mr_summary}}`
  Table-style summary of changed files and line counts.
- `{{mr_diff}}`
  Per-file diff markdown.

## Minimal Example

````md
# Architecture Review

MR: {{mr_title}}

Focus only on system boundaries, public API changes, and backwards compatibility.
Ignore correctness, security, performance, and general cleanup unless they directly affect architecture.

Code:

```text
{{code}}
```
````

## Suggested Pattern

- Keep the markdown prompt focused on one review angle.
- State what to ignore so the model does not drift into other review categories.
- Create separate prompt files for architecture-only, migration-only, test-only, or API-only review.
