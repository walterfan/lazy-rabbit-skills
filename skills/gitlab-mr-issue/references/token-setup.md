# GitLab Token Setup

Use a GitLab personal access token that can read merge requests and create
issues in the target project.

Recommended scopes:

- `read_api` for fetching MR metadata and discussions.
- `api` when creating issues through the GitLab API.

Set the token in the shell before running the skill script:

```bash
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
```

Optional environment variables:

```bash
export GITLAB_URL="https://gitlab.example.com"
export GITLAB_PROJECT="namespace/project"
```

Do not paste tokens into chat output or commit them to the repository.
