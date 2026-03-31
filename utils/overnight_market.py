#!/usr/bin/env python3
"""
隔夜市场数据获取 - 多数据源冗余设计

数据源优先级：
1. 美股：CNBC（稳定）
2. 中概股：CNBC
3. A50 期货：待补充
4. 人民币汇率：XE.com
"""

import requests
import re
import time
from typing import Dict, Optional

def get_us_markets_from_cnbc() -> dict:
    """
    从 CNBC 获取美股三大指数
    """
    urls = {
        'dow': 'https://www.cnbc.com/quotes/.DJI',
        'nasdaq': 'https://www.cnbc.com/quotes/.IXIC',
        'sp500': 'https://www.cnbc.com/quotes/.SPX',
    }
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    result = {}
    
    for name, url in urls.items():
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                text = resp.text
                price_match = re.search(r'"last"\s*:\s*"([\d,\.]+)"', text)
                change_match = re.search(r'"change"\s*:\s*"([+-][\d,\.]+)"', text)
                
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))
                    if change_match:
                        change = float(change_match.group(1).replace(',', ''))
                        prev_close = price - change
                        change_pct = (change / prev_close) * 100 if prev_close > 0 else 0
                    else:
                        change_pct = 0
                    
                    result[name] = {
                        'current': price,
                        'change': change_pct,
                        'comment': '上涨' if change_pct > 0.5 else '下跌' if change_pct < -0.5 else '震荡'
                    }
                else:
                    result[name] = {'current': 0, 'change': 0, 'comment': '解析失败'}
            else:
                result[name] = {'current': 0, 'change': 0, 'comment': f'HTTP {resp.status_code}'}
        except Exception as e:
            result[name] = {'current': 0, 'change': 0, 'comment': f'错误：{str(e)[:30]}'}
    
    return result


def get_china_adr() -> dict:
    """
    获取中概股表现（纳斯达克中国金龙指数 HXC）
    数据源：CNBC
    """
    url = 'https://www.cnbc.com/quotes/HXC'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            text = resp.text
            price_match = re.search(r'"last"\s*:\s*"([\d,\.]+)"', text)
            change_match = re.search(r'"change"\s*:\s*"([+-][\d,\.]+)"', text)
            
            if price_match:
                price = float(price_match.group(1).replace(',', ''))
                if change_match:
                    change = float(change_match.group(1).replace(',', ''))
                    prev_close = price - change
                    change_pct = (change / prev_close) * 100 if prev_close > 0 else 0
                else:
                    change_pct = 0
                
                return {
                    'current': price,
                    'change': change_pct,
                    'comment': '上涨' if change_pct > 1 else '下跌' if change_pct < -1 else '震荡'
                }
        
        return {'current': 0, 'change': 0, 'comment': '数据获取失败'}
    except Exception as e:
        return {'current': 0, 'change': 0, 'comment': f'错误：{str(e)[:30]}'}


def get_a50_future() -> dict:
    """
    获取 A50 期货
    数据源：待补充（目前返回模拟数据）
    """
    # TODO: 寻找可用的 A50 数据源
    return {'current': 0, 'change': 0, 'comment': '数据源寻找中'}


def get_usd_cny() -> dict:
    """
    获取人民币汇率（USD/CNY）
    数据源：中国银行（待实现）
    """
    # TODO: 实现中国银行外汇牌价解析
    # 当前返回模拟数据
    return {'rate': 7.25, 'change': 0, 'comment': '数据源接入中'}


def get_overnight_market() -> dict:
    """
    获取完整的隔夜市场数据
    """
    us_markets = get_us_markets_from_cnbc()
    china_adr = get_china_adr()
    a50_future = get_a50_future()
    usd_cny = get_usd_cny()
    
    # 综合情绪判断
    us_avg_change = sum(m.get('change', 0) for m in us_markets.values()) / 3 if us_markets else 0
    sentiment_score = us_avg_change * 0.4 + china_adr.get('change', 0) * 0.3 + a50_future.get('change', 0) * 0.3
    
    if sentiment_score > 0.5:
        sentiment = '偏多'
    elif sentiment_score < -0.5:
        sentiment = '偏空'
    else:
        sentiment = '中性'
    
    # 总结
    summary_parts = []
    if us_avg_change > 0.5:
        summary_parts.append('美股上涨')
    elif us_avg_change < -0.5:
        summary_parts.append('美股下跌')
    
    if china_adr.get('change', 0) > 1:
        summary_parts.append('中概股上涨')
    elif china_adr.get('change', 0) < -1:
        summary_parts.append('中概股下跌')
    
    if a50_future.get('change', 0) > 0.3:
        summary_parts.append('A50 期货上涨')
    elif a50_future.get('change', 0) < -0.3:
        summary_parts.append('A50 期货下跌')
    
    summary = '，'.join(summary_parts) if summary_parts else '市场波动较小'
    summary += f'，预计 A 股{"高开" if sentiment == "偏多" else "低开" if sentiment == "偏空" else "平开"}'
    
    return {
        'us_markets': us_markets,
        'china_adr': china_adr,
        'a50_future': a50_future,
        'usd_cny': usd_cny,
        'sentiment': sentiment,
        'summary': summary,
    }


if __name__ == '__main__':
    result = get_overnight_market()
    
    print("=== 隔夜市场数据 ===\n")
    
    print("美股表现:")
    for name, data in result['us_markets'].items():
        print(f"  {name}: {data['current']:.0f} ({data['change']:+.2f}%) - {data['comment']}")
    
    print(f"\n中概股：{result['china_adr']['current']:.0f} ({result['china_adr']['change']:+.2f}%) - {result['china_adr']['comment']}")
    print(f"A50 期货：{result['a50_future']['current']:.0f} ({result['a50_future']['change']:+.2f}%) - {result['a50_future']['comment']}")
    print(f"人民币汇率：{result['usd_cny']['rate']:.4f} - {result['usd_cny']['comment']}")
    
    print(f"\n市场情绪：{result['sentiment']}")
    print(f"总结：{result['summary']}")
