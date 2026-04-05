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
    获取美股三大指数（多数据源冗余）
    """
    from utils.overnight_market import get_overnight_market
    market = get_overnight_market()
    return market['us_markets']


def get_china_adr() -> dict:
    """
    获取中概股表现（多数据源冗余）
    """
    from utils.overnight_market import get_overnight_market
    market = get_overnight_market()
    return market['china_adr']


def get_a50_future() -> dict:
    """
    获取 A50 期货（多数据源冗余）
    """
    from utils.overnight_market import get_overnight_market
    market = get_overnight_market()
    return market['a50_future']


def get_usd_cny() -> dict:
    """
    获取人民币汇率（多数据源冗余）
    """
    from utils.overnight_market import get_overnight_market
    market = get_overnight_market()
    return market['usd_cny']


def get_auction_data(ts_code: str) -> dict:
    """
    获取集合竞价数据（腾讯财经）
    9:15-9:25 期间获取集合竞价数据
    """
    try:
        parts = ts_code.split('.')
        if len(parts) != 2:
            return None
        
        code, exchange = parts
        market = 'sz' if exchange.lower() == 'sz' else 'sh'
        
        url = f"http://qt.gtimg.cn/q={market}{code}"
        resp = requests.get(url, timeout=5)
        
        if resp.status_code == 200:
            data = resp.text.strip()
            if '=' in data and '"' in data:
                data_str = data.split('=')[1].strip('"')
                p = data_str.split('~')
                
                if len(p) >= 32:
                    current = float(p[3]) if p[3] else 0
                    prev_close = float(p[4]) if p[4] else current
                    open_price = float(p[5]) if p[5] else current
                    high = float(p[6]) if p[6] else current
                    low = float(p[7]) if p[7] else current
                    volume = float(p[8]) if p[8] else 0
                    amount = float(p[9]) if p[9] else 0
                    
                    change_pct = ((current - prev_close) / prev_close * 100) if prev_close > 0 else 0
                    match_volume = int(float(p[31]) * 100) if len(p) > 31 and p[31] else int(volume)
                    unmatched = int(float(p[32]) * 100) if len(p) > 32 and p[32] else 0
                    bid_ask_ratio = (match_volume + unmatched) / match_volume if match_volume > 0 else 1
                    
                    return {
                        'open_price': open_price,
                        'current': current,
                        'prev_close': prev_close,
                        'high': high,
                        'low': low,
                        'change_pct': change_pct,
                        'volume': int(volume * 100),
                        'amount': amount * 10000,
                        'match_volume': match_volume,
                        'unmatched': unmatched,
                        'bid_ask_ratio': bid_ask_ratio,
                    }
    except Exception as e:
        logger.warning(f"获取集合竞价数据失败 {ts_code}: {e}")
    
    return None


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
    分析持仓股票的盘前状态（包含集合竞价）
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
            
            # 获取集合竞价数据（9:25 有真实数据）
            auction_data = get_auction_data(code)
            
            # 获取估值分位
            try:
                pe_pb = get_pe_pb_percentile(code)
                pe_percentile = pe_pb.get('pe_percentile_5y', 0.5) * 100
            except:
                pe_percentile = 50
            
            # 计算与成本价的差距
            vs_cost = (current_price - cost_price) / cost_price * 100
            
            # 集合竞价分析
            if auction_data:
                auction_open = auction_data.get('open_price', current_price)
                auction_change = auction_data.get('change_pct', 0)
                auction_volume = auction_data.get('match_volume', 0)
                
                if auction_change > 2:
                    auction_signal = '🔴 强势高开'
                elif auction_change > 0.5:
                    auction_signal = '🟢 小幅高开'
                elif auction_change > -0.5:
                    auction_signal = '⚪ 平开'
                elif auction_change > -2:
                    auction_signal = '🔵 小幅低开'
                else:
                    auction_signal = '🔴 大幅低开'
                
                auction_summary = f"{auction_open:.2f} ({auction_change:+.2f}%), 竞价量：{auction_volume:,}股"
            else:
                auction_signal = '⏳ 未开始'
                auction_summary = '等待 9:15-9:25 集合竞价'
            
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
                'auction_signal': auction_signal,
                'auction_summary': auction_summary,
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
- **集合竞价：** {h['auction_signal']} {h['auction_summary']}
- **预期开盘：** {h['expected_open']}
- **关键位置：** {h['key_level']}
- **操作计划：** {h['action']}

"""
    
    report += f"""## 🎯 今日操作计划

### 总体策略
基于隔夜市场表现和集合竞价结果，建议采取 **{market['sentiment']}** 策略：

1. **集合竞价解读（9:25）：** 根据竞价信号调整今日操作
2. **开盘阶段（9:30-10:00）：** 观察开盘后走势，确认方向
3. **盘中监控（9:30-15:00）：** 关注持仓股是否触发预警规则
4. **关键位置：** 若跌破支撑位，准备执行补仓计划；若突破压力位，考虑减仓

### 重点关注
- 隔夜市场波动对 A 股的传导效应
- 人民币汇率变动对外资流向的影响
- 持仓股的集合竞价信号和盘中表现

---

## ⚠️ 风险提示

1. 隔夜市场波动可能影响 A 股开盘
2. 集合竞价信号需结合盘中确认
3. 严格执行投资宪法，不追涨杀跌

---

*AI 价值投资系统 v1.0 | 投资宪法原则*
"""
    
    return report


def push_to_dingtalk(content: str):
    """
    推送到钉钉（通过 Node.js 脚本调用钉钉连接器）
    """
    import subprocess
    import tempfile
    import os
    
    # 转义反引号
    escaped_content = content.replace('`', '\\`')
    
    # 创建临时 JS 脚本
    js_code = f"""
import {{ sendProactive }} from '/home/admin/.openclaw/extensions/dingtalk-connector/src/services/messaging.ts';

const config = {{
  clientId: "dinggmk7kpiddrrvi0l5",
  clientSecret: "9RR-37dNLUKRkzzS-1RN5CHsDSJnIKEtBCd3-O9MqB7SvYUduBwse8FhEtMnr2bN",
  gatewayToken: "7c945e183e33b18df341e2c3ad9ced59e0a7f156d7d20238"
}};

const userId = "01023647151178899";
const content = `{escaped_content}`;

async function push() {{
  try {{
    const result = await sendProactive(config, {{ userId }}, content, {{
      msgType: "markdown",
      title: "AI 价值投资系统",
      useAICard: false
    }});
    console.log('推送成功:', result);
  }} catch (error) {{
    console.error('推送失败:', error);
    process.exit(1);
  }}
}}

push();
"""
    
    try:
        # 写入临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(js_code)
            temp_file = f.name
        
        # 执行 Node.js 脚本
        result = subprocess.run(
            ['npx', 'tsx', temp_file],
            capture_output=True,
            text=True,
            timeout=30,
            cwd='/home/admin/.openclaw/extensions/dingtalk-connector',
            env={**os.environ, 'NODE_NO_WARNINGS': '1'}
        )
        
        if result.returncode == 0:
            logger.info("📤 Dingtalk 推送成功")
        else:
            logger.error(f"📤 Dingtalk 推送失败：{result.stderr}")
        
        # 清理临时文件
        os.unlink(temp_file)
        
    except Exception as e:
        logger.error(f"📤 Dingtalk 推送异常：{e}")

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
