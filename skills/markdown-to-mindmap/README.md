# markdown-to-mindmap

把 Markdown 文档转换成 PlantUML mindmap 脚本，并进一步渲染成 PNG 图片。

这个 skill 适合拿来处理几类内容：

- 会议笔记、读书笔记、学习提纲
- 有清晰标题层级的技术文档
- 需要从 Markdown 快速生成思维导图的演示材料
- 想用一个小而完整的例子演示 `promptfoo` 评估流程

它故意做得比较“笨”，但也因此比较稳：

- 主要看标题和列表，不靠大模型自由发挥
- 先生成 `.puml`，再渲染 `.png`
- 同时提供手工命令和 `promptfoo` 自动评估

## 目录结构

```text
markdown-to-mindmap/
├── README.md
├── skill.md
├── scripts/
│   ├── markdown_to_mindmap.py
│   ├── render_diagram.py
│   ├── render_markdown_mindmap.py
│   └── requirements.txt
├── evals/
│   ├── fixtures/
│   ├── expected/
│   ├── promptfooconfig.generation.yaml
│   └── promptfooconfig.e2e.yaml
└── references/
    └── detailed-guide.md
```

## 它能做什么

### 1. Markdown -> PlantUML mindmap

把下面这类 Markdown：

```markdown
# Building a Promptfoo Demo

## Goals
- Explain generation evals
- Show end-to-end rendering

## Workflow
- Write the skill
  - Add parser script
  - Add render wrapper
```

转换成类似这样的 PlantUML mindmap：

```text
@startmindmap
* Building a Promptfoo Demo
** Goals
*** Explain generation evals
*** Show end-to-end rendering
** Workflow
*** Write the skill
**** Add parser script
**** Add render wrapper
@endmindmap
```

### 2. Markdown -> PlantUML -> PNG

在生成 `.puml` 之后，再调用 PlantUML 渲染出 `.png`。

这部分既可以走本地 `plantuml` CLI，也可以走 PlantUML public server。

## 工作原理

当前实现遵循一套很朴素的映射规则：

- 第一个 H1 标题作为根节点
- H2/H3/H4 等标题作为子分支
- 无序列表和有序列表作为更深一层的节点
- 缩进决定列表层级
- fenced code block、空行和大部分自由文本会被忽略

如果 Markdown 没有 H1，就退回到你传入的标题，或者文件名。

## 环境要求

- Python 3.9+
- 如果走服务端渲染：`requests`
- 如果走本地渲染：`plantuml` CLI 在 `$PATH` 上
- 如果要跑自动评估：Node.js + `npx`

安装 Python 依赖：

```bash
pip install -r scripts/requirements.txt
```

如果你习惯用 `python` 而不是 `python3`，下面命令可以自行替换。

## 如何使用

先进入 skill 目录：

```bash
cd ~/.agents/skills/markdown-to-mindmap
```

### 用法一：只生成 `.puml`

```bash
python3 scripts/markdown_to_mindmap.py \
  -i evals/fixtures/sample_note.md \
  -o output/sample_note.puml
```

如果你不传 `-o`，它会直接把 PlantUML 输出到标准输出。

例如：

```bash
python3 scripts/markdown_to_mindmap.py -i evals/fixtures/sample_note.md
```

### 用法二：直接生成 PNG

如果本机没有装 `plantuml`，最省事的方式是走 server 模式：

```bash
PLANTUML_MODE=server python3 scripts/render_markdown_mindmap.py \
  -i evals/fixtures/sample_note.md \
  -o output/sample_note.png
```

执行成功后，它会返回一段 JSON，里面会告诉你：

- `success`
- `image_path`
- `puml_path`
- `image_bytes`
- `mindmap`

如果你本机已经装了 `plantuml`，可以不设 `PLANTUML_MODE=server`。

### 用法三：给没有 H1 的 Markdown 指定标题

```bash
python3 scripts/markdown_to_mindmap.py \
  -i some_note.md \
  --title "My Mindmap" \
  -o output/my_note.puml
```

## 用 Promptfoo 做评估和测试

这套 skill 自带了两类评估：

1. `generation eval`
   检查 Markdown 到 PlantUML 的生成结果是不是符合预期。
2. `e2e eval`
   检查 Markdown 到 `.puml` 再到 `.png` 的整条链路是不是跑通了。

这两层都很有用。前者看“写得对不对”，后者看“东西真的产出来没有”。AI skill 场景里，后者往往更实在。

## 评估一：Generation Eval

配置文件：

```text
evals/promptfooconfig.generation.yaml
```

它当前检查的内容包括：

- 输出里是否包含 `@startmindmap`
- 根节点标题是否正确
- 关键分支是否生成出来
- 对另一份 fixture 做结构性断言，确认层级节点数量和关键节点都在

运行命令：

```bash
npx promptfoo@latest eval -c evals/promptfooconfig.generation.yaml
```

如果你所在环境的 npm registry 比较慢，或者默认走私有镜像，建议直接这样跑：

```bash
npm_config_registry=https://registry.npmjs.org \
  npx -y promptfoo@0.121.5 eval -c evals/promptfooconfig.generation.yaml
```

## 评估二：End-to-End Eval

配置文件：

```text
evals/promptfooconfig.e2e.yaml
```

它检查的不是“回答得像不像”，而是：

- 返回值是不是合法 JSON
- 是否标记了 `"success": true`
- 是否产出了 `.puml`
- 是否产出了 `.png`
- `image_bytes` 是否大于 0

运行命令：

```bash
PLANTUML_MODE=server npx promptfoo@latest eval -c evals/promptfooconfig.e2e.yaml
```

如果 npm registry 有问题，就用这个更稳妥的版本：

```bash
npm_config_registry=https://registry.npmjs.org \
  PLANTUML_MODE=server \
  npx -y promptfoo@0.121.5 eval -c evals/promptfooconfig.e2e.yaml
```

## 为什么这套 Promptfoo 示例值得保留

很多 AI demo 只验证“模型回答看起来像不像对的”。这当然有价值，但还不够。

这个例子更像工程现场：

- 先生成结构化中间产物 `.puml`
- 再验证真正的最终产物 `.png`
- 既能看输出内容，也能看工作流是否闭环

如果你将来要评估别的 skill，比如：

- Markdown -> Mermaid
- 文本 -> SQL
- 文本 -> 配置文件
- 文本 -> API 调用链

都可以照着这个套路拆成两层：

1. 生成层评估
2. 端到端产物评估

## 常见问题

### 1. `python: command not found`

有些机器只有 `python3`，没有 `python`。直接把命令中的 `python` 换成 `python3` 即可。

### 2. 渲染时报 `requests` 缺失

先安装依赖：

```bash
pip install -r scripts/requirements.txt
```

### 3. PNG 没生成出来

先排查这几件事：

- 生成的 `.puml` 是否有效
- 是否设置了 `PLANTUML_MODE=server`
- PlantUML server 是否可达
- 输出目录是否可写

### 4. Promptfoo 路径解析不对

一定要在 skill 目录里运行 `promptfoo`：

```bash
cd ~/.agents/skills/markdown-to-mindmap
```

因为配置里用了相对路径的 `file://` provider 和 fixture。

### 5. npm 安装 `promptfoo` 很慢

这通常不是 `promptfoo` 本身的问题，而是 npm registry 配置问题。可以临时切到官方 registry：

```bash
npm_config_registry=https://registry.npmjs.org npx -y promptfoo@0.121.5 eval -c evals/promptfooconfig.generation.yaml
```

## 相关文件

- Skill 入口：`SKILL.md`
- 详细说明：`references/detailed-guide.md`
- 生成脚本：`scripts/markdown_to_mindmap.py`
- 渲染脚本：`scripts/render_markdown_mindmap.py`
- Generation eval：`evals/promptfooconfig.generation.yaml`
- E2E eval：`evals/promptfooconfig.e2e.yaml`

## 一句话总结

如果你只是想把 Markdown 变成思维导图，这个 skill 已经够用了。

如果你还想顺手演示“怎么像工程师一样评估一个 AI skill”，那它自带的 `promptfoo` 配置，比 PPT 更会说话。
