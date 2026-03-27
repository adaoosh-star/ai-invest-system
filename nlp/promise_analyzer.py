"""
事实一致性校验（P2）
投资宪法：段永平"本分"的量化落地 - 验证管理层承诺兑现率
"""

import re
from typing import List, Dict, Tuple

def classify_promises(text: str) -> Dict[str, List[str]]:
    """
    改进点 1：承诺分类
    只有明确承诺才纳入校验，模糊承诺跳过
    """
    clear_promises = []  # 明确承诺："计划"、"将实现"、"目标"
    vague_promises = []  # 模糊承诺："力争"、"争取"、"努力"
    long_term_plans = []  # 长期规划：3 年期
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 明确承诺：纳入兑现率计算
        if any(keyword in line for keyword in ['计划', '将实现', '目标', '确保', '承诺']):
            clear_promises.append(line)
        # 模糊承诺：跳过，不纳入评分
        elif any(keyword in line for keyword in ['力争', '争取', '努力', '力争实现', '争取达到']):
            vague_promises.append(line)
        # 长期规划：单独跨年度跟踪
        elif any(keyword in line for keyword in ['三年', '五年', '中长期', '2025-2027']):
            long_term_plans.append(line)
    
    return {
        'clear_promises': clear_promises,
        'vague_promises': vague_promises,
        'long_term_plans': long_term_plans,
        'summary': {
            'clear_count': len(clear_promises),
            'vague_count': len(vague_promises),
            'long_term_count': len(long_term_plans),
        }
    }

def extract_quantitative_targets(promise_text: str) -> List[Dict]:
    """
    从承诺文本中提取量化目标
    """
    targets = []
    
    # 匹配数字和百分比
    patterns = [
        r'增长\s*(\d+(?:\.\d+)?)\s*%',  # 增长 X%
        r'达到\s*(\d+(?:\.\d+)?)\s*%',  # 达到 X%
        r'超过\s*(\d+(?:\.\d+)?)\s*%',  # 超过 X%
        r'不低于\s*(\d+(?:\.\d+)?)',  # 不低于 X
        r'实现\s*(\d+(?:\.\d+)?)\s*(?:亿元 | 亿)?',  # 实现 X 亿
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, promise_text)
        for match in matches:
            targets.append({
                'value': float(match),
                'unit': '%' if '%' in pattern else '绝对值',
                'text': promise_text,
            })
    
    return targets

def calculate_fulfillment_rate(promises: List[str], actual_data: Dict) -> Dict:
    """
    计算承诺兑现率
    
    promises: 明确承诺列表
    actual_data: 实际完成数据
    {
        'revenue_growth': 0.15,  # 营收增长 15%
        'net_profit_growth': 0.20,  # 净利润增长 20%
        'roe': 0.18,  # ROE 18%
        'dividend_ratio': 0.30,  # 分红率 30%
    }
    """
    if not promises:
        return {
            'fulfillment_rate': None,
            'reason': '无明确承诺',
            'details': [],
        }
    
    fulfilled_count = 0
    total_count = 0
    details = []
    
    for promise in promises:
        targets = extract_quantitative_targets(promise)
        
        if not targets:
            # 无法量化的承诺，跳过
            continue
        
        total_count += 1
        fulfilled = True
        
        for target in targets:
            # 判断承诺类型
            if '营收' in promise or '收入' in promise:
                actual = actual_data.get('revenue_growth', 0)
            elif '利润' in promise or '净利润' in promise:
                actual = actual_data.get('net_profit_growth', 0)
            elif 'ROE' in promise or '净资产收益率' in promise:
                actual = actual_data.get('roe', 0)
            elif '分红' in promise:
                actual = actual_data.get('dividend_ratio', 0)
            else:
                # 无法匹配，假设兑现
                actual = target['value']
            
            # 判断是否兑现
            if actual >= target['value'] * 0.9:  # 90% 以上算兑现
                fulfilled = True
            else:
                fulfilled = False
        
        if fulfilled:
            fulfilled_count += 1
        
        details.append({
            'promise': promise,
            'fulfilled': fulfilled,
            'actual': actual if 'actual' in locals() else None,
        })
    
    fulfillment_rate = fulfilled_count / total_count if total_count > 0 else 0
    
    return {
        'fulfillment_rate': fulfillment_rate,
        'fulfilled_count': fulfilled_count,
        'total_count': total_count,
        'details': details,
    }

def management_integrity_score(ts_code: str, fulfillment_rate: float, other_factors: Dict) -> Dict:
    """
    管理层诚信评分（0-100 分）
    
    投资宪法：段永平"本分"的量化落地
    """
    score = 100
    
    # 1. 承诺兑现率（权重 40%）
    if fulfillment_rate is not None:
        score -= (1 - fulfillment_rate) * 40
    
    # 2. 关联交易（权重 20%）
    related_party_ratio = other_factors.get('related_party_ratio', 0)
    if related_party_ratio > 0.20:
        score -= 20
    elif related_party_ratio > 0.05:
        score -= 10
    
    # 3. 大股东减持（权重 20%）
    reduction_ratio = other_factors.get('shareholder_reduction', 0)
    if reduction_ratio > 0.20:
        score -= 20
    elif reduction_ratio > 0.05:
        score -= 10
    
    # 4. 审计意见（权重 10%）
    audit_opinion = other_factors.get('audit_opinion', '标准无保留')
    if audit_opinion != '标准无保留':
        score -= 10
    
    # 5. 诉讼记录（权重 10%）
    lawsuits = other_factors.get('major_lawsuits', 0)
    if lawsuits > 0:
        score -= 10
    
    # 确保分数在 0-100 之间
    score = max(0, min(100, score))
    
    # 判断
    if score >= 80:
        level = '✅ 诚信'
    elif score >= 60:
        level = '⚠️ 待查'
    else:
        level = '❌ 不诚信'
    
    return {
        'ts_code': ts_code,
        'score': score,
        'level': level,
        'fulfillment_rate': fulfillment_rate,
        'breakdown': {
            'promise_fulfillment': (1 - (1 - fulfillment_rate) * 40) if fulfillment_rate is not None else 100,
            'related_party': 100 - (20 if related_party_ratio > 0.20 else 10 if related_party_ratio > 0.05 else 0),
            'shareholder_reduction': 100 - (20 if reduction_ratio > 0.20 else 10 if reduction_ratio > 0.05 else 0),
            'audit_opinion': 100 if audit_opinion == '标准无保留' else 90,
            'lawsuits': 100 if lawsuits == 0 else 90,
        }
    }

# 测试
if __name__ == '__main__':
    print("=== 事实一致性校验测试 ===\n")
    
    # 模拟年报承诺文本
    annual_report_text = """
    2025 年经营计划：
    1. 计划实现营业收入增长 15%
    2. 力争实现净利润增长 20%
    3. 目标 ROE 达到 18%
    4. 确保分红比例不低于 30%
    5. 争取扩大市场份额
    6. 三年发展规划：2025-2027 年营收 CAGR≥20%
    """
    
    # 1. 承诺分类
    print("1. 承诺分类测试：")
    promises = classify_promises(annual_report_text)
    print(f"   明确承诺：{promises['summary']['clear_count']}条（纳入校验）")
    print(f"   模糊承诺：{promises['summary']['vague_count']}条（跳过）")
    print(f"   长期规划：{promises['summary']['long_term_count']}条（跨年度跟踪）")
    print()
    
    # 2. 兑现率计算
    print("2. 兑现率计算测试：")
    actual_data = {
        'revenue_growth': 0.18,  # 实际增长 18%（目标 15%）
        'net_profit_growth': 0.15,  # 实际增长 15%（模糊承诺，不纳入）
        'roe': 0.20,  # 实际 ROE 20%（目标 18%）
        'dividend_ratio': 0.35,  # 实际分红 35%（目标 30%）
    }
    
    fulfillment = calculate_fulfillment_rate(promises['clear_promises'], actual_data)
    print(f"   兑现率：{fulfillment['fulfillment_rate']:.0%}" if fulfillment['fulfillment_rate'] else f"   {fulfillment['reason']}")
    print()
    
    # 3. 诚信评分
    print("3. 诚信评分测试：")
    integrity = management_integrity_score('002270.SZ', fulfillment.get('fulfillment_rate'), {
        'related_party_ratio': 0.02,
        'shareholder_reduction': 0.00,
        'audit_opinion': '标准无保留',
        'major_lawsuits': 0,
    })
    print(f"   华明装备诚信评分：{integrity['score']}分 ({integrity['level']})")
    print()
    
    print("✅ 事实一致性校验测试完成")
