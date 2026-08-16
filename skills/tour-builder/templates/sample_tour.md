# Tour: API Console 上手

## 打开 API Keys 页面
target: nav-api-keys
side: right
左侧这一栏管理你的凭证。第一次来，先到这里看看有没有可用的 key。

## 新建一个 API Key
target: btn-create-key
side: bottom
action: click
点这里创建。给它起个能看懂的名字、勾上最小够用的权限范围。密钥只显示一次，创建后立刻复制保存。

## 在沙箱里试一次调用
target: panel-sandbox
side: left
把刚才的 key 填进沙箱，点“运行”，看第一条 golden path 请求是否成功返回。失败也没关系，右侧的 AI 助教会告诉你哪一步错了。

## 撤销泄露的 Key
target: btn-revoke
side: left
action: click
destructive: true
如果 key 不小心泄露了，在这里撤销。撤销立即生效且不可恢复，操作前先确认 key id。
