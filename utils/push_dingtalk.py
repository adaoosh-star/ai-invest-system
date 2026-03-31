#!/usr/bin/env python3
"""
钉钉推送 - 使用钉钉开放平台 API
"""

import requests
import json
import time

# 钉钉配置
CLIENT_ID = "dinggmk7kpiddrrvi0l5"
CLIENT_SECRET = "9RR-37dNLUKRkzzS-1RN5CHsDSJnIKEtBCd3-O9MqB7SvYUduBwse8FhEtMnr2bN"
USER_ID = "01023647151178899"

def push(content: str, title: str = "AI 价值投资系统") -> dict:
    """推送 Markdown 消息到钉钉"""
    try:
        # 1. 获取 access token
        token_url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
        token_resp = requests.post(token_url, json={
            "appKey": CLIENT_ID,
            "appSecret": CLIENT_SECRET
        }, timeout=10)
        
        token_result = token_resp.json()
        access_token = token_result.get('accessToken')
        
        if not access_token:
            return {'success': False, 'error': f"获取 token 失败：{token_result}"}
        
        # 2. 获取用户 userid（通过 UnionID 或手机号）
        # 这里直接使用已知的 userid
        
        # 3. 发送消息
        msg_url = "https://api.dingtalk.com/v1.0/robot/message/send"
        headers = {
            "x-acs-dingtalk-access-token": access_token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "agentId": "",  # 机器人 agentId，需要配置
            "userId": USER_ID,
            "msgKey": "sampleMarkdown",
            "msgParam": json.dumps({
                "title": title,
                "text": content
            })
        }
        
        msg_resp = requests.post(msg_url, json=payload, headers=headers, timeout=10)
        result = msg_resp.json()
        
        if result.get('code') == 'Success':
            return {'success': True, 'message': '推送成功'}
        else:
            return {'success': False, 'error': result.get('msg')}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    result = push("# 测试\n\n这是一条测试消息")
    print(f"推送结果：{result}")
