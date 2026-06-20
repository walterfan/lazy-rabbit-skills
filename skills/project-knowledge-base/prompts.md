# PKB Prompt Collection / PKB 预设提示词集合

A curated set of prompts for guiding AI to understand projects and complete development tasks. Use these with `/PKB-feed-ai` or directly in your AI assistant.

这个文件包含了一系列精心设计的提示词，用于引导 AI 理解项目和完成开发任务。

## Round 1: Project Onboarding / 第一轮：项目 Onboarding

### Foundational Understanding / 基础理解

> Feed the AI the project's Overview, Repo Map, and Architecture docs, then ask it to summarize, identify gaps, and propose a starter task.

```markdown
你将作为本项目的资深工程师。下面是项目的 Overview、Repo Map 和 Architecture 文档。

任务：
1) 用 1 页总结系统的组件、入口点和关键数据流。
2) 列出你还缺少的 10 个关键信息（按优先级排序）。
3) 提出一个你认为最适合作为"第一个上手改动"的小任务（包含测试）。

请逐项完成，每项都要具体、可验证。
```

### Architecture Validation / 架构验证

> Ask the AI to identify architectural patterns, draw dependency graphs, spot risks, and suggest improvements.

```markdown
基于提供的架构文档和代码仓库，请：

1) 识别主要的架构模式（如分层架构、微服务、事件驱动等）
2) 绘制关键组件的依赖关系图
3) 指出可能的架构风险或反模式
4) 建议 3 个可以改进的地方

请提供具体的文件路径和代码片段作为依据。
```

### Tech Stack Assessment / 技术栈评估

> Evaluate the project's technology choices: strengths, weaknesses, tech debt, and upgrade candidates.

```markdown
分析项目的技术栈选型：

1) 列出使用的主要技术和框架
2) 评估每个技术选择的优劣势
3) 识别可能的技术债
4) 建议需要升级或替换的技术

重点关注：性能、安全性、可维护性。
```

## Round 2: Deep-Dive into Business Flows / 第二轮：深入业务链路

### Flow Analysis / 流程分析

> Trace a complete call chain for a named workflow, marking transaction boundaries, idempotency points, retry logic, and async handoffs.

```markdown
下面是"[流程名称]"的流程说明和相关代码文件。

任务：
1) 画出完整的调用链（函数/模块级别），并标注：
   - 事务边界
   - 幂等点
   - 重试点
   - 异步处理点

2) 识别 5 个最可能出 bug 的边界条件，并说明原因。

3) 提供完整的测试清单：
   - 单元测试：应该测什么
   - 集成测试：应该测什么
   - E2E 测试：应该测什么

每项测试都要说明测试目标和预期结果。
```

### Data Flow Tracing / 数据流追踪

> Track data from ingestion to storage: entry points, transformations, persistence, and query paths.

```markdown
追踪数据从入口到存储的完整流程：

1) 数据如何进入系统（API/消息/事件）
2) 数据经过哪些转换和验证
3) 数据如何持久化（数据库/缓存/文件）
4) 数据如何被查询和展示

请绘制数据流图，并标注每个环节的：
- 数据格式（JSON/XML/Proto）
- 验证规则
- 转换逻辑
- 错误处理
```

### Failure Scenario Analysis / 异常场景分析

> Enumerate all failure points for a feature: current error handling, retry behavior, user-facing errors, and logging/alerting gaps.

```markdown
针对"[功能名称]"，分析所有可能的异常场景：

1) 列出所有可能的失败点
2) 对每个失败点：
   - 当前的错误处理逻辑
   - 是否有重试机制
   - 用户会看到什么错误信息
   - 是否有日志/告警

3) 识别缺失的错误处理
4) 建议改进方案

重点关注：用户体验、可恢复性、可观测性。
```

## Round 3: Module Acceptance / 第三轮：模块验收

### Module Comprehension Check / 模块理解验证

> Test the AI's understanding of a module: summarize responsibilities, list APIs, assess coupling, suggest improvements, and propose a small PR-level change.

```markdown
模块：[模块名称]

提供的材料：
- 模块职责说明
- API 文档
- 依赖关系
- 代码示例
- 测试用例

任务：
1) 用自己的话总结这个模块的职责和边界
2) 列出这个模块提供的主要 API 及其用途
3) 识别模块的依赖，并评估耦合度
4) 提出 3 个改进建议
5) 完成一个小改动（PR 级别，包含测试）

要求：改动要小、可测试、有明确的验收标准。
```

### Code Quality Assessment / 代码质量评估

> Evaluate code structure, naming, error handling, and test coverage for a specific module.

```markdown
评估"[模块名称]"的代码质量：

1) 代码结构
   - 是否遵循单一职责原则
   - 是否有明确的分层
   - 是否易于测试

2) 命名和可读性
   - 命名是否清晰
   - 是否需要注释才能理解
   - 是否有冗余代码

3) 错误处理
   - 是否有完整的错误处理
   - 错误信息是否清晰
   - 是否有日志记录

4) 测试覆盖
   - 单元测试覆盖率
   - 是否有集成测试
   - 测试质量如何

给出具体的改进建议和示例代码。
```

### Refactoring Suggestions / 重构建议

> Identify code smells in a module, propose refactoring plans with priority/cost/risk, and provide a small worked example.

```markdown
针对"[模块/文件]"，提供重构建议：

1) 识别代码异味
   - 过长的函数
   - 重复的代码
   - 复杂的条件逻辑
   - 过度的依赖

2) 提出重构方案
   - 优先级排序
   - 预期收益
   - 实施成本
   - 风险评估

3) 给出一个小重构的完整示例
   - 重构前的代码
   - 重构后的代码
   - 测试用例
   - 改进说明

要求：重构要保持功能不变，且要有测试保护。
```

## Development Tasks / 开发任务

### Implement a Requirement / 接需求

> Plan a feature implementation: design, impact analysis, execution plan, risk mitigation, and PR breakdown.

```markdown
需求：[需求描述]

验收标准：
- 标准 1
- 标准 2
- 标准 3

约束条件：
- 约束 1
- 约束 2

请按以下步骤输出：

1) 设计方案
   - 技术选型
   - 架构设计
   - 数据模型

2) 影响面分析
   - 受影响的模块
   - 需要修改的接口
   - 兼容性考虑

3) 实施计划
   - 需要改哪些文件
   - 每个文件改什么
   - 需要补哪些测试

4) 风险与回滚
   - 可能的风险点
   - 如何降低风险
   - 回滚方案

5) PR 计划
   - 分成 2-3 个提交
   - 每个提交包含什么
   - 提交顺序和原因

要求：设计要具体、可实施、可验证。
```

### Fix a Bug / 修复 Bug

> Root-cause analysis, fix proposal, test plan, and prevention measures for a reported bug.

```markdown
Bug 描述：[Bug 描述]

复现步骤：
1. 步骤 1
2. 步骤 2
3. 步骤 3

预期行为：[预期]
实际行为：[实际]

请完成：

1) 根因分析
   - 定位问题代码
   - 分析产生原因
   - 是否有类似问题

2) 修复方案
   - 方案描述
   - 代码改动
   - 影响评估

3) 测试计划
   - 如何验证修复
   - 需要补充的测试
   - 回归测试范围

4) 预防措施
   - 如何避免类似问题
   - 需要添加的检查
   - 文档/规范更新

要求：修复要彻底，不留隐患。
```

### Performance Optimization / 性能优化

> Profile a performance issue, propose ranked optimization strategies, and define monitoring/alerting for the fix.

```markdown
性能问题：[问题描述]

当前指标：
- 指标 1: [当前值]
- 指标 2: [当前值]

目标指标：
- 指标 1: [目标值]
- 指标 2: [目标值]

请完成：

1) 性能分析
   - 使用什么工具分析
   - 发现的瓶颈
   - 量化的数据

2) 优化方案
   - 方案 1：[描述、预期收益、实施难度]
   - 方案 2：[描述、预期收益、实施难度]
   - 方案 3：[描述、预期收益、实施难度]
   - 推荐方案及理由

3) 实施计划
   - 具体改动
   - 验证方法
   - 回滚方案

4) 监控告警
   - 需要监控的指标
   - 告警阈值
   - 如何响应

要求：优化要有数据支撑，可衡量。
```

## Code Review / 代码审查

### Comprehensive Review / 全面 Review

> Full code review covering correctness, quality, architecture, security, performance, and test coverage.

```markdown
请对以下代码进行全面的 Code Review：

[代码或 PR 链接]

Review 维度：

1) 功能正确性
   - 是否实现了需求
   - 是否有边界条件问题
   - 是否有潜在 bug

2) 代码质量
   - 可读性
   - 可维护性
   - 是否遵循规范

3) 架构设计
   - 是否合理
   - 是否符合现有架构
   - 是否有更好的方案

4) 安全性
   - 是否有安全漏洞
   - 输入验证是否充分
   - 敏感信息处理是否正确

5) 性能
   - 是否有性能问题
   - 是否需要优化
   - 是否需要性能测试

6) 测试
   - 测试覆盖是否充分
   - 测试用例是否合理
   - 是否需要补充测试

对每个问题给出：
- 严重程度（Blocker/Major/Minor）
- 具体位置
- 改进建议
- 示例代码（如果适用）
```

### Security Review / 安全 Review

> Security-focused audit: input validation, auth, data protection, error leakage, and dependency vulnerabilities.

```markdown
针对以下代码进行安全审查：

[代码或 PR 链接]

重点检查：

1) 输入验证
   - 是否验证所有外部输入
   - 验证逻辑是否充分
   - 是否有注入风险

2) 认证授权
   - 认证是否正确实施
   - 授权检查是否完整
   - 会话管理是否安全

3) 数据保护
   - 敏感数据是否加密
   - 密钥管理是否安全
   - 日志是否泄露敏感信息

4) 错误处理
   - 错误信息是否泄露敏感信息
   - 是否有异常未捕获
   - 失败是否安全

5) 依赖安全
   - 使用的库是否有已知漏洞
   - 版本是否最新
   - 是否有不必要的依赖

对每个安全问题给出：
- 风险等级（高/中/低）
- 具体描述
- 修复建议
- 参考资料（如 OWASP）
```

## Documentation Generation / 文档生成

### API Documentation / API 文档

> Generate complete API documentation: overview, request/response specs, examples, and usage notes.

```markdown
为以下 API 生成完整的文档：

[API 代码或路径]

文档应包含：

1) API 概述
   - 功能描述
   - 使用场景
   - 前置条件

2) 请求规范
   - HTTP 方法和路径
   - 请求头
   - 请求参数（路径/查询/请求体）
   - 参数验证规则

3) 响应规范
   - 成功响应（状态码、格式、字段说明）
   - 错误响应（可能的错误码、错误信息）

4) 示例
   - 请求示例（curl）
   - 成功响应示例
   - 错误响应示例

5) 注意事项
   - 速率限制
   - 权限要求
   - 最佳实践

格式：OpenAPI 3.0 或 Markdown
```

### Operations Runbook / 运维文档

> Generate an operations runbook: deployment guide, monitoring, troubleshooting, incident response, and maintenance tasks.

```markdown
生成"[功能/服务]"的运维文档：

1) 部署指南
   - 环境要求
   - 部署步骤
   - 配置说明
   - 验证方法

2) 监控指标
   - 关键指标列表
   - 正常值范围
   - 告警阈值
   - 查看方法

3) 常见问题
   - 问题描述
   - 可能原因
   - 诊断方法
   - 解决步骤

4) 应急响应
   - 常见故障场景
   - 应急处理流程
   - 回滚步骤
   - 联系方式

5) 维护任务
   - 日常检查项
   - 定期维护任务
   - 数据备份策略
   - 清理策略

格式：Markdown，包含可执行的命令
```

## Testing / 测试相关

### Test Case Design / 测试用例设计

> Design comprehensive test cases: normal scenarios, edge cases, performance, and security tests.

```markdown
为"[功能名称]"设计完整的测试用例：

功能描述：[描述]
输入：[输入说明]
输出：[输出说明]

请设计：

1) 正常场景测试
   - 典型用例
   - 边界值测试
   - 等价类划分

2) 异常场景测试
   - 无效输入
   - 缺失必填项
   - 格式错误

3) 性能测试
   - 正常负载
   - 高负载
   - 并发场景

4) 安全测试
   - 注入攻击
   - 权限检查
   - 敏感数据保护

对每个测试用例给出：
- 测试用例 ID
- 前置条件
- 测试步骤
- 预期结果
- 优先级
```

### Test Code Generation / 测试代码生成

> Generate unit tests for a function or module with proper mocking, assertions, and data coverage.

```markdown
为以下函数/模块生成测试代码：

[代码]

要求：

1) 单元测试
   - 覆盖所有公开方法
   - 测试正常路径
   - 测试边界条件
   - 测试异常情况

2) 测试数据
   - 使用有意义的测试数据
   - 包含边界值
   - 包含异常值

3) Mock/Stub
   - 合理使用 mock
   - 隔离外部依赖
   - 避免脆弱的测试

4) 断言
   - 清晰的断言
   - 完整的验证
   - 有意义的错误信息

测试框架：[指定框架，如 pytest, JUnit, Jest]
风格：[指定风格，如 AAA, BDD]
```

## Summary Reports / 总结报告

### Project Analysis Report / 项目分析报告

> Generate a comprehensive project analysis: executive summary, code quality, architecture, performance, security, testing, and action plan.

```markdown
生成项目"[项目名称]"的全面分析报告：

1) 执行摘要
   - 项目概况
   - 主要发现
   - 关键建议

2) 项目概览
   - 技术栈
   - 架构模式
   - 团队规模

3) 代码质量分析
   - 代码规模统计
   - 代码质量指标
   - 技术债识别

4) 架构评估
   - 架构模式分析
   - 模块耦合度
   - 改进建议

5) 性能评估
   - 性能瓶颈
   - 资源使用
   - 优化建议

6) 安全评估
   - 安全风险
   - 合规性检查
   - 修复建议

7) 测试覆盖
   - 测试覆盖率
   - 测试质量
   - 改进建议

8) 行动计划
   - 优先级排序
   - 实施路线图
   - 资源需求

格式：Markdown，包含图表
```

---

## Usage Tips / 使用建议

1. **Pick the right prompt**: Choose the template that matches your specific task.
2. **Provide full context**: Feed the relevant PKB docs and code alongside the prompt.
3. **Verify AI output**: Always validate the AI's understanding and generated content.
4. **Iterate**: Refine docs and code incrementally based on AI feedback.
5. **Keep fresh**: Update prompts and docs as the project evolves.

## Advanced Tips / 进阶技巧

1. **Combine prompts**: Chain multiple prompts into a complete workflow.
2. **Customize**: Adjust prompt content and focus for your project's specifics.
3. **Build a library**: Save frequently used prompts as team templates.
4. **Improve continuously**: Refine prompts based on real usage effectiveness.

---

**Version**: 1.1
**Author**: Walter Fan (walterfan@ustc.edu)
**Last Updated**: 2026-04-14
