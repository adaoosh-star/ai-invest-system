#!/usr/bin/env python3
"""测试 Gateway 推送 API"""

import requests
import json

GATEWAY_URL = "http://127.0.0.1:18789"
TOKEN = "7c945e183e33b18df341e2c3ad9ced59e0a7f156d7d20238"

# 测试不同的 API 端点
endpoints = [
    "/api/gateway/call",
    "/gateway/call",
    "/rpc",
    "/api/rpc",
    "/api/plugins/dingtalk-connector/call",
    "/plugins/dingtalk-connector/call",
]

payload = {
    "method": "dingtalk-connector.sendToUser",
    "params": {
        "userId": "01023647151178899",
        "content": "# 测试\n\n这是一条测试消息",
        "msgType": "markdown"
    }
}

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

for endpoint in endpoints:
    url = f"{GATEWAY_URL}{endpoint}"
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        print(f"{endpoint}: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        print(f"{endpoint}: ERROR - {e}")
