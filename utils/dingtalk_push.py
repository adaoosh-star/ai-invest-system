#!/usr/bin/env python3
"""
钉钉推送模块
用于将 Cron 任务结果推送到钉钉
"""

import requests
import json
from pathlib import Path
from datetime import datetime

# 钉钉机器人配置
DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"

def push_markdown(title: str, content: str) -> dict:
    """
    推送 Markdown 消息到钉钉
    
    参数：
    - title: 消息标题
    - content: Markdown 内容
    
    返回：
    - 推送结果
    """
    # 钉钉 Markdown 消息格式
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content
        },
        "at": {
            "isAtAll": True  # @所有人
        }
    }
    
    try:
        response = requests.post(DINGTALK_WEBHOOK, json=payload, timeout=10)
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
    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        },
        "at": {
            "isAtAll": False
        }
    }
    
    try:
        response = requests.post(DINGTALK_WEBHOOK, json=payload, timeout=10)
        result = response.json()
        
        if result.get('errcode') == 0:
            return {'success': True, 'message': '推送成功'}
        else:
            return {'success': False, 'error': result.get('errmsg')}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# 测试
if __name__ == '__main__':
    print("=== 钉钉推送测试 ===\n")
    
    # 测试 Markdown 推送
    result = push_markdown(
        "测试消息",
        "# 🦀 AI 价值投资系统\n\n**测试时间：** {}\n\n这是一条测试消息".format(
            datetime.now().strftime('%Y-%m-%d %H:%M')
        )
    )
    
    print(f"推送结果：{result}")
