#!/usr/bin/env python3
"""
美股数据获取 - 使用 CNBC API
"""

import requests
import re

def get_us_markets_from_cnbc():
    """
    从 CNBC 获取美股三大指数
    """
    urls = {
        'dow': 'https://www.cnbc.com/quotes/.DJI',
        'nasdaq': 'https://www.cnbc.com/quotes/.IXIC',
        'sp500': 'https://www.cnbc.com/quotes/.SPX',
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    result = {}
    
    for name, url in urls.items():
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                text = resp.text
                
                # 查找价格和涨跌幅
                price_match = re.search(r'"last"\s*:\s*"([\d,\.]+)"', text)
                change_match = re.search(r'"change"\s*:\s*"([+-][\d,\.]+)"', text)
                
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))
                    if change_match:
                        change = float(change_match.group(1).replace(',', ''))
                        # 计算昨收 = 现价 - 涨跌
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

if __name__ == '__main__':
    result = get_us_markets_from_cnbc()
    print("美股数据:")
    for name, data in result.items():
        print(f"  {name}: {data['current']:.2f} ({data['change']:+.2f}%) - {data['comment']}")
