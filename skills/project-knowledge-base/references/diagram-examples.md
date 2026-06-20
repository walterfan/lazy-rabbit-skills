# PKB 图表示例速查

## 架构图

### 系统架构
```mermaid
graph TB
    Client[客户端] --> API[API 网关]
    API --> Service1[服务 1]
    API --> Service2[服务 2]
    Service1 --> DB[(数据库)]
    Service2 --> DB
```

### 时序图
```mermaid
sequenceDiagram
    用户->>系统: 登录请求
    系统->>数据库: 验证凭证
    数据库-->>系统: 用户信息
    系统-->>用户: 访问令牌
```

### 状态图
```mermaid
stateDiagram-v2
    [*] --> 草稿
    草稿 --> 待审核: 提交
    待审核 --> 已批准: 批准
    待审核 --> 已拒绝: 拒绝
    已批准 --> [*]
    已拒绝 --> [*]
```

### 类图
```mermaid
classDiagram
    class 用户 {
        +字符串 ID
        +字符串 邮箱
        +登录()
        +登出()
    }
    class 订单 {
        +字符串 ID
        +日期 创建时间
        +提交()
    }
    用户 "1" --> "*" 订单: 创建
```

## 快速参考

| 图表类型 | 关键字 | 用途 |
|---------|-------|------|
| 流程图 | `flowchart` | 流程、决策 |
| 时序图 | `sequenceDiagram` | API 调用、交互 |
| 状态图 | `stateDiagram-v2` | 状态转换 |
| 类图 | `classDiagram` | 类关系、继承 |
| ER 图 | `erDiagram` | 数据模型 |
| 甘特图 | `gantt` | 项目计划 |

更多示例参见 [diagrams-guide.md](templates/docs/diagrams-guide.md)
