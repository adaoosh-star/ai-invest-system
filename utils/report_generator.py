"""
统一报告生成器
- 所有报告统一保存到文件
- 避免 print 长输出
- 提供完整分析报告生成
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from selection.checklist_20 import run_checklist
from model.integrity_score import IntegrityScore
from model.safety_margin import SafetyMargin
from data.data_fetcher import get_stock_name, get_valuation, get_price_change


def generate_checklist_report(ts_code: str, output_dir: str = None) -> str:
    """
    生成 20 项检查报告
    
    参数：
    - ts_code: 股票代码
    - output_dir: 输出目录（默认 cache/reports/）
    
    返回：报告文件路径
    """
    if not output_dir:
        output_dir = Path(__file__).parent.parent / 'cache' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行检查
    result = run_checklist(ts_code)
    stock_name = get_stock_name(ts_code)
    
    # 生成报告
    report = []
    report.append(f"# 🦀 AI 价值投资系统 v2.0 - 20 项检查报告")
    report.append(f"")
    report.append(f"**股票代码：** {ts_code}")
    report.append(f"**股票名称：** {stock_name}")
    report.append(f"**检查时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"")
    report.append(f"## 📊 检查结果汇总")
    report.append(f"")
    report.append(f"| 指标 | 数值 |")
    report.append(f"|------|------|")
    report.append(f"| 总项数 | {result['total']} 项 |")
    report.append(f"| ✅ 通过 | {result['passed']} 项 |")
    report.append(f"| ❌ 未通过 | {result['failed']} 项 |")
    report.append(f"| 通过率 | {result['pass_rate']:.1f}% |")
    report.append(f"| **投资建议** | **{result['recommendation']}** |")
    report.append(f"")
    report.append(f"## 📋 20 项检查详细结果")
    report.append(f"")
    report.append(f"| 序号 | 检查项 | 数值 | 标准 | 状态 |")
    report.append(f"|------|--------|------|------|------|")
    
    for i, item in enumerate(result['checklist'], 1):
        status = '✅' if item['pass'] else '❌'
        report.append(f"| {i} | {item['name']} | {item['value']} | {item['threshold']} | {status} |")
    
    report.append(f"")
    report.append(f"*AI 价值投资系统 v2.0*")
    
    # 保存报告
    ts_code_part = ts_code.replace('.', '_')
    output_file = output_dir / f'{ts_code_part}_checklist_{datetime.now().strftime("%Y%m%d")}.md'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    return str(output_file)


def generate_integrity_report(ts_code: str, output_dir: str = None) -> str:
    """
    生成诚信评分报告
    
    参数：
    - ts_code: 股票代码
    - output_dir: 输出目录
    
    返回：报告文件路径
    """
    if not output_dir:
        output_dir = Path(__file__).parent.parent / 'cache' / 'integrity'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    integrity = IntegrityScore(ts_code)
    result = integrity.run()
    
    return result['report_file']


def generate_margin_report(ts_code: str, output_dir: str = None) -> str:
    """
    生成安全边际报告
    
    参数：
    - ts_code: 股票代码
    - output_dir: 输出目录
    
    返回：报告文件路径
    """
    if not output_dir:
        output_dir = Path(__file__).parent.parent / 'cache' / 'margin'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    margin = SafetyMargin(ts_code)
    result = margin.run()
    
    return result['report_file']


def generate_full_report(ts_code: str, output_dir: str = None) -> str:
    """
    生成完整分析报告（20 项检查 + 诚信 + 安全边际）
    
    参数：
    - ts_code: 股票代码
    - output_dir: 输出目录
    
    返回：报告文件路径
    """
    if not output_dir:
        output_dir = Path(__file__).parent.parent / 'cache' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取数据
    stock_name = get_stock_name(ts_code)
    checklist = run_checklist(ts_code)
    valuation = get_valuation(ts_code)
    
    integrity = IntegrityScore(ts_code)
    integrity_result = integrity.run()
    
    margin = SafetyMargin(ts_code)
    margin_result = margin.run()
    
    # 综合评级
    if checklist['pass_rate'] >= 75 and integrity_result['score'] >= 75:
        rating = "✅ 值得投资"
        desc = "财务健康，诚信良好，符合投资标准"
    elif checklist['pass_rate'] >= 50:
        rating = "⚠️ 观望"
        desc = "部分指标未达标，建议继续观察"
    else:
        rating = "❌ 不建议投资"
        desc = "多项指标未达标，不符合投资标准"
    
    # 生成报告
    report = []
    report.append(f"# 🦀 AI 价值投资系统 v2.0 - 完整投资分析报告")
    report.append(f"")
    report.append(f"**股票代码：** {ts_code}")
    report.append(f"**股票名称：** {stock_name}")
    report.append(f"**分析时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"")
    
    # 一、核心结论
    report.append(f"## 🎯 一、核心结论")
    report.append(f"")
    report.append(f"| 项目 | 结果 |")
    report.append(f"|------|------|")
    report.append(f"| 20 项检查通过率 | {checklist['pass_rate']:.1f}% |")
    report.append(f"| 诚信评分 | {integrity_result['score']} 分 ({integrity_result['rating']}) |")
    report.append(f"| 安全边际要求 | {margin_result['final_margin']:.1%} |")
    report.append(f"| **投资建议** | **{rating}** |")
    report.append(f"")
    
    # 二、20 项检查
    report.append(f"## 📊 二、20 项检查（{checklist['pass_rate']:.1f}% 通过）")
    report.append(f"")
    report.append(f"**通过：** {checklist['passed']} 项 | **未通过：** {checklist['failed']} 项")
    report.append(f"")
    report.append(f"### 未通过项")
    report.append(f"")
    for i, item in enumerate(checklist['checklist'], 1):
        if not item['pass']:
            report.append(f"{i}. ❌ **{item['name']}**: {item['value']} (标准：{item['threshold']})")
    report.append(f"")
    
    # 三、估值分析
    report.append(f"## 💰 三、估值分析")
    report.append(f"")
    report.append(f"| 指标 | 数值 |")
    report.append(f"|------|------|")
    if valuation:
        pe = valuation.get('pe_ttm', 0)
        pe_pct = valuation.get('pe_percentile', 0)
        pb = valuation.get('pb', 0)
        pb_pct = valuation.get('pb_percentile', 0)
        report.append(f"| PE TTM | {pe:.1f} |")
        report.append(f"| PE 分位 | {pe_pct*100:.1f}% |" if pe_pct else "| PE 分位 | N/A |")
        report.append(f"| PB | {pb:.1f} |")
        report.append(f"| PB 分位 | {pb_pct*100:.1f}% |" if pb_pct else "| PB 分位 | N/A |")
    else:
        report.append(f"| 估值数据 | 获取失败 |")
    report.append(f"")
    
    # 四、诚信评分
    report.append(f"## 🏆 四、管理层诚信（{integrity_result['score']}分）")
    report.append(f"")
    if integrity_result.get('deductions'):
        report.append(f"**扣分项：**")
        for d in integrity_result['deductions']:
            report.append(f"- ❌ {d['type']}: -{abs(d['score'])} 分")
    else:
        report.append(f"✅ 无扣分项，诚信记录良好")
    report.append(f"")
    
    # 五、安全边际
    report.append(f"## 🛡️ 五、安全边际")
    report.append(f"")
    report.append(f"| 项目 | 数值 |")
    report.append(f"|------|------|")
    report.append(f"| 基础安全边际 | {margin_result['base_margin']:.1%} |")
    report.append(f"| 市场情绪调整 | {margin_result['adjustments']['market_sentiment']:+.1%} |")
    report.append(f"| 个股风险调整 | {margin_result['adjustments']['individual_risk']:+.1%} |")
    report.append(f"| **最终安全边际** | **{margin_result['final_margin']:.1%}** |")
    report.append(f"| **类型** | **{margin_result['margin_type']}** |")
    report.append(f"")
    report.append(f"**买入条件：** 价格 < 内在价值 × {1-margin_result['final_margin']:.1%}")
    report.append(f"")
    
    # 六、投资建议
    report.append(f"## 💡 六、投资建议")
    report.append(f"")
    report.append(f"**{rating}**")
    report.append(f"")
    report.append(f"{desc}")
    report.append(f"")
    report.append(f"### 操作建议")
    report.append(f"")
    report.append(f"1. **当前状态：** {checklist['pass_rate']:.1f}% 通过 20 项检查")
    report.append(f"2. **诚信评分：** {integrity_result['score']} 分 ({integrity_result['rating']})")
    report.append(f"3. **安全边际：** {margin_result['final_margin']:.1%}")
    report.append(f"4. **估值水平：** {'高估' if valuation and valuation.get('pe_percentile', 0) > 0.8 else '合理' if valuation and valuation.get('pe_percentile', 0) > 0.2 else '低估'}")
    report.append(f"")
    
    # 免责声明
    report.append(f"---")
    report.append(f"")
    report.append(f"**免责声明：** 本报告仅供参考，不构成投资建议。投资需谨慎，决策需自主。")
    report.append(f"")
    report.append(f"*AI 价值投资系统 v2.0 | 让投资更简单*")
    
    # 保存报告
    ts_code_part = ts_code.replace('.', '_')
    output_file = output_dir / f'{ts_code_part}_full_report_{datetime.now().strftime("%Y%m%d")}.md'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    return str(output_file)


# ========== 便捷函数 ==========

def analyze_stock(ts_code: str) -> dict:
    """
    分析股票并生成所有报告
    
    参数：
    - ts_code: 股票代码
    
    返回：报告文件路径字典
    """
    print(f"🦀 开始分析 {ts_code}...")
    
    reports = {}
    
    # 生成各报告
    reports['checklist'] = generate_checklist_report(ts_code)
    print(f"✅ 20 项检查报告：{reports['checklist']}")
    
    reports['integrity'] = generate_integrity_report(ts_code)
    print(f"✅ 诚信评分报告：{reports['integrity']}")
    
    reports['margin'] = generate_margin_report(ts_code)
    print(f"✅ 安全边际报告：{reports['margin']}")
    
    reports['full'] = generate_full_report(ts_code)
    print(f"✅ 完整分析报告：{reports['full']}")
    
    print()
    print(f"所有报告已保存到 cache/reports/ 目录")
    
    return reports


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        ts_code = sys.argv[1]
        analyze_stock(ts_code)
    else:
        print("用法：python report_generator.py <股票代码>")
        print("示例：python report_generator.py 000788.SZ")
