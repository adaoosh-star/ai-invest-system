"""
预警通知系统
投资宪法：只推送🟠橙色及以上预警，避免用户疲劳
"""

import requests
import yaml
from pathlib import Path
from datetime import datetime

# 加载配置
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'thresholds.yaml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 钉钉机器人配置（从环境变量或配置文件读取）
DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"

def send_dingtalk_alert(alert: dict) -> dict:
    """
    发送钉钉预警消息
    只推送🟠橙色及以上预警
    """
    # 过滤：只推送橙色及以上
    if alert['level'] not in ['🔴 红色', '🟠 橙色']:
        return {
            'success': False,
            'reason': '预警级别低于橙色，不推送',
        }
    
    # 构建消息
    title = f"{alert['level']} {alert['type']}预警"
    content = f"""## {title}

**股票：** {alert['ts_code']}
**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**详情：** {alert['message']}
**行动：** {alert['action']}

---
*AI 价值投资系统 | 投资宪法原则*"""
    
    # 钉钉消息格式
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
    
    # 发送
    try:
        response = requests.post(DINGTALK_WEBHOOK, json=payload, timeout=10)
        result = response.json()
        
        if result.get('errcode') == 0:
            return {
                'success': True,
                'message': '预警发送成功',
            }
        else:
            return {
                'success': False,
                'reason': f"钉钉 API 错误：{result.get('errmsg')}",
            }
    except Exception as e:
        return {
            'success': False,
            'reason': f"发送失败：{e}",
        }

def send_portfolio_alerts(monitor_result: dict) -> dict:
    """
    批量发送持仓预警
    """
    results = []
    
    for alert in monitor_result['alerts']:
        # 只推送橙色及以上
        if alert['level'] in ['🔴 红色', '🟠 橙色']:
            result = send_dingtalk_alert(alert)
            results.append({
                'alert': alert,
                'send_result': result,
            })
    
    return {
        'timestamp': datetime.now().isoformat(),
        'total_alerts': len(monitor_result['alerts']),
        'sent_count': len(results),
        'results': results,
    }

# 测试
if __name__ == '__main__':
    print("=== 预警通知系统测试 ===\n")
    
    # 模拟预警
    test_alerts = [
        {
            'ts_code': '002270.SZ',
            'level': '🟠 橙色',
            'type': '估值过高',
            'message': '002270.SZ PE 分位 94% > 90%，考虑减仓',
            'action': '考虑减仓',
        },
        {
            'ts_code': '000001.SZ',
            'level': '🔴 红色',
            'type': '现金流恶化',
            'message': '000001.SZ 现金流/净利润 0.40 < 0.5，查应收账款',
            'action': '查应收账款',
        },
        {
            'ts_code': '600519.SH',
            'level': '⚠️ 黄色',
            'type': 'ROE 下滑',
            'message': '600519.SH ROE 下降 4% > 3%，关注',
            'action': '关注',
        },
    ]
    
    print("测试预警：")
    for alert in test_alerts:
        print(f"  {alert['level']} {alert['type']}: {alert['message']}")
    print()
    
    # 模拟发送（注释掉实际发送，避免骚扰）
    print("发送结果（模拟）：")
    for alert in test_alerts:
        if alert['level'] in ['🔴 红色', '🟠 橙色']:
            print(f"  ✅ {alert['ts_code']} {alert['level']} 预警已发送")
        else:
            print(f"  ⏭️ {alert['ts_code']} {alert['level']} 预警跳过（级别低于橙色）")
    
    print("\n✅ 预警通知系统测试完成")
    print("\n注意：实际使用需配置钉钉机器人 Webhook")
