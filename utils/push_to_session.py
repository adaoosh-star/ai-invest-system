#!/usr/bin/env python3
"""
通过 OpenClaw Gateway 推送消息到当前钉钉会话
"""

import requests
import json
from pathlib import Path
from datetime import datetime

# OpenClaw Gateway 配置
GATEWAY_URL = "http://127.0.0.1:18789"
GATEWAY_TOKEN = "7c945e183e33b18df341e2c3ad9ced59e0a7f156d7d20238"

# 钉钉配置
DINGTALK_USER_ID = "01023647151178899"  # 创始人钉钉 ID

def push_to_dingtalk_session(content: str, title: str = None) -> dict:
    """
    通过 OpenClaw Gateway 推送消息到钉钉会话
    
    使用钉钉连接器的主动消息 API
    """
    try:
        # 构建钉钉主动消息请求
        # 参考：/home/admin/.openclaw/extensions/dingtalk-connector/src/services/messaging.ts
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title or "AI 价值投资系统",
                "text": content
            },
            "at": {
                "atUserIds": [DINGTALK_USER_ID],
                "isAtAll": False
            }
        }
        
        # 使用 Gateway 的钉钉连接器 API
        # 需要调用 dingtalk-connector 的 sendProactive 方法
        url = f"{GATEWAY_URL}/api/plugins/dingtalk-connector/send"
        
        headers = {
            "Authorization": f"Bearer {GATEWAY_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return {'success': True, 'message': '推送成功', 'result': result}
        else:
            return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def push_text_to_session(content: str) -> dict:
    """
    推送文本消息到钉钉会话
    """
    try:
        payload = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "atUserIds": [DINGTALK_USER_ID],
                "isAtAll": False
            }
        }
        
        url = f"{GATEWAY_URL}/api/plugins/dingtalk-connector/send"
        headers = {
            "Authorization": f"Bearer {GATEWAY_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return {'success': True, 'message': '推送成功', 'result': result}
        else:
            return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    # 测试推送
    test_content = f"""# 🦀 AI 价值投资系统 - 推送测试

**测试时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}

这是一条测试消息，验证 Cron 任务能否推送到钉钉。
"""
    
    result = push_to_dingtalk_session(test_content, "推送测试")
    print(f"推送结果：{result}")
