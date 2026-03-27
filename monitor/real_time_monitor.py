"""
实时监控预警
投资宪法：持有中 10 项检查清单，触发🟠橙色才通知人工
"""

import yaml
from pathlib import Path
from datetime import datetime

# 加载配置
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'thresholds.yaml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

def check_valuation_alert(ts_code: str, pe_percentile: float) -> dict:
    """
    估值预警（检查项 27）
    """
    thresholds = config['alert_thresholds']
    
    if pe_percentile > thresholds['pe_percentile_red']:
        return {
            'ts_code': ts_code,
            'level': '🔴 红色',
            'type': '估值过高',
            'message': f"{ts_code} PE 分位{pe_percentile:.1%} > {thresholds['pe_percentile_red']:.0%}，坚决卖出",
            'action': '减仓 30%',
        }
    elif pe_percentile > thresholds['pe_percentile_orange']:
        return {
            'ts_code': ts_code,
            'level': '🟠 橙色',
            'type': '估值过高',
            'message': f"{ts_code} PE 分位{pe_percentile:.1%} > {thresholds['pe_percentile_orange']:.0%}，考虑减仓",
            'action': '考虑减仓',
        }
    elif pe_percentile > thresholds['pe_percentile_yellow']:
        return {
            'ts_code': ts_code,
            'level': '⚠️ 黄色',
            'type': '估值偏高',
            'message': f"{ts_code} PE 分位{pe_percentile:.1%} > {thresholds['pe_percentile_yellow']:.0%}，关注",
            'action': '关注',
        }
    else:
        return {
            'ts_code': ts_code,
            'level': '✅ 正常',
            'type': '估值',
            'message': f"{ts_code} PE 分位{pe_percentile:.1%}，正常",
            'action': '无',
        }

def check_fundamental_alert(ts_code: str, financial_data: dict) -> list:
    """
    基本面预警（检查项 21-26）
    ROE/毛利率/负债率/现金流/营收/净利润跟踪
    """
    alerts = []
    thresholds = config['alert_thresholds']
    
    # 1. ROE 跟踪（检查项 21）
    roe_decline = financial_data.get('roe_decline', 0)
    if roe_decline > 0.10:
        alerts.append({
            'ts_code': ts_code,
            'level': '🔴 红色',
            'type': 'ROE 恶化',
            'message': f"{ts_code} ROE 下降{roe_decline:.1%} > 10%，基本面恶化",
            'action': '重新评估',
        })
    elif roe_decline > 0.05:
        alerts.append({
            'ts_code': ts_code,
            'level': '🟠 橙色',
            'type': 'ROE 恶化',
            'message': f"{ts_code} ROE 下降{roe_decline:.1%} > 5%，启动深度分析",
            'action': '启动深度分析',
        })
    elif roe_decline > 0.03:
        alerts.append({
            'ts_code': ts_code,
            'level': '⚠️ 黄色',
            'type': 'ROE 下滑',
            'message': f"{ts_code} ROE 下降{roe_decline:.1%} > 3%，关注",
            'action': '关注',
        })
    
    # 2. 毛利率跟踪（检查项 22）
    gross_margin_decline = financial_data.get('gross_margin_decline', 0)
    if gross_margin_decline > 0.05:
        alerts.append({
            'ts_code': ts_code,
            'level': '🟠 橙色',
            'type': '毛利率恶化',
            'message': f"{ts_code} 毛利率下降{gross_margin_decline:.1%} > 5%，查原因",
            'action': '查原因',
        })
    
    # 3. 负债率跟踪（检查项 23）
    debt_ratio = financial_data.get('debt_ratio', 0)
    if debt_ratio > thresholds['debt_ratio_red']:
        alerts.append({
            'ts_code': ts_code,
            'level': '🔴 红色',
            'type': '负债率过高',
            'message': f"{ts_code} 负债率{debt_ratio:.1%} > 70%，财务风险",
            'action': '查有息负债',
        })
    
    # 4. 现金流跟踪（检查项 24）
    cf_ratio = financial_data.get('cash_flow_ratio', 1)
    if cf_ratio < thresholds['cash_flow_ratio_orange']:
        alerts.append({
            'ts_code': ts_code,
            'level': '🟠 橙色',
            'type': '现金流恶化',
            'message': f"{ts_code} 现金流/净利润{cf_ratio:.2f} < 0.5，查应收账款",
            'action': '查应收账款',
        })
    elif cf_ratio < thresholds['cash_flow_ratio_yellow']:
        alerts.append({
            'ts_code': ts_code,
            'level': '⚠️ 黄色',
            'type': '现金流下滑',
            'message': f"{ts_code} 现金流/净利润{cf_ratio:.2f} < 0.8，关注",
            'action': '关注',
        })
    
    return alerts

def check_management_alert(ts_code: str, management_data: dict) -> dict:
    """
    管理层跟踪（检查项 29）
    减持/高管离职/关联交易激增
    """
    # 诚信评分
    integrity_score = management_data.get('integrity_score', 100)
    
    if integrity_score < 60:
        return {
            'ts_code': ts_code,
            'level': '🔴 红色',
            'type': '管理层诚信',
            'message': f"{ts_code} 诚信评分{integrity_score} < 60，警惕",
            'action': '重新评估诚信',
        }
    elif integrity_score < 80:
        return {
            'ts_code': ts_code,
            'level': '🟠 橙色',
            'type': '管理层诚信',
            'message': f"{ts_code} 诚信评分{integrity_score} < 80，关注",
            'action': '关注',
        }
    else:
        return {
            'ts_code': ts_code,
            'level': '✅ 正常',
            'type': '管理层诚信',
            'message': f"{ts_code} 诚信评分{integrity_score} ≥ 80，正常",
            'action': '无',
        }

def real_time_monitoring(portfolio: list) -> dict:
    """
    投资宪法：AI 实时监控持仓，触发🟠橙色才通知人工
    
    portfolio: 持仓列表
    [
        {
            'ts_code': '002270.SZ',
            'name': '华明装备',
            'pe_percentile': 0.94,
            'financial_data': {...},
            'management_data': {...},
        }
    ]
    """
    all_alerts = []
    
    for stock in portfolio:
        ts_code = stock['ts_code']
        
        # 1. 估值预警
        valuation_alert = check_valuation_alert(ts_code, stock.get('pe_percentile', 0))
        if valuation_alert['level'] in ['🔴 红色', '🟠 橙色']:
            all_alerts.append(valuation_alert)
        
        # 2. 基本面预警
        fundamental_alerts = check_fundamental_alert(ts_code, stock.get('financial_data', {}))
        all_alerts.extend(fundamental_alerts)
        
        # 3. 管理层预警
        management_alert = check_management_alert(ts_code, stock.get('management_data', {}))
        if management_alert['level'] in ['🔴 红色', '🟠 橙色']:
            all_alerts.append(management_alert)
    
    # 按严重程度排序
    level_order = {'🔴 红色': 0, '🟠 橙色': 1, '⚠️ 黄色': 2, '✅ 正常': 3}
    all_alerts.sort(key=lambda x: level_order.get(x['level'], 3))
    
    return {
        'timestamp': datetime.now().isoformat(),
        'portfolio_size': len(portfolio),
        'alerts': all_alerts,
        'summary': {
            'red': sum(1 for a in all_alerts if a['level'] == '🔴 红色'),
            'orange': sum(1 for a in all_alerts if a['level'] == '🟠 橙色'),
            'yellow': sum(1 for a in all_alerts if a['level'] == '⚠️ 黄色'),
        }
    }

# 测试
if __name__ == '__main__':
    print("=== 实时监控预警测试 ===\n")
    
    # 模拟持仓
    portfolio = [
        {
            'ts_code': '002270.SZ',
            'name': '华明装备',
            'pe_percentile': 0.94,
            'financial_data': {
                'roe_decline': 0.02,
                'gross_margin_decline': 0.01,
                'debt_ratio': 0.39,
                'cash_flow_ratio': 0.85,
            },
            'management_data': {
                'integrity_score': 85,
            },
        },
        {
            'ts_code': '000001.SZ',
            'name': '平安银行',
            'pe_percentile': 0.10,
            'financial_data': {
                'roe_decline': 0.08,
                'gross_margin_decline': 0.06,
                'debt_ratio': 0.90,
                'cash_flow_ratio': 0.40,
            },
            'management_data': {
                'integrity_score': 75,
            },
        },
    ]
    
    result = real_time_monitoring(portfolio)
    
    print(f"监控时间：{result['timestamp']}")
    print(f"持仓数量：{result['portfolio_size']}")
    print(f"\n预警汇总：")
    print(f"  🔴 红色：{result['summary']['red']}")
    print(f"  🟠 橙色：{result['summary']['orange']}")
    print(f"  ⚠️ 黄色：{result['summary']['yellow']}")
    
    if result['alerts']:
        print(f"\n预警详情：")
        for alert in result['alerts']:
            print(f"  {alert['level']} {alert['type']}: {alert['message']}")
            print(f"     行动：{alert['action']}")
