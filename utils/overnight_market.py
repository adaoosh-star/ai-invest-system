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
    获取 A50 期货（富时中国 A50）
    数据源：中财网（轻量级，无需浏览器）
    URL: https://quote.cfi.cn/quote30961_30961.html
    """
    try:
        resp = requests.get(
            'https://quote.cfi.cn/quote30961_30961.html',
            timeout=10,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.cfi.cn/'
            }
        )
        if resp.status_code == 200:
            import re
            content = resp.text
            # 查找价格：ind_pclose green'>14624.31</span>
            price_match = re.search(r"ind_pclose\s+\w+'>([\d.]+)</span>", content)
            # 查找百分比：(green'>(-0.12%)
            pct_match = re.search(r"\(([\-\d.]+)%\)", content)
            
            if price_match:
                current = float(price_match.group(1))
                change_pct = float(pct_match.group(1)) if pct_match else 0
                return {
                    'current': current,
                    'change': change_pct,
                    'comment': '上涨' if change_pct > 0.3 else '下跌' if change_pct < -0.3 else '震荡'
                }
    except Exception as e:
        print(f'A50 CFI ERROR: {e}')
    
    # 备用方案：东方财富 Playwright
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://quote.eastmoney.com/globalfuture/CN00Y.html', timeout=15000)
            page.wait_for_timeout(5000)
            content = page.content()
            browser.close()
        
        import re
        price_match = re.search(r'最新：.*?>([\d.]+)</span>', content, re.S)
        pct_match = re.search(r'涨幅：.*?>([\-\d.]+)%', content, re.S)
        
        if price_match:
            current = float(price_match.group(1))
            change_pct = float(pct_match.group(1)) if pct_match else 0
            return {
                'current': current,
                'change': change_pct,
                'comment': '上涨' if change_pct > 0.3 else '下跌' if change_pct < -0.3 else '震荡'
            }
    except Exception as e:
        print(f'A50 Eastmoney Playwright ERROR: {e}')
    
    return {'current': 0, 'change': 0, 'comment': '数据源维护中'}


def get_usd_cny() -> dict:
    """
    获取人民币汇率（USD/CNY）
    数据源：exchangerate-api.com（免费 API）
    """
    try:
        resp = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            rate = data.get('rates', {}).get('CNY', 0)
            if rate > 0:
                # 假设昨日汇率为今日汇率（简化处理）
                return {
                    'rate': rate,
                    'change': 0,
                    'comment': '稳定' if 7.0 <= rate <= 7.5 else '波动'
                }
    except:
        pass
    
    # 降级：返回临时数据
    return {'rate': 7.25, 'change': 0, 'comment': '数据源维护中'}


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
