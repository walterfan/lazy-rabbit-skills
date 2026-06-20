# lazy-rabbit-skills

[English](README.md) | 中文

Lazy Rabbit 的个人 AI 技能（Skill）合集。

每个技能位于 `skills/<name>/SKILL.md`，遵循
[agent skill](https://agents.md) 约定：开头是包含 `name` 和 `description`
的 front-matter，后面是说明、参考资料以及智能体可按需加载的脚本。

## 技能列表

### 文档与知识库

| 技能 | 说明 |
|------|------|
| [`agents-md-generate`](skills/agents-md-generate/SKILL.md) | 创建、刷新或迁移面向编码智能体的 `AGENTS.md` 引导文件。 |
| [`project-knowledge-base`](skills/project-knowledge-base/SKILL.md) | 构建并维护项目知识库（Markdown/MyST、C4、ADR、运维手册、中英双语 Sphinx HTML）。 |
| [`pkb-collect`](skills/pkb-collect/SKILL.md) | 将外部知识导入并整合进已有的项目知识库。 |
| [`pkb-refer`](skills/pkb-refer/SKILL.md) | 在回答之前先查阅项目知识库。 |
| [`feature-design-doc`](skills/feature-design-doc/SKILL.md) | 基于实用模板生成功能级技术设计文档。 |
| [`microservice-design-doc`](skills/microservice-design-doc/SKILL.md) | 为微服务项目生成结构化设计文档。 |
| [`write-user-story`](skills/write-user-story/SKILL.md) | 编写规范的敏捷用户故事。 |

### 图表与头脑风暴

| 技能 | 说明 |
|------|------|
| [`diagram-render`](skills/diagram-render/SKILL.md) | 将图表代码（PlantUML、Mermaid、Graphviz）渲染为 PNG/SVG。 |
| [`brainstorm-mindmap`](skills/brainstorm-mindmap/SKILL.md) | 把想法、问题或文章转化为深度思考的思维导图。 |
| [`markdown-to-mindmap`](skills/markdown-to-mindmap/SKILL.md) | 将 Markdown 笔记/大纲转换为 PlantUML 思维导图图片。 |

### 编程语言开发

| 技能 | 说明 |
|------|------|
| [`lazy-cpp-dev`](skills/lazy-cpp-dev/SKILL.md) | C++ 开发、评审与现代化改造助手。 |
| [`cpp-core-guide`](skills/cpp-core-guide/SKILL.md) | C++ Core Guidelines 参考与审查助手。 |
| [`lazy-go-dev`](skills/lazy-go-dev/SKILL.md) | 地道的 Go 开发与评审助手。 |
| [`lazy-java-dev`](skills/lazy-java-dev/SKILL.md) | Spring Boot / MyBatis 的 Java 后端开发与评审助手。 |
| [`lazy-python-dev`](skills/lazy-python-dev/SKILL.md) | 库风格的 Python 开发助手（Poetry、Ruff、pytest）。 |

### 代码评审与 GitLab

| 技能 | 说明 |
|------|------|
| [`gitlab-mr-review`](skills/gitlab-mr-review/SKILL.md) | 通过 URL 或分支对比评审 GitLab Merge Request。 |
| [`gitlab-mr-issue`](skills/gitlab-mr-issue/SKILL.md) | 把 MR 评论中可执行的建议转化为 GitLab issue。 |
| [`gitlab-mr-split`](skills/gitlab-mr-split/SKILL.md) | 将大型 MR 拆分为更小、更安全的子 MR。 |
| [`gitlab-mr-testcase`](skills/gitlab-mr-testcase/SKILL.md) | 结合 MR diff 与设计文档为 GitLab MR 生成测试用例。 |

### 运维与排障

| 技能 | 说明 |
|------|------|
| [`lazy-network-doctor`](skills/lazy-network-doctor/SKILL.md) | 本地网络排障（ping/dig/netstat 等）。 |
| [`lazy-memgraph-helper`](skills/lazy-memgraph-helper/SKILL.md) | 操作 Memgraph 图数据库。 |
| [`lazy-sqlite-helper`](skills/lazy-sqlite-helper/SKILL.md) | 操作 SQLite 数据库。 |

### 流程、规划与质量

| 技能 | 说明 |
|------|------|
| [`lazy-scrum-team`](skills/lazy-scrum-team/SKILL.md) | 覆盖整个 Sprint 生命周期的一体化 AI 虚拟 Scrum 团队。 |
| [`lazy-design-challenge`](skills/lazy-design-challenge/SKILL.md) | 逐个分支地挑战假设，对技术设计进行压力测试。 |
| [`socratic-design-review`](skills/socratic-design-review/SKILL.md) | 用严谨的苏格拉底式提问评审设计（九大思维元素、Paul 六类提问、CBT 反诘、禅宗话头）——只提问，不给答案。 |
| [`lazy-harness-audit`](skills/lazy-harness-audit/SKILL.md) | 审计并评分项目的 AI 编码智能体工作环境（harness）。 |
| [`lazy-harness-helper`](skills/lazy-harness-helper/SKILL.md) | 改进项目的 AI 编码智能体工作环境（harness）。 |
| [`lazy-skill-write`](skills/lazy-skill-write/SKILL.md) | 使用 CEVF 质量框架编写高质量 AI 技能。 |
| [`lazy-skill-check`](skills/lazy-skill-check/SKILL.md) | 验证并基准测试 AI 技能。 |

## 快速开始（一行命令）

无需克隆仓库，用一条命令下载并安装所有技能：

```bash
curl -fsSL https://raw.githubusercontent.com/walterfan/lazy-rabbit-skills/master/setup.sh | bash
```

`setup.sh` 会把仓库下载到 `~/.lazy-rabbit-skills`，然后运行 `install.sh`
将所有技能链接到你的各个智能体。建议先检查再运行：

```bash
curl -fsSL https://raw.githubusercontent.com/walterfan/lazy-rabbit-skills/master/setup.sh -o setup.sh
less setup.sh
bash setup.sh
```

通过环境变量或透传参数进行自定义：

```bash
# 仅安装到指定的智能体
curl -fsSL .../setup.sh | LRS_TARGETS=claude,codex bash

# 仅安装指定技能（参数会透传给 install.sh）
curl -fsSL .../setup.sh | bash -s -- gitlab-mr-review lazy-go-dev

# 覆盖已存在的链接
curl -fsSL .../setup.sh | LRS_FORCE=1 bash
```

| 变量 | 默认值 | 用途 |
|------|--------|------|
| `LRS_REF` | `master` | 要下载的分支/标签 |
| `LRS_DIR` | `~/.lazy-rabbit-skills` | 仓库安装目录 |
| `LRS_TARGETS` | install.sh 默认值 | 逗号分隔的智能体目标 |
| `LRS_FORCE` | 未设置 | 设为 `1` 以覆盖已存在的链接 |

随时重新运行同一条命令即可更新到最新的技能。

## 安装（从克隆的仓库）

使用 `install.sh` 把技能接入你的各个智能体。它会在 `~/.agents/skills/<name>`
下创建一个指向本仓库的标准（canonical）软链接，再把它链接到各个智能体的
技能目录：

```
~/.agents/skills/<name>            -> <repo>/skills/<name>   （标准链接）
~/.claude/skills/<name>            -> ~/.agents/skills/<name>
~/.codex/skills/<name>             -> ~/.agents/skills/<name>
~/.cursor/skills/<name>            -> ~/.agents/skills/<name>
~/.config/opencode/skills/<name>  -> ~/.agents/skills/<name>
```

由于标准链接指向本仓库，在这里编辑技能会立即对所有智能体生效。

```bash
./install.sh                              # 安装全部技能
./install.sh gitlab-mr-review             # 安装单个技能
./install.sh lazy-go-dev lazy-python-dev  # 安装多个技能
./install.sh --targets claude,codex lazy-skill-write
./install.sh --dry-run --all              # 预览而不做改动
./install.sh --force --all                # 覆盖已存在的链接
```

选项：`--all`、`--targets <claude,codex,cursor,opencode>`、`--force`、
`--dry-run`、`--help`。

## 卸载

`uninstall.sh` 只删除软链接（绝不删除真实文件）。各智能体下的链接仅当其指向
本仓库的标准链接时才会被删除，因此由其他工具安装的技能不受影响。

```bash
./uninstall.sh                            # 卸载本仓库的全部技能
./uninstall.sh gitlab-mr-review           # 卸载单个技能
./uninstall.sh --targets cursor lazy-go-dev
./uninstall.sh --keep-agents --all        # 删除各智能体链接，保留 ~/.agents
./uninstall.sh --dry-run --all            # 预览而不做改动
```

选项：`--all`、`--targets <...>`、`--keep-agents`、`--dry-run`、`--help`。

## 许可证

见 [LICENSE](LICENSE)。
