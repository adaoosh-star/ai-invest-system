#!/usr/bin/env python3
"""
直接推送钉钉消息 - 无需配置
使用钉钉开放平台 API
"""

import requests
import json

# 钉钉机器人 Webhook（需要您提供）
WEBHOOK = ""

def push(content):
    """推送 Markdown 消息"""
    if not WEBHOOK:
        print(f"⚠️ 未配置 Webhook，消息内容:\n{content}")
        return
    
    payload = {
        "msgtype": "markdown",
        "markdown": {"title": "AI 价值投资系统", "text": content},
        "at": {"isAtAll": True}
    }
    
    r = requests.post(WEBHOOK, json=payload, timeout=10)
    print(f"推送结果：{r.json()}")

if __name__ == '__main__':
    push("# 测试\n\n这是一条测试消息")
