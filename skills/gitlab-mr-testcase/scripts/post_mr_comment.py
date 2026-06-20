#!/usr/bin/env python3
"""Post a comment on a GitLab Merge Request with the test cases summary and matrix.

This is the companion to ``generate_testcases.py``. After the AI fills in the prompt
template and produces a markdown file with the actual test cases, this script reads
that file, extracts only the high-signal sections — Change Summary / Spec Coverage
Map, Traceability Matrix / Open Questions, and the Gate Verdict block — and posts
them as an MR comment. The full test case list stays in the file and is referenced
by a footer link.

Uses the vendored ``gitlab_api`` helper under ``../lib/`` (originally from the
``gitlab-mr-review`` skill — see ``../lib/SOURCES.md``) for both reference parsing
and the actual ``POST /projects/.../merge_requests/.../notes`` call.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

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

from gitlab_api import (  # noqa: E402
    GitLabAPIError,
    parse_merge_request_reference,
    post_merge_request_comment,
)


MAX_COMMENT_CHARS = 60_000  # GitLab note bodies max out around 1 MB; stay well under.

# Section headings (case-insensitive) that mark the START of the summary block. Any
# ATX heading at level 1-3 that contains one of these phrases is accepted.
START_HEADING_KEYWORDS = (
    "change summary",
    "spec coverage map",
)

# Headings that mark the END (the start of the case list). Extraction stops just
# before the first match.
END_HEADING_PATTERNS = (
    re.compile(r"^#{1,3}\s+TC-\d+\b", re.IGNORECASE),
    re.compile(r"^#{1,3}\s+AC-\d+\b", re.IGNORECASE),
    re.compile(r"^#{1,3}\s+(?:acceptance\s+)?test\s+case\s+list\b", re.IGNORECASE),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Post a GitLab Merge Request comment with the test cases summary and "
            "matrix extracted from the AI-generated test case markdown."
        ),
    )
    parser.add_argument(
        "mr_reference",
        help="Merge Request URL, namespace/project!iid, or plain IID with project context.",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--file",
        metavar="PATH",
        help="Markdown file containing the AI-filled test cases.",
    )
    src.add_argument(
        "--stdin",
        action="store_true",
        help="Read the test cases markdown from stdin instead of a file.",
    )
    parser.add_argument(
        "--full-file",
        action="store_true",
        help="Post the entire input verbatim instead of extracting the summary/matrix/verdict.",
    )
    parser.add_argument(
        "--header",
        default="Test Case Quality Gate (auto-generated)",
        help="H2 heading prefixed to the comment body. Set to empty string to skip.",
    )
    parser.add_argument(
        "--footer-link",
        default=None,
        help=(
            "Optional repo-relative path or URL to the full test cases file, added to "
            "the comment footer. Defaults to --file when --file is used."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the comment body that would be posted instead of calling the API.",
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
    return parser.parse_args()


def _looks_like_start_heading(line: str) -> bool:
    if not line.startswith("#"):
        return False
    stripped = re.sub(r"^#{1,3}\s+", "", line).strip().lower()
    return any(keyword in stripped for keyword in START_HEADING_KEYWORDS)


def extract_summary_block(markdown: str) -> Tuple[str, List[str]]:
    """Extract the summary / matrix / gate verdict block from filled-in markdown.

    Returns ``(extracted_text, notes)``. ``notes`` lists any extraction concerns
    (e.g., no Gate Verdict found) so the caller can surface them.
    """
    lines = markdown.splitlines()
    start = -1
    for index, line in enumerate(lines):
        if _looks_like_start_heading(line):
            start = index
            break
    if start < 0:
        return "", [
            "Could not find a 'Change Summary' or 'Spec Coverage Map' heading; "
            "the input does not look like a filled-in test case document."
        ]

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if any(pattern.match(lines[index]) for pattern in END_HEADING_PATTERNS):
            end = index
            break

    extracted = "\n".join(lines[start:end]).rstrip()
    notes: List[str] = []
    if "Skip line-by-line review" not in extracted:
        notes.append(
            "Extracted block does not contain a Gate Verdict line — comment will still "
            "be posted but the reviewer should check whether the AI emitted one."
        )
    return extracted, notes


def build_comment_body(
    body: str,
    header: str,
    footer_link: Optional[str],
    extraction_notes: List[str],
) -> str:
    parts: List[str] = []
    header = (header or "").strip()
    if header:
        parts.append("## {header}".format(header=header))
        parts.append("")

    parts.append(body.rstrip())
    parts.append("")
    parts.append("---")
    footer_lines: List[str] = []
    if footer_link:
        footer_lines.append("Full test cases: `{link}`".format(link=footer_link))
    footer_lines.append("_Posted by `gitlab-mr-testcase`. Re-run the skill to refresh._")
    parts.append("  \n".join(footer_lines))

    if extraction_notes:
        parts.append("")
        parts.append("> **Extraction notes**")
        for note in extraction_notes:
            parts.append("> - {note}".format(note=note))

    text = "\n".join(parts).rstrip() + "\n"
    if len(text) > MAX_COMMENT_CHARS:
        truncated = text[: MAX_COMMENT_CHARS - 200].rstrip()
        text = truncated + (
            "\n\n_...comment truncated to fit GitLab note limits. See the full test "
            "cases file for the rest._\n"
        )
    return text


def read_input(args: argparse.Namespace) -> str:
    if args.stdin:
        data = sys.stdin.read()
        if not data.strip():
            raise ValueError("stdin was empty; expected the test cases markdown.")
        return data
    path = Path(args.file).expanduser()
    if not path.is_file():
        raise ValueError(
            "input file not found: {path}".format(path=path)
        )
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ValueError(
            "failed to read input file {path}: {error}".format(path=path, error=exc)
        ) from exc


def resolve_footer_link(args: argparse.Namespace) -> Optional[str]:
    if args.footer_link is not None:
        return args.footer_link.strip() or None
    if args.file:
        return args.file
    return None


def main() -> int:
    args = parse_args()

    if not args.dry_run and not args.token:
        print(
            "Missing GitLab token. Set GITLAB_TOKEN or pass --token. "
            "Use --dry-run to preview without posting.",
            file=sys.stderr,
        )
        return 2

    try:
        content = read_input(args)
    except ValueError as exc:
        print("Failed to read input: {error}".format(error=exc), file=sys.stderr)
        return 1

    extraction_notes: List[str] = []
    if args.full_file:
        body = content.rstrip()
    else:
        body, extraction_notes = extract_summary_block(content)
        if not body:
            for note in extraction_notes:
                print("[gitlab-mr-testcase] " + note, file=sys.stderr)
            print(
                "No summary/matrix block found. Re-run with --full-file to post the entire "
                "document, or fix the heading structure (## Change Summary or ## Spec "
                "Coverage Map).",
                file=sys.stderr,
            )
            return 1

    comment = build_comment_body(
        body=body,
        header=args.header,
        footer_link=resolve_footer_link(args),
        extraction_notes=extraction_notes,
    )

    if args.dry_run:
        sys.stdout.write(comment)
        if not comment.endswith("\n"):
            sys.stdout.write("\n")
        for note in extraction_notes:
            print("[dry-run note] " + note, file=sys.stderr)
        return 0

    try:
        resolved_url, resolved_project, mr_iid = parse_merge_request_reference(
            args.mr_reference,
            gitlab_url=args.gitlab_url,
            default_project=args.project,
        )
        post_merge_request_comment(
            resolved_url,
            resolved_project,
            mr_iid,
            comment,
            args.token,
        )
    except (GitLabAPIError, OSError, ValueError) as exc:
        print("Failed to post MR comment: {error}".format(error=exc), file=sys.stderr)
        return 1

    print(
        "Posted comment on {project}!{iid} ({url}/-/merge_requests/{iid})".format(
            project=resolved_project, iid=mr_iid, url=resolved_url.rstrip("/"),
        )
    )
    for note in extraction_notes:
        print("[note] " + note, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
