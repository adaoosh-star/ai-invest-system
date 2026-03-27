"""
完整分析流程（P1 版本）
- 20 项财务检查
- A 股风险检查
- 事实一致性校验（NLP 公告分析）
- 生成完整报告
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from selection.checklist_20 import fetch_financial_data, run_full_checklist
from nlp.announcement_analyzer import analyze_promises

def run_complete_analysis(ts_code: str, output_report: bool = True, nlp_mode: str = 'simple'):
    """
    执行完整分析流程（P1 版本）
    
    参数：
    - ts_code: 股票代码
    - output_report: 是否输出完整报告
    - nlp_mode: NLP 分析模式 ('simple' 简化版 | 'full' 完整版)
                 默认简化版（快速，不下载 PDF）
    
    返回：
    - dict: 完整分析结果（包含 report 完整报告文本）
    """
    # 1. 获取财务数据
    financial_data = fetch_financial_data(ts_code)
    if financial_data is None:
        return {'error': '数据获取失败'}
    
    # 2. 执行 20 项检查 + A 股风险检查
    checklist_result = run_full_checklist(ts_code, financial_data)
    
    # 3. 事实一致性校验（NLP）- P1 新增
    try:
        nlp_result = analyze_promises(ts_code, mode=nlp_mode)
    except Exception as e:
        nlp_result = {
            'status': '⚠️ 获取失败',
            'message': f'NLP 数据获取失败：{str(e)}',
            'promises': [],
            'fulfillment_rate': None,
            'mode': nlp_mode,
        }
    
    # 4. 生成综合结论
    conclusion = generate_final_conclusion(checklist_result, nlp_result)
    
    # 5. 生成报告
    report = ""
    filepath = None
    if output_report:
        report = generate_full_report(ts_code, checklist_result, nlp_result, conclusion)
        filepath = save_report(ts_code, report)
    
    return {
        'ts_code': ts_code,
        'checklist': checklist_result,
        'nlp': nlp_result,
        'conclusion': conclusion,
        'report': report,
        'filepath': filepath,
    }


def generate_final_conclusion(checklist_result: dict, nlp_result: dict) -> dict:
    """生成综合结论"""
    pass_rate = checklist_result['summary']['pass_rate']
    risk_summary = checklist_result.get('risk_check', {}).get('summary', {})
    
    # 基础结论（基于 20 项检查）
    if pass_rate >= 0.75:
        base_recommendation = '✅ 可买入'
    elif pass_rate >= 0.50:
        base_recommendation = '⚠️ 待查'
    else:
        base_recommendation = '❌ 放弃'
    
    # 风险调整
    high_risk_count = risk_summary.get('high', 0)
    if high_risk_count > 0:
        base_recommendation = '🔴 高风险 - 不建议投资'
    
    # NLP 降级处理：获取失败不影响核心结论
    nlp_status = nlp_result.get('status', '未执行')
    if '失败' in nlp_status or '⚠️' in nlp_status:
        nlp_note = '（NLP 数据获取失败，不影响核心结论）'
    else:
        nlp_note = ''
    
    return {
        'recommendation': base_recommendation,
        'pass_rate': pass_rate,
        'risk_level': '高' if high_risk_count > 0 else '中' if risk_summary.get('medium', 0) > 0 else '低',
        'nlp_status': nlp_status,
        'nlp_note': nlp_note,
        'reasons': [],
    }


def generate_full_report(ts_code: str, checklist_result: dict, nlp_result: dict, conclusion: dict) -> str:
    """生成完整报告"""
    report = []
    report.append(f"# 🦀 AI 价值投资系统 v1.0 - {ts_code} 完整分析报告")
    report.append(f"**报告时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append("## 📊 核心结论")
    report.append(f"**建议：** {conclusion['recommendation']} {conclusion.get('nlp_note', '')}")
    report.append(f"**通过率：** {conclusion['pass_rate']:.0%}")
    report.append(f"**风险等级：** {conclusion['risk_level']}")
    report.append(f"**NLP 校验：** {conclusion['nlp_status']}")
    report.append("")
    
    # 20 项检查结果
    report.append("## 一、20 项检查清单")
    for r in checklist_result['results']:
        status = '✅' if r['passed'] else '❌'
        report.append(f"- {status} {r['item']}: {r['value']}")
    report.append("")
    
    # A 股风险检查
    report.append("## 二、A 股风险检查")
    risks = checklist_result.get('risk_check', {}).get('risks', [])
    for risk in risks:
        report.append(f"- {risk['level']} {risk['risk_type']}: {risk['message']}")
    report.append("")
    
    # NLP 校验
    report.append("## 三、事实一致性校验")
    report.append(f"- 状态：{nlp_result.get('status', '未执行')}")
    report.append(f"- 说明：{nlp_result.get('message', '无')}")
    if nlp_result.get('promises'):
        report.append(f"- 承诺数量：{len(nlp_result['promises'])}")
        report.append(f"- 兑现率：{nlp_result.get('fulfillment_rate', 'N/A')}")
    report.append("")
    
    return "\n".join(report)


def save_report(ts_code: str, report: str):
    """保存报告，返回文件路径"""
    cache_dir = Path(__file__).parent.parent / 'cache'
    cache_dir.mkdir(exist_ok=True)
    
    filename = f"{ts_code.replace('.', '_')}_完整报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = cache_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return str(filepath)


# 主程序
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        ts_code = sys.argv[1]
    else:
        ts_code = '002270.SZ'  # 默认华明装备
    
    run_complete_analysis(ts_code)
