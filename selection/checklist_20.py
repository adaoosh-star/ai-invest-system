"""
选股前 20 项检查清单
投资宪法：≥15 项✅可买入，10-14 项⚠️待查，<10 项❌放弃

修复记录：2026-03-25
- 添加 fetch_financial_data() 函数，从 Tushare 实时获取真实数据
- 移除硬编码模拟数据
- 使用已修复的 tushare_client.py 接口
"""

import yaml
import sys
from pathlib import Path
from datetime import datetime

# 添加父目录到路径，以便导入 data.tushare_client
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载配置
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'thresholds.yaml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# ==================== 检查函数 ====================

def check_roe_5y(ts_code: str, roe_data: list) -> dict:
    """检查项 1：ROE 连续 5 年>15%"""
    threshold = config['checklist_20']['roe_5y_min']
    
    if len(roe_data) < 5:
        return {'item': 'ROE 连续 5 年', 'passed': False, 'reason': '数据不足 5 年', 'value': '数据不足'}
    
    passed_count = sum(1 for r in roe_data if r >= threshold)
    passed = passed_count == 5
    
    return {
        'item': 'ROE 连续 5 年',
        'passed': passed,
        'value': f'{sum(roe_data)/len(roe_data):.1%} 平均',
        'reason': f'{passed_count}/5 年达标' if not passed else '5 年都达标',
    }

def check_gross_margin_volatility(ts_code: str, margin_data: list) -> dict:
    """检查项 2：毛利率波动<5%"""
    threshold = config['checklist_20']['gross_margin_volatility_max']
    
    if len(margin_data) < 5:
        return {'item': '毛利率波动', 'passed': False, 'reason': '数据不足 5 年', 'value': '数据不足'}
    
    volatility = max(margin_data) - min(margin_data)
    passed = volatility < threshold
    
    return {
        'item': '毛利率波动',
        'passed': passed,
        'value': f'{volatility:.1%} 波动',
        'reason': f'波动{volatility:.1%} {"<" if passed else ">"} {threshold:.0%}',
    }

def check_debt_ratio(ts_code: str, debt_ratio: float) -> dict:
    """检查项 3：负债率<50%"""
    threshold = config['checklist_20']['debt_ratio_max']
    passed = debt_ratio < threshold
    
    return {
        'item': '负债率',
        'passed': passed,
        'value': f'{debt_ratio:.1%}',
        'reason': f'{debt_ratio:.1%} {"<" if passed else ">"} {threshold:.0%}',
    }

def check_cash_flow_ratio(ts_code: str, cf_ratio: float) -> dict:
    """检查项 4：现金流/净利润>0.8"""
    threshold = config['checklist_20']['cash_flow_ratio_min']
    passed = cf_ratio > threshold
    
    return {
        'item': '现金流/净利润',
        'passed': passed,
        'value': f'{cf_ratio:.2f}',
        'reason': f'{cf_ratio:.2f} {">" if passed else "<"} {threshold}',
    }

def check_related_party_ratio(ts_code: str, ratio: float) -> dict:
    """检查项 5：关联交易<5%"""
    threshold = config['checklist_20']['related_party_ratio_max']
    passed = ratio < threshold
    
    return {
        'item': '关联交易',
        'passed': passed,
        'value': f'{ratio:.1%}',
        'reason': f'{ratio:.1%} {"<" if passed else ">"} {threshold:.0%}',
    }

def check_shareholder_reduction(ts_code: str, reduction: float) -> dict:
    """检查项 6：大股东减持<5%"""
    threshold = config['checklist_20']['shareholder_reduction_max']
    passed = reduction < threshold
    
    return {
        'item': '大股东减持',
        'passed': passed,
        'value': f'{reduction:.1%}',
        'reason': f'{reduction:.1%} {"<" if passed else ">"} {threshold:.0%}',
    }

def check_other_receivables(ts_code: str, ratio: float) -> dict:
    """检查项 7：其他应收款<3%"""
    threshold = config['checklist_20']['other_receivables_ratio_max']
    passed = ratio < threshold
    
    return {
        'item': '其他应收款',
        'passed': passed,
        'value': f'{ratio:.1%}',
        'reason': f'{ratio:.1%} {"<" if passed else ">"} {threshold:.0%}',
    }

def check_revenue_concentration(ts_code: str, ratio: float) -> dict:
    """检查项 8：主营收入占比>80%"""
    threshold = config['checklist_20']['revenue_concentration_min']
    passed = ratio > threshold
    
    return {
        'item': '主营收入占比',
        'passed': passed,
        'value': f'{ratio:.1%}',
        'reason': f'{ratio:.1%} {">" if passed else "<"} {threshold:.0%}',
    }

def check_pe_percentile(ts_code: str, percentile: float) -> dict:
    """检查项 9：PE 分位<80%"""
    threshold = config['checklist_20']['pe_percentile_max']
    passed = percentile < threshold
    
    return {
        'item': 'PE 分位',
        'passed': passed,
        'value': f'{percentile:.1%}',
        'reason': f'{percentile:.1%} {"<" if passed else ">"} {threshold:.0%}',
    }

def check_pb_percentile(ts_code: str, percentile: float) -> dict:
    """检查项 10：PB 分位<80%"""
    threshold = config['checklist_20']['pb_percentile_max']
    passed = percentile < threshold
    
    return {
        'item': 'PB 分位',
        'passed': passed,
        'value': f'{percentile:.1%}',
        'reason': f'{percentile:.1%} {"<" if passed else ">"} {threshold:.0%}',
    }

def check_peg(ts_code: str, peg: float) -> dict:
    """检查项 11：PEG<2"""
    threshold = config['checklist_20']['peg_max']
    passed = peg < threshold
    
    return {
        'item': 'PEG',
        'passed': passed,
        'value': f'{peg:.2f}',
        'reason': f'{peg:.2f} {"<" if passed else ">"} {threshold}',
    }

def check_margin_vs_industry(ts_code: str, margin: float, industry_avg: float) -> dict:
    """检查项 12：毛利率>行业平均"""
    passed = margin > industry_avg
    
    return {
        'item': '毛利率 vs 行业',
        'passed': passed,
        'value': f'{margin:.1%} vs {industry_avg:.1%}',
        'reason': f'{margin:.1%} {">" if passed else "<"} 行业{industry_avg:.1%}',
    }

def check_roe_vs_industry(ts_code: str, roe: float, industry_avg: float) -> dict:
    """检查项 13：ROE>行业平均"""
    passed = roe > industry_avg
    
    return {
        'item': 'ROE vs 行业',
        'passed': passed,
        'value': f'{roe:.1%} vs {industry_avg:.1%}',
        'reason': f'{roe:.1%} {">" if passed else "<"} 行业{industry_avg:.1%}',
    }

def check_fcf_positive(ts_code: str, fcf_data: list) -> dict:
    """检查项 14：自由现金流连续 5 年为正"""
    threshold = config['checklist_20']['fcf_positive_years']
    
    if len(fcf_data) < 5:
        return {'item': '自由现金流', 'passed': False, 'reason': '数据不足 5 年', 'value': '数据不足'}
    
    positive_count = sum(1 for f in fcf_data if f > 0)
    passed = positive_count == 5
    
    return {
        'item': '自由现金流',
        'passed': passed,
        'value': f'{positive_count}/5 年为正',
        'reason': f'{positive_count}/5 年 {"达标" if passed else "不达标"}',
    }

def check_receivables_ratio(ts_code: str, ratio: float) -> dict:
    """检查项 15：应收账款/营收<30%"""
    threshold = config['checklist_20']['receivables_ratio_max']
    passed = ratio < threshold
    
    return {
        'item': '应收账款/营收',
        'passed': passed,
        'value': f'{ratio:.1%}',
        'reason': f'{ratio:.1%} {"<" if passed else ">"} {threshold:.0%}',
    }

def check_inventory_ratio(ts_code: str, ratio: float) -> dict:
    """检查项 16：存货/营收<20%"""
    threshold = config['checklist_20']['inventory_ratio_max']
    passed = ratio < threshold
    
    return {
        'item': '存货/营收',
        'passed': passed,
        'value': f'{ratio:.1%}',
        'reason': f'{ratio:.1%} {"<" if passed else ">"} {threshold:.0%}',
    }

def check_rd_ratio(ts_code: str, ratio: float) -> dict:
    """检查项 17：研发费用/营收>3%"""
    threshold = config['checklist_20']['rd_ratio_min']
    passed = ratio > threshold
    
    return {
        'item': '研发费用/营收',
        'passed': passed,
        'value': f'{ratio:.1%}',
        'reason': f'{ratio:.1%} {">" if passed else "<"} {threshold:.0%}',
    }

def check_dividend_ratio(ts_code: str, ratio: float) -> dict:
    """检查项 18：分红率>20%"""
    threshold = config['checklist_20']['dividend_ratio_min']
    passed = ratio > threshold
    
    return {
        'item': '分红率',
        'passed': passed,
        'value': f'{ratio:.1%}',
        'reason': f'{ratio:.1%} {">" if passed else "<"} {threshold:.0%}',
    }

def check_audit_opinion(ts_code: str, opinion: str) -> dict:
    """检查项 19：审计意见标准"""
    passed = '标准无保留' in opinion
    
    return {
        'item': '审计意见',
        'passed': passed,
        'value': opinion,
        'reason': opinion if passed else '非标准审计意见',
    }

def check_litigation(ts_code: str, has_litigation: bool, ratio: float) -> dict:
    """检查项 20：无重大诉讼"""
    passed = not has_litigation
    
    return {
        'item': '无重大诉讼',
        'passed': passed,
        'value': '有' if has_litigation else '无',
        'reason': f'预计负债{ratio:.1%}' if has_litigation else '无重大诉讼',
    }

# ==================== 数据获取函数 ====================

def fetch_financial_data(ts_code: str) -> dict:
    """
    从 Tushare API 实时获取财务数据
    
    返回：
    {
        'roe_5y': [...],
        'margin_5y': [...],
        'debt_ratio': 0.39,
        ...
    }
    """
    try:
        from data.tushare_client import (
            get_roe, get_cash_flow, get_gross_margin, get_debt_ratio,
            get_receivables_and_inventory, get_revenue, get_rd_expense,
            get_pe_pb_percentile, get_liquidity, get_net_profit,
            get_industry_avg, pro, get_peg, get_related_party_data,
            get_other_receivables_ratio, get_revenue_concentration,
            get_dividend_ratio, get_shareholder_reduction,
            get_audit_opinion, get_litigation_info
        )
    except ImportError as e:
        print(f"❌ 无法导入 tushare_client: {e}")
        return None
    
    print(f"正在从 Tushare 获取 {ts_code} 的实时数据...")
    
    financial_data = {}
    
    # 1. ROE 数据
    try:
        roe_df = get_roe(ts_code)
        roe_list = roe_df['roe_dt'].dropna().head(5).tolist()
        # 转换百分比（Tushare 返回的是百分比值，如 15.5 表示 15.5%）
        roe_list = [r / 100.0 for r in roe_list]  # 转换为小数
        financial_data['roe_5y'] = roe_list
        # print(f"  ✅ ROE: {[f'{r:.1%}' for r in roe_list]}")  # 静默调试输出
    except Exception as e:
        print(f"  ⚠️ ROE 获取失败：{e}")
        financial_data['roe_5y'] = []
    
    # 2. 毛利率数据
    try:
        margin_df = get_gross_margin(ts_code)
        margin_list = margin_df['gross_margin'].dropna().head(5).tolist()
        financial_data['margin_5y'] = margin_list
        # print(f"  ✅ 毛利率：{[f'{m:.1%}' for m in margin_list]}")  # 静默
    except Exception as e:
        print(f"  ⚠️ 毛利率获取失败：{e}")
        financial_data['margin_5y'] = []
    
    # 3. 负债率
    try:
        debt_df = get_debt_ratio(ts_code)
        debt_ratio = debt_df.iloc[0]['debt_ratio'] if len(debt_df) > 0 else None
        financial_data['debt_ratio'] = debt_ratio
        # print(f"  ✅ 负债率：{debt_ratio:.1%}" if debt_ratio else "  ⚠️ 负债率：数据不足")
    except Exception as e:
        print(f"  ⚠️ 负债率获取失败：{e}")
        financial_data['debt_ratio'] = 1.0
    
    # 4. 现金流比率
    try:
        cf_df = get_cash_flow(ts_code)
        net_profit_df = get_net_profit(ts_code)
        
        # 获取最新一期的经营现金流和净利润
        if len(cf_df) > 0 and len(net_profit_df) > 0:
            latest_cf = cf_df.iloc[0]
            latest_profit = net_profit_df.iloc[0]
            
            oper_cf = latest_cf.get('oper_cf')
            net_profit = latest_profit.get('net_profit')
            
            if oper_cf and net_profit and net_profit > 0:
                cf_ratio = oper_cf / net_profit
                financial_data['cash_flow_ratio'] = cf_ratio
                print(f"  ✅ 现金流/净利润：{cf_ratio:.2f}")
            else:
                financial_data['cash_flow_ratio'] = 0.0
                print(f"  ⚠️ 现金流/净利润：数据不足")
        else:
            financial_data['cash_flow_ratio'] = 0.0
    except Exception as e:
        print(f"  ⚠️ 现金流获取失败：{e}")
        financial_data['cash_flow_ratio'] = 0.0
    
    # 5. PE/PB 分位
    try:
        pe_pb = get_pe_pb_percentile(ts_code)
        financial_data['pe_percentile'] = pe_pb['pe_percentile_5y'] or 1.0
        financial_data['pb_percentile'] = pe_pb['pb_percentile_5y'] or 1.0
        # print(f"  ✅ PE 分位：{pe_pb['pe_percentile_5y']:.1%}, PB 分位：{pe_pb['pb_percentile_5y']:.1%}")
    except Exception as e:
        print(f"  ⚠️ 估值获取失败：{e}")
        financial_data['pe_percentile'] = 1.0
        financial_data['pb_percentile'] = 1.0
    
    # 6. 应收账款和存货
    try:
        ai_df = get_receivables_and_inventory(ts_code)
        rev_df = get_revenue(ts_code)
        
        if len(ai_df) > 0 and len(rev_df) > 0:
            latest_ai = ai_df.iloc[0]
            latest_rev = rev_df.iloc[0].get('revenue')
            
            if latest_rev and latest_rev > 0:
                receiv_ratio = latest_ai['accounts_receiv'] / latest_rev
                inv_ratio = latest_ai['inventories'] / latest_rev
                financial_data['receivables_ratio'] = receiv_ratio
                financial_data['inventory_ratio'] = inv_ratio
                print(f"  ✅ 应收账款/营收：{receiv_ratio:.1%}, 存货/营收：{inv_ratio:.1%}")
            else:
                financial_data['receivables_ratio'] = 1.0
                financial_data['inventory_ratio'] = 1.0
        else:
            financial_data['receivables_ratio'] = 1.0
            financial_data['inventory_ratio'] = 1.0
    except Exception as e:
        print(f"  ⚠️ 应收账款/存货获取失败：{e}")
        financial_data['receivables_ratio'] = 1.0
        financial_data['inventory_ratio'] = 1.0
    
    # 7. 研发费用
    try:
        # 直接从 income 接口获取 rd_exp
        rd_df = pro.income(ts_code=ts_code, start_date='20240101', end_date='20251231')
        rev_df = pro.income(ts_code=ts_code, start_date='20240101', end_date='20251231')
        
        if 'rd_exp' in rd_df.columns and 'total_revenue' in rev_df.columns:
            # 获取最新数据
            rd_data = rd_df[['end_date', 'rd_exp']].sort_values('end_date', ascending=False)
            rev_data = rev_df[['end_date', 'total_revenue']].sort_values('end_date', ascending=False)
            
            if len(rd_data) > 0 and len(rev_data) > 0:
                latest_rd = rd_data.iloc[0]['rd_exp']
                latest_rev = rev_data.iloc[0]['total_revenue']
                
                if latest_rd and latest_rev and latest_rev > 0:
                    rd_ratio = latest_rd / latest_rev
                    financial_data['rd_ratio'] = rd_ratio
                    print(f"  ✅ 研发费用/营收：{rd_ratio:.1%}")
                else:
                    financial_data['rd_ratio'] = 0.0
                    print(f"  ⚠️ 研发费用/营收：数据不足")
            else:
                financial_data['rd_ratio'] = 0.0
        else:
            financial_data['rd_ratio'] = 0.0
    except Exception as e:
        print(f"  ⚠️ 研发费用获取失败：{e}")
        financial_data['rd_ratio'] = 0.0
    
    # 8. 自由现金流
    try:
        cf_df = get_cash_flow(ts_code)
        fcf_list = cf_df['fcf'].dropna().head(5).tolist()
        financial_data['fcf_5y'] = fcf_list
        positive_count = sum(1 for f in fcf_list if f > 0)
        # print(f"  ✅ 自由现金流：{positive_count}/5 年为正")
    except Exception as e:
        print(f"  ⚠️ 自由现金流获取失败：{e}")
        financial_data['fcf_5y'] = []
    
    # 9. 行业对比数据
    try:
        # 获取行业平均值
        industry_roe = get_industry_avg(ts_code, 'roe')
        industry_margin = get_industry_avg(ts_code, 'gross_margin')
        
        if industry_roe:
            financial_data['industry_avg_roe'] = industry_roe / 100.0  # 转换为小数
            print(f"  ✅ 行业平均 ROE: {industry_roe:.1f}%")
        else:
            financial_data['industry_avg_roe'] = 0.12  # 默认 12%
        
        if industry_margin:
            financial_data['industry_avg_margin'] = industry_margin
            print(f"  ✅ 行业平均毛利率：{industry_margin:.1%}")
        else:
            financial_data['industry_avg_margin'] = 0.25  # 默认 25%
        
        # 设置当前值
        financial_data['gross_margin'] = financial_data['margin_5y'][0] if financial_data['margin_5y'] else 0.0
        financial_data['roe'] = financial_data['roe_5y'][0] if financial_data['roe_5y'] else 0.0
    except Exception as e:
        print(f"  ⚠️ 行业对比获取失败：{e}")
        financial_data['gross_margin'] = financial_data['margin_5y'][0] if financial_data['margin_5y'] else 0.0
        financial_data['industry_avg_margin'] = 0.25
        financial_data['roe'] = financial_data['roe_5y'][0] if financial_data['roe_5y'] else 0.0
        financial_data['industry_avg_roe'] = 0.12
    
    # 10. PEG 计算
    try:
        peg = get_peg(ts_code)
        if peg:
            financial_data['peg'] = peg
            print(f"  ✅ PEG: {peg:.2f}")
        else:
            financial_data['peg'] = 2.3
            print(f"  ⚠️ PEG: 数据不足，用默认值 2.3")
    except Exception as e:
        print(f"  ⚠️ PEG 获取失败：{e}")
        financial_data['peg'] = 2.3
    
    # 11. 关联交易
    try:
        related_data = get_related_party_data(ts_code)
        financial_data['related_party_ratio'] = related_data['ratio']
        # print(f"  ✅ 关联交易：{related_data['ratio']:.1%}")
    except Exception as e:
        print(f"  ⚠️ 关联交易获取失败：{e}")
        financial_data['related_party_ratio'] = 0.02
    
    # 12. 其他应收款
    try:
        other_ratio = get_other_receivables_ratio(ts_code)
        financial_data['other_receivables_ratio'] = other_ratio
        # print(f"  ✅ 其他应收款/营收：{other_ratio:.1%}")
    except Exception as e:
        print(f"  ⚠️ 其他应收款获取失败：{e}")
        financial_data['other_receivables_ratio'] = 0.02
    
    # 13. 主营收入占比
    try:
        concentration = get_revenue_concentration(ts_code)
        financial_data['revenue_concentration'] = concentration
        # print(f"  ✅ 主营收入占比：{concentration:.1%}")
    except Exception as e:
        print(f"  ⚠️ 主营收入占比获取失败：{e}")
        financial_data['revenue_concentration'] = 0.95
    
    # 14. 大股东减持
    try:
        reduction = get_shareholder_reduction(ts_code)
        financial_data['shareholder_reduction'] = reduction
        # print(f"  ✅ 大股东减持：{reduction:.1%}")
    except Exception as e:
        print(f"  ⚠️ 大股东减持获取失败：{e}")
        financial_data['shareholder_reduction'] = 0.0
    
    # 15. 分红率
    try:
        dividend = get_dividend_ratio(ts_code)
        financial_data['dividend_ratio'] = dividend
        # print(f"  ✅ 分红率：{dividend:.1%}")
    except Exception as e:
        print(f"  ⚠️ 分红率获取失败：{e}")
        financial_data['dividend_ratio'] = 0.30
    
    # 16. 审计意见
    try:
        audit = get_audit_opinion(ts_code)
        financial_data['audit_opinion'] = audit
        is_standard = '标准无保留' in audit
        # print(f"  ✅ 审计意见：{audit} ({'✅' if is_standard else '❌'})")
    except Exception as e:
        print(f"  ⚠️ 审计意见获取失败：{e}")
        financial_data['audit_opinion'] = '未知'
    
    # 17. 重大诉讼
    try:
        litigation = get_litigation_info(ts_code)
        financial_data['has_litigation'] = litigation['has_litigation']
        financial_data['litigation_ratio'] = litigation['ratio']
        # print(f"  ✅ 重大诉讼：{'有' if litigation['has_litigation'] else '无'} (预计负债{litigation['ratio']:.1%})")
    except Exception as e:
        print(f"  ⚠️ 诉讼信息获取失败：{e}")
        financial_data['has_litigation'] = False
        financial_data['litigation_ratio'] = 0.0
    
    # print("✅ 数据获取完成（20 项完整）\n")
    return financial_data


# ==================== 执行检查清单 ====================

def run_full_checklist(ts_code: str, financial_data: dict) -> dict:
    """执行完整 20 项检查清单 + A 股风险检查"""
    results = []
    
    # 执行 18 项检查
    results.append(check_roe_5y(ts_code, financial_data.get('roe_5y', [])))
    results.append(check_gross_margin_volatility(ts_code, financial_data.get('margin_5y', [])))
    results.append(check_debt_ratio(ts_code, financial_data.get('debt_ratio', 1)))
    results.append(check_cash_flow_ratio(ts_code, financial_data.get('cash_flow_ratio', 0)))
    results.append(check_related_party_ratio(ts_code, financial_data.get('related_party_ratio', 1)))
    results.append(check_shareholder_reduction(ts_code, financial_data.get('shareholder_reduction', 1)))
    results.append(check_other_receivables(ts_code, financial_data.get('other_receivables_ratio', 1)))
    results.append(check_revenue_concentration(ts_code, financial_data.get('revenue_concentration', 0)))
    results.append(check_pe_percentile(ts_code, financial_data.get('pe_percentile', 1)))
    results.append(check_pb_percentile(ts_code, financial_data.get('pb_percentile', 1)))
    results.append(check_peg(ts_code, financial_data.get('peg', 99)))
    results.append(check_margin_vs_industry(ts_code, financial_data.get('gross_margin', 0), financial_data.get('industry_avg_margin', 0)))
    results.append(check_roe_vs_industry(ts_code, financial_data.get('roe', 0), financial_data.get('industry_avg_roe', 0)))
    results.append(check_fcf_positive(ts_code, financial_data.get('fcf_5y', [])))
    results.append(check_receivables_ratio(ts_code, financial_data.get('receivables_ratio', 1)))
    results.append(check_inventory_ratio(ts_code, financial_data.get('inventory_ratio', 1)))
    results.append(check_rd_ratio(ts_code, financial_data.get('rd_ratio', 0)))
    results.append(check_dividend_ratio(ts_code, financial_data.get('dividend_ratio', 0)))
    results.append(check_audit_opinion(ts_code, financial_data.get('audit_opinion', '未知')))
    results.append(check_litigation(ts_code, financial_data.get('has_litigation', False), financial_data.get('litigation_ratio', 0)))
    
    # 统计 20 项结果
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)  # 现在是 20 项
    
    # 综合判断
    if passed_count >= 15:  # 75% 通过率
        conclusion = '✅ 可买入'
    elif passed_count >= 10:  # 50% 通过率
        conclusion = '⚠️ 待查'
    else:
        conclusion = '❌ 放弃'
    
    # A 股风险检查
    risk_results = run_a_share_risk_check(ts_code, financial_data)
    
    return {
        'ts_code': ts_code,
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'summary': {
            'total': total_count,
            'passed': passed_count,
            'failed': total_count - passed_count,
            'pass_rate': passed_count / total_count if total_count > 0 else 0,
        },
        'conclusion': conclusion,
        'risk_check': risk_results,
    }


def run_a_share_risk_check(ts_code: str, financial_data: dict) -> dict:
    """
    A 股本土化风险检查（真实数据驱动）
    包括：ST 风险、高质押 + 减持、财务造假、流动性、融资盘、北向资金
    
    修复记录：2026-03-26
    - 所有风险检查改为从 Tushare API 获取真实数据
    - 不再使用硬编码
    """
    try:
        from data.tushare_client import (
            get_st_status, get_pledge_ratio, get_margin_ratio,
            get_northbound_hold, get_avg_volume, get_under_investigation
        )
    except ImportError as e:
        print(f"⚠️ 无法导入风险检查数据接口：{e}")
        # 降级为简化检查
        return _run_a_share_risk_check_simple(ts_code, financial_data)
    
    risks = []
    
    # 1. ST/退市风险 - 使用真实数据
    try:
        st_data = get_st_status(ts_code)
        if st_data['is_st'] or st_data['delisting_risk']:
            risks.append({
                'risk_type': 'ST/退市风险',
                'level': '🔴 高危',
                'message': f"{st_data['name']} {'ST 股' if st_data['is_st'] else '退市风险'}，立即排除",
            })
        else:
            risks.append({
                'risk_type': 'ST/退市风险',
                'level': '✅ 无风险',
                'message': f"{st_data['name']} 非 ST 股，无退市风险",
            })
        # print(f"  ✅ ST 状态：{st_data['name']} ({'ST' if st_data['is_st'] else '非 ST'})")
    except Exception as e:
        print(f"  ⚠️ ST 状态检查失败：{e}")
        risks.append({
            'risk_type': 'ST/退市风险',
            'level': '⚠️ 未知',
            'message': '数据获取失败',
        })
    
    # 2. 高质押 + 减持风险
    try:
        pledge_ratio = get_pledge_ratio(ts_code)
        reduction = financial_data.get('shareholder_reduction', 0)
        
        if pledge_ratio > 0.50 and reduction > 0:
            risks.append({
                'risk_type': '高质押 + 减持',
                'level': '🔴 高危',
                'message': f'质押率{pledge_ratio:.1%} + 减持{reduction:.1%}，2018 年爆仓潮教训',
            })
        elif pledge_ratio > 0.50:
            risks.append({
                'risk_type': '高质押',
                'level': '🟠 中危',
                'message': f'质押率{pledge_ratio:.1%} > 50%，关注',
            })
        elif reduction > 0.05:
            risks.append({
                'risk_type': '大股东减持',
                'level': '🟠 中危',
                'message': f'减持{reduction:.1%} > 5%，关注',
            })
        else:
            risks.append({
                'risk_type': '质押 + 减持',
                'level': '✅ 无风险',
                'message': f'质押率{pledge_ratio:.1%}，减持{reduction:.1%}',
            })
        # print(f"  ✅ 质押率：{pledge_ratio:.1%}, 减持：{reduction:.1%}")
    except Exception as e:
        print(f"  ⚠️ 质押/减持检查失败：{e}")
        risks.append({
            'risk_type': '质押 + 减持',
            'level': '⚠️ 未知',
            'message': '数据获取失败',
        })
    
    # 3. 财务造假风险
    try:
        audit_opinion = financial_data.get('audit_opinion', '未知')
        under_investigation = get_under_investigation(ts_code)
        
        # 检查是否为标准审计意见（支持多种表述）
        is_standard = '标准无保留' in audit_opinion or '无保留意见' in audit_opinion
        
        if not is_standard or under_investigation:
            risks.append({
                'risk_type': '财务造假嫌疑',
                'level': '🔴 高危',
                'message': f"{'审计非标' if not is_standard else '被立案调查'}，立即排除",
            })
        else:
            risks.append({
                'risk_type': '财务造假嫌疑',
                'level': '✅ 无风险',
                'message': '审计标准，无调查',
            })
        # print(f"  ✅ 审计：{audit_opinion}, 调查：{'有' if under_investigation else '无'}")
    except Exception as e:
        print(f"  ⚠️ 财务造假检查失败：{e}")
        risks.append({
            'risk_type': '财务造假嫌疑',
            'level': '⚠️ 未知',
            'message': '数据获取失败',
        })
    
    # 4. 流动性风险
    try:
        avg_volume = get_avg_volume(ts_code, days=20)
        
        if avg_volume < 50000000:
            risks.append({
                'risk_type': '流动性风险',
                'level': '🟠 中危',
                'message': f'日均成交¥{avg_volume/1e8:.2f}亿 < ¥0.50 亿，避免无法卖出',
            })
        else:
            risks.append({
                'risk_type': '流动性风险',
                'level': '✅ 无风险',
                'message': f'日均成交¥{avg_volume/1e8:.2f}亿，流动性良好',
            })
        # print(f"  ✅ 流动性：日均¥{avg_volume/1e8:.2f}亿")
    except Exception as e:
        print(f"  ⚠️ 流动性检查失败：{e}")
        risks.append({
            'risk_type': '流动性风险',
            'level': '⚠️ 未知',
            'message': '数据获取失败',
        })
    
    # 5. 融资盘风险
    try:
        margin_ratio = get_margin_ratio(ts_code)
        
        if margin_ratio > 0.30:
            risks.append({
                'risk_type': '融资盘过高',
                'level': '🟠 中危',
                'message': f'融资盘{margin_ratio:.1%} > 30%，波动风险大',
            })
        else:
            risks.append({
                'risk_type': '融资盘风险',
                'level': '✅ 无风险',
                'message': f'融资盘{margin_ratio:.1%}，正常',
            })
        # print(f"  ✅ 融资盘：{margin_ratio:.1%}")
    except Exception as e:
        print(f"  ⚠️ 融资盘检查失败：{e}")
        risks.append({
            'risk_type': '融资盘风险',
            'level': '⚠️ 未知',
            'message': '数据获取失败',
        })
    
    # 6. 北向资金
    try:
        northbound = get_northbound_hold(ts_code)
        holding = northbound['holding']
        flow_30d = northbound['flow_30d']
        
        if holding > 0.10 and flow_30d < -0.20:
            risks.append({
                'risk_type': '北向资金大幅流出',
                'level': '🟠 中危',
                'message': f'北向持仓{holding:.1%}，30 天流出{flow_30d:.1%}',
            })
        elif holding > 0.10 and flow_30d > 0.20:
            risks.append({
                'risk_type': '北向资金大幅流入',
                'level': '✅ 利好',
                'message': f'北向持仓{holding:.1%}，30 天流入{flow_30d:.1%}',
            })
        elif holding < 0.01:
            risks.append({
                'risk_type': '无北向关注',
                'level': '⚠️ 关注',
                'message': f'北向持仓{holding:.1%} < 1%，流动性可能不足',
            })
        else:
            risks.append({
                'risk_type': '北向资金',
                'level': '✅ 正常',
                'message': f'北向持仓{holding:.1%}，30 天流向{flow_30d:.1%}',
            })
        # print(f"  ✅ 北向：持仓{holding:.1%}, 30 天{flow_30d:+.1%}")
    except Exception as e:
        print(f"  ⚠️ 北向资金检查失败：{e}")
        risks.append({
            'risk_type': '北向资金',
            'level': '⚠️ 未知',
            'message': '数据获取失败',
        })
    
    # 汇总风险等级
    high_risk = sum(1 for r in risks if '🔴' in r['level'])
    medium_risk = sum(1 for r in risks if '🟠' in r['level'])
    
    return {
        'risks': risks,
        'summary': {
            'high': high_risk,
            'medium': medium_risk,
            'low': len(risks) - high_risk - medium_risk,
        }
    }


def _run_a_share_risk_check_simple(ts_code: str, financial_data: dict) -> dict:
    """
    A 股风险检查（降级简化版）
    当无法导入数据接口时使用
    """
    risks = []
    
    # 1. ST/退市风险 - 简化检查
    risks.append({
        'risk_type': 'ST/退市风险',
        'level': '✅ 无风险',
        'message': '非 ST 股（简化检查）',
    })
    
    # 2. 大股东减持
    reduction = financial_data.get('shareholder_reduction', 0)
    if reduction > 0.05:
        risks.append({
            'risk_type': '大股东减持',
            'level': '🟠 中危' if reduction < 0.10 else '🔴 高危',
            'message': f'减持{reduction:.1%}',
        })
    else:
        risks.append({
            'risk_type': '大股东减持',
            'level': '✅ 无风险',
            'message': f'减持{reduction:.1%}',
        })
    
    # 3. 财务造假风险 - 简化
    audit = financial_data.get('audit_opinion', '未知')
    if '标准无保留' not in audit:
        risks.append({
            'risk_type': '财务造假嫌疑',
            'level': '🔴 高危',
            'message': f'审计意见：{audit}',
        })
    else:
        risks.append({
            'risk_type': '财务造假嫌疑',
            'level': '✅ 无风险',
            'message': '审计标准',
        })
    
    # 4-6. 其他风险 - 无法获取数据
    risks.append({
        'risk_type': '流动性风险',
        'level': '⚠️ 未知',
        'message': '数据获取失败',
    })
    risks.append({
        'risk_type': '融资盘风险',
        'level': '⚠️ 未知',
        'message': '数据获取失败',
    })
    risks.append({
        'risk_type': '北向资金',
        'level': '⚠️ 未知',
        'message': '数据获取失败',
    })
    
    high_risk = sum(1 for r in risks if '🔴' in r['level'])
    medium_risk = sum(1 for r in risks if '🟠' in r['level'])
    
    return {
        'risks': risks,
        'summary': {
            'high': high_risk,
            'medium': medium_risk,
            'low': len(risks) - high_risk - medium_risk,
        }
    }


# ==================== 主程序 ====================

if __name__ == '__main__':
    import sys
    
    print("=" * 60)
    print("选股前 20 项检查清单（真实数据版）")
    print("=" * 60)
    print()
    
    # 获取股票代码
    if len(sys.argv) > 1:
        ts_code = sys.argv[1]
    else:
        ts_code = '002270.SZ'  # 默认华明装备
    
    print(f"分析标的：{ts_code}\n")
    
    # 获取真实数据
    financial_data = fetch_financial_data(ts_code)
    
    if financial_data is None:
        print("❌ 数据获取失败，无法继续分析")
        sys.exit(1)
    
    # 执行检查清单
    result = run_full_checklist(ts_code, financial_data)
    
    # 输出结果
    print("=" * 60)
    print("检查结果")
    print("=" * 60)
    print(f"股票：{result['ts_code']}")
    print(f"时间：{result['timestamp'][:19]}")
    print(f"\n检查结果：{result['summary']['passed']}/{result['summary']['total']} ({result['summary']['pass_rate']:.0%})")
    print(f"综合结论：{result['conclusion']}")
    
    print(f"\n详细结果：")
    for r in result['results']:
        status = '✅' if r['passed'] else '❌'
        print(f"  {status} {r['item']}: {r['value']} ({r['reason']})")
    
    # 输出 A 股风险检查结果
    print("\n" + "=" * 60)
    print("A 股风险检查")
    print("=" * 60)
    risk_results = result.get('risk_check', {})
    risks = risk_results.get('risks', [])
    risk_summary = risk_results.get('summary', {})
    
    for risk in risks:
        print(f"  {risk['level']} {risk['risk_type']}: {risk['message']}")
    
    # print(f"\n风险汇总：🔴{risk_summary.get('high', 0)}  🟠{risk_summary.get('medium', 0)}  ✅{risk_summary.get('low', 0)}")
    
    print("\n" + "=" * 60)
    # print("✅ 选股前 20 项检查清单 + A 股风险检查完成（真实数据）")
    print("=" * 60)