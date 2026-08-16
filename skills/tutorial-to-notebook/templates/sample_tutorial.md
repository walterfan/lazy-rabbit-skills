Title: Speech-to-Text 快速上手
Category: Tech
Tags: tutorial, api

# 给应用加一个"语音转文字"功能

本教程带你把转写服务接进自己的后端：上传一段音频，拿回文字。

## 第 1 步：初始化

先准备好 client。令牌通过 OAuth2 授权注入，别写死在代码里。

```python
import os, requests

BASE = "https://api.example-speech.com/v1"
headers = {"Authorization": f"Bearer {os.environ['SPEECH_TOKEN']}"}
```

## 第 2 步：上传音频

上传一段音频，服务返回一个任务号。

```python
with open("sample-zh.wav", "rb") as f:
    r = requests.post(f"{BASE}/transcriptions",
                      headers=headers,
                      files={"audio": f},
                      data={"language": "zh"})
r.raise_for_status()
job_id = r.json()["job_id"]
print(job_id)
```

上传成功后大致返回：

```json
{ "job_id": "job_7c3e1a", "status": "queued" }
```

## 第 3 步：取回结果

转写是异步的，需要轮询直到完成。

```python
import time
while True:
    result = requests.get(f"{BASE}/transcriptions/{job_id}", headers=headers).json()
    if result["status"] == "done":
        break
    time.sleep(2)
print(result["text"])
```

到这里，你已经把整条链路跑通了。
