#!/usr/bin/env python3
"""
盘后复盘报告
交易日 15:30 执行，分析当日收盘数据、技术分析、资金流向，总结当日操作

数据源：
- 收盘数据：腾讯财经 API
- 日线数据：Tushare
- 技术指标：自主计算
"""

import sys
import yaml
import numpy as np
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


def get_daily_data(ts_code: str, days: int = 30) -> dict:
    """
    获取日线数据（Tushare）
    """
    try:
        from data.data_fetcher import get_daily_data as fetch_daily
        
        df = fetch_daily(ts_code, days=days)
        
        if len(df) > 0:
            latest = df.iloc[0]
            
            # 计算均线
            close_prices = df['close'].values
            
            ma5 = np.mean(close_prices[:min(5, len(close_prices))])
            ma10 = np.mean(close_prices[:min(10, len(close_prices))])
            ma20 = np.mean(close_prices[:min(20, len(close_prices))])
            
            return {
                'open': float(latest.get('open', 0)),
                'high': float(latest.get('high', 0)),
                'low': float(latest.get('low', 0)),
                'close': float(latest.get('close', 0)),
                'change_pct': float(latest.get('pct_chg', 0)),
                'volume': float(latest.get('vol', 0)) * 100,  # 手→股
                'amount': float(latest.get('amount', 0)) * 1000,  # 千元→元
                'turnover_rate': float(latest.get('turnover_rate', 0)),
                'ma5': ma5,
                'ma10': ma10,
                'ma20': ma20,
                'close_prices': close_prices,
            }
    except Exception as e:
        logger.warning(f"获取日线数据失败 {ts_code}: {e}")
    
    return None


def get_pe_pb(ts_code: str) -> dict:
    """
    获取 PE/PB 数据
    """
    try:
        from data.tushare_client import get_pe_pb_percentile
        return get_pe_pb_percentile(ts_code)
    except:
        return {'pe_ttm': 0, 'pb': 0, 'pe_percentile_5y': 50}


def calculate_macd(close_prices: np.ndarray) -> dict:
    """
    计算 MACD 指标
    """
    if len(close_prices) < 26:
        return {'dif': 0, 'dea': 0, 'hist': 0}
    
    # EMA12
    ema12 = np.zeros(len(close_prices))
    ema12[0] = close_prices[0]
    for i in range(1, len(close_prices)):
        ema12[i] = close_prices[i] * 2/13 + ema12[i-1] * 11/13
    
    # EMA26
    ema26 = np.zeros(len(close_prices))
    ema26[0] = close_prices[0]
    for i in range(1, len(close_prices)):
        ema26[i] = close_prices[i] * 2/27 + ema26[i-1] * 25/27
    
    # DIF
    dif = ema12 - ema26
    
    # DEA (DIF 的 9 日 EMA)
    dea = np.zeros(len(dif))
    dea[0] = dif[0]
    for i in range(1, len(dif)):
        dea[i] = dif[i] * 2/10 + dea[i-1] * 8/10
    
    # MACD 柱
    hist = (dif - dea) * 2
    
    return {
        'dif': dif[-1],
        'dea': dea[-1],
        'hist': hist[-1],
    }


def calculate_kdj(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> dict:
    """
    计算 KDJ 指标
    """
    if len(close) < 9:
        return {'k': 50, 'd': 50, 'j': 50}
    
    n = min(9, len(close))
    
    # RSV = (收盘价 - 最低值) / (最高值 - 最低值) * 100
    rsv = np.zeros(len(close))
    for i in range(len(close)):
        start_idx = max(0, i - n + 1)
        period_high = np.max(high[start_idx:i+1])
        period_low = np.min(low[start_idx:i+1])
        if period_high != period_low:
            rsv[i] = (close[i] - period_low) / (period_high - period_low) * 100
        else:
            rsv[i] = 50
    
    # K = RSV 的 3 日 SMA
    k = np.zeros(len(rsv))
    k[0] = 50
    for i in range(1, len(rsv)):
        k[i] = rsv[i] * 1/3 + k[i-1] * 2/3
    
    # D = K 的 3 日 SMA
    d = np.zeros(len(k))
    d[0] = 50
    for i in range(1, len(k)):
        d[i] = k[i] * 1/3 + d[i-1] * 2/3
    
    # J = 3K - 2D
    j = 3 * k - 2 * d
    
    return {
        'k': k[-1],
        'd': d[-1],
        'j': j[-1],
    }


def calculate_rsi(close: np.ndarray, period: int = 14) -> float:
    """
    计算 RSI 指标
    """
    if len(close) < period + 1:
        return 50
    
    # 计算涨跌幅
    delta = np.diff(close)
    
    # 分离涨跌
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    
    # 平均涨幅和跌幅
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    
    # RS 和 RSI
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def analyze_holding(code: str, name: str, daily_data: dict, cost_price: float) -> dict:
    """
    分析持仓股票当日表现
    """
    close_price = daily_data['close']
    change_pct = daily_data['change_pct']
    
    # 与成本价比较
    vs_cost = (close_price - cost_price) / cost_price * 100
    
    # 判断趋势（均线排列）
    ma5 = daily_data['ma5']
    ma10 = daily_data['ma10']
    ma20 = daily_data['ma20']
    
    if close_price > ma5 > ma10 > ma20:
        trend = '多头排列'
        trend_signal = '🟢'
    elif close_price < ma5 < ma10 < ma20:
        trend = '空头排列'
        trend_signal = '🔴'
    else:
        trend = '震荡整理'
        trend_signal = '🟡'
    
    # 计算技术指标
    close_prices = daily_data['close_prices']
    
    # 需要高低价数据来计算 KDJ
    # 简化处理：使用收盘价近似
    high_prices = close_prices * 1.02
    low_prices = close_prices * 0.98
    
    macd = calculate_macd(close_prices)
    kdj = calculate_kdj(high_prices, low_prices, close_prices)
    rsi = calculate_rsi(close_prices)
    
    # MACD 信号
    macd_signal = '金叉' if macd['dif'] > macd['dea'] else '死叉'
    
    # KDJ 信号
    if kdj['k'] > 80:
        kdj_signal = '超买'
    elif kdj['k'] < 20:
        kdj_signal = '超卖'
    else:
        kdj_signal = '中性'
    
    # RSI 信号
    if rsi > 70:
        rsi_signal = '超买'
    elif rsi < 30:
        rsi_signal = '超卖'
    elif rsi > 50:
        rsi_signal = '偏强'
    else:
        rsi_signal = '偏弱'
    
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
        'ma5': ma5,
        'ma10': ma10,
        'ma20': ma20,
        'macd': macd,
        'macd_signal': macd_signal,
        'kdj': kdj,
        'kdj_signal': kdj_signal,
        'rsi': rsi,
        'rsi_signal': rsi_signal,
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
        
        if daily_data:
            analysis = analyze_holding(code, name, daily_data, cost_price)
            analysis['shares'] = shares
            analysis['cost_price'] = cost_price
            daily_results.append(analysis)
        else:
            # 数据获取失败
            daily_results.append({
                'code': code,
                'name': name,
                'close_price': cost_price,
                'change_pct': 0,
                'open': cost_price,
                'high': cost_price,
                'low': cost_price,
                'volume': 0,
                'amount': 0,
                'turnover_rate': 0,
                'vs_cost': 0,
                'trend': '数据获取失败',
                'trend_signal': '⚪',
                'ma5': cost_price,
                'ma10': cost_price,
                'ma20': cost_price,
                'macd': {'dif': 0, 'dea': 0, 'hist': 0},
                'macd_signal': '-',
                'kdj': {'k': 50, 'd': 50, 'j': 50},
                'kdj_signal': '-',
                'rsi': 50,
                'rsi_signal': '-',
                'shares': shares,
                'cost_price': cost_price,
                'action': '等待数据更新',
            })
    
    # 计算整体情况
    total_market_value = sum(r['close_price'] * r['shares'] for r in daily_results)
    total_cost = sum(r['cost_price'] * r['shares'] for r in daily_results)
    total_profit_loss = total_market_value - total_cost
    total_profit_loss_pct = total_profit_loss / total_cost * 100 if total_cost > 0 else 0
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
| **成交量** | {r['volume']:,.0f} 股 |
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
| **MACD** | DIF:{r['macd']['dif']:.2f} DEA:{r['macd']['dea']:.2f} | {r['macd_signal']} |
| **KDJ** | K:{r['kdj']['k']:.1f} D:{r['kdj']['d']:.1f} J:{r['kdj']['j']:.1f} | {r['kdj_signal']} |
| **RSI** | {r['rsi']:.1f} | {r['rsi_signal']} |

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

*AI 价值投资系统 v2.0 | 投资宪法原则*
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
    主函数：生成并输出盘后复盘报告
    """
    logger.info("开始生成盘后复盘报告")
    
    try:
        report = generate_report()
        
        # 推送到钉钉
        push_to_dingtalk(report)
        
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
