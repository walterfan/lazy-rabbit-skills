#!/usr/bin/env python3
"""GitLab API helpers for Merge Request review workflows.

This module is a Python translation of the helpers in internal/util/gitlab.go,
with a small amount of extra reference parsing to make MR review smoother.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import ssl
from urllib import error, parse, request

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


class GitLabAPIError(RuntimeError):
    """Raised when the GitLab API returns an unexpected response."""


@dataclass
class ChangeItem:
    diff: str = ""
    new_path: str = ""
    old_path: str = ""
    a_mode: str = ""
    b_mode: str = ""
    new_file: bool = False
    renamed_file: bool = False
    deleted_file: bool = False
    generated_file: bool = False


@dataclass
class ChangeStatistics:
    changed_lines: int = 0
    added_lines: int = 0
    deleted_lines: int = 0


@dataclass
class MergeRequestInfo:
    title: str = ""
    description: str = ""
    changes: List[ChangeItem] = field(default_factory=list)


@dataclass
class FileSummary:
    index: int
    old_path: str
    new_path: str
    added: bool
    deleted: bool
    renamed: bool
    changed: bool
    changed_lines: int
    added_lines: int
    deleted_lines: int


@dataclass
class MRSummary:
    title: str = ""
    description: str = ""
    files: List[FileSummary] = field(default_factory=list)
    total_files: int = 0


@dataclass
class GitLabUserProfile:
    id: int = 0
    username: str = ""
    name: str = ""
    email: str = ""
    web_url: str = ""


def _normalize_base_url(gitlab_url: str) -> str:
    return gitlab_url.rstrip("/")


def _headers(private_token: str, include_json: bool = False) -> Dict[str, str]:
    headers = {"PRIVATE-TOKEN": private_token}
    if include_json:
        headers["Content-Type"] = "application/json"
    return headers


def _request_json(
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
    for key, value in _headers(private_token, include_json=include_json).items():
        req.add_header(key, value)

    try:
        with request.urlopen(req, context=_SSL_CTX) as response:
            body = response.read().decode("utf-8")
            if not body:
                return None
            return json.loads(body)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitLabAPIError("GitLab API error: {status} - {body}".format(status=exc.code, body=body))
    except error.URLError as exc:
        raise GitLabAPIError("GitLab request failed: {error}".format(error=exc.reason))


def parse_diff_stats(diff: str) -> ChangeStatistics:
    stats = ChangeStatistics()
    for line in diff.splitlines():
        if not line:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            stats.added_lines += 1
        if line.startswith("-") and not line.startswith("---"):
            stats.deleted_lines += 1
    stats.changed_lines = stats.added_lines + stats.deleted_lines
    return stats


def _format_bool_as_yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _format_bool_as_yn(value: bool) -> str:
    return "Y" if value else "N"


def test_gitlab_connection(gitlab_url: str, private_token: str) -> GitLabUserProfile:
    api_url = "{base}/api/v4/user".format(base=_normalize_base_url(gitlab_url))
    payload = _request_json("GET", api_url, private_token)
    return GitLabUserProfile(**payload)


def get_project_id_by_name(gitlab_url: str, project_name: str, private_token: str) -> str:
    base = _normalize_base_url(gitlab_url)
    search_url = "{base}/api/v4/projects?search={query}".format(
        base=base,
        query=parse.quote(project_name, safe=""),
    )
    projects = _request_json("GET", search_url, private_token)
    if not projects:
        raise GitLabAPIError("no project found matching name: {name}".format(name=project_name))

    for project in projects:
        if project.get("path_with_namespace") == project_name:
            return str(project["id"])

    return str(projects[0]["id"])


def change_items_to_markdown(mr_info: MergeRequestInfo) -> str:
    if not mr_info.changes:
        return "No changes found."

    lines = [
        "## Merge Request",
        "",
        "* Title: `{title}`".format(title=mr_info.title),
        "* Description: `{description}`".format(description=mr_info.description),
        "",
        "### changes",
        "",
    ]

    for change in mr_info.changes:
        lines.extend(
            [
                "* Old Path: `{old}`".format(old=change.old_path),
                "* New Path: `{new}`".format(new=change.new_path),
                "* Added: {value}".format(value=_format_bool_as_yes_no(change.new_file)),
                "* Renamed: {value}".format(value=_format_bool_as_yes_no(change.renamed_file)),
                "* Deleted: {value}".format(value=_format_bool_as_yes_no(change.deleted_file)),
                "",
                "* Code Diff:",
                "```diff",
                change.diff,
                "```",
                "",
                "------",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def convert_to_mr_summary(mr_info: MergeRequestInfo) -> MRSummary:
    summary = MRSummary(
        title=mr_info.title,
        description=mr_info.description,
        files=[],
        total_files=len(mr_info.changes),
    )

    for index, change in enumerate(mr_info.changes, start=1):
        stats = parse_diff_stats(change.diff)
        changed = not change.new_file and not change.deleted_file and stats.changed_lines > 0
        summary.files.append(
            FileSummary(
                index=index,
                old_path=change.old_path,
                new_path=change.new_path,
                added=change.new_file,
                deleted=change.deleted_file,
                renamed=change.renamed_file,
                changed=changed,
                changed_lines=stats.changed_lines,
                added_lines=stats.added_lines,
                deleted_lines=stats.deleted_lines,
            )
        )

    return summary


def mr_summary_to_markdown_table(summary: MRSummary) -> str:
    lines = [
        "## Merge Request Summary",
        "",
        "**Title:** {title}".format(title=summary.title),
        "",
    ]

    if summary.description:
        lines.extend(
            [
                "**Description:** {description}".format(description=summary.description),
                "",
            ]
        )

    lines.extend(
        [
            "**Total Files Changed:** {count}".format(count=summary.total_files),
            "",
            "| # | Old Path | New Path | Added | Deleted | Renamed | Changed | Changed Lines | Added Lines | Deleted Lines |",
            "|---|----------|----------|-------|---------|---------|---------|---------------|-------------|---------------|",
        ]
    )

    for file_summary in summary.files:
        lines.append(
            "| {index} | {old_path} | {new_path} | {added} | {deleted} | {renamed} | {changed} | {changed_lines} | {added_lines} | {deleted_lines} |".format(
                index=file_summary.index,
                old_path=file_summary.old_path,
                new_path=file_summary.new_path,
                added=_format_bool_as_yn(file_summary.added),
                deleted=_format_bool_as_yn(file_summary.deleted),
                renamed=_format_bool_as_yn(file_summary.renamed),
                changed=_format_bool_as_yn(file_summary.changed),
                changed_lines=file_summary.changed_lines,
                added_lines=file_summary.added_lines,
                deleted_lines=file_summary.deleted_lines,
            )
        )

    return "\n".join(lines)


def get_merge_request_info(
    gitlab_url: str,
    project_id: str,
    merge_request_id: str,
    private_token: str,
) -> MergeRequestInfo:
    base = _normalize_base_url(gitlab_url)
    api_url = "{base}/api/v4/projects/{project}/merge_requests/{mr}/changes".format(
        base=base,
        project=parse.quote(project_id, safe=""),
        mr=parse.quote(merge_request_id, safe=""),
    )
    payload = _request_json("GET", api_url, private_token)
    _ci_fields = {f.name for f in ChangeItem.__dataclass_fields__.values()}
    changes = [ChangeItem(**{k: v for k, v in change.items() if k in _ci_fields}) for change in payload.get("changes", [])]
    return MergeRequestInfo(
        title=payload.get("title", ""),
        description=payload.get("description", ""),
        changes=changes,
    )


def get_merge_request_change(
    gitlab_url: str,
    project_id: str,
    merge_request_id: str,
    private_token: str,
) -> str:
    mr_info = get_merge_request_info(gitlab_url, project_id, merge_request_id, private_token)
    return change_items_to_markdown(mr_info)


def get_gitlab_file_content(
    gitlab_url: str,
    project_id: str,
    file_path: str,
    branch: str,
    private_token: str,
) -> str:
    base = _normalize_base_url(gitlab_url)
    api_url = (
        "{base}/api/v4/projects/{project}/repository/files/{file_path}?ref={branch}".format(
            base=base,
            project=parse.quote(project_id, safe=""),
            file_path=parse.quote(file_path, safe=""),
            branch=parse.quote(branch, safe=""),
        )
    )
    payload = _request_json("GET", api_url, private_token)
    content = payload.get("content", "")
    encoding = payload.get("encoding", "")
    if encoding == "base64":
        return base64.b64decode(content).decode("utf-8")
    return content


def post_merge_request_comment(
    gitlab_url: str,
    project_id: str,
    merge_request_id: str,
    comment: str,
    private_token: str,
) -> None:
    base = _normalize_base_url(gitlab_url)
    api_url = "{base}/api/v4/projects/{project}/merge_requests/{mr}/notes".format(
        base=base,
        project=parse.quote(project_id, safe=""),
        mr=parse.quote(merge_request_id, safe=""),
    )
    _request_json("POST", api_url, private_token, payload={"body": comment})


def parse_merge_request_reference(
    mr_reference: str,
    gitlab_url: Optional[str] = None,
    default_project: Optional[str] = None,
) -> Tuple[str, str, str]:
    """Return (gitlab_url, project_path_or_id, merge_request_iid)."""

    reference = mr_reference.strip()
    project = default_project
    base_url = _normalize_base_url(gitlab_url or "https://gitlab.example.com")

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
            raise ValueError(
                "plain MR IID requires --project or GITLAB_PROJECT/GITLAB_PROJECT_ID"
            )
        return base_url, project, reference

    raise ValueError(
        "unsupported MR reference. Use a full MR URL, namespace/project!iid, or a plain IID with project context."
    )
