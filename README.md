# lazy-rabbit-skills

Lazy Rabbit's personal collection of AI skills.

Each skill lives under `skills/<name>/SKILL.md` and follows the
[agent skill](https://agents.md) convention: a short front-matter block with a
`name` and `description`, followed by instructions, references, and scripts the
agent can load on demand.

## Skills

### Documentation & knowledge base

| Skill | Description |
|-------|-------------|
| `agents-md-generate` | Create, refresh, or migrate `AGENTS.md` onboarding files for coding agents. |
| `project-knowledge-base` | Build and maintain a Project Knowledge Base (Markdown/MyST, C4, ADRs, runbooks, bilingual Sphinx HTML). |
| `pkb-collect` | Import and ingest external knowledge into an existing Project Knowledge Base. |
| `pkb-refer` | Consult the Project Knowledge Base before answering. |
| `feature-design-doc` | Generate feature-level technical design specs from a practical template. |
| `microservice-design-doc` | Generate structured design documents for microservice projects. |
| `write-user-story` | Write well-formed agile user stories. |

### Diagrams & brainstorming

| Skill | Description |
|-------|-------------|
| `diagram-render` | Render diagram-as-code (PlantUML, Mermaid, Graphviz) to PNG/SVG. |
| `brainstorm-mindmap` | Turn an idea, problem, or article into a deep-thinking mind map. |
| `markdown-to-mindmap` | Convert Markdown notes/outlines into a PlantUML mind map image. |

### Language-specific development

| Skill | Description |
|-------|-------------|
| `lazy-cpp-dev` | C++ development, review, and modernization helper. |
| `cpp-core-guide` | C++ Core Guidelines reference and audit helper. |
| `lazy-go-dev` | Idiomatic Go development and review helper. |
| `lazy-java-dev` | Spring Boot / MyBatis Java backend development and review helper. |
| `lazy-python-dev` | Python library-style development helper (Poetry, Ruff, pytest). |

### Code review & GitLab

| Skill | Description |
|-------|-------------|
| `gitlab-mr-review` | Review a GitLab Merge Request from a URL or branch comparison. |
| `gitlab-mr-issue` | Turn actionable MR comments into GitLab issues. |
| `gitlab-mr-split` | Split a large MR into smaller, safer sub-MRs. |
| `gitlab-mr-testcase` | Generate test cases for a GitLab MR from its diff and a design spec. |

### Ops & troubleshooting

| Skill | Description |
|-------|-------------|
| `lazy-network-doctor` | Local network troubleshooting (ping/dig/netstat/etc). |
| `lazy-memgraph-helper` | Work with Memgraph graph databases. |
| `lazy-sqlite-helper` | Work with SQLite databases. |

### Process, planning & quality

| Skill | Description |
|-------|-------------|
| `lazy-scrum-team` | All-in-one AI virtual Scrum team covering the sprint lifecycle. |
| `lazy-design-challenge` | Stress-test technical designs by challenging assumptions one branch at a time. |
| `socratic-design-review` | Review a design with disciplined Socratic questioning (nine lenses, Paul's six types, CBT disputation, Zen 话头) — asks, never answers. |
| `lazy-harness-audit` | Audit and score a project's AI coding-agent harness. |
| `lazy-harness-helper` | Improve a project's AI coding-agent harness. |
| `lazy-skill-write` | Author effective AI skills using the CEVF quality framework. |
| `lazy-skill-check` | Validate and benchmark AI skills. |

## Quick start (one-liner)

Download and install every skill with a single command — no clone needed:

```bash
curl -fsSL https://raw.githubusercontent.com/walterfan/lazy-rabbit-skills/master/setup.sh | bash
```

`setup.sh` downloads the repo into `~/.lazy-rabbit-skills`, then runs
`install.sh` to link all skills into your agents. To inspect before running
(recommended):

```bash
curl -fsSL https://raw.githubusercontent.com/walterfan/lazy-rabbit-skills/master/setup.sh -o setup.sh
less setup.sh
bash setup.sh
```

Customize via environment variables or pass-through args:

```bash
# only certain agents
curl -fsSL .../setup.sh | LRS_TARGETS=claude,codex bash

# only specific skills (args are forwarded to install.sh)
curl -fsSL .../setup.sh | bash -s -- gitlab-mr-review lazy-go-dev

# overwrite existing links
curl -fsSL .../setup.sh | LRS_FORCE=1 bash
```

| Variable | Default | Purpose |
|----------|---------|---------|
| `LRS_REF` | `master` | Branch/tag to download |
| `LRS_DIR` | `~/.lazy-rabbit-skills` | Where the repo is installed |
| `LRS_TARGETS` | install.sh default | Comma-separated agent targets |
| `LRS_FORCE` | unset | Set to `1` to overwrite existing links |

Re-run the same command anytime to update to the latest skills.

## Install (from a clone)

Use `install.sh` to wire the skills into your agents. It creates a canonical
symlink under `~/.agents/skills/<name>` pointing at this repo, then links that
into each agent's skills directory:

```
~/.agents/skills/<name>            -> <repo>/skills/<name>   (canonical)
~/.claude/skills/<name>            -> ~/.agents/skills/<name>
~/.codex/skills/<name>             -> ~/.agents/skills/<name>
~/.cursor/skills/<name>            -> ~/.agents/skills/<name>
~/.config/opencode/skills/<name>  -> ~/.agents/skills/<name>
```

Because the canonical link points back at this repo, editing a skill here
updates every agent immediately.

```bash
./install.sh                              # install ALL skills
./install.sh gitlab-mr-review             # install one skill
./install.sh lazy-go-dev lazy-python-dev  # install several
./install.sh --targets claude,codex lazy-skill-write
./install.sh --dry-run --all              # preview without changes
./install.sh --force --all                # overwrite existing links
```

Options: `--all`, `--targets <claude,codex,cursor,opencode>`, `--force`,
`--dry-run`, `--help`.

## Uninstall

`uninstall.sh` removes the symlinks (never real files). Per-agent links are
only removed when they point at this repo's canonical link, so skills installed
by other tools are left untouched.

```bash
./uninstall.sh                            # uninstall ALL repo skills
./uninstall.sh gitlab-mr-review           # uninstall one skill
./uninstall.sh --targets cursor lazy-go-dev
./uninstall.sh --keep-agents --all        # remove agent links, keep ~/.agents
./uninstall.sh --dry-run --all            # preview without changes
```

Options: `--all`, `--targets <...>`, `--keep-agents`, `--dry-run`, `--help`.

## License

See [LICENSE](LICENSE).
