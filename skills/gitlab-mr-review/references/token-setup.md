# GitLab Token Setup

Use this reference when the user does not already have a GitLab personal access token.

If the user is reviewing local changes with `--local-diff`, they do not need a GitLab token.

## Recommended Setup

Store the token in an environment variable:

```bash
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
export GITLAB_URL="https://gitlab.example.com"
```

If your GitLab host uses a self-signed certificate in the user's environment and they explicitly approve disabling verification, they can also set:

```bash
export GITLAB_NO_SSL_VERIFY=1
```

If the user reviews MRs from one project repeatedly, they can also set:

```bash
export GITLAB_PROJECT="group/subgroup/project"
```

If `GITLAB_PROJECT` is not set and the user runs the skill inside a git checkout, the script will also try:

```bash
git remote -v
```

Then it parses the `origin` remote URL. For example, `git@gitlab.example.com:group/project.git` becomes `group/project`.

If the user is reviewing a different repository, pass its path explicitly:

```bash
python3 /absolute/path/to/skills/gitlab-mr-review/scripts/review_mr.py 123 \
  --project-root /absolute/path/to/target-project
```

For pre-MR local review:

```bash
python3 /absolute/path/to/skills/gitlab-mr-review/scripts/review_mr.py \
  --local-diff \
  --project-root /absolute/path/to/target-project
```

## How to Create a GitLab Token

1. Sign in to GitLab in the browser.
2. Open the avatar menu in the top-right corner.
3. Go to `Preferences` or `Edit profile`.
4. Open `Access Tokens`.
   On some GitLab versions this appears under `User Settings` > `Access Tokens`.
5. Create a personal access token.
6. Give it a clear name such as `mr-review-skill`.
7. Set an expiration date that fits the user's security policy.
8. Grant the minimum scopes needed.
   In most cases `api` is the simplest choice because the MR diff endpoints live behind the API.
   If the user wants stricter permissions and their GitLab instance supports it, use the smallest read-oriented scope that still works for merge request and repository APIs.
9. Click `Create personal access token`.
10. Copy the token immediately.
    GitLab usually shows it only once.

## Verification

The bundled Python module includes a connection check:

```bash
python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path("skills/gitlab-mr-review/scripts").resolve()))
from gitlab_api import test_gitlab_connection

profile = test_gitlab_connection("https://gitlab.example.com", "<token>")
print(profile.username, profile.name)
PY
```

If SSL verification fails because of a trusted self-signed certificate and the user has approved the risk, retry with:

```bash
python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path("skills/gitlab-mr-review/scripts").resolve()))
from gitlab_api import test_gitlab_connection

profile = test_gitlab_connection("https://gitlab.example.com", "<token>", no_ssl_verify=True)
print(profile.username, profile.name)
PY
```

## Security Guidance

- Do not hardcode tokens in source files.
- Do not paste tokens into shared prompts or screenshots.
- Prefer short-lived tokens when practical.
- If a token was exposed, revoke it in GitLab and create a new one.
- Disable SSL verification only when the user explicitly approves it and the team trusts the self-signed certificate path.
