---
name: lazy-skill-check
description: >-
  Validate and benchmark AI Skills as first-class artifacts. Use when user
  mentions "test this skill", "check skill quality", "skill lint", "skill
  regression", "benchmark this skill", "验证这个 skill", "测一下这个 skill", or
  asks whether a SKILL.md plus its references and scripts will actually trigger
  and behave correctly. Run a four-layer pyramid: structure lint, trigger eval,
  behavior eval, and optional A/B benchmark.
version: 1.1.0
author: walterfan@ustc.edu
tags:
  - skill-testing
  - evaluation
  - benchmark
  - meta-skill
category: dev-tools
platforms:
  - claude-code
  - codex
  - cursor
visibility: public
license: CC-BY-NC-ND-4.0
metadata:
  author: Walter Fan
  version: "1.1"
---

# lazy-skill-check：给 AI Skill 做体检的 skill

## Contract

- **scope_in**: 单个 skill 目录、两个待对比的 skill 目录，或与 skill 评测相关的层级选择；被测对象是 `SKILL.md` 及其 `references/`、`scripts/`、`assets/` 等配套内容。
- **scope_out**: 普通 LLM API 压测、与 skill 无关的通用代码测试、未提供路径且无法定位目标 skill 的请求。
- **Preconditions**: 用户已提供可读取的目标路径；运行评测所需脚本或适配器可用；若要跑 L4，用户已明确确认成本与范围。
- **Postconditions**: 输出一份分层结论清晰的 skill 测试报告，说明通过/失败状态、关键指标、失败原因与下一步修复建议。

## Execution

### Phase 1: Read target and classify scope
- Entry: 用户提供一个或两个 skill 路径，或明确说要检查某个 skill。
- Steps:
  1. 读取目标 `SKILL.md`，确认 skill 名称、description、references、scripts 和核心工作流。
  2. 判断本次运行包含 L1/L2/L3 哪些层，L4 仅在用户明确要求时启用。
- Exit: 目标路径、测试层级和必要输入都已明确。
- On fail: 如果路径不存在、`SKILL.md` 不可读或目标不是 skill 目录，立即停止并要求用户修正输入。

### Phase 2: Run the evaluation pyramid
- Entry: Phase 1 完成，且目标可访问。
- Steps:
  1. 先跑 L1 结构 lint。
  2. L1 通过后再跑 L2 触发 eval 和 L3 行为 eval。
  3. 仅在显式确认后运行 L4 A/B benchmark。
- Exit: 每一层都有结果、指标和失败分类。
- On fail: L1 失败时不继续高层；L2 或 L3 失败时保留证据并在报告中标记具体失败类型；外部工具缺失时 fall back 到手工分析并说明限制。

### Phase 3: Synthesize the report
- Entry: 已收集各层结果或明确的阻塞原因。
- Steps:
  1. 按统一报告模板汇总 PASS、FAIL、warning、成本和耗时。
  2. 给出最小可执行的修复建议，优先修低层问题。
- Exit: 形成 `skill-test-report.md` 或等价报告输出。
- On fail: 若无法生成完整报告，至少输出已完成层的结果和剩余阻塞项。

## Verification

### Hard gates
- `SKILL.md` 可读取，且目标路径明确。
- 每一层结果都带结论或阻塞原因，不能静默跳过。
- 报告必须包含层级结果、关键失败项和下一步建议。

### Soft gates
- L2 提供 Precision、Recall、F1 或等价判断。
- L3 提供结果断言、路径断言、代价断言中的命中情况。
- L4 提供 v1/v2 对比与是否建议合并的结论。

## Feedback

### Failure modes
- L1 失败：skill 结构或引用有问题，先修 `SKILL.md` 和资源完整性。
- L2 失败：description 触发边界过宽或过窄，需要补 trigger wording 和正负样本。
- L3 失败：工作流、工具调用顺序或 references 信息不足，需要收紧执行步骤。
- L4 波动大：case 太少或 judge 不稳定，需要扩充样本并固定模型版本。

### Improvement triggers
- 新增脚本、adapter 或 agent 后端时，补对应的行为 case。
- description 大改后，重新生成 trigger cases 并回归 L2。
- 报告出现重复误判时，更新 failure modes 和边界样例。

## 你是谁

你是一个专门**测试其他 AI Skill** 的执行者。用户给你一个 skill 目录路径，你按四层金字塔跑完评估，输出一份带结论的报告。

不要重新发明测试方法。照着下面的流程跑。每一层失败的处理方式都不同，严格区分。

## 四层测试金字塔

| 层 | 测什么 | 跑多久 | 失败含义 |
| --- | --- | --- | --- |
| L1 结构 lint | SKILL.md 合法、引用不断、字段齐全 | 秒级 | 低级错误，直接返工 |
| L2 触发 eval | agent 能不能在该用时触发，不该用时不触发 | 分钟级 | description 有问题 |
| L3 行为 eval | 真起一个 agent 跑一遍，看步骤 + 产出 | 分钟级 | 工作流或资源有问题 |
| L4 A/B benchmark | 新旧版本盲评对比 | 小时级 | 改动到底是好是坏 |

## 输入

用户提供下列信息之一：

- **skill 目录路径**：最常见。例如 `./my-skill/` 或绝对路径。
- **两个 skill 目录**：用于 L4 A/B 对比。例如 `v1/my-skill/` vs `v2/my-skill/`。
- **跳过哪些层**：可选。默认跑 L1 + L2 + L3，L4 需要显式要求（因为耗钱）。

如果用户没说清楚要不要跑 L4，问一句：**"要跑完整四层（含 benchmark，约 $0.x）还是只跑前三层？"**

## 工作流

### 步骤 0：读取 skill

先用 `Read` 工具读取 `<skill_dir>/SKILL.md`。拿到：

- 这个 skill 叫什么（`name`）
- description 的原文
- 声明了哪些 references / scripts / assets
- 核心工作流写了什么

如果连 SKILL.md 都读不到，直接报错退出，不要继续。

### 步骤 1：L1 结构 lint（必跑）

运行：

```bash
python3 {{SKILL_DIR}}/scripts/lint.py <target_skill_dir>
```

这个脚本检查：

- YAML frontmatter 能解析
- `name`、`description` 字段非空
- description 长度在合理范围（建议 50-1024 字符）
- 引用的 `references/*.md`、`scripts/*` 文件存在
- 没有 `TODO` / `FIXME` / `XXX` 残留
- 文件编码是 UTF-8，换行是 LF

输出是 JSON：`{"passed": bool, "errors": [...], "warnings": [...]}`。

**如果 L1 fail**：不要继续后面的层。先把 L1 的错误列清楚，让用户修完再来。低级错误在这一层解决成本最低。

### 步骤 2：L2 触发 eval（默认跑）

**前置**：需要一个 `trigger-cases.yaml`。如果 skill 作者没提供，就根据 description 自己生成 10 条（5 正样本 + 5 负样本）。生成时遵循：

- **正样本**：用户说这些话时，agent **应该**触发这个 skill
- **负样本**：用户说这些话时，agent **不应该**触发这个 skill（常见陷阱：同领域但动作不同、关键词相似但意图不同）

样例结构见 `references/trigger-cases-template.yaml`。

运行：

```bash
python3 {{SKILL_DIR}}/scripts/trigger_eval.py \
  --skill <target_skill_dir> \
  --cases <trigger-cases.yaml> \
  --judge-model claude-haiku-4-5
```

这个脚本对每条 prompt 问一个便宜模型："给定 description '...', 用户说 '...'，这个 skill 该不该触发？"然后和 expect 对一下。

看三个指标：

- **Precision（精度）**：触发的里面有多少是对的。低 → description 太宽，误触发。
- **Recall（召回）**：该触发的里面有多少真触发了。低 → description 太窄，漏触发。
- **F1**：综合分。建议阈值 ≥ 0.85。

**如果 L2 fail**：告诉用户 description 有问题，给出具体改进建议（哪些正样本漏了、哪些负样本误触发了）。可以继续 L3，但标记为"触发层有疑问"。

### 步骤 3：L3 行为 eval（默认跑）

**前置**：需要 `behavior-cases/` 目录，每个子文件是一个 YAML case。如果没有，就根据 SKILL.md 里的工作流描述生成 3-5 个。样例见 `references/behavior-case-template.yaml`。

每个 case 包含：

- `prompt`：给 agent 的任务
- `setup`：准备文件（可选，比如给它一个 sample PDF）
- `expect`：期望的最终状态 / 工具调用 / 产出

运行：

```bash
bash {{SKILL_DIR}}/scripts/behavior_run.sh \
  <target_skill_dir> \
  <behavior-cases-dir> \
  <output-dir>
```

这个脚本会对每个 case 起一次 Claude Code headless（`claude --bare -p ... --output-format json --max-turns 10 --max-budget-usd 0.10`），把产出、工具调用序列、token 消耗、耗时全部收集到 `<output-dir>/*.json`。

然后对每个 case 判定：

- **结果断言**：期望的产出文件 / 输出字符串是否正确
- **路径断言**：期望用的工具是否真用了、顺序对不对
- **代价断言**：成本 < 阈值、时长 < 阈值

**如果 L3 fail**：按失败 case 的类型告诉用户问题在哪：
- 结果错 → SKILL.md 的工作流描述有歧义，或 references 缺关键信息
- 路径错 → 工具调用指示不清楚，或顺序没说死
- 代价超 → 任务太重 / SKILL.md 太啰嗦，token 被吃光了

### 步骤 4：L4 A/B benchmark（可选）

**前置**：两个 skill 目录（v1、v2）。

运行：

```bash
python3 {{SKILL_DIR}}/scripts/benchmark.py \
  --v1 <v1_skill_dir> \
  --v2 <v2_skill_dir> \
  --cases <behavior-cases-dir> \
  --repeat 3 \
  --judge-model claude-sonnet-4-5
```

每个 case 对 v1、v2 各跑 `repeat` 次，然后：

- **定量**：对比 pass rate、平均 token、平均耗时、工具调用次数
- **定性**：把 v1、v2 的输出去掉标识后让 judge 模型盲评哪个好

输出是一份 markdown 报告，包括：

- 每个 case 的 v1 vs v2 对比
- 胜率、平均分、显著性提示
- 总结：应该合并 v2 吗？

## 输出：报告格式

把四层结果合成一份 `skill-test-report.md`：

```markdown
# Skill Test Report: <skill_name>

**Tested at**: <timestamp>
**Overall**: PASS / FAIL / PASS with warnings

## L1 Structure Lint
- Errors: ...
- Warnings: ...

## L2 Trigger Eval
- Precision: xx%, Recall: xx%, F1: xx
- Failed cases: ...
- Recommendation: ...

## L3 Behavior Eval
- <N>/<total> cases passed
- Failed: ...
- Avg cost: $x, Avg duration: x.xs

## L4 Benchmark (optional)
- v1 pass rate: xx%, v2 pass rate: xx%
- Judge blind-comparison: v2 won x / y / z (win/loss/tie)
- Verdict: merge / hold / needs more testing

## 综合建议
<3-5 句话，告诉作者下一步该改什么>
```

报告存到 `<target_skill_dir>/../skill-test-reports/<timestamp>.md`。

## 核心原则

1. **低层 fail 不跑高层**。L1 挂了别硬跑 L2，省钱省时间。
2. **所有 agent 子调用都带 `--max-budget-usd`**。不要让 meta skill 自己烧爆账单。
3. **model 版本固定写死在命令里**。用 `claude-sonnet-4-5` 这种具体版本号，不要用 `claude-latest`。
4. **L3 至少跑 3 次取均值**。单次结果不可信。
5. **对 judge 模型用不同厂商或不同 size**。不要让同一个模型既当被测又当判官。
6. **报告要带日期和 model 版本**。没这俩，三个月后回头看等于白跑。

## 不该做的事

- 不要自动合并 v2。最终决策交给人。
- 不要在用户没 confirm 的情况下跑 L4（耗钱）。
- 不要把 `skill-test-reports/` 提交到版本库（建议加到 `.gitignore`）。
- 不要假设被测 skill 一定是 Claude Code 格式，先读 SKILL.md 看它是哪家风格。

## 常用命令速查

统一入口 `lazyskillcheck` 是一个薄调度层，所有子命令也可以直接调底层脚本。

```bash
# 自带单元测试，先跑它确认工具链没坏
python3 scripts/lazyskillcheck.py selftest

# L1：结构 lint
python3 scripts/lazyskillcheck.py lint ./my-skill

# L2：触发评估（默认 claude-haiku；换 openai 判官）
python3 scripts/lazyskillcheck.py trigger ./my-skill \
    --judge-model claude-haiku-4-5
python3 scripts/lazyskillcheck.py trigger ./my-skill \
    --judge-model gpt-4o --judge-vendor openai

# L3：行为评估（切 agent：claude / codex / cursor）
python3 scripts/lazyskillcheck.py behavior ./my-skill --agent claude
python3 scripts/lazyskillcheck.py behavior ./my-skill --agent codex
python3 scripts/lazyskillcheck.py behavior ./my-skill --agent cursor

# L4：A/B benchmark（小心账单）
python3 scripts/lazyskillcheck.py benchmark \
    --v1 ./my-skill-v1 --v2 ./my-skill-v2 \
    --cases ./my-skill/references/behavior \
    --repeat 3

# 跑前三层一条龙（lint → trigger → behavior），behavior 默认 Claude
python3 scripts/lazyskillcheck.py all ./my-skill

# 从 SKILL.md 脚手架出 trigger-cases.yaml + behavior/smoke.yaml
python3 scripts/lazyskillcheck.py gen ./my-skill
```

### 跨 agent 支持

`behavior` 层目前支持三种 agent 后端，自动把各家 headless 输出喂给统一 parser：

| AGENT        | CLI          | 默认调用                                   |
| ------------ | ------------ | ------------------------------------------ |
| `claude`     | `claude`     | `claude --bare -p ... --output-format json` |
| `codex`      | `codex`      | `codex exec --json ...`                    |
| `cursor`     | `cursor-agent` | `cursor-agent -p --output-format json`   |

解析器在 `scripts/agent_runs.py`，按 payload 内容嗅探厂商；也可以用 `--agent` 强制指定。

### 跨厂商 judge

`trigger` 和 `benchmark` 的 judge 模型统一走 `scripts/judge.py`：

- 模型名以 `claude-` / `sonnet` / `haiku` / `opus` 开头 → Anthropic（API 优先，缺 key 时回落 `claude` CLI）
- 模型名以 `gpt-` / `o*` 开头或包含 `codex` → OpenAI（API 优先，缺 key 时回落 `codex exec`）
- 想手动切换，用 `--judge-vendor anthropic|openai` 或 `LAZY_SKILL_CHECK_JUDGE_VENDOR`

建议判官跟被测 skill 不同厂商，避免"自家夸自家"的 position/style bias。

### pytest 适配

已有 pytest 基础设施的项目可以直接复用：

```python
# tests/test_skills.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path("/path/to/lazy-skill-check/scripts")))
from pytest_adapter import register_skill

register_skill(
    skill_dir="skills/my-skill",
    trigger_cases="skills/my-skill/references/trigger-cases.yaml",
    behavior_cases_dir="skills/my-skill/references/behavior",
    runs_dir="tests/.skill-runs/my-skill",
)
```

运行 `pytest` 会得到三组参数化用例：`test_skill_lint` / `test_skill_trigger` / `test_skill_behavior`，完整示例见 `references/pytest-example.md`。

## 参考

- 文章：[给 Cursor、Codex、Claude Code 用的 AI Skill，到底该怎么测](content/journal/journal_20260420_test_ai_skill_for_coding_agents.md)
- 文章：[用 Promptfoo 给 AI skill 做体检](content/journal/journal_20260415_promptfoo_ai_skill_evaluation.md)
- Anthropic skill-creator：<https://github.com/anthropics/skills/tree/main/skills/skill-creator>
- Claude Code Headless：<https://docs.claude.com/en/docs/claude-code/headless>
- Codex Non-interactive：<https://developers.openai.com/codex/noninteractive/>
- Cursor Agent Output Format：<https://cursor.com/docs/cli/reference/output-format>
