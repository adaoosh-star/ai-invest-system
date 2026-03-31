#!/usr/bin/env python3
"""
盘前预判报告
交易日 8:30 执行，分析隔夜市场、美股表现、A50 期货等，给出操作计划

数据源：
- 隔夜市场：新浪财经 API
- A50 期货：新浪财经
- 人民币汇率：新浪财经
- 持仓数据：Tushare + 腾讯财经
"""

import sys
import yaml
import json
import requests
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
logger = get_logger('premarket_report')

# 加载持仓配置
HOLDINGS_PATH = Path(__file__).parent.parent / 'config' / 'holdings.yaml'
with open(HOLDINGS_PATH, 'r', encoding='utf-8') as f:
    holdings_config = yaml.safe_load(f)


def get_us_markets() -> dict:
    """
    获取美股三大指数（东方财富 API - 更稳定）
    """
    result = {}
    try:
        # 东方财富美股指数代码
        symbols = {
            'dow': '100.DJIA',      # 道琼斯
            'nasdaq': '100.NDX',    # 纳斯达克 100
            'sp500': '100.SPX',     # 标普 500
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/',
        }
        
        for name, symbol in symbols.items():
            try:
                # 东方财富 API
                url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={symbol}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60"
                resp = requests.get(url, timeout=5, headers=headers)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('data'):
                        d = data['data']
                        current = d.get('f47', 0)  # 当前价
                        prev_close = d.get('f46', 1)  # 昨收
                        change = d.get('f48', 0)  # 涨跌幅
                        change_pct = d.get('f49', 0)  # 涨跌幅百分比
                        
                        result[name] = {
                            'current': current,
                            'change': change_pct,
                            'comment': '上涨' if change_pct > 0.5 else '下跌' if change_pct < -0.5 else '震荡'
                        }
            except Exception as e:
                logger.debug(f"获取{name}失败：{e}")
                result[name] = {'current': 0, 'change': 0, 'comment': '获取失败'}
    except Exception as e:
        logger.warning(f"获取美股数据异常：{e}")
    
    # 确保所有字段都存在
    for name in ['dow', 'nasdaq', 'sp500']:
        if name not in result:
            result[name] = {'current': 0, 'change': 0, 'comment': '数据获取失败'}
    
    return result


def get_china_adr() -> dict:
    """
    获取中概股表现（纳斯达克中国金龙指数）
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn/',
    }
    try:
        url = "https://hq.sinajs.cn/list=HXC"
        resp = requests.get(url, timeout=3, headers=headers)
        if resp.status_code == 200:
            data = resp.text.strip()
            if '=' in data and '"' in data:
                parts = data.split('=')[1].strip('"').split(',')
                if len(parts) >= 4 and parts[2] and parts[3]:
                    current = float(parts[3])
                    prev_close = float(parts[2])
                    change = ((current - prev_close) / prev_close * 100) if prev_close > 0 else 0
                    return {
                        'current': current,
                        'change': change,
                        'comment': '上涨' if change > 1 else '下跌' if change < -1 else '震荡'
                    }
    except Exception as e:
        logger.debug(f"获取中概股数据失败：{e}")
    
    return {'current': 0, 'change': 0, 'comment': '数据获取失败'}


def get_a50_future() -> dict:
    """
    获取 A50 期货（新浪财经）
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn/',
    }
    try:
        # 富时中国 A50 期货
        url = "https://hq.sinajs.cn/list=s_FCHI"
        resp = requests.get(url, timeout=3, headers=headers)
        if resp.status_code == 200:
            data = resp.text.strip()
            if '=' in data and '"' in data:
                parts = data.split('=')[1].strip('"').split(',')
                if len(parts) >= 4 and parts[2] and parts[3]:
                    current = float(parts[3])
                    prev_close = float(parts[2])
                    change = ((current - prev_close) / prev_close * 100) if prev_close > 0 else 0
                    return {
                        'current': current,
                        'change': change,
                        'comment': '上涨' if change > 0.3 else '下跌' if change < -0.3 else '震荡'
                    }
    except Exception as e:
        logger.debug(f"获取 A50 期货数据失败：{e}")
    
    return {'current': 0, 'change': 0, 'comment': '数据获取失败'}


def get_usd_cny() -> dict:
    """
    获取人民币汇率（在岸）
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn/',
    }
    try:
        url = "https://hq.sinajs.cn/list=s_USDCNY"
        resp = requests.get(url, timeout=3, headers=headers)
        if resp.status_code == 200:
            data = resp.text.strip()
            if '=' in data and '"' in data:
                parts = data.split('=')[1].strip('"').split(',')
                if len(parts) >= 4 and parts[2] and parts[3]:
                    current = float(parts[3])
                    prev_close = float(parts[2])
                    change = current - prev_close
                    return {
                        'rate': current,
                        'change': change,
                        'comment': '人民币贬值' if change > 0.01 else '人民币升值' if change < -0.01 else '基本稳定'
                    }
    except Exception as e:
        logger.debug(f"获取汇率数据失败：{e}")
    
    return {'rate': 0, 'change': 0, 'comment': '数据获取失败'}


def get_overnight_market() -> dict:
    """
    获取隔夜市场数据
    """
    us_markets = get_us_markets()
    china_adr = get_china_adr()
    a50_future = get_a50_future()
    usd_cny = get_usd_cny()
    
    # 综合情绪判断
    us_avg_change = sum(m.get('change', 0) for m in us_markets.values()) / 3 if us_markets else 0
    sentiment_score = us_avg_change * 0.3 + china_adr.get('change', 0) * 0.3 + a50_future.get('change', 0) * 0.4
    
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


def get_holding_analysis() -> list:
    """
    分析持仓股票的盘前状态
    """
    from data.tushare_client import get_pe_pb_percentile
    from data.realtime_fetcher import fetch_realtime_price
    
    holdings = holdings_config.get('holdings', [])
    analysis = []
    
    for holding in holdings:
        code = holding['code']
        name = holding['name']
        shares = holding['shares']
        cost_price = holding['cost_price']
        
        try:
            # 获取最新价格（昨日收盘）
            price_data = fetch_realtime_price(code, use_cache=True)
            current_price = price_data.get('price', cost_price)
            
            # 获取估值分位
            try:
                pe_pb = get_pe_pb_percentile(code)
                pe_percentile = pe_pb.get('pe_percentile_5y', 50)
            except:
                pe_percentile = 50
            
            # 计算与成本价的差距
            vs_cost = (current_price - cost_price) / cost_price * 100
            
            # 判断预期开盘
            if vs_cost > 20:
                expected_open = '盈利较多，注意止盈机会'
            elif vs_cost > 10:
                expected_open = '盈利状态，继续持有'
            elif vs_cost > -5:
                expected_open = '成本线附近，正常波动'
            elif vs_cost > -10:
                expected_open = '小幅亏损，准备补仓'
            else:
                expected_open = '深度亏损，关注补仓机会'
            
            # 关键位置
            support = cost_price * 0.95
            resistance = cost_price * 1.05
            
            analysis.append({
                'code': code,
                'name': name,
                'shares': shares,
                'cost_price': cost_price,
                'current_price': current_price,
                'pe_percentile': pe_percentile,
                'vs_cost': vs_cost,
                'expected_open': expected_open,
                'key_level': f"支撑位：¥{support:.2f}, 压力位：¥{resistance:.2f}",
                'action': '观望，等待盘中确认',
            })
        except Exception as e:
            logger.error(f"分析持仓 {code} 失败：{e}")
            analysis.append({
                'code': code,
                'name': name,
                'shares': shares,
                'cost_price': cost_price,
                'current_price': 0,
                'pe_percentile': 50,
                'vs_cost': 0,
                'expected_open': '数据获取失败',
                'key_level': '-',
                'action': '等待数据更新',
            })
    
    return analysis


def generate_report() -> str:
    """
    生成盘前预判报告
    """
    now = datetime.now()
    market = get_overnight_market()
    holdings = get_holding_analysis()
    
    # 构建 Markdown 报告
    us = market['us_markets']
    report = f"""# 🌅 AI 价值投资系统 - 盘前预判报告

**报告时间：** {now.strftime('%Y-%m-%d %H:%M')}  
**交易日期：** {now.strftime('%Y-%m-%d')} 周{['一','二','三','四','五','六','日'][now.weekday()]}

---

## 📊 隔夜市场概览

### 美股表现
| 指数 | 收盘 | 涨跌幅 | 评论 |
|------|------|--------|------|
| 道琼斯 | {us.get('dow', {}).get('current', 0):.0f} | {us.get('dow', {}).get('change', 0):+.1f}% | {us.get('dow', {}).get('comment', '-')} |
| 纳斯达克 | {us.get('nasdaq', {}).get('current', 0):.0f} | {us.get('nasdaq', {}).get('change', 0):+.1f}% | {us.get('nasdaq', {}).get('comment', '-')} |
| 标普 500 | {us.get('sp500', {}).get('current', 0):.0f} | {us.get('sp500', {}).get('change', 0):+.1f}% | {us.get('sp500', {}).get('comment', '-')} |

### 其他指标
- **中概股：** {market['china_adr'].get('current', 0):.0f} ({market['china_adr'].get('change', 0):+.1f}%) - {market['china_adr'].get('comment', '-')}
- **A50 期货：** {market['a50_future'].get('current', 0):.0f} ({market['a50_future'].get('change', 0):+.1f}%) - {market['a50_future'].get('comment', '-')}
- **人民币汇率：** {market['usd_cny'].get('rate', 0):.4f} ({market['usd_cny'].get('change', 0):+.3f}) - {market['usd_cny'].get('comment', '-')}

### 市场情绪
**整体情绪：** {market['sentiment']}  
**隔夜总结：** {market['summary']}

---

## 📈 持仓分析

"""
    
    for h in holdings:
        current_price = h['current_price'] if h['current_price'] else h['cost_price']
        vs_cost = h['vs_cost'] if h['vs_cost'] else 0
        pe_percentile = h['pe_percentile'] if h['pe_percentile'] else 50
        
        report += f"""### {h['name']} ({h['code']})
- **持仓：** {h['shares']:,} 股
- **成本价：** ¥{h['cost_price']:.3f}
- **最新价：** ¥{current_price:.2f} ({vs_cost:+.1f}%)
- **PE 分位：** {pe_percentile:.0f}%
- **预期开盘：** {h['expected_open']}
- **关键位置：** {h['key_level']}
- **操作计划：** {h['action']}

"""
    
    report += f"""## 🎯 今日操作计划

### 总体策略
基于隔夜市场表现，建议采取 **{market['sentiment']}** 策略：

1. **开盘阶段（9:15-9:30）：** 观察集合竞价，确认开盘价是否符合预期
2. **盘中监控（9:30-15:00）：** 关注持仓股是否触发预警规则
3. **关键位置：** 若跌破支撑位，准备执行补仓计划；若突破压力位，考虑减仓

### 重点关注
- 隔夜市场波动对 A 股的传导效应
- 人民币汇率变动对外资流向的影响
- 持仓股的盘中表现

---

## ⚠️ 风险提示

1. 隔夜市场波动可能影响 A 股开盘
2. 盘中需关注实时资金流向
3. 严格执行投资宪法，不追涨杀跌

---

*AI 价值投资系统 v1.0 | 投资宪法原则*
"""
    
    return report


def push_to_dingtalk(content: str):
    """
    推送到钉钉（通过 OpenClaw 会话）
    输出到 stdout，由 OpenClaw 捕获并推送到当前会话
    """
    # 直接输出完整报告，OpenClaw 会推送到钉钉
    print(content)

def main():
    """
    主函数：生成并输出盘前报告
    """
    logger.info("开始生成盘前预判报告")
    
    try:
        report = generate_report()
        
        # 推送到钉钉
        push_to_dingtalk(report)
        
        # 保存到文件
        now = datetime.now()
        output_path = PROJECT_ROOT / 'cache' / f'premarket_{now.strftime("%Y%m%d_%H%M")}.md'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"盘前报告已保存：{output_path}")
        
    except Exception as e:
        logger.error(f"生成盘前报告失败：{e}", exc_info=True)
        print(f"❌ 盘前报告生成失败：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
