"""
持仓监控 v2.0 - 推送优化模块

功能：
- 仅预警时推送（无预警时不推送）
- 配置开关控制
- 日志记录

稳定性保障：
- 独立新文件，不修改原有 holding_monitor.py
- 配置开关默认开启
- 可随时回滚到原文件
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
logger = get_logger('holding_monitor_v2')

# 加载 P0 配置
P0_CONFIG_PATH = PROJECT_ROOT / 'config' / 'p0_config.yaml'
with open(P0_CONFIG_PATH, 'r', encoding='utf-8') as f:
    p0_config = yaml.safe_load(f)

# 加载持仓配置
HOLDINGS_PATH = PROJECT_ROOT / 'config' / 'holdings.yaml'
with open(HOLDINGS_PATH, 'r', encoding='utf-8') as f:
    holdings_config = yaml.safe_load(f)

# 导入原模块（复用现有逻辑）
from monitor.holding_monitor import generate_report, format_report


def should_push(alerts: list, config: dict) -> bool:
    """
    判断是否应该推送
    
    规则：
    1. 开启 alert_only_mode 时，仅预警时推送
    2. 预警级别：红色、橙色、绿色机会
    3. 无预警时不推送（仅记录日志）
    """
    push_config = config.get('push_optimization', {})
    alert_only_mode = push_config.get('enabled', True) and push_config.get('alert_only_mode', True)
    
    if not alert_only_mode:
        # 关闭优化，始终推送（v1.0 行为）
        return True
    
    # 检查是否有预警
    if not alerts or len(alerts) == 0:
        return False
    
    # 检查预警级别
    alert_levels = push_config.get('alert_conditions', [])
    push_levels = {'补仓位触发', '减仓位触发', 'ST 风险', '质押风险', 
                   '大股东减持', '流动性风险', '估值过高'}
    
    for alert in alerts:
        alert_type = alert.get('type', '')
        alert_level = alert.get('level', '')
        
        # 红色/橙色预警始终推送
        if alert_level in ['🔴 红色', '🟠 橙色']:
            return True
        
        # 绿色机会也推送（补仓机会）
        if alert_level == '🟢 机会':
            return True
    
    return False


def run_monitoring_v2(verbose: bool = False) -> dict:
    """
    v2.0 持仓监控（推送优化版）
    
    Args:
        verbose: 是否强制输出详细报告（用于测试）
    
    Returns:
        dict: 监控结果 + 推送决策
    """
    logger.info("开始 v2.0 持仓监控（推送优化）")
    
    # 生成报告（复用 v1.0 逻辑）
    report = generate_report()
    
    # 判断是否推送
    should_push_result = should_push(report['alerts'], p0_config)
    
    # 构建结果
    result = {
        'timestamp': datetime.now().isoformat(),
        'report': report,
        'push_decision': {
            'should_push': should_push_result,
            'alert_count': len(report['alerts']),
            'reason': '有预警' if should_push_result else '无预警',
        },
        'config': {
            'alert_only_mode': p0_config['push_optimization']['alert_only_mode'],
            'version': '2.0',
        }
    }
    
    # 日志记录
    if should_push_result:
        logger.info(f"推送决策：推送（{len(report['alerts'])} 个预警）")
    else:
        logger.info("推送决策：不推送（无预警）")
        logger.info(f"报告已保存到日志：cache/monitor/{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    
    # 保存报告到文件（无预警时也保存，供创始人查看）
    save_report_to_file(report)
    
    return result


def save_report_to_file(report: dict) -> str:
    """
    保存报告到文件
    """
    cache_dir = PROJECT_ROOT / 'cache' / 'monitor'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filepath = cache_dir / f"{timestamp}_report.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"报告已保存：{filepath}")
    return str(filepath)


def format_push_message(report: dict) -> str:
    """
    格式化推送消息（简洁版）
    
    仅在有预警时推送，包含：
    - 预警摘要
    - 行动建议
    """
    if not report['alerts']:
        return None
    
    lines = []
    lines.append("🦀 **AI 价值投资系统 v2.0 - 持仓预警**")
    lines.append("")
    lines.append(f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    
    # 按级别排序
    level_order = {'🔴 红色': 0, '🟠 橙色': 1, '🟢 机会': 2}
    sorted_alerts = sorted(report['alerts'], key=lambda x: level_order.get(x['level'], 3))
    
    for alert in sorted_alerts[:5]:  # 最多 5 条
        lines.append(f"{alert['level']} **{alert['type']}** - {alert['stock']}")
        lines.append(f"  {alert['message']}")
        lines.append(f"  👉 行动：{alert['action']}")
        lines.append("")
    
    if len(sorted_alerts) > 5:
        lines.append(f"... 还有 {len(sorted_alerts) - 5} 条预警，请查看详细报告")
    
    lines.append("")
    lines.append(f"📎 详细报告：cache/monitor/")
    
    return "\n".join(lines)


# CLI 入口
if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"AI 价值投资系统 v2.0 - 持仓监控（推送优化）")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 运行监控
    result = run_monitoring_v2(verbose=True)
    
    # 输出结果
    print(f"推送决策：{'推送' if result['push_decision']['should_push'] else '不推送'}")
    print(f"预警数量：{result['push_decision']['alert_count']}")
    print(f"原因：{result['push_decision']['reason']}")
    print()
    
    if result['push_decision']['should_push']:
        # 有预警，输出推送消息
        message = format_push_message(result['report'])
        print(message)
    else:
        # 无预警，输出摘要
        summary = result['report']['summary']
        print(f"✅ 持仓正常，无预警")
        print(f"总市值：¥{summary['total_market_value']:,.0f} ({summary['total_pnl_ratio']:+.2f}%)")
        print(f"详细报告：cache/monitor/")
    
    print(f"\n{'='*60}\n")
