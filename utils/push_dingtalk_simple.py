#!/usr/bin/env python3
"""
钉钉推送 - 最简单的方式
使用钉钉开放平台的 sessionWebhook
"""

import requests
import json
import hmac
import hashlib
import base64
import urllib.parse
import time

# 钉钉配置
CLIENT_ID = "dinggmk7kpiddrrvi0l5"
CLIENT_SECRET = "9RR-37dNLUKRkzzS-1RN5CHsDSJnIKEtBCd3-O9MqB7SvYUduBwse8FhEtMnr2bN"
USER_ID = "01023647151178899"

def push(content: str, title: str = "AI 价值投资系统") -> dict:
    """推送 Markdown 消息到钉钉"""
    try:
        # 方法：使用钉钉内部机器人的 sessionWebhook
        # 格式：https://api.dingtalk.com/robot/send?session=xxx
        
        # 1. 获取 session webhook
        # 需要通过 Gateway 获取，或者使用已知的 session
        
        # 2. 直接发送
        # 使用钉钉的机器人 API
        timestamp = str(round(time.time() * 1000))
        secret = CLIENT_SECRET
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        # 机器人 webhook（需要配置）
        webhook = f"https://oapi.dingtalk.com/robot/send?access_token={CLIENT_SECRET}&timestamp={timestamp}&sign={sign}"
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content
            },
            "at": {
                "atUserIds": [USER_ID],
                "isAtAll": False
            }
        }
        
        resp = requests.post(webhook, json=payload, timeout=10)
        result = resp.json()
        
        if result.get('errcode') == 0:
            return {'success': True, 'message': '推送成功'}
        else:
            return {'success': False, 'error': result.get('errmsg')}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    result = push("# 测试\n\n这是一条测试消息")
    print(f"推送结果：{result}")
