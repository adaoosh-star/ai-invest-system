#!/usr/bin/env python3
"""
集合竞价报告
交易日 9:25 执行，分析集合竞价结果，给出最终操作计划
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
logger = get_logger('auction_report')

# 加载持仓配置
HOLDINGS_PATH = Path(__file__).parent.parent / 'config' / 'holdings.yaml'
with open(HOLDINGS_PATH, 'r', encoding='utf-8') as f:
    holdings_config = yaml.safe_load(f)

def get_auction_data(ts_code: str) -> dict:
    """
    获取集合竞价数据
    TODO: 实现真实 API 获取
    """
    # 模拟数据
    import random
    base_price = 33.0 if '002270' in ts_code else 2.0
    
    # 随机生成竞价结果
    change_pct = random.uniform(-2.0, 2.0)
    open_price = base_price * (1 + change_pct / 100)
    volume = random.randint(10000, 500000)
    amount = volume * open_price
    
    return {
        'open_price': open_price,
        'change_pct': change_pct,
        'volume': volume,
        'amount': amount,
        'match_volume': int(volume * 0.8),  # 匹配成交量
        'unmatched': int(volume * 0.2),  # 未匹配量
        'bid_ask_ratio': random.uniform(0.8, 1.2),  # 买卖比
    }

def analyze_auction(code: str, name: str, auction_data: dict, cost_price: float) -> dict:
    """
    分析集合竞价结果
    """
    open_price = auction_data['open_price']
    change_pct = auction_data['change_pct']
    
    # 判断竞价强弱
    if change_pct > 1.5:
        strength = '强势高开'
        signal = '🟢'
    elif change_pct > 0:
        strength = '小幅高开'
        signal = '🟡'
    elif change_pct > -1.0:
        strength = '平开或微跌'
        signal = '⚪'
    else:
        strength = '低开'
        signal = '🔴'
    
    # 与成本价比较
    vs_cost = (open_price - cost_price) / cost_price * 100
    
    # 操作建议
    if vs_cost > 20:
        action = '盈利较多，可考虑部分止盈'
    elif vs_cost > 10:
        action = '盈利状态，继续持有'
    elif vs_cost > -5:
        action = '正常波动，观望'
    elif vs_cost > -10:
        action = '接近补仓位，准备资金'
    else:
        action = '到达补仓区间，执行补仓计划'
    
    return {
        'code': code,
        'name': name,
        'open_price': open_price,
        'change_pct': change_pct,
        'strength': strength,
        'signal': signal,
        'vs_cost': vs_cost,
        'volume': auction_data['volume'],
        'amount': auction_data['amount'],
        'bid_ask_ratio': auction_data['bid_ask_ratio'],
        'action': action,
    }

def generate_report() -> str:
    """
    生成集合竞价报告
    """
    now = datetime.now()
    holdings = holdings_config.get('holdings', [])
    
    auction_results = []
    for holding in holdings:
        code = holding['code']
        name = holding['name']
        cost_price = holding['cost_price']
        shares = holding['shares']
        
        auction_data = get_auction_data(code)
        analysis = analyze_auction(code, name, auction_data, cost_price)
        analysis['shares'] = shares
        analysis['cost_price'] = cost_price
        auction_results.append(analysis)
    
    # 计算整体情况
    total_market_value = sum(r['open_price'] * r['shares'] for r in auction_results)
    avg_change = sum(r['change_pct'] for r in auction_results) / len(auction_results) if auction_results else 0
    
    # 构建 Markdown 报告
    report = f"""# 🔔 AI 价值投资系统 - 集合竞价报告

**报告时间：** {now.strftime('%Y-%m-%d %H:%M')}  
**交易日期：** {now.strftime('%Y-%m-%d')} 周{['一','二','三','四','五','六','日'][now.weekday()]}  
**竞价阶段：** 9:15-9:25

---

## 📊 竞价总览

| 指标 | 数值 |
|------|------|
| **持仓总市值** | ¥{total_market_value:,.0f} |
| **平均涨跌幅** | {avg_change:+.2f}% |
| **竞价情绪** | {'偏强' if avg_change > 0.5 else '中性' if avg_change > -0.5 else '偏弱'} |

---

## 📈 持仓竞价分析

"""
    
    for r in auction_results:
        market_value = r['open_price'] * r['shares']
        profit_loss = (r['open_price'] - r['cost_price']) * r['shares']
        profit_loss_pct = r['vs_cost']
        
        report += f"""### {r['signal']} {r['name']} ({r['code']})

| 项目 | 数值 |
|------|------|
| **竞价开盘** | ¥{r['open_price']:.2f} ({r['change_pct']:+.2f}%) |
| **竞价强度** | {r['strength']} |
| **持仓市值** | ¥{market_value:,.0f} |
| **浮动盈亏** | ¥{profit_loss:+,.0f} ({profit_loss_pct:+.1f}%) |
| **竞价成交量** | {r['volume']:,} 股 (¥{r['amount']:,.0f}) |
| **买卖比** | {r['bid_ask_ratio']:.2f} |

**操作建议：** {r['action']}

---

"""
    
    report += f"""## 🎯 今日操作计划

### 集合竞价总结
基于竞价结果，今日策略建议：

"""
    
    # 根据竞价结果给出总体建议
    if avg_change > 1.0:
        report += "- **整体高开：** 注意冲高回落风险，不建议追高\n"
    elif avg_change > 0:
        report += "- **小幅高开：** 正常开盘，按原计划执行\n"
    elif avg_change > -1.0:
        report += "- **平开或微跌：** 观察盘中走势，寻找机会\n"
    else:
        report += "- **低开：** 关注是否有补仓机会\n"
    
    report += """
### 盘中关注点

1. **9:30-10:00** - 开盘后走势确认
2. **10:00-11:30** - 上午交易时段，关注量能
3. **13:00-14:30** - 下午交易时段，观察资金流向
4. **14:30-15:00** - 尾盘阶段，决定是否调整仓位

### 预警触发条件

- **减仓信号：** 盘中涨幅>5% 且 PE 分位>90%
- **补仓信号：** 盘中跌幅>3% 且到达补仓位
- **止损信号：** 触及投资宪法硬底线

---

## ⚠️ 风险提示

1. 集合竞价仅反映开盘预期，盘中可能变化
2. 严格执行投资宪法，不情绪化交易
3. 关注盘中实时预警通知

---

*AI 价值投资系统 v1.0 | 投资宪法原则*
"""
    
    return report

def main():
    """
    主函数：生成并输出集合竞价报告
    """
    logger.info("开始生成集合竞价报告")
    
    try:
        report = generate_report()
        
        # 输出报告到 stdout（供 cron 推送钉钉）
        print(report)
        
        # 保存到文件
        now = datetime.now()
        output_path = PROJECT_ROOT / 'cache' / f'auction_{now.strftime("%Y%m%d_%H%M")}.md'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"集合竞价报告已保存：{output_path}")
        
    except Exception as e:
        logger.error(f"生成集合竞价报告失败：{e}", exc_info=True)
        print(f"❌ 集合竞价报告生成失败：{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
