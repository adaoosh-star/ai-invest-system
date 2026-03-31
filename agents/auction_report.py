#!/usr/bin/env python3
"""
集合竞价报告
交易日 9:25 执行，分析集合竞价结果，给出最终操作计划

数据源：
- 集合竞价：腾讯财经/东方财富 API
- 持仓成本：本地配置
"""

import sys
import yaml
import requests
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
    获取集合竞价数据（腾讯财经）
    9:15-9:25 期间获取集合竞价数据
    """
    try:
        # 转换股票代码
        parts = ts_code.split('.')
        if len(parts) != 2:
            return None
        
        code, exchange = parts
        market = 'sz' if exchange.lower() == 'sz' else 'sh'
        
        # 腾讯财经集合竞价数据
        url = f"http://qt.gtimg.cn/q={market}{code}"
        resp = requests.get(url, timeout=5)
        
        if resp.status_code == 200:
            # 解析：v_sz002270="51~名称~代码~当前价~收盘价~开盘价~最高~最低~成交量~成交额~..."
            data = resp.text.strip()
            if '=' in data and '"' in data:
                data_str = data.split('=')[1].strip('"')
                p = data_str.split('~')
                
                if len(p) >= 32:
                    # 字段映射（腾讯财经格式）
                    # p[3]=当前价，p[4]=昨收，p[5]=开盘，p[6]=最高，p[7]=最低
                    # p[8]=成交量（手），p[9]=成交额（万元），p[31]=竞价匹配量，p[32]=竞价未匹配量
                    current = float(p[3]) if p[3] else 0
                    prev_close = float(p[4]) if p[4] else current
                    open_price = float(p[5]) if p[5] else current
                    high = float(p[6]) if p[6] else current
                    low = float(p[7]) if p[7] else current
                    volume = float(p[8]) if p[8] else 0  # 手
                    amount = float(p[9]) if p[9] else 0  # 万元
                    
                    # 计算涨跌幅
                    change_pct = ((current - prev_close) / prev_close * 100) if prev_close > 0 else 0
                    
                    # 竞价数据（如果有）
                    match_volume = int(float(p[31]) * 100) if len(p) > 31 and p[31] else int(volume)
                    unmatched = int(float(p[32]) * 100) if len(p) > 32 and p[32] else 0
                    
                    # 买卖比
                    bid_ask_ratio = (match_volume + unmatched) / match_volume if match_volume > 0 else 1
                    
                    return {
                        'open_price': open_price,
                        'current': current,
                        'prev_close': prev_close,
                        'high': high,
                        'low': low,
                        'change_pct': change_pct,
                        'volume': int(volume * 100),  # 转换为股
                        'amount': amount * 10000,  # 转换为元
                        'match_volume': match_volume,
                        'unmatched': unmatched,
                        'bid_ask_ratio': bid_ask_ratio,
                    }
    except Exception as e:
        logger.warning(f"获取集合竞价数据失败 {ts_code}: {e}")
    
    return None


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
    
    # 买卖盘分析
    bid_ask = auction_data['bid_ask_ratio']
    if bid_ask > 1.2:
        bid_ask_comment = '买盘较强'
    elif bid_ask < 0.8:
        bid_ask_comment = '卖盘较强'
    else:
        bid_ask_comment = '买卖平衡'
    
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
        'bid_ask_ratio': bid_ask,
        'bid_ask_comment': bid_ask_comment,
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
        
        if auction_data:
            analysis = analyze_auction(code, name, auction_data, cost_price)
            analysis['shares'] = shares
            analysis['cost_price'] = cost_price
            auction_results.append(analysis)
        else:
            # 数据获取失败，使用默认值
            auction_results.append({
                'code': code,
                'name': name,
                'open_price': cost_price,
                'change_pct': 0,
                'strength': '数据获取失败',
                'signal': '⚪',
                'vs_cost': 0,
                'shares': shares,
                'cost_price': cost_price,
                'volume': 0,
                'amount': 0,
                'bid_ask_ratio': 1,
                'bid_ask_comment': '-',
                'action': '等待数据更新',
            })
    
    # 计算整体情况
    total_market_value = sum(r['open_price'] * r['shares'] for r in auction_results)
    avg_change = sum(r['change_pct'] for r in auction_results) / len(auction_results) if auction_results else 0
    
    # 竞价情绪
    if avg_change > 0.5:
        auction_sentiment = '偏强'
    elif avg_change > -0.5:
        auction_sentiment = '中性'
    else:
        auction_sentiment = '偏弱'
    
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
| **竞价情绪** | {auction_sentiment} |

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
| **买卖比** | {r['bid_ask_ratio']:.2f} ({r['bid_ask_comment']}) |

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


def push_to_dingtalk(content: str):
    """
    推送到钉钉（通过 Node.js 脚本调用钉钉连接器）
    """
    import subprocess
    import tempfile
    import os
    
    js_code = """
import { sendProactive } from '/home/admin/.openclaw/extensions/dingtalk-connector/src/services/messaging.ts';

const config = {
  clientId: "dinggmk7kpiddrrvi0l5",
  clientSecret: "9RR-37dNLUKRkzzS-1RN5CHsDSJnIKEtBCd3-O9MqB7SvYUduBwse8FhEtMnr2bN",
  gatewayToken: "7c945e183e33b18df341e2c3ad9ced59e0a7f156d7d20238"
};

const userId = "01023647151178899";
const content = `""" + content.replace('`', '\\`') + """`;

async function push() {
  try {
    const result = await sendProactive(config, { userId }, content, {
      msgType: "markdown",
      title: "AI 价值投资系统",
      useAICard: false
    });
    console.log("钉钉推送结果:", JSON.stringify(result));
  } catch (err) {
    console.error("钉钉推送失败:", err.message);
  }
}

push();
"""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mjs', delete=False) as f:
            f.write(js_code)
            temp_file = f.name
        
        result = subprocess.run(
            ['npx', 'tsx', temp_file],
            cwd='/home/admin/.openclaw/extensions/dingtalk-connector',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"钉钉推送：{result.stdout}", file=sys.stderr)
        os.unlink(temp_file)
    except Exception as e:
        print(f"钉钉推送异常：{e}", file=sys.stderr)

def main():
    """
    主函数：生成并输出集合竞价报告
    """
    logger.info("开始生成集合竞价报告")
    
    try:
        report = generate_report()
        
        # 推送到钉钉
        push_to_dingtalk(report)
        
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
