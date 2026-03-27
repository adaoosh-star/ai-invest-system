"""
交叉验证机制
投资宪法：数据一致性校验 + 行业适配（改进点 5）
"""

import yaml
from pathlib import Path

# 加载配置
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'thresholds.yaml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

def cross_validate_annual_report(ts_code: str, annual_report_data: dict, tushare_data: dict) -> dict:
    """
    年报数据 vs Tushare 数据交叉验证
    投资宪法：差异>5% 自动预警
    """
    issues = []
    
    # 营收对比
    if 'revenue' in annual_report_data and 'revenue' in tushare_data:
        diff = abs(annual_report_data['revenue'] - tushare_data['revenue'])
        diff_rate = diff / tushare_data['revenue']
        if diff_rate > 0.05:
            issues.append({
                'field': '营收',
                'annual_report': annual_report_data['revenue'],
                'tushare': tushare_data['revenue'],
                'diff_rate': diff_rate,
                'alert': f"{ts_code} 营收差异{diff_rate:.2%}，需人工核查"
            })
    
    # 净利润对比
    if 'net_profit' in annual_report_data and 'net_profit' in tushare_data:
        diff = abs(annual_report_data['net_profit'] - tushare_data['net_profit'])
        diff_rate = diff / tushare_data['net_profit']
        if diff_rate > 0.05:
            issues.append({
                'field': '净利润',
                'annual_report': annual_report_data['net_profit'],
                'tushare': tushare_data['net_profit'],
                'diff_rate': diff_rate,
                'alert': f"{ts_code} 净利润差异{diff_rate:.2%}，需人工核查"
            })
    
    return {
        'ts_code': ts_code,
        'is_valid': len(issues) == 0,
        'issues': issues,
    }

def check_revenue_cf_divergence(ts_code: str, industry: str, revenue_growth: float, cash_flow_growth: float) -> dict:
    """
    改进点 5：营收 - 现金流背离判断的行业适配
    
    消费行业：营收增长>20% 且现金流下降>10% → 预警
    制造业：营收增长>30% 且现金流下降>20% → 预警（旺季备货会短期背离）
    """
    # 获取行业阈值
    if industry == '制造业':
        # 制造业旺季备货、大客户账期拉长会短期背离
        revenue_threshold = 0.30
        cf_threshold = -0.20
        reason = "制造业阈值（旺季备货/大客户账期）"
    else:
        # 消费行业用通用标准
        revenue_threshold = 0.20
        cf_threshold = -0.10
        reason = "通用标准"
    
    # 判断
    if revenue_growth > revenue_threshold and cash_flow_growth < cf_threshold:
        return {
            'ts_code': ts_code,
            'industry': industry,
            'revenue_growth': revenue_growth,
            'cash_flow_growth': cash_flow_growth,
            'is_abnormal': True,
            'alert': f"⚠️ {ts_code} 营收增长{revenue_growth:.1%}，现金流下降{-cash_flow_growth:.1%}，需关注（{reason}）",
        }
    
    return {
        'ts_code': ts_code,
        'industry': industry,
        'revenue_growth': revenue_growth,
        'cash_flow_growth': cash_flow_growth,
        'is_abnormal': False,
        'alert': f"✅ {ts_code} 营收与现金流匹配",
    }

def validate_data_consistency(ts_code: str, data_sources: dict) -> dict:
    """
    综合数据一致性验证
    """
    results = []
    
    # 1. 年报 vs Tushare
    if 'annual_report' in data_sources and 'tushare' in data_sources:
        result = cross_validate_annual_report(
            ts_code,
            data_sources['annual_report'],
            data_sources['tushare']
        )
        results.append(result)
    
    # 2. 营收 - 现金流匹配性
    if 'industry' in data_sources and 'revenue_growth' in data_sources and 'cash_flow_growth' in data_sources:
        result = check_revenue_cf_divergence(
            ts_code,
            data_sources['industry'],
            data_sources['revenue_growth'],
            data_sources['cash_flow_growth']
        )
        results.append(result)
    
    # 综合判断
    has_issues = any(r.get('is_abnormal', False) or not r.get('is_valid', True) for r in results)
    
    return {
        'ts_code': ts_code,
        'is_valid': not has_issues,
        'results': results,
    }

# 测试
if __name__ == '__main__':
    # 测试制造业背离判断
    result_mfg = check_revenue_cf_divergence('002270.SZ', '制造业', 0.35, -0.15)
    print(f"制造业测试：{result_mfg}")
    
    # 测试消费行业背离判断
    result_consumer = check_revenue_cf_divergence('000858.SZ', '消费', 0.25, -0.15)
    print(f"消费行业测试：{result_consumer}")
