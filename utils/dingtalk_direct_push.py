#!/usr/bin/env python3
"""
直接调用钉钉 API 推送消息
使用钉钉开放平台的内部 API
"""

import requests
import json
import hmac
import hashlib
import base64
import urllib.parse
import time
from pathlib import Path

# 钉钉配置
CLIENT_ID = "dinggmk7kpiddrrvi0l5"
CLIENT_SECRET = "9RR-37dNLUKRkzzS-1RN5CHsDSJnIKEtBCd3-O9MqB7SvYUduBwse8FhEtMnr2bN"
GATEWAY_TOKEN = "7c945e183e33b18df341e2c3ad9ced59e0a7f156d7d20238"

# 创始人钉钉 ID
USER_ID = "01023647151178899"

def get_access_token():
    """获取钉钉 access token"""
    url = "https://api.dingtalk.com/v2.0/oauth2/accessToken"
    payload = {
        "appKey": CLIENT_ID,
        "appSecret": CLIENT_SECRET
    }
    resp = requests.post(url, json=payload, timeout=10)
    result = resp.json()
    if result.get('code') == 'InvalidParameter':
        # 可能是配置问题，返回 None
        return None
    return result.get('accessToken')

def push_markdown(content: str, title: str = "AI 价值投资系统") -> dict:
    """
    推送 Markdown 消息到钉钉
    """
    try:
        # 方法 1: 使用钉钉开放平台 API
        access_token = get_access_token()
        
        if access_token:
            # 发送单聊消息
            url = "https://api.dingtalk.com/v2.0/robot/message/send"
            headers = {
                "x-acs-dingtalk-access-token": access_token,
                "Content-Type": "application/json"
            }
            payload = {
                "agentId": "",  # 需要机器人 agentId
                "userId": USER_ID,
                "msgKey": "sampleMarkdown",
                "msgParam": json.dumps({
                    "title": title,
                    "text": content
                })
            }
            
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            result = resp.json()
            
            if result.get('code') == 'Success':
                return {'success': True, 'message': '推送成功'}
            else:
                return {'success': False, 'error': result.get('msg')}
        
        return {'success': False, 'error': '无法获取 access token'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    # 测试
    content = "# 测试\n\n这是一条测试消息"
    result = push_markdown(content)
    print(f"推送结果：{result}")
