"""
A 股本土化风险量化（P2）
投资宪法：Stop Doing List 的 A 股特有條款
"""

from typing import Dict, List

def check_st_risk(ts_code: str, stock_info: Dict) -> Dict:
    """
    ST 股/退市风险检查
    """
    is_st = stock_info.get('is_st', False)
    delisting_risk = stock_info.get('delisting_risk', False)
    
    if is_st or delisting_risk:
        return {
            'ts_code': ts_code,
            'risk_type': 'ST/退市风险',
            'level': '🔴 高危',
            'message': f"{ts_code} {'ST 股' if is_st else '退市风险'}，立即排除",
            'action': '排除',
        }
    else:
        return {
            'ts_code': ts_code,
            'risk_type': 'ST/退市风险',
            'level': '✅ 无风险',
            'message': f"{ts_code} 非 ST 股，无退市风险",
            'action': '无',
        }

def check_pledge_reduction(ts_code: str, stock_info: Dict) -> Dict:
    """
    高质押 + 减持检查
    投资宪法：不投高质押 + 减持（质押率>50% 且大股东减持）
    """
    pledge_ratio = stock_info.get('pledge_ratio', 0)  # 质押率
    reduction_ratio = stock_info.get('reduction_ratio', 0)  # 减持比例
    
    if pledge_ratio > 0.50 and reduction_ratio > 0:
        return {
            'ts_code': ts_code,
            'risk_type': '高质押 + 减持',
            'level': '🔴 高危',
            'message': f"{ts_code} 质押率{pledge_ratio:.1%} + 减持{reduction_ratio:.1%}，2018 年爆仓潮教训",
            'action': '排除',
        }
    elif pledge_ratio > 0.50:
        return {
            'ts_code': ts_code,
            'risk_type': '高质押',
            'level': '🟠 中危',
            'message': f"{ts_code} 质押率{pledge_ratio:.1%} > 50%，关注",
            'action': '关注',
        }
    elif reduction_ratio > 0.05:
        return {
            'ts_code': ts_code,
            'risk_type': '大股东减持',
            'level': '🟠 中危',
            'message': f"{ts_code} 减持{reduction_ratio:.1%} > 5%，关注",
            'action': '关注',
        }
    else:
        return {
            'ts_code': ts_code,
            'risk_type': '质押 + 减持',
            'level': '✅ 无风险',
            'message': f"{ts_code} 质押率{pledge_ratio:.1%}，无减持",
            'action': '无',
        }

def check_financial_fraud(ts_code: str, stock_info: Dict) -> Dict:
    """
    财务造假嫌疑检查
    投资宪法：不投财务造假（审计非标/被立案调查）
    """
    audit_opinion = stock_info.get('audit_opinion', '标准无保留')
    under_investigation = stock_info.get('under_investigation', False)
    
    if audit_opinion != '标准无保留' or under_investigation:
        return {
            'ts_code': ts_code,
            'risk_type': '财务造假嫌疑',
            'level': '🔴 高危',
            'message': f"{ts_code} {'审计非标' if audit_opinion != '标准无保留' else '被立案调查'}，立即排除",
            'action': '排除',
        }
    else:
        return {
            'ts_code': ts_code,
            'risk_type': '财务造假嫌疑',
            'level': '✅ 无风险',
            'message': f"{ts_code} 审计标准，无调查",
            'action': '无',
        }

def check_liquidity_risk(ts_code: str, stock_info: Dict) -> Dict:
    """
    流动性风险检查
    投资宪法：不投流动性差（日均成交<5000 万）
    """
    avg_volume = stock_info.get('avg_volume_20d', 0)  # 近 20 日日均成交额
    
    if avg_volume < 50000000:
        return {
            'ts_code': ts_code,
            'risk_type': '流动性风险',
            'level': '🟠 中危',
            'message': f"{ts_code} 日均成交¥{avg_volume/1e8:.2f}亿 < ¥0.50 亿，避免无法卖出",
            'action': '排除',
        }
    else:
        return {
            'ts_code': ts_code,
            'risk_type': '流动性风险',
            'level': '✅ 无风险',
            'message': f"{ts_code} 日均成交¥{avg_volume/1e8:.2f}亿，流动性良好",
            'action': '无',
        }

def check_margin_financing_risk(ts_code: str, stock_info: Dict) -> Dict:
    """
    融资盘过高风险检查
    投资宪法：不投融资盘过高（融资盘>30%）
    """
    margin_ratio = stock_info.get('margin_ratio', 0)  # 融资盘占比
    
    if margin_ratio > 0.30:
        return {
            'ts_code': ts_code,
            'risk_type': '融资盘过高',
            'level': '🟠 中危',
            'message': f"{ts_code} 融资盘{margin_ratio:.1%} > 30%，波动风险大",
            'action': '关注',
        }
    else:
        return {
            'ts_code': ts_code,
            'risk_type': '融资盘风险',
            'level': '✅ 无风险',
            'message': f"{ts_code} 融资盘{margin_ratio:.1%}，正常",
            'action': '无',
        }

def check_northbound_flow(ts_code: str, stock_info: Dict) -> Dict:
    """
    北向资金异动检查
    投资宪法：A 股特有指标
    """
    northbound_holding = stock_info.get('northbound_holding', 0)  # 北向持仓占比
    northbound_flow_30d = stock_info.get('northbound_flow_30d', 0)  # 30 天流向
    
    if northbound_holding > 0.10 and northbound_flow_30d < -0.20:
        return {
            'ts_code': ts_code,
            'risk_type': '北向资金大幅流出',
            'level': '🟠 中危',
            'message': f"{ts_code} 北向持仓{northbound_holding:.1%}，30 天流出{northbound_flow_30d:.1%}",
            'action': '关注',
        }
    elif northbound_holding > 0.10 and northbound_flow_30d > 0.20:
        return {
            'ts_code': ts_code,
            'risk_type': '北向资金大幅流入',
            'level': '✅ 利好',
            'message': f"{ts_code} 北向持仓{northbound_holding:.1%}，30 天流入{northbound_flow_30d:.1%}",
            'action': '看好',
        }
    elif northbound_holding < 0.01:
        return {
            'ts_code': ts_code,
            'risk_type': '无北向关注',
            'level': '⚠️ 关注',
            'message': f"{ts_code} 北向持仓{northbound_holding:.1%} < 1%，流动性可能不足",
            'action': '关注',
        }
    else:
        return {
            'ts_code': ts_code,
            'risk_type': '北向资金',
            'level': '✅ 正常',
            'message': f"{ts_code} 北向持仓{northbound_holding:.1%}，30 天流向{northbound_flow_30d:.1%}",
            'action': '无',
        }

def comprehensive_risk_assessment(ts_code: str, stock_info: Dict) -> Dict:
    """
    综合风险评估
    """
    risks = []
    
    # 执行所有风险检查
    risks.append(check_st_risk(ts_code, stock_info))
    risks.append(check_pledge_reduction(ts_code, stock_info))
    risks.append(check_financial_fraud(ts_code, stock_info))
    risks.append(check_liquidity_risk(ts_code, stock_info))
    risks.append(check_margin_financing_risk(ts_code, stock_info))
    risks.append(check_northbound_flow(ts_code, stock_info))
    
    # 统计风险等级
    red_count = sum(1 for r in risks if r['level'] == '🔴 高危')
    orange_count = sum(1 for r in risks if r['level'] == '🟠 中危')
    
    # 综合判断
    if red_count > 0:
        conclusion = '❌ 排除（高危风险）'
    elif orange_count >= 2:
        conclusion = '⚠️ 谨慎（多个中危风险）'
    elif orange_count == 1:
        conclusion = '⚠️ 关注（单个中危风险）'
    else:
        conclusion = '✅ 通过（无重大风险）'
    
    return {
        'ts_code': ts_code,
        'risks': risks,
        'summary': {
            'red': red_count,
            'orange': orange_count,
        },
        'conclusion': conclusion,
    }

# 测试
if __name__ == '__main__':
    print("=== A 股本土化风险量化测试 ===\n")
    
    # 测试华明装备
    print("1. 华明装备 (002270.SZ) 风险评估：")
    result = comprehensive_risk_assessment('002270.SZ', {
        'is_st': False,
        'delisting_risk': False,
        'pledge_ratio': 0.05,
        'reduction_ratio': 0.00,
        'audit_opinion': '标准无保留',
        'under_investigation': False,
        'avg_volume_20d': 7.85e8,
        'margin_ratio': 0.05,
        'northbound_holding': 0.03,
        'northbound_flow_30d': 0.05,
    })
    
    print(f"   综合结论：{result['conclusion']}")
    print(f"   风险汇总：🔴{result['summary']['red']} 🟠{result['summary']['orange']}")
    
    for risk in result['risks']:
        if risk['level'] != '✅ 无风险':
            print(f"   {risk['level']} {risk['risk_type']}: {risk['message']}")
    print()
    
    # 测试高风险股票
    print("2. 高风险股票模拟测试：")
    result = comprehensive_risk_assessment('000001.SZ', {
        'is_st': False,
        'delisting_risk': False,
        'pledge_ratio': 0.60,  # 高质押
        'reduction_ratio': 0.10,  # 减持
        'audit_opinion': '标准无保留',
        'under_investigation': False,
        'avg_volume_20d': 5e8,
        'margin_ratio': 0.35,  # 融资盘高
        'northbound_holding': 0.15,
        'northbound_flow_30d': -0.25,  # 北向流出
    })
    
    print(f"   综合结论：{result['conclusion']}")
    print(f"   风险汇总：🔴{result['summary']['red']} 🟠{result['summary']['orange']}")
    
    for risk in result['risks']:
        if risk['level'] != '✅ 无风险':
            print(f"   {risk['level']} {risk['risk_type']}: {risk['message']}")
    print()
    
    print("✅ A 股本土化风险量化测试完成")
