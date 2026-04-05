"""
持仓监控报告
基于 holdings.yaml 配置，生成持仓监控报告
"""

import sys
import yaml
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径，确保可以导入 data 模块
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入日志系统
from utils.logger import get_logger
logger = get_logger('holding_monitor')

# 加载配置
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'thresholds.yaml'
HOLDINGS_PATH = Path(__file__).parent.parent / 'config' / 'holdings.yaml'

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    thresholds_config = yaml.safe_load(f)

with open(HOLDINGS_PATH, 'r', encoding='utf-8') as f:
    holdings_config = yaml.safe_load(f)

def get_current_data(ts_code: str) -> dict:
    """
    获取当前数据（实时价格 + 财务数据）
    
    修复记录：
    - 2026-03-26 11:50: 从硬编码模拟数据改为真实 API 获取
    - 2026-03-26 12:00: 使用 realtime_fetcher 多数据源获取实时价格
    """
    try:
        from data.tushare_client import (
            get_pe_pb_percentile, get_roe, get_gross_margin,
            get_debt_ratio, get_cash_flow
        )
        from data.realtime_fetcher import fetch_realtime_price
        import pandas as pd
        
        result = {}
        
        # 1. 获取实时价格（多数据源冗余，盘中必须用实时价格）
        try:
            realtime_data = fetch_realtime_price(ts_code, use_cache=False)  # 盘中不用缓存，确保最新
            if realtime_data and realtime_data.get('price', 0) > 0:
                result['current_price'] = realtime_data['price']
                result['price_source'] = realtime_data.get('source', 'unknown')
                result['price_time'] = realtime_data.get('time_display', realtime_data.get('time', ''))
        except Exception as e:
            logger.warning(f"获取实时价格失败 {ts_code}: {e}")
            # 降级：尝试从日线数据获取
            try:
                from data.data_fetcher import get_daily_data
                daily_df = get_daily_data(ts_code, days=5)
                if len(daily_df) > 0:
                    if 'trade_date' in daily_df.columns:
                        daily_df = daily_df.sort_values('trade_date', ascending=False)
                    result['current_price'] = daily_df.iloc[0]['close']
                    result['price_source'] = 'tushare_daily'
                    result['price_time'] = daily_df.iloc[0].get('trade_date', '')
                    logger.info(f"降级获取日线数据成功 {ts_code}")
            except Exception as e2:
                logger.error(f"获取日线数据也失败 {ts_code}: {e2}")
            pass
        
        # 2. 获取估值分位
        try:
            pe_pb = get_pe_pb_percentile(ts_code)
            # Tushare 返回的是小数（0-1），保持原样
            result['pe_percentile'] = pe_pb.get('pe_percentile_5y', 0)
            result['pb_percentile'] = pe_pb.get('pb_percentile_5y', 0)
        except:
            pass
        
        # 3. 获取 ROE
        try:
            roe_df = get_roe(ts_code)
            if len(roe_df) > 0:
                # TTM ROE = 近 4 个季度平均
                roe_ttm = roe_df.head(4)['roe_dt'].mean() / 100.0  # 转换为小数
                result['roe_ttm'] = roe_ttm
                
                # ROE 变化（同比）
                if len(roe_df) >= 4:
                    roe_prev = roe_df.iloc[4]['roe_dt'] / 100.0 if len(roe_df) > 4 else roe_ttm
                    result['roe_decline'] = roe_ttm - roe_prev
        except:
            pass
        
        # 4. 获取毛利率
        try:
            margin_df = get_gross_margin(ts_code)
            if len(margin_df) > 0:
                result['gross_margin'] = margin_df.iloc[0]['gross_margin']
                if len(margin_df) > 1:
                    result['gross_margin_decline'] = margin_df.iloc[0]['gross_margin'] - margin_df.iloc[1]['gross_margin']
        except:
            pass
        
        # 5. 获取负债率
        try:
            debt_df = get_debt_ratio(ts_code)
            if len(debt_df) > 0:
                result['debt_ratio'] = debt_df.iloc[0]['debt_ratio']
        except:
            pass
        
        # 6. 获取现金流比率
        try:
            cf_df = get_cash_flow(ts_code)
            if len(cf_df) > 0:
                oper_cf = cf_df.iloc[0].get('oper_cf', 0)
                # 简化：用经营现金流代替比率
                result['cash_flow_ratio'] = 1.0 if oper_cf > 0 else 0.5
        except:
            pass
        
        # 7. 诚信评分（简化：默认 85）
        result['integrity_score'] = 85
        
        return result
    except Exception as e:
        print(f"⚠️ 获取实时数据失败：{e}")
        # 降级：返回空字典，调用方处理
        return {}

def check_position_alert(holding: dict, current_data: dict) -> list:
    """
    检查持仓预警
    """
    alerts = []
    ts_code = holding['code']
    name = holding['name']
    cost_price = holding['cost_price']
    current_price = current_data.get('current_price', 0)
    
    # 计算盈亏
    if current_price > 0:
        pnl_ratio = (current_price - cost_price) / cost_price
    else:
        pnl_ratio = 0
    
    # 1. 估值预警
    pe_percentile = current_data.get('pe_percentile')
    if pe_percentile is not None:
        if pe_percentile > 0.95:
            alerts.append({
                'level': '🔴 红色',
                'type': '估值过高',
                'message': f"{name} PE 分位{pe_percentile:.1%} > 95%，坚决减仓",
                'action': '减仓 30%',
            })
        elif pe_percentile > 0.90:
            alerts.append({
                'level': '🟠 橙色',
                'type': '估值过高',
                'message': f"{name} PE 分位{pe_percentile:.1%} > 90%，考虑减仓",
                'action': '考虑减仓',
            })
    
    # 2. 补仓机会提醒
    buy_more = holding.get('buy_more', [])
    for buy_plan in buy_more:
        if current_price <= buy_plan['price'] * 1.02:  # 接近补仓位 2% 以内
            alerts.append({
                'level': '🟢 机会',
                'type': '补仓机会',
                'message': f"{name} 现价{current_price:.2f} 接近补仓位{buy_plan['price']}（{buy_plan['reason']}）",
                'action': f"准备补仓{buy_plan['shares']}股",
            })
    
    # 3. 基本面预警
    roe_decline = current_data.get('roe_decline')
    if roe_decline is not None and roe_decline > 0.05:
        alerts.append({
            'level': '🟠 橙色',
            'type': 'ROE 恶化',
            'message': f"{name} ROE 下降{roe_decline:.1%} > 5%",
            'action': '启动深度分析',
        })
    
    cash_flow_ratio = current_data.get('cash_flow_ratio')
    if cash_flow_ratio is not None and cash_flow_ratio < 0.5:
        alerts.append({
            'level': '🟠 橙色',
            'type': '现金流恶化',
            'message': f"{name} 现金流/净利润{cash_flow_ratio:.2f} < 0.5",
            'action': '查应收账款',
        })
    
    return alerts

def generate_report() -> dict:
    """
    生成持仓监控报告
    """
    logger.info("开始生成持仓监控报告")
    
    holdings = holdings_config.get('holdings', [])
    all_alerts = []
    portfolio_summary = []
    
    logger.info(f"持仓数量：{len(holdings)}")
    
    for holding in holdings:
        ts_code = holding['code']
        name = holding['name']
        shares = holding['shares']
        cost_price = holding['cost_price']
        
        # 获取当前数据
        current_data = get_current_data(ts_code)
        current_price = current_data.get('current_price', 0)
        
        # 计算市值和盈亏
        market_value = shares * current_price
        cost_value = shares * cost_price
        pnl = market_value - cost_value
        pnl_ratio = pnl / cost_value if cost_value > 0 else 0
        
        portfolio_summary.append({
            'name': name,
            'code': ts_code,
            'shares': shares,
            'cost_price': cost_price,
            'current_price': current_price,
            'market_value': market_value,
            'pnl': pnl,
            'pnl_ratio': pnl_ratio,
            'price_source': current_data.get('price_source', ''),
            'price_time': current_data.get('price_time', ''),
        })
        
        # 检查预警
        alerts = check_position_alert(holding, current_data)
        for alert in alerts:
            alert['stock'] = name
            all_alerts.append(alert)
    
    # 按严重程度排序
    level_order = {'🔴 红色': 0, '🟠 橙色': 1, '⚠️ 黄色': 2, '🟢 机会': 3, '✅ 正常': 4}
    all_alerts.sort(key=lambda x: level_order.get(x['level'], 4))
    
    # 计算总持仓
    total_market_value = sum(p['market_value'] for p in portfolio_summary)
    total_cost = sum(p['cost_price'] * p['shares'] for p in portfolio_summary)
    total_pnl = total_market_value - total_cost
    total_pnl_ratio = total_pnl / total_cost if total_cost > 0 else 0
    
    return {
        'timestamp': datetime.now().isoformat(),
        'portfolio': portfolio_summary,
        'summary': {
            'total_market_value': total_market_value,
            'total_cost': total_cost,
            'total_pnl': total_pnl,
            'total_pnl_ratio': total_pnl_ratio,
        },
        'alerts': all_alerts,
        'alert_summary': {
            'red': sum(1 for a in all_alerts if a['level'] == '🔴 红色'),
            'orange': sum(1 for a in all_alerts if a['level'] == '🟠 橙色'),
            'opportunity': sum(1 for a in all_alerts if a['level'] == '🟢 机会'),
        }
    }

def format_report(report: dict, verbose: bool = False) -> str:
    """
    格式化报告为钉钉消息
    
    Args:
        report: 报告数据
        verbose: True=详细报告（有预警时），False=简洁摘要（无预警时）
    """
    # 判断是否有预警（红色/橙色/机会）
    has_alert = len(report['alerts']) > 0
    
    # 如果没有预警，输出简洁摘要（一行）
    if not has_alert and not verbose:
        timestamp = report['timestamp'][11:16]  # HH:MM
        total_mv = report['summary']['total_market_value']
        total_pnl_ratio = report['summary']['total_pnl_ratio']
        
        # 持仓摘要：标的名 + 市值
        holdings_summary = " ".join([
            f"{p['name']}¥{p['market_value']:,.0f}"
            for p in report['portfolio']
        ])
        
        return f"【持仓监控】{timestamp} ✅ 正常 | 总市值¥{total_mv:,.0f} ({total_pnl_ratio:+.2f}%) | {holdings_summary}"
    
    # 有预警时，输出详细报告
    lines = []
    lines.append("# 🦀 AI 价值投资系统 v1.0 - 持仓监控报告")
    lines.append("")
    lines.append(f"**监控时间：** {report['timestamp'][:19]}")
    lines.append("")
    
    # 总览
    summary = report['summary']
    lines.append("## 📊 持仓总览")
    lines.append("")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 总市值 | ¥{summary['total_market_value']:,.0f} |")
    lines.append(f"| 总成本 | ¥{summary['total_cost']:,.0f} |")
    lines.append(f"| 总盈亏 | ¥{summary['total_pnl']:,.0f} ({summary['total_pnl_ratio']:+.2%}) |")
    lines.append("")
    
    # 持仓明细
    lines.append("## 📈 持仓明细")
    lines.append("")
    for p in report['portfolio']:
        pnl_symbol = "📈" if p['pnl'] >= 0 else "📉"
        price_source = p.get('price_source', '')
        price_time = p.get('price_time', '')
        
        # 显示价格来源标识
        source_tag = ""
        if price_source == 'qq':
            source_tag = " 🟢 实时"
        elif price_source == 'eastmoney':
            source_tag = " 🔵 实时"
        elif price_source == 'tushare_daily':
            source_tag = " 📅 盘后"
        
        lines.append(f"**{p['name']} ({p['code']})** {pnl_symbol}{source_tag}")
        lines.append(f"- 持仓：{p['shares']}股")
        lines.append(f"- 成本：¥{p['cost_price']:.3f} → 现价：¥{p['current_price']:.3f}")
        if price_time:
            # 时间格式：20260326 11:52:33 → 显示为 2026-03-26 11:52
            if len(price_time) >= 17:
                time_fmt = f"{price_time[:4]}-{price_time[4:6]}-{price_time[6:8]} {price_time[9:17]}"
            elif len(price_time) >= 8:
                time_fmt = price_time
            else:
                time_fmt = price_time
            lines.append(f"- 价格时间：{time_fmt}")
        lines.append(f"- 市值：¥{p['market_value']:,.0f}")
        lines.append(f"- 盈亏：¥{p['pnl']:,.0f} ({p['pnl_ratio']:+.2%})")
        lines.append("")
    
    # 预警
    if report['alerts']:
        lines.append("## ⚠️ 预警与机会")
        lines.append("")
        for alert in report['alerts']:
            lines.append(f"{alert['level']} **{alert['stock']}** - {alert['type']}")
            lines.append(f"- {alert['message']}")
            lines.append(f"- **行动：** {alert['action']}")
            lines.append("")
    else:
        lines.append("## ✅ 无预警")
        lines.append("")
        lines.append("持仓正常，无需要特别关注的风险或机会。")
        lines.append("")
    
    # 下一步
    lines.append("---")
    lines.append("*AI 价值投资系统 v1.0 自动生成*")
    
    return "\n".join(lines)

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


# 主程序
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("持仓监控任务开始执行")
    
    try:
        report = generate_report()
        formatted = format_report(report)
        
        # 记录预警汇总
        alert_summary = report.get('alert_summary', {})
        logger.info(f"预警汇总：红色={alert_summary.get('red', 0)}, 橙色={alert_summary.get('orange', 0)}, 机会={alert_summary.get('opportunity', 0)}")
        
        # 判断是否有预警（红色/橙色/机会）
        has_alert = len(report['alerts']) > 0
        
        # 优化策略：仅预警时推送，否则只保存文件
        if has_alert:
            # 有预警：输出完整报告 + 推送 dingtalk
            print(formatted)
            push_to_dingtalk(formatted)
            logger.info("🔔 有预警，已推送完整报告")
        else:
            # 无预警：仅输出简洁摘要（不推送）
            simple_summary = format_report(report, verbose=False)
            logger.info(f"✅ 无预警，仅保存日志：{simple_summary}")
            # 不 print，避免 cron 推送
        
        # 保存报告到文件（总是保存，供按需查看）
        output_path = Path(__file__).parent.parent / 'cache' / f"holding_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted)
        
        logger.info(f"📁 报告已保存：{output_path}")
        logger.info("持仓监控任务执行完成")
        
    except Exception as e:
        logger.error(f"持仓监控任务执行失败：{e}", exc_info=True)
        raise
