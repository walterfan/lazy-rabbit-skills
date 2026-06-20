#!/usr/bin/env python3
"""Generate a scripted terminal demo for the agents-md-generate skill."""

import json
import sys

COLS, ROWS = 110, 35

CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
GRAY = "\033[0;90m"
PURPLE = "\033[0;35m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

events = []
t = 0.0


def out(text, delay=0.0):
    global t
    t += delay
    events.append([round(t, 3), "o", text])


def nl(n=1):
    out("\r\n" * n)


def pause(seconds):
    global t
    t += seconds


def clear():
    out("\033[2J\033[H")


def type_user(message, after=1.0):
    out(f"{BOLD}{GREEN}>{RESET} ")
    for ch in message:
        out(ch, delay=0.045)
    nl()
    pause(after)


def assistant(lines, char_delay=0.014):
    for line in lines:
        if line == "":
            nl()
            continue
        for ch in line:
            out(ch, delay=char_delay)
        nl()
    pause(0.35)


def tool_call(tool, args, result_lines, tool_delay=0.55):
    pause(0.25)
    out(f"{BOLD}{CYAN}[tool] {tool}{RESET}{DIM}({args}){RESET}")
    nl()
    pause(tool_delay)
    for line in result_lines:
        out(f"  {DIM}|{RESET} {line}\r\n")
    nl()
    pause(0.35)


def skill_invoked(skill_name):
    pause(0.25)
    out(f"{DIM}  Skill loaded: {PURPLE}{skill_name}{RESET}")
    nl(2)
    pause(0.65)


def phase(title):
    out(f"{BOLD}{title}{RESET}")
    nl(2)
    pause(0.45)


def end_countdown(seconds=35):
    nl(2)
    for remaining in range(seconds, 0, -1):
        out(f"\r  {DIM}Replaying in {remaining}s...   {RESET}", delay=1.0)
    nl(2)


clear()
pause(0.4)

out(f"{BOLD}  Claude Code{RESET}  {DIM}claude-sonnet-4-6{RESET}")
nl()
out(f"{DIM}  /Users/me/workspace/acme-payments{RESET}")
nl(2)
pause(0.8)

type_user(
    "Create a concise AGENTS.md for this repo. Optimize for Codex, Claude Code, and Cursor. "
    "We have a man/ project knowledge base. Improve any existing CLAUDE.md, and create "
    "CLAUDE.md / GEMINI.md symlinks if appropriate."
)

skill_invoked("agents-md-generate")

assistant(
    [
        "I will generate a compact AGENTS.md instead of duplicating the project knowledge base.",
        "",
        "Assumptions:",
        "- Primary tools: Codex, Claude Code, Cursor.",
        "- man/ is the deep source of architecture and runbooks, so AGENTS.md will link to it.",
        "- Existing CLAUDE.md becomes input; I will not overwrite it silently.",
        "- Symlinks are requested, so I will create CLAUDE.md and GEMINI.md links only after checking conflicts.",
        "",
        "Success criteria: root AGENTS.md exists, stays under 100 lines, has no placeholders, commands are verified "
        "or marked TODO verify, and compatibility links resolve.",
    ]
)

phase("Phase 1 - Discover repository facts")

tool_call(
    "Read",
    "skills/agents-md-generate/SKILL.md",
    [
        "Use progressive disclosure: AGENTS.md is the operating map; man/ and docs/ keep depth.",
        "Ask for AI tool preferences and symlink intent.",
        "Merge existing AGENTS.md or CLAUDE.md instead of replacing blindly.",
    ],
)

tool_call(
    "Bash",
    "bash scripts/discover_repo.sh /Users/me/workspace/acme-payments",
    [
        '{ "language": "go", "package_manager": "go-mod", "task_runner": "make",',
        '  "kb_path": "man", "existing_agent_files": ["CLAUDE.md"],',
        '  "agent_client_dirs": [".claude", ".cursor"], "readme_exists": true }',
    ],
)

tool_call(
    "Read",
    "CLAUDE.md README.md man/index.md Makefile",
    [
        "CLAUDE.md: long agent instructions with duplicated architecture notes.",
        "README.md: payment orchestration service for internal integrations.",
        "man/index.md: canonical architecture, operations, and change workflow index.",
        "Makefile: build, test, lint, test-focus targets exist.",
    ],
)

assistant(
    [
        "The repo already has useful agent rules, but CLAUDE.md duplicates man/ architecture content.",
        "I will migrate the reusable rules into AGENTS.md, link man/index.md for depth, and keep the root file short.",
    ]
)

phase("Phase 2 - Draft a concise AGENTS.md")

tool_call(
    "ApplyPatch",
    "create AGENTS.md",
    [
        "Added Context Map with README, man/index.md, and key directories.",
        "Added Commands using make build, make test, make lint, and make test-focus.",
        "Added Harness Rules: no fabrication, ask on material ambiguity, simplicity, surgical edits, verification.",
        "Added AI Tooling for Codex, Claude Code, and Cursor.",
    ],
)

tool_call(
    "Bash",
    "sed -n '1,120p' AGENTS.md",
    [
        "# AGENTS.md - acme-payments",
        "Payment orchestration service for internal integrations.",
        "",
        "## Context Map",
        "- README: ./README.md",
        "- Project Knowledge Base: ./man/index.md",
        "- cmd/: service entry points",
        "- internal/: domain logic and adapters",
        "",
        "## Harness Rules",
        "- Never fabricate paths, APIs, commands, tests, or results; inspect first.",
        "- Verify before reporting done; a plausible diff is not proof.",
    ],
)

assistant(
    [
        "Notice what stayed out of AGENTS.md: architecture diagrams, runbooks, and tutorial material.",
        "Those remain in man/, so the agent gets a strong map without a second source of truth.",
    ]
)

phase("Phase 3 - Wire compatibility for preferred tools")

tool_call(
    "Bash",
    "test -e CLAUDE.md; test -e GEMINI.md",
    [
        "CLAUDE.md exists and is not a symlink.",
        "GEMINI.md does not exist.",
    ],
)

assistant(
    [
        "CLAUDE.md already exists, so I will not replace it without an explicit migration decision.",
        "GEMINI.md is clear, so I can link it to AGENTS.md.",
    ]
)

tool_call(
    "Bash",
    "ln -s AGENTS.md GEMINI.md && readlink GEMINI.md",
    [
        "AGENTS.md",
    ],
)

phase("Phase 4 - Verify and summarize")

tool_call(
    "Bash",
    "wc -l AGENTS.md && rg -n '\\{\\{|TODO verify' AGENTS.md && make test-focus",
    [
        "82 AGENTS.md",
        "no unresolved placeholders",
        "make test-focus: PASS",
    ],
)

assistant(
    [
        f"{GREEN}Done.{RESET} Created a concise AGENTS.md that raises the repo harness level without duplicating man/.",
        "",
        "Summary:",
        "- Files improved: AGENTS.md",
        "- Line count: 82",
        "- Optimized for: Codex, Claude Code, Cursor",
        "- Symlinks: GEMINI.md -> AGENTS.md created; CLAUDE.md left untouched because it already exists",
        "- Verification: placeholders clean, focused test command passed",
        "",
        "Suggested next step: review whether to replace existing CLAUDE.md with a symlink after comparing its remaining project-specific rules.",
    ]
)

end_countdown(35)

output_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/agents-md-generate-demo.cast"
with open(output_path, "w", encoding="utf-8") as f:
    header = {
        "version": 2,
        "width": COLS,
        "height": ROWS,
        "title": "agents-md-generate demo",
        "env": {"TERM": "xterm-256color", "SHELL": "/bin/zsh"},
    }
    f.write(json.dumps(header) + "\n")
    for event in events:
        f.write(json.dumps(event) + "\n")

print(f"Generated {len(events)} events, duration={t:.1f}s -> {output_path}")
