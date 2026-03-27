"""
双轨阈值模型
投资宪法：通用底线不变，行业优秀线可调整
"""

import yaml
from pathlib import Path

# 加载配置
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'thresholds.yaml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

def get_industry_threshold(industry: str) -> dict:
    """
    获取行业差异化优秀阈值
    """
    default = {'roe_excellent': 0.12, 'gross_margin_excellent': 0.25}
    return config['industry_excellent'].get(industry, default)

def check_hard_bottom(ts_code: str, financial_data: dict) -> dict:
    """
    投资宪法：通用硬底线检查
    ROE≥10%、现金流≥0.8、负债≤70%
    """
    issues = []
    passed = True
    
    # 1. ROE 连续 3 年≥10%
    roe_avg = financial_data.get('roe_avg_3y', 0)
    if roe_avg < config['hard_bottom']['roe_min']:
        issues.append(f"ROE 连续 3 年平均{roe_avg:.1%} < {config['hard_bottom']['roe_min']:.0%}")
        passed = False
    
    # 2. 现金流/净利润≥0.8
    cf_ratio = financial_data.get('cash_flow_ratio', 0)
    if cf_ratio < config['hard_bottom']['cash_flow_ratio_min']:
        issues.append(f"现金流/净利润{cf_ratio:.2f} < {config['hard_bottom']['cash_flow_ratio_min']}")
        passed = False
    
    # 3. 负债率≤70%
    debt_ratio = financial_data.get('debt_ratio', 1)
    if debt_ratio > config['hard_bottom']['debt_ratio_max']:
        issues.append(f"负债率{debt_ratio:.1%} > {config['hard_bottom']['debt_ratio_max']:.0%}")
        passed = False
    
    return {
        'ts_code': ts_code,
        'passed': passed,
        'issues': issues,
    }

def check_excellent_line(ts_code: str, industry: str, financial_data: dict) -> dict:
    """
    行业差异化优秀线检查
    过了硬底线后，筛选优秀公司
    """
    threshold = get_industry_threshold(industry)
    issues = []
    score = 0
    max_score = 0
    
    # ROE 优秀线
    roe_avg = financial_data.get('roe_avg_3y', 0)
    if threshold['roe_excellent']:
        max_score += 1
        if roe_avg >= threshold['roe_excellent']:
            score += 1
        else:
            issues.append(f"ROE{roe_avg:.1%} < {industry}优秀线{threshold['roe_excellent']:.0%}")
    
    # 毛利率优秀线
    gross_margin = financial_data.get('gross_margin', 0)
    if threshold.get('gross_margin_excellent'):
        max_score += 1
        if gross_margin >= threshold['gross_margin_excellent']:
            score += 1
        else:
            issues.append(f"毛利率{gross_margin:.1%} < {industry}优秀线{threshold['gross_margin_excellent']:.0%}")
    
    return {
        'ts_code': ts_code,
        'industry': industry,
        'score': score,
        'max_score': max_score,
        'pass_rate': score / max_score if max_score > 0 else 0,
        'issues': issues,
        'is_excellent': score == max_score,
    }

def calculate_safety_margin(market_pe_percentile: float, bond_yield: float = 0.025) -> float:
    """
    改进点 4：安全边际动态校准
    根据全市场估值水位 + 无风险利率，调整买入门槛
    """
    # 低利率适配：10 年期国债<2.5%，PE 分位阈值下调 5%（相当于门槛放宽）
    if bond_yield < config['safety_margin']['bond_yield_threshold']:
        market_pe_percentile = market_pe_percentile * (1 - config['safety_margin']['bond_yield_adjustment'])
    
    # 根据 PE 分位返回折扣率
    if market_pe_percentile > config['safety_margin']['extreme_high']:
        return config['safety_margin']['discount_extreme_high']  # 6 折
    elif market_pe_percentile > config['safety_margin']['high']:
        return config['safety_margin']['discount_high']  # 7 折
    elif market_pe_percentile > config['safety_margin']['reasonable']:
        return config['safety_margin']['discount_reasonable']  # 8 折
    elif market_pe_percentile > config['safety_margin']['low']:
        return config['safety_margin']['discount_low']  # 85 折
    else:
        return config['safety_margin']['discount_extreme_low']  # 9 折

# 测试
if __name__ == '__main__':
    # 测试硬底线检查
    print("=== 硬底线测试 ===")
    result = check_hard_bottom('002270.SZ', {
        'roe_avg_3y': 0.22,
        'cash_flow_ratio': 1.16,
        'debt_ratio': 0.39,
    })
    print(f"华明装备：{'✅ 通过' if result['passed'] else '❌ 不通过'}")
    if result['issues']:
        print(f"问题：{result['issues']}")
    print()
    
    # 测试行业优秀线
    print("=== 行业优秀线测试 ===")
    result = check_excellent_line('002270.SZ', '制造业', {
        'roe_avg_3y': 0.22,
        'gross_margin': 0.54,
    })
    print(f"华明装备（制造业）：得分{result['score']}/{result['max_score']} ({result['pass_rate']:.0%})")
    print(f"是否优秀：{'✅ 是' if result['is_excellent'] else '⚠️ 否'}")
    if result['issues']:
        print(f"问题：{result['issues']}")
    print()
    
    # 测试安全边际动态校准
    print("=== 安全边际动态校准测试 ===")
    test_cases = [
        (0.95, 0.025, "市场极度泡沫"),
        (0.75, 0.025, "市场偏贵"),
        (0.50, 0.025, "市场合理"),
        (0.15, 0.025, "市场偏便宜"),
        (0.05, 0.025, "市场极度低估"),
        (0.95, 0.020, "市场极度泡沫 + 低利率"),
    ]
    
    for pe_pct, bond_yield, desc in test_cases:
        discount = calculate_safety_margin(pe_pct, bond_yield)
        print(f"{desc}（PE 分位{pe_pct:.0%}, 国债{bond_yield:.1%}）：要求{discount:.0%}折")
