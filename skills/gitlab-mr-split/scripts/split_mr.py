#!/usr/bin/env python3
"""Split a large GitLab Merge Request into smaller, sequential sub-MRs.

Usage:
    python3 split_mr.py analyze <mr-reference> [options]
    python3 split_mr.py plan <mr-reference> [options]
    python3 split_mr.py execute <mr-reference> --plan <plan.json> [options]
    python3 split_mr.py split <mr-reference> [options]

Subcommands:
    analyze   Fetch MR and show file grouping summary
    plan      Generate a split plan (JSON) for review
    execute   Execute a previously saved split plan
    split     Plan + execute in one step (confirms before creating)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import ssl
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional, Tuple

# Add the gitlab-mr-review scripts to path for reuse
_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REVIEW_SCRIPTS = os.path.join(os.path.dirname(_SKILL_DIR), "gitlab-mr-review", "scripts")
if os.path.isdir(_REVIEW_SCRIPTS):
    sys.path.insert(0, _REVIEW_SCRIPTS)

try:
    from gitlab_api import (
        GitLabAPIError,
        ChangeItem,
        parse_diff_stats,
        parse_merge_request_reference,
        _normalize_base_url,
        _request_json,
        _SSL_CTX,
    )
except ImportError:
    print(
        "ERROR: Could not import gitlab_api module. "
        "Ensure skills/gitlab-mr-review/scripts/gitlab_api.py exists.",
        file=sys.stderr,
    )
    sys.exit(1)

from urllib import parse as urlparse


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FileEntry:
    path: str
    old_path: str
    is_new: bool = False
    is_deleted: bool = False
    is_renamed: bool = False
    added_lines: int = 0
    deleted_lines: int = 0
    changed_lines: int = 0
    diff: str = ""


@dataclass
class SplitGroup:
    name: str
    index: int
    files: List[str] = field(default_factory=list)
    total_added: int = 0
    total_deleted: int = 0
    total_changed: int = 0


@dataclass
class SplitPlan:
    original_mr_url: str
    original_title: str
    original_description: str
    source_branch: str
    target_branch: str
    project_path: str
    gitlab_url: str
    strategy: str
    groups: List[SplitGroup] = field(default_factory=list)
    target_mode: str = "chain"  # "chain" or "parallel"


@dataclass
class CreatedMR:
    index: int
    title: str
    branch: str
    target_branch: str
    url: str
    file_count: int
    added_lines: int
    deleted_lines: int


# ---------------------------------------------------------------------------
# GitLab API extensions (branch + MR creation)
# ---------------------------------------------------------------------------

@dataclass
class MRFullInfo:
    """Merge request metadata plus parsed changes."""
    title: str = ""
    description: str = ""
    source_branch: str = ""
    target_branch: str = ""
    changes: List[ChangeItem] = field(default_factory=list)


def get_mr_full_info(
    gitlab_url: str, project_id: str, mr_iid: str, token: str
) -> MRFullInfo:
    """Fetch MR metadata and changes in a single API call.

    The /merge_requests/:iid/changes endpoint returns title, description,
    source_branch, target_branch, AND the diff changes — no need for two calls.
    """
    base = _normalize_base_url(gitlab_url)
    api_url = "{base}/api/v4/projects/{project}/merge_requests/{mr}/changes".format(
        base=base,
        project=urlparse.quote(project_id, safe=""),
        mr=urlparse.quote(mr_iid, safe=""),
    )
    payload = _request_json("GET", api_url, token)
    _ci_fields = {f.name for f in ChangeItem.__dataclass_fields__.values()}
    changes = [
        ChangeItem(**{k: v for k, v in change.items() if k in _ci_fields})
        for change in payload.get("changes", [])
    ]
    return MRFullInfo(
        title=payload.get("title", ""),
        description=payload.get("description", ""),
        source_branch=payload.get("source_branch", ""),
        target_branch=payload.get("target_branch", ""),
        changes=changes,
    )


def create_branch(
    gitlab_url: str, project_id: str, branch_name: str, ref: str, token: str
) -> None:
    """Create a new branch from a ref."""
    base = _normalize_base_url(gitlab_url)
    api_url = "{base}/api/v4/projects/{project}/repository/branches".format(
        base=base,
        project=urlparse.quote(project_id, safe=""),
    )
    _request_json("POST", api_url, token, payload={
        "branch": branch_name,
        "ref": ref,
    })


def commit_files_to_branch(
    gitlab_url: str,
    project_id: str,
    branch_name: str,
    file_actions: List[Dict[str, str]],
    commit_message: str,
    token: str,
) -> None:
    """Create a commit on a branch with the given file actions."""
    base = _normalize_base_url(gitlab_url)
    api_url = "{base}/api/v4/projects/{project}/repository/commits".format(
        base=base,
        project=urlparse.quote(project_id, safe=""),
    )
    _request_json("POST", api_url, token, payload={
        "branch": branch_name,
        "commit_message": commit_message,
        "actions": file_actions,
    })


class FileNotFoundOnRef(Exception):
    """Raised when a file does not exist at the given ref."""


class BinaryFileError(Exception):
    """Raised when a file is binary and cannot be handled as text."""


def get_file_content_at_ref(
    gitlab_url: str, project_id: str, file_path: str, ref: str, token: str
) -> Optional[str]:
    """Get file content at a specific ref.

    Returns None only when the file does not exist (404).
    Raises BinaryFileError for binary files.
    Raises GitLabAPIError for other API failures (403, 500, etc.).
    """
    base_url = _normalize_base_url(gitlab_url)
    api_url = (
        "{base}/api/v4/projects/{project}/repository/files/{fp}?ref={ref}".format(
            base=base_url,
            project=urlparse.quote(project_id, safe=""),
            fp=urlparse.quote(file_path, safe=""),
            ref=urlparse.quote(ref, safe=""),
        )
    )
    try:
        data = _request_json("GET", api_url, token)
        content = data.get("content", "")
        encoding = data.get("encoding", "")
        if encoding == "base64":
            raw = base64.b64decode(content)
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                raise BinaryFileError(
                    "File {fp} at ref {ref} appears to be binary".format(fp=file_path, ref=ref)
                )
        return content
    except GitLabAPIError as e:
        err_str = str(e)
        if "404" in err_str:
            return None
        raise


def create_merge_request(
    gitlab_url: str,
    project_id: str,
    source_branch: str,
    target_branch: str,
    title: str,
    description: str,
    token: str,
) -> str:
    """Create a merge request. Returns the MR web URL."""
    base = _normalize_base_url(gitlab_url)
    api_url = "{base}/api/v4/projects/{project}/merge_requests".format(
        base=base,
        project=urlparse.quote(project_id, safe=""),
    )
    data = _request_json("POST", api_url, token, payload={
        "source_branch": source_branch,
        "target_branch": target_branch,
        "title": title,
        "description": description,
        "remove_source_branch": True,
    })
    return data.get("web_url", "")


# ---------------------------------------------------------------------------
# Grouping strategies
# ---------------------------------------------------------------------------

LAYER_PATTERNS = {
    "model": [r"model[s]?/", r"entity/", r"domain/", r"Model\.", r"Entity\."],
    "service": [r"service[s]?/", r"usecase[s]?/", r"Service\.", r"UseCase\."],
    "controller": [r"controller[s]?/", r"handler[s]?/", r"api/", r"Controller\.", r"Handler\."],
    "repository": [r"repository/", r"repositories/", r"dao/", r"Repository\.", r"Dao\."],
    "config": [r"config/", r"\.ya?ml$", r"\.properties$", r"\.toml$"],
    "test": [r"tests?/", r"Test\.", r"_test\.", r"test_", r"Spec\."],
    "migration": [r"migrations?/", r"db/migrate/", r"\.sql$"],
}


def _detect_layer(path: str) -> str:
    for layer, patterns in LAYER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, path):
                return layer
    return "other"


def _group_by_directory(files: List[FileEntry], depth: int = 1) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = defaultdict(list)
    for f in files:
        parts = PurePosixPath(f.path).parts
        key = "/".join(parts[:depth]) if len(parts) > depth else parts[0] if parts else "root"
        groups[key].append(f.path)
    return dict(groups)


def _group_by_layer(files: List[FileEntry], colocate_tests: bool = True) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = defaultdict(list)
    test_files: List[FileEntry] = []

    for f in files:
        layer = _detect_layer(f.path)
        if layer == "test" and colocate_tests:
            test_files.append(f)
        else:
            groups[layer].append(f.path)

    if colocate_tests:
        for tf in test_files:
            # Try to match test to a source group
            name = PurePosixPath(tf.path).stem
            # Remove common test prefixes/suffixes
            clean = re.sub(r"^test_|_test$|Test$|Spec$", "", name)
            placed = False
            for group_name, group_files in groups.items():
                if group_name == "test":
                    continue
                for gf in group_files:
                    if clean.lower() in PurePosixPath(gf).stem.lower():
                        groups[group_name].append(tf.path)
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                groups["test"].append(tf.path)

    return {k: v for k, v in groups.items() if v}


def _group_by_dependency(files: List[FileEntry]) -> Dict[str, List[str]]:
    """Simple dependency grouping based on import analysis within the changed files."""
    import_patterns = [
        # Python
        r"^\s*(?:from|import)\s+([\w.]+)",
        # Java/Kotlin/JS/TS
        r"^\s*import\s+.*?['\"]([^'\"]+)['\"]",
        r"^\s*import\s+([\w.]+)",
        # Go
        r'^\s*"([^"]+)"',
        # C/C++
        r'^\s*#include\s*[<"]([^>"]+)[>"]',
        # JS require
        r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""",
    ]

    file_set = {f.path for f in files}
    deps: Dict[str, set] = {f.path: set() for f in files}

    for f in files:
        for line in f.diff.splitlines():
            if not line.startswith("+") or line.startswith("+++"):
                continue
            for pattern in import_patterns:
                m = re.search(pattern, line[1:])
                if m:
                    imported = m.group(1)
                    # Check if any changed file matches
                    for other in file_set:
                        if other == f.path:
                            continue
                        stem = PurePosixPath(other).stem
                        if stem in imported or imported.replace(".", "/") in other:
                            deps[f.path].add(other)

    # Topological layering
    layers: List[List[str]] = []
    remaining = set(file_set)
    placed = set()

    while remaining:
        # Find files with no unresolved dependencies
        layer = []
        for f in sorted(remaining):
            unresolved = deps.get(f, set()) - placed
            if not unresolved:
                layer.append(f)
        if not layer:
            # Cycle detected — dump remaining into last layer
            layer = sorted(remaining)
        layers.append(layer)
        for f in layer:
            remaining.discard(f)
            placed.add(f)

    groups = {}
    for i, layer in enumerate(layers):
        groups["layer-{n}".format(n=i + 1)] = layer
    return groups


def group_files(
    files: List[FileEntry],
    strategy: str = "by-directory",
    depth: int = 1,
    num_parts: Optional[int] = None,
    colocate_tests: bool = True,
) -> Dict[str, List[str]]:
    """Group files using the specified strategy."""
    if strategy == "by-directory":
        groups = _group_by_directory(files, depth=depth)
    elif strategy == "by-layer":
        groups = _group_by_layer(files, colocate_tests=colocate_tests)
    elif strategy == "by-dependency":
        groups = _group_by_dependency(files)
    else:
        raise ValueError("Unknown strategy: {s}. Use by-directory, by-layer, by-dependency, or custom.".format(s=strategy))

    # If num_parts specified, merge smallest groups until we reach target
    if num_parts and len(groups) > num_parts:
        group_list = sorted(groups.items(), key=lambda x: len(x[1]))
        while len(group_list) > num_parts:
            # Merge two smallest
            smallest = group_list.pop(0)
            second = group_list.pop(0)
            merged_name = "{a}+{b}".format(a=smallest[0], b=second[0])
            merged_files = smallest[1] + second[1]
            group_list.append((merged_name, merged_files))
            group_list.sort(key=lambda x: len(x[1]))
        groups = dict(group_list)

    return groups


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def fetch_mr_files(
    gitlab_url: str, project_id: str, mr_iid: str, token: str
) -> Tuple[MRFullInfo, List[FileEntry]]:
    """Fetch MR info and convert changes to FileEntry list (single API call)."""
    mr_info = get_mr_full_info(gitlab_url, project_id, mr_iid, token)
    files = []
    for change in mr_info.changes:
        stats = parse_diff_stats(change.diff)
        files.append(FileEntry(
            path=change.new_path,
            old_path=change.old_path,
            is_new=change.new_file,
            is_deleted=change.deleted_file,
            is_renamed=change.renamed_file,
            added_lines=stats.added_lines,
            deleted_lines=stats.deleted_lines,
            changed_lines=stats.changed_lines,
            diff=change.diff,
        ))
    return mr_info, files


def build_split_plan(
    gitlab_url: str,
    project_path: str,
    mr_iid: str,
    token: str,
    strategy: str = "by-directory",
    num_parts: Optional[int] = None,
    depth: int = 1,
    colocate_tests: bool = True,
    target_mode: str = "chain",
    custom_plan_path: Optional[str] = None,
) -> SplitPlan:
    """Build a split plan for the given MR."""
    project_id = project_path
    mr_info, files = fetch_mr_files(gitlab_url, project_id, mr_iid, token)
    title = mr_info.title
    description = mr_info.description
    source_branch = mr_info.source_branch
    target_branch = mr_info.target_branch

    mr_web_url = "{base}/{project}/-/merge_requests/{iid}".format(
        base=_normalize_base_url(gitlab_url),
        project=project_path,
        iid=mr_iid,
    )

    if custom_plan_path:
        with open(custom_plan_path) as f:
            custom = json.load(f)
        groups_dict = {
            g["name"]: g["files"] for g in custom.get("groups", [])
        }
    else:
        groups_dict = group_files(
            files, strategy=strategy, depth=depth,
            num_parts=num_parts, colocate_tests=colocate_tests,
        )

    file_stats = {f.path: f for f in files}
    groups = []
    for idx, (name, file_list) in enumerate(sorted(groups_dict.items()), start=1):
        total_added = sum(file_stats[fp].added_lines for fp in file_list if fp in file_stats)
        total_deleted = sum(file_stats[fp].deleted_lines for fp in file_list if fp in file_stats)
        groups.append(SplitGroup(
            name=name,
            index=idx,
            files=file_list,
            total_added=total_added,
            total_deleted=total_deleted,
            total_changed=total_added + total_deleted,
        ))

    plan = SplitPlan(
        original_mr_url=mr_web_url,
        original_title=title,
        original_description=description,
        source_branch=source_branch,
        target_branch=target_branch,
        project_path=project_path,
        gitlab_url=gitlab_url,
        strategy=strategy,
        groups=groups,
        target_mode=target_mode,
    )

    # Validate the plan
    all_file_paths = [f.path for f in files]
    validation_errors = validate_split_plan(plan, all_file_paths)
    if validation_errors:
        print("WARNING: Split plan has validation issues:", file=sys.stderr)
        for err in validation_errors:
            print("  - {err}".format(err=err), file=sys.stderr)

    return plan


def validate_split_plan(plan: SplitPlan, all_mr_files: List[str]) -> List[str]:
    """Validate the split plan. Returns a list of error messages (empty = valid)."""
    errors = []

    # Check no empty groups
    for g in plan.groups:
        if not g.files:
            errors.append("Group '{name}' (#{idx}) has no files.".format(
                name=g.name, idx=g.index))

    # Check all files covered
    plan_files = []
    for g in plan.groups:
        plan_files.extend(g.files)
    plan_set = set(plan_files)
    mr_set = set(all_mr_files)

    missing = mr_set - plan_set
    if missing:
        errors.append("Files in MR but not in any group: {files}".format(
            files=", ".join(sorted(missing))))

    extra = plan_set - mr_set
    if extra:
        errors.append("Files in plan but not in MR: {files}".format(
            files=", ".join(sorted(extra))))

    # Check no duplicates
    seen = {}
    for g in plan.groups:
        for f in g.files:
            if f in seen:
                errors.append("File '{f}' appears in both group '{a}' and '{b}'.".format(
                    f=f, a=seen[f], b=g.name))
            else:
                seen[f] = g.name

    return errors


def execute_split_plan(
    plan: SplitPlan, token: str, dry_run: bool = False
) -> List[CreatedMR]:
    """Execute the split plan by creating branches and MRs."""
    results = []
    n = len(plan.groups)

    for group in plan.groups:
        k = group.index
        branch_name = "{src}-split-{k}".format(src=plan.source_branch, k=k)
        sub_title = "{title} -{k}/{n}".format(title=plan.original_title, k=k, n=n)

        if plan.target_mode == "chain" and k > 1:
            mr_target = "{src}-split-{prev}".format(src=plan.source_branch, prev=k - 1)
        else:
            mr_target = plan.target_branch

        # Build description
        dep_note = ""
        if k > 1 and plan.target_mode == "chain":
            dep_note = "\n> **Depends on**: Part {prev}/{n} (merge that first)\n".format(prev=k - 1, n=n)

        file_list_md = "\n".join("- `{f}`".format(f=f) for f in group.files)
        mr_description = (
            "## Part {k}/{n} of [{original_title}]({url})\n\n"
            "{dep_note}"
            "### Changed files\n{file_list}\n\n"
            "### Stats\n"
            "- Added lines: +{added}\n"
            "- Deleted lines: -{deleted}\n\n"
            "---\n"
            "*Auto-generated by gitlab-mr-split*"
        ).format(
            k=k, n=n,
            original_title=plan.original_title,
            url=plan.original_mr_url,
            dep_note=dep_note,
            file_list=file_list_md,
            added=group.total_added,
            deleted=group.total_deleted,
        )

        if dry_run:
            print("[DRY RUN] Would create branch: {branch}".format(branch=branch_name))
            print("[DRY RUN] Would create MR: {title} -> {target}".format(
                title=sub_title, target=mr_target))
            results.append(CreatedMR(
                index=k, title=sub_title, branch=branch_name,
                target_branch=mr_target, url="(dry-run)",
                file_count=len(group.files),
                added_lines=group.total_added,
                deleted_lines=group.total_deleted,
            ))
            continue

        # Create branch from source branch (which has all changes)
        # For chain mode: branch from target, then apply this group's changes
        branch_base = plan.target_branch if k == 1 else "{src}-split-{prev}".format(
            src=plan.source_branch, prev=k - 1
        )
        if plan.target_mode == "parallel":
            branch_base = plan.target_branch

        try:
            create_branch(plan.gitlab_url, plan.project_path, branch_name, branch_base, token)
        except GitLabAPIError as e:
            print("ERROR creating branch {branch}: {err}".format(branch=branch_name, err=e),
                  file=sys.stderr)
            continue

        # Apply file changes via commits API
        actions = []
        skipped_binary = []
        for file_path in group.files:
            try:
                # Get the file content from the source branch (which has all the MR changes)
                content = get_file_content_at_ref(
                    plan.gitlab_url, plan.project_path, file_path,
                    plan.source_branch, token
                )
                # Check if file exists on the base
                base_content = get_file_content_at_ref(
                    plan.gitlab_url, plan.project_path, file_path,
                    branch_base, token
                )
            except BinaryFileError:
                skipped_binary.append(file_path)
                print("WARNING: Skipping binary file: {fp}".format(fp=file_path),
                      file=sys.stderr)
                continue

            if content is None:
                # File was deleted in the MR
                if base_content is not None:
                    actions.append({
                        "action": "delete",
                        "file_path": file_path,
                    })
            elif base_content is None:
                # New file
                actions.append({
                    "action": "create",
                    "file_path": file_path,
                    "content": content,
                })
            else:
                # Updated file
                actions.append({
                    "action": "update",
                    "file_path": file_path,
                    "content": content,
                })

        if skipped_binary:
            print("WARNING: {n} binary file(s) skipped in group {name}. "
                  "These must be added manually.".format(
                      n=len(skipped_binary), name=group.name),
                  file=sys.stderr)

        if actions:
            try:
                commit_files_to_branch(
                    plan.gitlab_url, plan.project_path, branch_name, actions,
                    "Part {k}/{n}: {name}".format(k=k, n=n, name=group.name),
                    token,
                )
            except GitLabAPIError as e:
                print("ERROR committing to {branch}: {err}".format(branch=branch_name, err=e),
                      file=sys.stderr)
                continue

        # Create the merge request
        try:
            mr_url = create_merge_request(
                plan.gitlab_url, plan.project_path, branch_name, mr_target,
                sub_title, mr_description, token,
            )
            results.append(CreatedMR(
                index=k, title=sub_title, branch=branch_name,
                target_branch=mr_target, url=mr_url,
                file_count=len(group.files),
                added_lines=group.total_added,
                deleted_lines=group.total_deleted,
            ))
            print("Created MR {k}/{n}: {url}".format(k=k, n=n, url=mr_url))
        except GitLabAPIError as e:
            print("ERROR creating MR for {branch}: {err}".format(branch=branch_name, err=e),
                  file=sys.stderr)

    return results


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_plan_table(plan: SplitPlan) -> str:
    n = len(plan.groups)
    lines = [
        "## Split Plan for: {title}".format(title=plan.original_title),
        "",
        "- **Original MR**: {url}".format(url=plan.original_mr_url),
        "- **Source branch**: `{src}`".format(src=plan.source_branch),
        "- **Target branch**: `{tgt}`".format(tgt=plan.target_branch),
        "- **Strategy**: {s}".format(s=plan.strategy),
        "- **Target mode**: {m}".format(m=plan.target_mode),
        "- **Sub-MRs**: {n}".format(n=n),
        "",
        "| # | Group | Files | +Added | -Deleted | Target |",
        "|---|-------|-------|--------|----------|--------|",
    ]
    for g in plan.groups:
        if plan.target_mode == "chain" and g.index > 1:
            target = "{src}-split-{prev}".format(src=plan.source_branch, prev=g.index - 1)
        else:
            target = plan.target_branch
        lines.append(
            "| {k}/{n} | {name} | {files} | +{added} | -{deleted} | `{target}` |".format(
                k=g.index, n=n, name=g.name, files=len(g.files),
                added=g.total_added, deleted=g.total_deleted, target=target,
            )
        )
    lines.append("")
    for g in plan.groups:
        lines.append("### Group {k}/{n}: {name}".format(k=g.index, n=n, name=g.name))
        for f in g.files:
            lines.append("- `{f}`".format(f=f))
        lines.append("")
    return "\n".join(lines)


def format_results_table(results: List[CreatedMR]) -> str:
    n = len(results)
    lines = [
        "## Created Sub-MRs",
        "",
        "| # | Title | Branch | Target | Files | Changes | URL |",
        "|---|-------|--------|--------|-------|---------|-----|",
    ]
    for r in results:
        lines.append(
            "| {k}/{n} | {title} | `{branch}` | `{target}` | {files} | +{added}/-{deleted} | {url} |".format(
                k=r.index, n=n, title=r.title, branch=r.branch,
                target=r.target_branch, files=r.file_count,
                added=r.added_lines, deleted=r.deleted_lines, url=r.url,
            )
        )
    lines.extend([
        "",
        "### Merge Order",
        "",
        "Merge these sub-MRs **in order** (1/{n} first, then 2/{n}, etc.).".format(n=n),
        "After merging each sub-MR, retarget the next one to `{target}` if needed.".format(
            target=results[0].target_branch if results else "main"),
        "",
        "After all sub-MRs are merged, close the original MR.",
    ])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _resolve_env() -> Tuple[str, str]:
    token = os.environ.get("GITLAB_TOKEN", "")
    gitlab_url = (
        os.environ.get("GITLAB_URL")
        or os.environ.get("GITLAB_BASE_URL")
        or "https://gitlab.example.com"
    )
    return token, gitlab_url


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a large GitLab MR into smaller sub-MRs"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Common args
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("mr_reference", help="MR URL, namespace/project!iid, or plain IID")
    common.add_argument("--project", help="GitLab project path (fallback for plain IID)")
    common.add_argument("--gitlab-url", help="GitLab base URL (default: from env or https://gitlab.example.com)")
    common.add_argument("--no-ssl-verify", action="store_true", help="Disable SSL verification")

    # analyze
    sub.add_parser("analyze", parents=[common], help="Analyze MR and show file grouping")

    # plan
    plan_parser = sub.add_parser("plan", parents=[common], help="Generate split plan")
    plan_parser.add_argument("--strategy", default="by-directory",
                             choices=["by-directory", "by-layer", "by-dependency", "custom"],
                             help="Grouping strategy")
    plan_parser.add_argument("--num-parts", type=int, help="Target number of sub-MRs")
    plan_parser.add_argument("--group-depth", type=int, default=1, help="Directory depth for by-directory")
    plan_parser.add_argument("--no-colocate-tests", action="store_true",
                             help="Don't group tests with their source files")
    plan_parser.add_argument("--target-mode", default="chain", choices=["chain", "parallel"],
                             help="How sub-MRs target branches")
    plan_parser.add_argument("--output", "-o", help="Save plan to JSON file")

    # execute
    exec_parser = sub.add_parser("execute", parents=[common], help="Execute a saved split plan")
    exec_parser.add_argument("--plan", required=True, help="Path to plan JSON file")
    exec_parser.add_argument("--dry-run", action="store_true", help="Preview without creating")

    # split (plan + execute)
    split_parser = sub.add_parser("split", parents=[common], help="Plan and execute in one step")
    split_parser.add_argument("--strategy", default="by-directory",
                              choices=["by-directory", "by-layer", "by-dependency", "custom"],
                              help="Grouping strategy")
    split_parser.add_argument("--num-parts", type=int, help="Target number of sub-MRs")
    split_parser.add_argument("--group-depth", type=int, default=1, help="Directory depth for by-directory")
    split_parser.add_argument("--no-colocate-tests", action="store_true")
    split_parser.add_argument("--target-mode", default="chain", choices=["chain", "parallel"])
    split_parser.add_argument("--custom-plan", help="Path to custom group JSON")
    split_parser.add_argument("--dry-run", action="store_true", help="Preview without creating")
    split_parser.add_argument("--yes", "-y", action="store_true",
                              help="Skip confirmation prompt and execute immediately")

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    token, env_gitlab_url = _resolve_env()

    if not token:
        print("ERROR: GITLAB_TOKEN environment variable is not set.", file=sys.stderr)
        print("Export it with: export GITLAB_TOKEN='glpat-xxxxxxxxxxxxxxxxxxxx'", file=sys.stderr)
        sys.exit(1)

    if args.no_ssl_verify:
        _SSL_CTX.check_hostname = False
        _SSL_CTX.verify_mode = ssl.CERT_NONE

    gitlab_url = args.gitlab_url or env_gitlab_url
    default_project = (
        args.project
        or os.environ.get("GITLAB_PROJECT")
        or os.environ.get("GITLAB_PROJECT_ID")
    )

    try:
        parsed_url, project_path, mr_iid = parse_merge_request_reference(
            args.mr_reference, gitlab_url=gitlab_url, default_project=default_project
        )
        gitlab_url = parsed_url
    except ValueError as e:
        print("ERROR: {err}".format(err=e), file=sys.stderr)
        sys.exit(1)

    if args.command == "analyze":
        mr_info, files = fetch_mr_files(gitlab_url, project_path, mr_iid, token)
        title, src, tgt = mr_info.title, mr_info.source_branch, mr_info.target_branch
        print("## MR Analysis: {title}".format(title=title))
        print("")
        print("- **Source**: `{src}` -> **Target**: `{tgt}`".format(src=src, tgt=tgt))
        print("- **Total files**: {n}".format(n=len(files)))
        total_added = sum(f.added_lines for f in files)
        total_deleted = sum(f.deleted_lines for f in files)
        print("- **Total changes**: +{a}/-{d}".format(a=total_added, d=total_deleted))
        print("")

        if len(files) < 3:
            print("NOTE: This MR has fewer than 3 files. Splitting may not be beneficial.")
            print("")

        # Show groupings for each strategy
        for strategy in ["by-directory", "by-layer"]:
            groups = group_files(files, strategy=strategy)
            print("### Suggested grouping ({s}):".format(s=strategy))
            for name, file_list in sorted(groups.items()):
                grp_added = sum(f.added_lines for f in files if f.path in file_list)
                grp_deleted = sum(f.deleted_lines for f in files if f.path in file_list)
                print("- **{name}** ({n} files, +{a}/-{d})".format(
                    name=name, n=len(file_list), a=grp_added, d=grp_deleted))
                for fp in file_list:
                    print("  - `{f}`".format(f=fp))
            print("")

        # Output as JSON for programmatic use
        analysis = {
            "title": title,
            "source_branch": src,
            "target_branch": tgt,
            "total_files": len(files),
            "total_added": total_added,
            "total_deleted": total_deleted,
            "files": [
                {"path": f.path, "added": f.added_lines, "deleted": f.deleted_lines,
                 "is_new": f.is_new, "is_deleted": f.is_deleted}
                for f in files
            ],
        }
        print("```json")
        print(json.dumps(analysis, indent=2))
        print("```")

    elif args.command == "plan":
        plan = build_split_plan(
            gitlab_url, project_path, mr_iid, token,
            strategy=args.strategy,
            num_parts=args.num_parts,
            depth=args.group_depth,
            colocate_tests=not args.no_colocate_tests,
            target_mode=args.target_mode,
        )
        print(format_plan_table(plan))

        if args.output:
            plan_dict = asdict(plan)
            with open(args.output, "w") as f:
                json.dump(plan_dict, f, indent=2)
            print("Plan saved to: {path}".format(path=args.output))

    elif args.command == "execute":
        with open(args.plan) as f:
            plan_dict = json.load(f)

        groups = [SplitGroup(**g) for g in plan_dict.pop("groups", [])]
        plan = SplitPlan(**plan_dict, groups=groups)

        dry_run = getattr(args, "dry_run", False)
        results = execute_split_plan(plan, token, dry_run=dry_run)
        print("")
        print(format_results_table(results))

    elif args.command == "split":
        plan = build_split_plan(
            gitlab_url, project_path, mr_iid, token,
            strategy=args.strategy,
            num_parts=args.num_parts,
            depth=args.group_depth,
            colocate_tests=not args.no_colocate_tests,
            target_mode=args.target_mode,
            custom_plan_path=args.custom_plan,
        )
        print(format_plan_table(plan))
        print("")

        dry_run = getattr(args, "dry_run", False)
        if dry_run:
            print("--- DRY RUN MODE ---")
        elif not args.yes:
            answer = input(
                "This will create {n} branches and {n} merge requests. "
                "Proceed? [y/N] ".format(n=len(plan.groups))
            )
            if answer.strip().lower() not in ("y", "yes"):
                print("Aborted.")
                sys.exit(0)

        results = execute_split_plan(plan, token, dry_run=dry_run)
        print("")
        print(format_results_table(results))


if __name__ == "__main__":
    main()
