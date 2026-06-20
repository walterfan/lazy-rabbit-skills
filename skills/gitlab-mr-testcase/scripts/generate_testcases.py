#!/usr/bin/env python3
"""Render a test-case generation prompt from a GitLab MR (or local diff), a design spec, and an optional Jira issue.

MR fetching, diff budgeting, and project-context collection are provided by helpers
vendored under ``../lib/`` (originally from the ``gitlab-mr-review`` skill — see
``../lib/SOURCES.md``). On top of those this script adds:

- One or more design spec sources (`--spec PATH_OR_URL`, repeatable). Local files are
  read verbatim. URLs are best-effort fetched; auth-protected pages fall back to a
  reference link.
- Optional Jira-issue-driven spec discovery (`--jira-issue KEY_OR_URL`). When the
  user provides a Jira issue and skips `--spec`, the script fetches the issue via
  the Atlassian REST API (using `JIRA_API_TOKEN` + `JIRA_USER_EMAIL`), embeds the
  issue description as a spec source, and tries to fetch any design-spec-looking
  URLs found in the description as additional spec sources. The Jira reference is
  also embedded in the prompt for traceability either way.
- A `--test-focus` selector that picks one bundled test-generation prompt template
  (`integration` or `acceptance`).
- Automatic output to `./tests/<name>.md`, `./test/<name>.md`, or `./<name>.md` so
  the generated content is always persisted as a reviewable artifact. `--output-file`
  overrides the path; `--stdout` restores the legacy stdout behavior.

The intent is single-focus, evidence-bounded, and tied to a quality gate: when all
generated cases pass, the reviewer can skip line-by-line review of an AI-written MR.
Spec is therefore required — without it the gate has no anchor.
"""

from __future__ import annotations

import argparse
import base64
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
VENDORED_LIB = SKILL_DIR / "lib"

if not VENDORED_LIB.is_dir():
    print(
        "Vendored helpers not found at {path}. The 'lib/' directory should ship "
        "with this skill; re-install it.".format(path=VENDORED_LIB),
        file=sys.stderr,
    )
    raise SystemExit(2)

sys.path.insert(0, str(VENDORED_LIB))

from gitlab_api import GitLabAPIError  # noqa: E402
from review_mr import (  # noqa: E402
    DEFAULT_MAX_CHANGED_LINES,
    DEFAULT_MAX_DIFF_CHARS,
    DEFAULT_MAX_FILES,
    build_local_sections,
    build_sections,
    load_prompt_template,
    render_template,
)


PROMPTS_DIR = SKILL_DIR / "assets" / "prompts"
BUILTIN_PROMPTS = {
    "integration": PROMPTS_DIR / "integration-tests.md",
    "acceptance": PROMPTS_DIR / "acceptance-tests.md",
}

TEST_FOCUS_ALIASES = {
    "default": "integration",
    "pytest": "integration",
    "integration-test": "integration",
    "integration_tests": "integration",
    "acceptance-test": "acceptance",
    "acceptance_tests": "acceptance",
    "atc": "acceptance",
    "bdd": "acceptance",
}

MAX_SPEC_BYTES_PER_FILE = 60_000
MAX_TOTAL_SPEC_BYTES = 120_000
SPEC_FETCH_TIMEOUT_SECONDS = 15
JIRA_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")
DEFAULT_JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://your-org.atlassian.net")

# Hosts that, when seen as a URL inside a Jira description, are treated as likely
# tech-design-spec links worth attempting to fetch. Conservative on purpose: random
# blog links should not get pulled in as spec sources.
# Override with the SPEC_URL_HOST_HINTS env var (comma-separated) for your own
# internal documentation hosts.
SPEC_URL_HOST_HINTS = tuple(
    h.strip()
    for h in os.getenv(
        "SPEC_URL_HOST_HINTS",
        "atlassian.net/wiki,confluence",
    ).split(",")
    if h.strip()
)

OUTPUT_DIR_PREFERENCE = ("tests", "test")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a test-case prompt from a GitLab MR (or local diff) plus a design spec. "
            "If --jira-issue is provided without --spec, the spec is auto-discovered from "
            "the Jira issue description. The rendered prompt is written to a markdown file "
            "under ./tests/, ./test/, or the current directory."
        ),
    )
    parser.add_argument(
        "mr_reference",
        nargs="?",
        help="Merge Request URL, namespace/project!iid, or plain IID when project context is available.",
    )
    parser.add_argument(
        "--local-diff",
        action="store_true",
        help="Use local tracked changes from `git diff HEAD` instead of fetching a remote MR.",
    )
    parser.add_argument(
        "--spec",
        action="append",
        default=[],
        metavar="PATH_OR_URL",
        help=(
            "Design spec source. Local path or http(s) URL. Required unless --jira-issue is "
            "provided and Jira auth is configured. Repeat to pass multiple specs. Local files "
            "are read verbatim. URLs are best-effort fetched; auth-protected pages fall back "
            "to a reference link."
        ),
    )
    parser.add_argument(
        "--spec-file",
        action="append",
        default=[],
        metavar="PATH",
        help="Backward-compat alias for --spec, local paths only.",
    )
    parser.add_argument(
        "--jira-issue",
        default=None,
        metavar="KEY_OR_URL",
        help=(
            "Jira issue reference (e.g. PROJ-1234 or a Jira /browse/ URL). Always embedded "
            "in the prompt for traceability. When --spec is not given and JIRA_API_TOKEN + "
            "JIRA_USER_EMAIL are set in the environment, the script fetches the issue and "
            "uses its description (plus any design-spec URLs found inside it) as the spec."
        ),
    )
    parser.add_argument(
        "--jira-base-url",
        default=os.getenv("JIRA_BASE_URL") or DEFAULT_JIRA_BASE_URL,
        help="Atlassian Cloud base URL for Jira API. Default: %(default)s.",
    )
    parser.add_argument(
        "--test-focus",
        default=os.getenv("MR_TESTCASE_FOCUS") or "integration",
        help=(
            "One test type per round. Built-in: integration (default), acceptance. "
            "Aliases: pytest, atc, bdd. Ignored when --prompt-file is provided."
        ),
    )
    parser.add_argument(
        "--prompt-file",
        default=None,
        help="Custom test-case prompt template. Overrides --test-focus when provided.",
    )
    parser.add_argument(
        "--gitlab-url",
        default=os.getenv("GITLAB_URL") or os.getenv("GITLAB_BASE_URL") or "https://gitlab.example.com",
        help="GitLab base URL. Ignored when a full MR URL is provided.",
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GITLAB_PROJECT") or os.getenv("GITLAB_PROJECT_ID"),
        help="Project path or ID for plain MR IIDs.",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GITLAB_TOKEN") or os.getenv("GITLAB_PRIVATE_TOKEN"),
        help="GitLab private token. Prefer GITLAB_TOKEN in the environment.",
    )
    parser.add_argument(
        "--project-root",
        default=os.getenv("MR_REVIEW_PROJECT_ROOT") or os.getcwd(),
        help="Project root used to collect repository context (language, frameworks, README).",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=int(os.getenv("MR_TESTCASE_MAX_FILES") or os.getenv("MR_REVIEW_MAX_FILES") or DEFAULT_MAX_FILES),
        help="Maximum number of changed files to include in the prompt payload.",
    )
    parser.add_argument(
        "--max-changed-lines",
        type=int,
        default=int(
            os.getenv("MR_TESTCASE_MAX_CHANGED_LINES")
            or os.getenv("MR_REVIEW_MAX_CHANGED_LINES")
            or DEFAULT_MAX_CHANGED_LINES
        ),
        help="Maximum changed-line budget across selected files.",
    )
    parser.add_argument(
        "--max-diff-chars",
        type=int,
        default=int(
            os.getenv("MR_TESTCASE_MAX_DIFF_CHARS")
            or os.getenv("MR_REVIEW_MAX_DIFF_CHARS")
            or DEFAULT_MAX_DIFF_CHARS
        ),
        help="Maximum total diff characters included in the prompt payload.",
    )
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="Include files marked as generated by GitLab.",
    )
    parser.add_argument(
        "--skip-project-match-check",
        action="store_true",
        help="Skip local checkout versus GitLab project validation.",
    )
    parser.add_argument(
        "--language",
        default="auto",
        help="Override detected language for prompt header (default: auto).",
    )
    parser.add_argument(
        "--format",
        choices=("prompt", "bundle", "summary", "diff", "spec"),
        default="prompt",
        help=(
            "Output format. 'prompt' renders the test-case template; "
            "'bundle' / 'summary' / 'diff' print raw MR sections; "
            "'spec' prints just the collected spec content."
        ),
    )
    parser.add_argument(
        "--output-file",
        help="Write result to this exact path. Overrides the auto-output directory.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Directory to write the auto-named output file into. Defaults to "
            "./tests/ if it exists, else ./test/, else the current directory."
        ),
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the result to stdout instead of writing a file.",
    )
    return parser.parse_args()


def normalize_test_focus(test_focus: str) -> str:
    normalized = test_focus.strip().lower()
    return TEST_FOCUS_ALIASES.get(normalized, normalized)


def resolve_prompt_path(test_focus: str, explicit_prompt_file: Optional[str]) -> Path:
    if explicit_prompt_file:
        path = Path(explicit_prompt_file).expanduser()
        if not path.is_file():
            raise ValueError(
                "custom prompt file does not exist: {path}".format(path=path)
            )
        return path
    normalized = normalize_test_focus(test_focus)
    prompt_path = BUILTIN_PROMPTS.get(normalized)
    if not prompt_path:
        available = ", ".join(sorted(BUILTIN_PROMPTS))
        raise ValueError(
            "unsupported test focus '{focus}'. Supported built-in focuses: {available}".format(
                focus=test_focus, available=available,
            )
        )
    if not prompt_path.is_file():
        raise ValueError(
            "bundled prompt template is missing: {path}".format(path=prompt_path)
        )
    return prompt_path


def _looks_like_url(raw: str) -> bool:
    parsed = urlparse.urlparse(raw)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _looks_like_text(content_type: str, body: str) -> bool:
    ct = (content_type or "").lower()
    if any(marker in ct for marker in ("text/markdown", "text/plain", "text/x-")):
        return True
    if "application/json" in ct:
        return True
    if "text/html" in ct:
        return False
    stripped = body.lstrip().lower()
    if stripped.startswith(("<!doctype html", "<html", "<head", "<body")):
        return False
    return True


def _fetch_spec_url(url: str) -> Tuple[str, Optional[str]]:
    """Best-effort fetch of a spec URL.

    Returns ``(content, error_message)``. When ``content`` is empty, ``error_message``
    explains why so the caller can fall back to a reference-only embed.
    """
    try:
        req = urlrequest.Request(
            url,
            headers={
                "User-Agent": "gitlab-mr-testcase/0.3 (+spec-fetch)",
                "Accept": "text/markdown, text/plain, application/json;q=0.8, */*;q=0.5",
            },
        )
        with urlrequest.urlopen(req, timeout=SPEC_FETCH_TIMEOUT_SECONDS) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read(MAX_SPEC_BYTES_PER_FILE + 1024)
            body = raw.decode("utf-8", errors="replace")
    except urlerror.HTTPError as exc:
        return "", "HTTP {code} from {url}".format(code=exc.code, url=url)
    except urlerror.URLError as exc:
        return "", "URL error from {url}: {reason}".format(url=url, reason=exc.reason)
    except (TimeoutError, OSError) as exc:
        return "", "fetch failed for {url}: {error}".format(url=url, error=exc)

    if not body.strip():
        return "", "empty response body from {url}".format(url=url)
    if not _looks_like_text(content_type, body):
        return "", (
            "response from {url} looks like HTML or binary "
            "(Content-Type: {ct}); auto-fetch not supported for auth-protected pages"
        ).format(url=url, ct=content_type or "unknown")
    return body, None


def _looks_like_spec_url(url: str) -> bool:
    lowered = url.lower()
    return any(hint in lowered for hint in SPEC_URL_HOST_HINTS)


def _extract_urls(text: str) -> List[str]:
    pattern = re.compile(r"https?://[^\s\)\]\}\"'<>,]+")
    seen: Dict[str, None] = {}
    for match in pattern.findall(text or ""):
        cleaned = match.rstrip(".,;:")
        if cleaned not in seen:
            seen[cleaned] = None
    return list(seen.keys())


def _adf_to_text(node: Any) -> str:
    """Best-effort Atlassian Document Format → plain text conversion.

    Atlassian Cloud's REST API can return ``description`` as ADF JSON. We don't need
    perfect fidelity, just enough text so the model can read requirements and so the
    URL extractor can find spec links.
    """
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_adf_to_text(item) for item in node)
    if not isinstance(node, dict):
        return ""

    node_type = node.get("type")
    if node_type == "text":
        text = node.get("text", "")
        for mark in node.get("marks", []) or []:
            if mark.get("type") == "link":
                href = (mark.get("attrs") or {}).get("href")
                if href and href not in text:
                    text = "{text} ({href})".format(text=text, href=href)
        return text
    if node_type in ("inlineCard", "blockCard", "embedCard"):
        return (node.get("attrs") or {}).get("url", "")
    if node_type == "mention":
        attrs = node.get("attrs") or {}
        return "@" + (attrs.get("text") or attrs.get("displayName") or attrs.get("id") or "")
    if node_type == "hardBreak":
        return "\n"

    inner = _adf_to_text(node.get("content"))
    block_types = {
        "paragraph",
        "heading",
        "listItem",
        "bulletList",
        "orderedList",
        "blockquote",
        "codeBlock",
        "panel",
        "rule",
    }
    if node_type in block_types:
        return inner + "\n\n"
    return inner


def _description_to_text(description: Any) -> str:
    if description is None:
        return ""
    if isinstance(description, str):
        return description
    return _adf_to_text(description).strip()


def fetch_jira_issue(
    issue_key: str,
    jira_base_url: str,
    email: str,
    api_token: str,
) -> Dict[str, Any]:
    """Fetch a Jira issue via Atlassian Cloud REST API v3 with Basic auth.

    Raises ``ValueError`` with a human-readable message on auth, HTTP, or parsing
    failures. The caller decides whether the failure is fatal or a soft fallback.
    """
    base = jira_base_url.rstrip("/")
    fields = "summary,description,issuelinks,labels,issuetype,status"
    url = "{base}/rest/api/3/issue/{key}?fields={fields}".format(
        base=base, key=urlparse.quote(issue_key, safe=""), fields=fields,
    )
    credentials = base64.b64encode(
        "{email}:{token}".format(email=email, token=api_token).encode("utf-8")
    ).decode("ascii")
    req = urlrequest.Request(
        url,
        headers={
            "Authorization": "Basic " + credentials,
            "Accept": "application/json",
            "User-Agent": "gitlab-mr-testcase/0.3 (+jira-fetch)",
        },
    )
    try:
        with urlrequest.urlopen(req, timeout=SPEC_FETCH_TIMEOUT_SECONDS) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urlerror.HTTPError as exc:
        raise ValueError(
            "Jira fetch failed for {key}: HTTP {code}. Check JIRA_API_TOKEN and "
            "JIRA_USER_EMAIL, and confirm the issue key exists.".format(
                key=issue_key, code=exc.code,
            )
        ) from exc
    except urlerror.URLError as exc:
        raise ValueError(
            "Jira fetch failed for {key}: {reason}".format(key=issue_key, reason=exc.reason)
        ) from exc
    except (TimeoutError, OSError) as exc:
        raise ValueError(
            "Jira fetch failed for {key}: {error}".format(key=issue_key, error=exc)
        ) from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Jira returned non-JSON response for {key}: {error}".format(
                key=issue_key, error=exc,
            )
        ) from exc


def _budget_truncate(content: str, label: str, remaining: int, notes: List[str]) -> str:
    """Apply per-source and total-budget truncation; record any truncation in ``notes``."""
    if len(content) > MAX_SPEC_BYTES_PER_FILE:
        content = content[:MAX_SPEC_BYTES_PER_FILE].rstrip()
        notes.append(
            "{label} truncated to {limit} chars".format(label=label, limit=MAX_SPEC_BYTES_PER_FILE)
        )
    if len(content) > remaining:
        content = content[:remaining].rstrip()
        notes.append("{label} truncated to fit total spec budget".format(label=label))
    return content


def _resolve_explicit_source(raw: str, notes: List[str]) -> Tuple[str, str, str, bool]:
    """Resolve one user-supplied spec source.

    Returns ``(label, kind, content, is_reference_only)``. When the URL fetch fails,
    ``content`` is empty and ``is_reference_only`` is True so the caller embeds a
    reference rather than spec text.
    """
    if _looks_like_url(raw):
        content, fetch_error = _fetch_spec_url(raw)
        if fetch_error or not content:
            notes.append(
                "{url} not fetched ({reason}); embedded as reference only. "
                "Export the page to a local file (Markdown or text) and pass it with --spec to include full content.".format(
                    url=raw, reason=fetch_error or "no content",
                )
            )
            return raw, "URL", "", True
        return raw, "URL", content, False

    resolved = Path(raw).expanduser()
    if not resolved.is_file():
        raise ValueError(
            "spec source not found: {path}. Pass an existing file path or an http(s) URL.".format(
                path=resolved,
            )
        )
    try:
        content = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ValueError(
            "failed to read spec file {path}: {error}".format(path=resolved, error=exc)
        ) from exc
    return str(resolved), "file", content, False


def _jira_derived_sources(
    issue: Dict[str, Any],
    issue_key: str,
    notes: List[str],
) -> List[Tuple[str, str, str, bool]]:
    """Build spec sources from a Jira issue: description first, then any spec URLs in it."""
    fields = issue.get("fields") or {}
    description_text = _description_to_text(fields.get("description"))
    summary = (fields.get("summary") or "").strip()

    sources: List[Tuple[str, str, str, bool]] = []

    if description_text or summary:
        header = "# {key}: {summary}".format(key=issue_key, summary=summary or "(no summary)")
        body = description_text or "_(Jira description is empty.)_"
        sources.append((
            "jira:{key}".format(key=issue_key),
            "jira-description",
            "{header}\n\n{body}".format(header=header, body=body),
            False,
        ))
    else:
        notes.append(
            "Jira issue {key} has no description or summary; nothing to embed as a spec.".format(
                key=issue_key,
            )
        )

    seen_urls: Dict[str, None] = {}
    candidate_urls = _extract_urls(description_text)
    for url in candidate_urls:
        if not _looks_like_spec_url(url) or url in seen_urls:
            continue
        seen_urls[url] = None
        content, fetch_error = _fetch_spec_url(url)
        if fetch_error or not content:
            notes.append(
                "{url} (from Jira) not fetched ({reason}); embedded as reference only.".format(
                    url=url, reason=fetch_error or "no content",
                )
            )
            sources.append((url, "URL (via Jira)", "", True))
        else:
            sources.append((url, "URL (via Jira)", content, False))

    return sources


def load_specs(
    explicit_sources: List[str],
    jira_issue: Optional[Dict[str, Any]] = None,
    jira_key: str = "",
) -> Dict[str, str]:
    """Load explicit spec sources and any sources derived from a Jira issue.

    Raises ``ValueError`` when there is nothing to anchor the gate to: no explicit
    sources AND no usable Jira description / Jira-extracted URLs.
    """
    notes: List[str] = []
    prepared: List[Tuple[str, str, str, bool]] = []

    if jira_issue is not None and jira_key:
        prepared.extend(_jira_derived_sources(jira_issue, jira_key, notes))

    for raw in explicit_sources:
        prepared.append(_resolve_explicit_source(raw, notes))

    if not prepared:
        raise ValueError(
            "design spec is required: pass --spec PATH_OR_URL, or pass --jira-issue with "
            "JIRA_API_TOKEN + JIRA_USER_EMAIL set so the spec can be discovered from the "
            "Jira issue description."
        )

    sections: List[str] = []
    rendered_labels: List[str] = []
    total_chars = 0

    for label, kind, content, is_reference_only in prepared:
        if is_reference_only:
            rendered_labels.append(label)
            sections.append(
                "### Spec reference ({kind}, not fetched): {label}\n\n"
                "_Auto-fetch failed or the source requires authentication. "
                "The human reviewer must read this source out of band, or pre-download "
                "it and re-run with `--spec /path/to/exported-file.md`._".format(
                    kind=kind, label=label,
                )
            )
            continue

        remaining = MAX_TOTAL_SPEC_BYTES - total_chars
        if remaining <= 0:
            notes.append("{label} skipped (total spec budget exhausted)".format(label=label))
            continue
        content = _budget_truncate(content, label, remaining, notes)
        rendered_labels.append(label)
        sections.append(
            "### Spec ({kind}): `{label}`\n\n{content}".format(
                kind=kind, label=label, content=content.strip(),
            )
        )
        total_chars += len(content)

    status_parts = ["Loaded {count} spec source(s).".format(count=len(rendered_labels))]
    if notes:
        status_parts.append("Notes: " + "; ".join(notes) + ".")

    return {
        "spec_content": "\n\n".join(sections).strip(),
        "spec_paths": ", ".join(rendered_labels) if rendered_labels else "(none)",
        "spec_status": " ".join(status_parts),
    }


def resolve_jira_reference(jira_issue: Optional[str], jira_base_url: str) -> Dict[str, str]:
    """Normalize the optional Jira issue input into a markdown reference block."""
    if not jira_issue:
        return {
            "jira_issue_reference": "_No Jira issue was supplied._",
            "jira_issue_key": "",
            "jira_issue_url": "",
        }

    raw = jira_issue.strip()
    if _looks_like_url(raw):
        url = raw
        match = re.search(r"/browse/([A-Z][A-Z0-9_]+-\d+)", url)
        key = match.group(1) if match else ""
    elif JIRA_KEY_PATTERN.match(raw):
        key = raw
        url = "{base}/browse/{key}".format(base=jira_base_url.rstrip("/"), key=key)
    else:
        raise ValueError(
            "invalid --jira-issue value '{raw}'. Expected an issue key like PROJ-1234 "
            "or a Jira URL containing /browse/<KEY>.".format(raw=raw)
        )

    parts = ["**Jira issue**: "]
    if key:
        parts.append("`{key}`".format(key=key))
    if url:
        if key:
            parts.append(" ({url})".format(url=url))
        else:
            parts.append(url)
    reference = "".join(parts) + (
        "\n\n_When `JIRA_API_TOKEN` and `JIRA_USER_EMAIL` are set, the script also fetches "
        "the issue and uses its description (plus any design-spec URLs inside it) as the "
        "spec. Pass `--spec` to override or augment that._"
    )

    return {
        "jira_issue_reference": reference,
        "jira_issue_key": key,
        "jira_issue_url": url,
    }


def pick_output_path(
    project_root: str,
    explicit_output: Optional[str],
    explicit_dir: Optional[str],
    derived_filename: str,
) -> Path:
    if explicit_output:
        return Path(explicit_output).expanduser()

    if explicit_dir:
        target_dir = Path(explicit_dir).expanduser()
    else:
        project_root_path = Path(project_root).expanduser()
        target_dir = project_root_path
        for candidate in OUTPUT_DIR_PREFERENCE:
            candidate_path = project_root_path / candidate
            if candidate_path.is_dir():
                target_dir = candidate_path
                break

    return target_dir / derived_filename


def _slugify(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return cleaned or fallback


def derive_filename(
    test_focus: str,
    mr_reference: Optional[str],
    jira_key: str,
    local_diff: bool,
) -> str:
    focus = _slugify(test_focus, "tests")
    if jira_key:
        identifier = _slugify(jira_key, "issue")
    elif mr_reference:
        match = re.search(r"!(\d+)$", mr_reference) or re.search(r"/merge_requests/(\d+)", mr_reference)
        if match:
            identifier = "mr-" + match.group(1)
        elif mr_reference.strip().isdigit():
            identifier = "mr-" + mr_reference.strip()
        else:
            identifier = _slugify(mr_reference, "mr")[:60]
    elif local_diff:
        identifier = "local-" + _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    else:
        identifier = "testcases"
    return "{identifier}-{focus}-testcases.md".format(identifier=identifier, focus=focus)


def render_testcase_prompt(template: str, context: Dict[str, str]) -> str:
    return render_template(template, context)


def write_output(content: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def _attempt_jira_fetch(
    jira_reference: Dict[str, str],
    jira_base_url: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Decide whether to fetch the Jira issue and do it. Returns ``(issue_or_none, error_or_none)``."""
    key = jira_reference.get("jira_issue_key") or ""
    if not key:
        return None, "Jira reference has no extractable key; skipping issue fetch."

    email = os.getenv("JIRA_USER_EMAIL") or os.getenv("JIRA_USER")
    token = os.getenv("JIRA_API_TOKEN") or os.getenv("JIRA_TOKEN")
    if not email or not token:
        return None, (
            "JIRA_USER_EMAIL and JIRA_API_TOKEN are not both set; cannot fetch Jira issue "
            "{key} for auto spec discovery.".format(key=key)
        )

    try:
        issue = fetch_jira_issue(key, jira_base_url, email, token)
    except ValueError as exc:
        return None, str(exc)
    return issue, None


def main() -> int:
    args = parse_args()

    if not args.local_diff and not args.mr_reference:
        print(
            "Provide a Merge Request reference or pass --local-diff to use local changes.",
            file=sys.stderr,
        )
        return 2

    if not args.local_diff and not args.token:
        print(
            "Missing GitLab token. Set GITLAB_TOKEN or pass --token. "
            "The token needs the `api` scope (read+write) to fetch MR details.",
            file=sys.stderr,
        )
        return 2

    jira_fetch_note: Optional[str] = None

    try:
        if args.local_diff:
            sections = build_local_sections(
                args.project_root,
                args.max_files,
                args.max_changed_lines,
                args.max_diff_chars,
                args.include_generated,
            )
        else:
            sections = build_sections(
                args.mr_reference or "",
                args.gitlab_url,
                args.project,
                args.token,
                args.project_root,
                args.max_files,
                args.max_changed_lines,
                args.max_diff_chars,
                args.include_generated,
                args.skip_project_match_check,
            )

        jira_sections = resolve_jira_reference(args.jira_issue, args.jira_base_url)
        explicit_specs = list(args.spec) + list(args.spec_file)

        jira_issue_data: Optional[Dict[str, Any]] = None
        if args.jira_issue and not explicit_specs:
            jira_issue_data, jira_fetch_note = _attempt_jira_fetch(jira_sections, args.jira_base_url)
            if jira_issue_data is None and jira_fetch_note:
                print("[gitlab-mr-testcase] " + jira_fetch_note, file=sys.stderr)

        spec_sections = load_specs(
            explicit_specs,
            jira_issue=jira_issue_data,
            jira_key=jira_sections.get("jira_issue_key") or "",
        )

        prompt_path = resolve_prompt_path(args.test_focus, args.prompt_file)
    except (GitLabAPIError, OSError, ValueError) as exc:
        message = "Failed to build test-case prompt: {error}".format(error=exc)
        if "design spec is required" in str(exc) and args.jira_issue and jira_fetch_note:
            message += "\n  Jira auto-discovery did not produce a spec: " + jira_fetch_note
        print(message, file=sys.stderr)
        return 1

    if args.language != "auto":
        sections["language"] = args.language

    sections.update(spec_sections)
    sections.update(jira_sections)
    sections["test_focus"] = normalize_test_focus(args.test_focus)
    sections["review_focus"] = sections["test_focus"]

    if args.format == "spec":
        output = spec_sections["spec_content"]
    elif args.format == "bundle":
        output = sections["bundle"]
    elif args.format == "summary":
        output = sections["mr_summary"]
    elif args.format == "diff":
        output = sections["mr_diff"]
    else:
        template = load_prompt_template(str(prompt_path))
        output = render_testcase_prompt(template, sections)

    if args.stdout:
        print(output)
        return 0

    derived = derive_filename(
        sections["test_focus"],
        args.mr_reference,
        jira_sections.get("jira_issue_key") or "",
        args.local_diff,
    )
    output_path = pick_output_path(
        args.project_root,
        args.output_file,
        args.output_dir,
        derived,
    )
    write_output(output, output_path)
    print("Wrote: {path}".format(path=output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
