#!/usr/bin/env python3
"""
盘后复盘报告
交易日 15:30 执行，分析当日收盘数据、技术分析、资金流向，总结当日操作
"""

import sys
import yaml
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
logger = get_logger('postmarket_report')

# 加载持仓配置
HOLDINGS_PATH = Path(__file__).parent.parent / 'config' / 'holdings.yaml'
with open(HOLDINGS_PATH, 'r', encoding='utf-8') as f:
    holdings_config = yaml.safe_load(f)

def get_daily_data(ts_code: str) -> dict:
    """
    获取当日收盘数据
    TODO: 实现真实 API 获取
    """
    # 模拟数据
    import random
    base_price = 33.0 if '002270' in ts_code else 2.0
    
    # 随机生成日 K 数据
    change_pct = random.uniform(-3.0, 3.0)
    close_price = base_price * (1 + change_pct / 100)
    open_price = base_price * (1 + random.uniform(-1.0, 1.0) / 100)
    high_price = max(open_price, close_price) * (1 + random.uniform(0, 2.0) / 100)
    low_price = min(open_price, close_price) * (1 - random.uniform(0, 2.0) / 100)
    volume = random.randint(1000000, 50000000)
    amount = volume * close_price
    
    return {
        'open': open_price,
        'high': high_price,
        'low': low_price,
        'close': close_price,
        'change_pct': change_pct,
        'volume': volume,
        'amount': amount,
        'turnover_rate': random.uniform(1.0, 10.0),
        'pe_ttm': random.uniform(15, 30),
        'pb': random.uniform(2, 5),
    }

def get_technical_indicators(ts_code: str) -> dict:
    """
    获取技术指标
    TODO: 实现真实计算
    """
    import random
    return {
        'ma5': random.uniform(32, 34) if '002270' in ts_code else random.uniform(1.9, 2.1),
        'ma10': random.uniform(31, 35) if '002270' in ts_code else random.uniform(1.85, 2.15),
        'ma20': random.uniform(30, 36) if '002270' in ts_code else random.uniform(1.8, 2.2),
        'macd': {'dif': random.uniform(-1, 1), 'dea': random.uniform(-1, 1), 'hist': random.uniform(-0.5, 0.5)},
        'kdj': {'k': random.uniform(20, 80), 'd': random.uniform(20, 80), 'j': random.uniform(10, 90)},
        'rsi': random.uniform(30, 70),
        'boll': {'upper': random.uniform(35, 37), 'mid': random.uniform(32, 34), 'lower': random.uniform(29, 31)},
    }

def analyze_holding(code: str, name: str, daily_data: dict, tech: dict, cost_price: float) -> dict:
    """
    分析持仓股票当日表现
    """
    close_price = daily_data['close']
    change_pct = daily_data['change_pct']
    
    # 与成本价比较
    vs_cost = (close_price - cost_price) / cost_price * 100
    
    # 判断趋势
    if close_price > tech['ma5'] > tech['ma10'] > tech['ma20']:
        trend = '多头排列'
        trend_signal = '🟢'
    elif close_price < tech['ma5'] < tech['ma10'] < tech['ma20']:
        trend = '空头排列'
        trend_signal = '🔴'
    else:
        trend = '震荡整理'
        trend_signal = '🟡'
    
    # MACD 信号
    macd_signal = '金叉' if tech['macd']['dif'] > tech['macd']['dea'] else '死叉'
    
    # KDJ 信号
    kdj_signal = '超买' if tech['kdj']['k'] > 80 else '超卖' if tech['kdj']['k'] < 20 else '中性'
    
    # 操作建议
    if vs_cost > 20:
        action = '盈利较多，可考虑分批止盈'
    elif vs_cost > 10:
        action = '盈利状态，继续持有，设好止盈位'
    elif vs_cost > -5:
        action = '正常波动，继续持有'
    elif vs_cost > -10:
        action = '接近补仓位，准备资金'
    else:
        action = '到达补仓区间，可执行补仓计划'
    
    return {
        'code': code,
        'name': name,
        'close_price': close_price,
        'change_pct': change_pct,
        'open': daily_data['open'],
        'high': daily_data['high'],
        'low': daily_data['low'],
        'volume': daily_data['volume'],
        'amount': daily_data['amount'],
        'turnover_rate': daily_data['turnover_rate'],
        'vs_cost': vs_cost,
        'trend': trend,
        'trend_signal': trend_signal,
        'ma5': tech['ma5'],
        'ma10': tech['ma10'],
        'ma20': tech['ma20'],
        'macd_signal': macd_signal,
        'kdj_signal': kdj_signal,
        'rsi': tech['rsi'],
        'action': action,
    }

def generate_report() -> str:
    """
    生成盘后复盘报告
    """
    now = datetime.now()
    holdings = holdings_config.get('holdings', [])
    
    daily_results = []
    for holding in holdings:
        code = holding['code']
        name = holding['name']
        cost_price = holding['cost_price']
        shares = holding['shares']
        
        daily_data = get_daily_data(code)
        tech = get_technical_indicators(code)
        analysis = analyze_holding(code, name, daily_data, tech, cost_price)
        analysis['shares'] = shares
        analysis['cost_price'] = cost_price
        daily_results.append(analysis)
    
    # 计算整体情况
    total_market_value = sum(r['close_price'] * r['shares'] for r in daily_results)
    total_cost = sum(r['cost_price'] * r['shares'] for r in daily_results)
    total_profit_loss = total_market_value - total_cost
    total_profit_loss_pct = total_profit_loss / total_cost * 100
    avg_change = sum(r['change_pct'] for r in daily_results) / len(daily_results) if daily_results else 0
    
    # 构建 Markdown 报告
    report = f"""# 🌆 AI 价值投资系统 - 盘后复盘报告

**报告时间：** {now.strftime('%Y-%m-%d %H:%M')}  
**交易日期：** {now.strftime('%Y-%m-%d')} 周{['一','二','三','四','五','六','日'][now.weekday()]}  
**收盘时间：** 15:00

---

## 📊 持仓总览

| 指标 | 数值 |
|------|------|
| **总市值** | ¥{total_market_value:,.0f} |
| **总成本** | ¥{total_cost:,.0f} |
| **浮动盈亏** | ¥{total_profit_loss:+,.0f} ({total_profit_loss_pct:+.2f}%) |
| **平均涨跌** | {avg_change:+.2f}% |
| **持仓数量** | {len(holdings)} 只 |

---

## 📈 持仓个股分析

"""
    
    for r in daily_results:
        market_value = r['close_price'] * r['shares']
        profit_loss = (r['close_price'] - r['cost_price']) * r['shares']
        profit_loss_pct = r['vs_cost']
        
        report += f"""### {r['trend_signal']} {r['name']} ({r['code']}) - {r['trend']}

#### 价格数据
| 项目 | 数值 |
|------|------|
| **收盘价** | ¥{r['close_price']:.2f} ({r['change_pct']:+.2f}%) |
| **开盘 - 最高 - 最低** | ¥{r['open']:.2f} / ¥{r['high']:.2f} / ¥{r['low']:.2f} |
| **成交量** | {r['volume']:,} 手 |
| **成交额** | ¥{r['amount']:,.0f} |
| **换手率** | {r['turnover_rate']:.2f}% |

#### 持仓盈亏
| 项目 | 数值 |
|------|------|
| **持仓数量** | {r['shares']:,} 股 |
| **成本价** | ¥{r['cost_price']:.3f} |
| **市值** | ¥{market_value:,.0f} |
| **浮动盈亏** | ¥{profit_loss:+,.0f} ({profit_loss_pct:+.1f}%) |

#### 技术指标
| 指标 | 数值 | 信号 |
|------|------|------|
| **均线** | MA5:¥{r['ma5']:.2f} MA10:¥{r['ma10']:.2f} MA20:¥{r['ma20']:.2f} | {r['trend']} |
| **MACD** | DIF:{r['macd_signal']} | {r['macd_signal']} |
| **KDJ** | K:{r['kdj_signal']} | {r['kdj_signal']} |
| **RSI** | {r['rsi']:.1f} | {'偏强' if r['rsi'] > 50 else '偏弱'} |

**操作建议：** {r['action']}

---

"""
    
    report += f"""## 🎯 明日操作计划

### 今日总结
基于今日收盘情况：

1. **整体表现：** {'盈利' if total_profit_loss > 0 else '亏损'} ¥{abs(total_profit_loss):,.0f} ({total_profit_loss_pct:+.2f}%)
2. **市场情绪：** {'偏强' if avg_change > 0.5 else '中性' if avg_change > -0.5 else '偏弱'}
3. **仓位状态：** {'合理' if -10 < total_profit_loss_pct < 20 else '需要调整'}

### 明日策略

"""
    
    # 根据今日表现给出明日建议
    if total_profit_loss_pct > 15:
        report += "- **盈利较多：** 考虑分批止盈，锁定利润\n"
    elif total_profit_loss_pct > 5:
        report += "- **盈利状态：** 继续持有，设好止盈位\n"
    elif total_profit_loss_pct > -5:
        report += "- **正常波动：** 继续持有，观察走势\n"
    elif total_profit_loss_pct > -10:
        report += "- **小幅亏损：** 准备补仓资金，等待机会\n"
    else:
        report += "- **较大亏损：** 到达补仓区间，可执行补仓计划\n"
    
    report += """
### 重点关注

1. **集合竞价（9:15-9:25）：** 观察开盘预期
2. **开盘走势（9:30-10:00）：** 确认今日趋势延续或反转
3. **盘中预警：** 关注钉钉实时推送
4. **尾盘阶段（14:30-15:00）：** 决定是否调整仓位

---

## 📚 投资宪法复盘

### 今日是否遵守投资宪法？

- [ ] 没有追涨杀跌
- [ ] 没有情绪化交易
- [ ] 严格执行预警规则
- [ ] 按计划执行补仓/减仓
- [ ] 保持合理仓位

### 需要改进的地方

_（每日反思，持续改进）_

---

## ⚠️ 风险提示

1. 技术指标仅供参考，不作为唯一决策依据
2. 严格执行投资宪法，不突破硬底线
3. 关注夜间公告和外围市场

---

*AI 价值投资系统 v1.0 | 投资宪法原则*
"""
    
    return report

def main():
    """
    主函数：生成并输出盘后复盘报告
    """
    logger.info("开始生成盘后复盘报告")
    
    try:
        report = generate_report()
        
        # 输出报告到 stdout（供 cron 推送钉钉）
        print(report)
        
        # 保存到文件
        now = datetime.now()
        output_path = PROJECT_ROOT / 'cache' / f'postmarket_{now.strftime("%Y%m%d_%H%M")}.md'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"盘后复盘报告已保存：{output_path}")
        
    except Exception as e:
        logger.error(f"生成盘后复盘报告失败：{e}", exc_info=True)
        print(f"❌ 盘后复盘报告生成失败：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
