#!/usr/bin/env python3
"""
Cron 任务结果推送到钉钉
使用 OpenClaw 钉钉连接器的推送机制
"""

import requests
import json
import os
from pathlib import Path
from datetime import datetime

# 钉钉配置（从环境变量或配置文件读取）
DINGTALK_ACCESS_TOKEN = os.getenv('DINGTALK_ACCESS_TOKEN', '')
DINGTALK_USER_ID = os.getenv('DINGTALK_USER_ID', '01023647151178899')  # 创始人钉钉 ID

def push_markdown(title: str, content: str) -> dict:
    """
    推送 Markdown 消息到钉钉
    """
    if not DINGTALK_ACCESS_TOKEN:
        return {'success': False, 'error': '缺少 DINGTALK_ACCESS_TOKEN'}
    
    # 钉钉机器人 API
    webhook = f"https://oapi.dingtalk.com/robot/send?access_token={DINGTALK_ACCESS_TOKEN}"
    
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content
        },
        "at": {
            "atUserIds": [DINGTALK_USER_ID],
            "isAtAll": False
        }
    }
    
    try:
        response = requests.post(webhook, json=payload, timeout=10)
        result = response.json()
        
        if result.get('errcode') == 0:
            return {'success': True, 'message': '推送成功'}
        else:
            return {'success': False, 'error': result.get('errmsg')}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def push_text(content: str) -> dict:
    """
    推送文本消息到钉钉
    """
    if not DINGTALK_ACCESS_TOKEN:
        return {'success': False, 'error': '缺少 DINGTALK_ACCESS_TOKEN'}
    
    webhook = f"https://oapi.dingtalk.com/robot/send?access_token={DINGTALK_ACCESS_TOKEN}"
    
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
    
    try:
        response = requests.post(webhook, json=payload, timeout=10)
        result = response.json()
        
        if result.get('errcode') == 0:
            return {'success': True, 'message': '推送成功'}
        else:
            return {'success': False, 'error': result.get('errmsg')}
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    # 测试推送
    result = push_markdown(
        "测试消息",
        f"# 🦀 AI 价值投资系统\n\n**测试时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n这是一条测试推送消息"
    )
    print(f"推送结果：{result}")
