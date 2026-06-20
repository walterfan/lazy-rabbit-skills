#!/usr/bin/env python3
"""Draft and optionally create GitLab issues from MR discussions."""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib import error, parse, request


DEFAULT_GITLAB_URL = "https://gitlab.example.com"
DEFAULT_LABELS = ["mr-follow-up", "code-review"]

_SSL_CTX = ssl.create_default_context()


class GitLabAPIError(RuntimeError):
    """Raised when GitLab returns an error response."""


@dataclass
class CommentSource:
    discussion_id: str
    note_ids: List[int] = field(default_factory=list)
    author: str = ""
    file_path: str = ""
    line: Optional[int] = None
    url: str = ""
    resolved: bool = False
    resolvable: bool = False


@dataclass
class IssueDraft:
    title: str
    description: str
    labels: List[str]
    source: CommentSource


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate GitLab issue drafts from Merge Request discussions."
    )
    parser.add_argument(
        "mr_reference",
        nargs="?",
        help="Merge Request URL, namespace/project!iid, or plain IID with --project.",
    )
    parser.add_argument(
        "--gitlab-url",
        default=os.getenv("GITLAB_URL") or os.getenv("GITLAB_BASE_URL") or DEFAULT_GITLAB_URL,
        help="GitLab base URL. Ignored when a full MR URL is used.",
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GITLAB_PROJECT") or os.getenv("GITLAB_PROJECT_ID"),
        help="Project path or ID for plain MR IIDs.",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("GITLAB_TOKEN") or os.getenv("GITLAB_PRIVATE_TOKEN"),
        help="GitLab token. Prefer GITLAB_TOKEN in the environment.",
    )
    parser.add_argument(
        "--include-resolved",
        action="store_true",
        help="Include resolved discussions. By default only unresolved or non-resolvable comments are drafted.",
    )
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        default=(os.getenv("GITLAB_NO_SSL_VERIFY") or "").lower() in {"1", "true", "yes", "on"},
        help="Disable SSL verification only after explicit user approval.",
    )
    parser.add_argument(
        "--labels",
        default=",".join(DEFAULT_LABELS),
        help="Comma-separated labels to apply to generated issue drafts.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Draft output format.",
    )
    parser.add_argument(
        "--output-file",
        help="Optional path for writing draft output.",
    )
    parser.add_argument(
        "--input-file",
        help="Confirmed JSON draft file used with --create.",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create issues from --input-file. Requires --confirmed.",
    )
    parser.add_argument(
        "--confirmed",
        action="store_true",
        help="Required guard for --create after the user confirms the issue plan.",
    )
    return parser.parse_args()


def configure_ssl(no_ssl_verify: bool) -> None:
    if not no_ssl_verify:
        return
    _SSL_CTX.check_hostname = False
    _SSL_CTX.verify_mode = ssl.CERT_NONE


def normalize_base_url(gitlab_url: str) -> str:
    return gitlab_url.rstrip("/")


def request_json(
    method: str,
    api_url: str,
    private_token: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Any:
    data = None
    include_json = payload is not None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = request.Request(api_url, data=data, method=method.upper())
    req.add_header("PRIVATE-TOKEN", private_token)
    if include_json:
        req.add_header("Content-Type", "application/json")

    try:
        with request.urlopen(req, context=_SSL_CTX) as response:
            body = response.read().decode("utf-8")
            if not body:
                return None
            return json.loads(body)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitLabAPIError(
            "GitLab API error: {status} - {body}".format(status=exc.code, body=body)
        ) from exc
    except error.URLError as exc:
        raise GitLabAPIError("GitLab request failed: {error}".format(error=exc.reason)) from exc


def parse_merge_request_reference(
    mr_reference: str,
    gitlab_url: Optional[str] = None,
    default_project: Optional[str] = None,
) -> Tuple[str, str, str]:
    """Return (gitlab_url, project_path_or_id, merge_request_iid)."""

    reference = mr_reference.strip()
    project = default_project
    base_url = normalize_base_url(gitlab_url or DEFAULT_GITLAB_URL)

    if reference.startswith("http://") or reference.startswith("https://"):
        parsed = parse.urlparse(reference)
        base_url = "{scheme}://{netloc}".format(scheme=parsed.scheme, netloc=parsed.netloc)
        marker = "/-/merge_requests/"
        if marker not in parsed.path:
            raise ValueError("merge request URL must contain '/-/merge_requests/<iid>'")
        project_path, _, remainder = parsed.path.partition(marker)
        project_path = project_path.lstrip("/")
        merge_request_iid = remainder.split("/", 1)[0]
        if not project_path or not merge_request_iid:
            raise ValueError("could not parse project path or merge request IID from URL")
        return base_url, project_path, merge_request_iid

    if "!" in reference:
        project, merge_request_iid = reference.rsplit("!", 1)
        if project and merge_request_iid:
            return base_url, project, merge_request_iid

    if reference.isdigit():
        if not project:
            raise ValueError("plain MR IID requires --project or GITLAB_PROJECT")
        return base_url, project, reference

    raise ValueError(
        "unsupported MR reference. Use a full MR URL, namespace/project!iid, or plain IID with project context."
    )


def project_api_path(project: str) -> str:
    return parse.quote(project, safe="")


def get_merge_request(
    gitlab_url: str,
    project: str,
    merge_request_iid: str,
    private_token: str,
) -> Dict[str, Any]:
    api_url = "{base}/api/v4/projects/{project}/merge_requests/{mr}".format(
        base=normalize_base_url(gitlab_url),
        project=project_api_path(project),
        mr=parse.quote(merge_request_iid, safe=""),
    )
    return request_json("GET", api_url, private_token)


def get_merge_request_discussions(
    gitlab_url: str,
    project: str,
    merge_request_iid: str,
    private_token: str,
) -> List[Dict[str, Any]]:
    discussions: List[Dict[str, Any]] = []
    page = 1
    per_page = 100
    while True:
        api_url = "{base}/api/v4/projects/{project}/merge_requests/{mr}/discussions?per_page={per_page}&page={page}".format(
            base=normalize_base_url(gitlab_url),
            project=project_api_path(project),
            mr=parse.quote(merge_request_iid, safe=""),
            per_page=per_page,
            page=page,
        )
        payload = request_json("GET", api_url, private_token) or []
        discussions.extend(payload)
        if len(payload) < per_page:
            return discussions
        page += 1


def create_issue(
    gitlab_url: str,
    project: str,
    private_token: str,
    title: str,
    description: str,
    labels: Iterable[str],
) -> Dict[str, Any]:
    api_url = "{base}/api/v4/projects/{project}/issues".format(
        base=normalize_base_url(gitlab_url),
        project=project_api_path(project),
    )
    payload = {
        "title": title,
        "description": description,
        "labels": ",".join(labels),
    }
    return request_json("POST", api_url, private_token, payload=payload)


def plain_text(markdown: str) -> str:
    text = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[*_>#\[\]()]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def make_title(body: str, file_path: str = "") -> str:
    text = plain_text(body)
    if not text:
        text = "Follow up on MR review comment"
    sentence = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
    sentence = sentence.strip(" -:")
    if len(sentence) > 80:
        sentence = sentence[:77].rstrip() + "..."
    if sentence and not sentence.lower().startswith(("fix", "add", "update", "remove", "handle", "document")):
        sentence = "Follow up: {text}".format(text=sentence)
    if file_path:
        return "{title} ({path})".format(title=sentence, path=Path(file_path).name)
    return sentence


def note_position(note: Dict[str, Any]) -> Tuple[str, Optional[int]]:
    position = note.get("position") or {}
    file_path = position.get("new_path") or position.get("old_path") or ""
    line = position.get("new_line") or position.get("old_line")
    return file_path, line


def should_include_discussion(discussion: Dict[str, Any], include_resolved: bool) -> bool:
    notes = [note for note in discussion.get("notes", []) if not note.get("system")]
    if not notes:
        return False
    if include_resolved:
        return True
    resolvable = any(bool(note.get("resolvable")) for note in notes)
    unresolved = any(bool(note.get("resolvable")) and not bool(note.get("resolved")) for note in notes)
    return unresolved or not resolvable


def build_issue_drafts(
    gitlab_url: str,
    project: str,
    merge_request_iid: str,
    mr: Dict[str, Any],
    discussions: List[Dict[str, Any]],
    labels: List[str],
    include_resolved: bool,
) -> List[IssueDraft]:
    drafts: List[IssueDraft] = []
    mr_url = mr.get("web_url") or "{base}/{project}/-/merge_requests/{iid}".format(
        base=normalize_base_url(gitlab_url),
        project=project,
        iid=merge_request_iid,
    )

    for discussion in discussions:
        if not should_include_discussion(discussion, include_resolved):
            continue

        notes = [note for note in discussion.get("notes", []) if not note.get("system")]
        if not notes:
            continue

        first_note = notes[0]
        file_path, line = note_position(first_note)
        source = CommentSource(
            discussion_id=str(discussion.get("id", "")),
            note_ids=[int(note.get("id")) for note in notes if note.get("id")],
            author=(first_note.get("author") or {}).get("username", ""),
            file_path=file_path,
            line=line,
            url=first_note.get("url") or mr_url,
            resolved=all(bool(note.get("resolved")) for note in notes if note.get("resolvable")),
            resolvable=any(bool(note.get("resolvable")) for note in notes),
        )
        quoted_comments = []
        for note in notes:
            author = (note.get("author") or {}).get("username", "unknown")
            body = note.get("body", "").strip()
            if body:
                quoted_comments.append("> @{author}: {body}".format(author=author, body=body))

        location = file_path
        if line:
            location = "{path}:{line}".format(path=file_path, line=line)
        if not location:
            location = "Merge Request discussion"

        description = "\n".join(
            [
                "## Context",
                "This issue was generated from review feedback on {mr_url}.".format(mr_url=mr_url),
                "",
                "## Source",
                "- Discussion: `{discussion_id}`".format(discussion_id=source.discussion_id),
                "- Location: `{location}`".format(location=location),
                "- First author: `@{author}`".format(author=source.author or "unknown"),
                "",
                "## Review comments",
                "\n\n".join(quoted_comments),
                "",
                "## Acceptance criteria",
                "- Review the referenced MR comment and decide the required code change.",
                "- Implement the follow-up in the target repository.",
                "- Add or update tests when behavior changes.",
            ]
        ).strip()

        drafts.append(
            IssueDraft(
                title=make_title(first_note.get("body", ""), file_path=file_path),
                description=description,
                labels=labels,
                source=source,
            )
        )

    return drafts


def draft_to_dict(draft: IssueDraft) -> Dict[str, Any]:
    return {
        "title": draft.title,
        "description": draft.description,
        "labels": draft.labels,
        "source": {
            "discussion_id": draft.source.discussion_id,
            "note_ids": draft.source.note_ids,
            "author": draft.source.author,
            "file_path": draft.source.file_path,
            "line": draft.source.line,
            "url": draft.source.url,
            "resolved": draft.source.resolved,
            "resolvable": draft.source.resolvable,
        },
    }


def render_markdown(payload: Dict[str, Any]) -> str:
    drafts = payload.get("drafts", [])
    lines = [
        "# GitLab MR Issue Drafts",
        "",
        "- Project: `{project}`".format(project=payload.get("project", "")),
        "- Merge Request: `{iid}`".format(iid=payload.get("merge_request_iid", "")),
        "- MR title: {title}".format(title=payload.get("mr_title", "")),
        "- Draft issues: {count}".format(count=len(drafts)),
        "",
    ]

    if not drafts:
        lines.append("No actionable MR comments were found.")
        return "\n".join(lines).rstrip()

    for index, draft in enumerate(drafts, start=1):
        source = draft.get("source", {})
        location = source.get("file_path") or "MR discussion"
        if source.get("line"):
            location = "{path}:{line}".format(path=location, line=source["line"])
        lines.extend(
            [
                "## Issue {index}: {title}".format(index=index, title=draft.get("title", "")),
                "",
                "- Labels: `{labels}`".format(labels=", ".join(draft.get("labels", []))),
                "- Source: discussion `{discussion}`, `{location}`, `@{author}`".format(
                    discussion=source.get("discussion_id", ""),
                    location=location,
                    author=source.get("author") or "unknown",
                ),
                "- Source URL: {url}".format(url=source.get("url", "")),
                "",
                draft.get("description", ""),
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def write_or_print(text: str, output_file: Optional[str]) -> None:
    if output_file:
        Path(output_file).write_text(text, encoding="utf-8")
        return
    print(text)


def load_confirmed_payload(input_file: str) -> Dict[str, Any]:
    path = Path(input_file)
    if not path.exists():
        raise ValueError("confirmed input file does not exist: {path}".format(path=path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("drafts"), list):
        raise ValueError("confirmed input file must contain a drafts array")
    return payload


def create_confirmed_issues(args: argparse.Namespace) -> int:
    if not args.confirmed:
        raise ValueError("--create requires --confirmed after explicit user confirmation")
    if not args.input_file:
        raise ValueError("--create requires --input-file containing confirmed issue drafts")
    if not args.token:
        raise ValueError("GITLAB_TOKEN is required to create issues")

    payload = load_confirmed_payload(args.input_file)
    gitlab_url = payload.get("gitlab_url") or args.gitlab_url
    project = payload.get("project") or args.project
    if not project:
        raise ValueError("confirmed payload must include project")

    created = []
    for draft in payload.get("drafts", []):
        title = (draft.get("title") or "").strip()
        description = (draft.get("description") or "").strip()
        labels = draft.get("labels") or DEFAULT_LABELS
        if not title or not description:
            created.append({"title": title, "status": "skipped", "reason": "missing title or description"})
            continue
        issue = create_issue(gitlab_url, project, args.token, title, description, labels)
        created.append(
            {
                "title": title,
                "status": "created",
                "iid": issue.get("iid"),
                "web_url": issue.get("web_url"),
            }
        )

    print(json.dumps({"created": created}, indent=2, sort_keys=True))
    return 0


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    if not args.mr_reference:
        raise ValueError("mr_reference is required unless --create is used")
    if not args.token:
        raise ValueError("GITLAB_TOKEN is required to fetch MR discussions")

    gitlab_url, project, merge_request_iid = parse_merge_request_reference(
        args.mr_reference,
        gitlab_url=args.gitlab_url,
        default_project=args.project,
    )
    labels = [label.strip() for label in args.labels.split(",") if label.strip()]
    mr = get_merge_request(gitlab_url, project, merge_request_iid, args.token)
    discussions = get_merge_request_discussions(gitlab_url, project, merge_request_iid, args.token)
    drafts = build_issue_drafts(
        gitlab_url,
        project,
        merge_request_iid,
        mr,
        discussions,
        labels,
        include_resolved=args.include_resolved,
    )
    return {
        "gitlab_url": gitlab_url,
        "project": project,
        "merge_request_iid": merge_request_iid,
        "mr_title": mr.get("title", ""),
        "mr_url": mr.get("web_url", ""),
        "drafts": [draft_to_dict(draft) for draft in drafts],
    }


def main() -> int:
    args = parse_args()
    configure_ssl(args.no_ssl_verify)
    try:
        if args.create:
            return create_confirmed_issues(args)

        payload = build_payload(args)
        if args.format == "json":
            output = json.dumps(payload, indent=2, sort_keys=True)
        else:
            output = render_markdown(payload)
        write_or_print(output, args.output_file)
        return 0
    except (GitLabAPIError, ValueError, json.JSONDecodeError) as exc:
        print("ERROR: {error}".format(error=exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
