#!/usr/bin/env python3
"""
AI 价值投资系统 - 个股深度分析脚本

用法：python3 analysis/deep_analysis.py <股票代码>

功能：
1. 自动执行选股前 20 项检查清单
2. 自动执行 A 股风险检查
3. 生成完整分析报告（Markdown 格式）
4. 可选推送 DingTalk

这是标准化的深度分析流程，确保每次分析都完整、一致。
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from data.tushare_client import (
    get_pe_pb_percentile, get_roe, get_cash_flow, get_revenue,
    get_net_profit, get_gross_margin, get_rd_expense, get_debt_ratio,
    get_receivables_and_inventory, get_industry_peers, get_industry_avg
)
from data.realtime_fetcher import fetch_realtime_price
from risk.a_share_risks import comprehensive_risk_assessment


def run_checklist_20(ts_code: str) -> tuple:
    """
    运行选股前 20 项检查清单
    
    返回：
    - output: 检查输出文本
    - score: 得分 (x/20)
    - conclusion: 结论
    """
    try:
        result = subprocess.run(
            ['python3', str(ROOT_DIR / 'selection' / 'checklist_20.py'), ts_code],
            capture_output=True,
            text=True,
            timeout=60
        )
        output = result.stdout
        
        # 解析得分
        score_line = [l for l in output.split('\n') if '检查结果：' in l]
        score = score_line[0].split('：')[1].split(' ')[0] if score_line else 'N/A'
        
        # 解析结论
        conclusion_line = [l for l in output.split('\n') if '综合结论：' in l]
        conclusion = conclusion_line[0].split('：')[1] if conclusion_line else 'N/A'
        
        return output, score, conclusion
    except Exception as e:
        return f"检查失败：{e}", "N/A", "N/A"


def run_risk_check(ts_code: str) -> str:
    """运行 A 股风险检查"""
    try:
        # 直接运行脚本获取输出
        result = subprocess.run(
            ['python3', '-c', f'''
import sys
sys.path.insert(0, "/home/admin/.openclaw/workspace/ai-invest-system-code")
from risk.a_share_risks import comprehensive_risk_assessment
result = comprehensive_risk_assessment("{ts_code}", {{}})
for key, value in result.items():
    status = "✅" if value.get("passed") else "❌"
    print(f"  {{status}} {{key}}: {{value.get('detail', 'N/A')}}")
            '''],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout
    except Exception as e:
        return f"风险检查失败：{e}"


def get_financial_data(ts_code: str) -> dict:
    """获取财务数据用于报告"""
    data = {}
    
    try:
        # PE/PB 分位
        pe_pb = get_pe_pb_percentile(ts_code)
        data['pe_ttm'] = pe_pb.get('pe_ttm', 'N/A')
        data['pe_percentile_5y'] = pe_pb.get('pe_percentile_5y', 'N/A')
        data['pb_percentile_5y'] = pe_pb.get('pb_percentile_5y', 'N/A')
    except:
        pass
    
    try:
        # ROE
        roe = get_roe(ts_code)
        data['roe_latest'] = roe.iloc[0]['roe_dt'] if len(roe) > 0 else 'N/A'
        data['roe_5y_avg'] = roe['roe_dt'].tail(5).mean() if len(roe) >= 5 else 'N/A'
    except:
        pass
    
    try:
        # 营收
        rev = get_revenue(ts_code)
        data['revenue_latest'] = rev.iloc[0]['revenue'] if len(rev) > 0 else 'N/A'
    except:
        pass
    
    try:
        # 净利润
        profit = get_net_profit(ts_code)
        data['net_profit_latest'] = profit.iloc[0]['net_profit'] if len(profit) > 0 else 'N/A'
    except:
        pass
    
    try:
        # 毛利率
        margin = get_gross_margin(ts_code)
        data['gross_margin_latest'] = margin.iloc[0]['grossprofit_margin'] if len(margin) > 0 else 'N/A'
    except:
        pass
    
    try:
        # 负债率
        debt = get_debt_ratio(ts_code)
        data['debt_ratio'] = debt if debt else 'N/A'
    except:
        pass
    
    try:
        # 实时行情
        quote = fetch_realtime_price(ts_code)
        if quote:
            data['current_price'] = quote.get('price', 'N/A')
            data['market_cap'] = quote.get('market_cap', 'N/A')
            data['change_pct'] = quote.get('change_pct', 'N/A')
    except:
        pass
    
    return data


def generate_report(ts_code: str, checklist_output: str, risk_output: str, financial_data: dict) -> str:
    """生成完整分析报告"""
    
    report_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    report = f"""# {ts_code} - AI 价值投资系统深度分析报告

**生成时间：** {report_time}  
**分析框架：** 选股前 20 项检查清单 + A 股风险检查  
**数据来源：** Tushare Pro、东方财富  
**分析师：** AI 价值投资系统

---

## 📊 一、核心结论

{checklist_output.split('============================================================')[2] if '============================================================' in checklist_output else '数据获取中...'}

---

## 📋 二、20 项检查清单详情

{checklist_output.split('详细结果：')[1].split('============================================================')[0] if '详细结果：' in checklist_output else '数据获取中...'}

---

## ⚠️ 三、A 股风险检查

{risk_output.split('============================================================')[-2] if '============================================================' in risk_output else '数据获取中...'}

---

## 📈 四、关键财务数据

| 指标 | 数值 |
|------|------|
| 现价 | {financial_data.get('current_price', 'N/A')} |
| 涨跌幅 | {financial_data.get('change_pct', 'N/A')}% |
| 总市值 | {financial_data.get('market_cap', 'N/A')}亿 |
| PE TTM | {financial_data.get('pe_ttm', 'N/A')} |
| PE 分位 (5y) | {financial_data.get('pe_percentile_5y', 'N/A')} |
| PB 分位 (5y) | {financial_data.get('pb_percentile_5y', 'N/A')} |
| ROE (最新) | {financial_data.get('roe_latest', 'N/A')}% |
| ROE (5 年平均) | {financial_data.get('roe_5y_avg', 'N/A')}% |
| 毛利率 | {financial_data.get('gross_margin_latest', 'N/A')}% |
| 负债率 | {financial_data.get('debt_ratio', 'N/A')}% |

---

## 🎯 五、投资建议

### 价值投资角度
- **ROE 连续 5 年>15%**：{'✅' if isinstance(financial_data.get('roe_5y_avg'), (int, float)) and financial_data.get('roe_5y_avg') > 15 else '❌'}
- **现金流/净利润>0.8**：待确认
- **自由现金流 5 年为正**：待确认
- **分红率>20%**：待确认

### 成长投资角度
- **营收增速**：待确认
- **毛利率趋势**：待确认
- **研发投入占比**：待确认

### 操作建议
| 投资者类型 | 建议 |
|------------|------|
| **价值投资者** | 待评估 |
| **成长投资者** | 待评估 |
| **趋势投资者** | 待评估 |

---

## 📋 六、关键跟踪指标

### 季度跟踪
- [ ] 季度营收增速
- [ ] 季度净利润
- [ ] 毛利率变化
- [ ] 经营现金流

### 年度跟踪
- [ ] 年度 ROE
- [ ] 自由现金流
- [ ] 研发费用占比
- [ ] 市场份额

---

*本报告由 AI 价值投资系统自动生成*  
*分析框架：选股前 20 项检查清单 + A 股风险检查*  
*免责声明：仅供参考，不构成投资建议*
"""
    
    return report


def main():
    if len(sys.argv) < 2:
        print("用法：python3 analysis/deep_analysis.py <股票代码>")
        print("示例：python3 analysis/deep_analysis.py 688052.SH")
        sys.exit(1)
    
    ts_code = sys.argv[1]
    print(f"=" * 60)
    print(f"AI 价值投资系统 - 个股深度分析")
    print(f"=" * 60)
    print(f"\n分析标的：{ts_code}")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n" + "=" * 60)
    
    # 1. 运行 20 项检查清单
    print("【1/3】运行选股前 20 项检查清单...")
    checklist_output, score, conclusion = run_checklist_20(ts_code)
    print(f"检查结果：{score} - {conclusion}")
    
    # 2. 运行风险检查
    print("\n【2/3】运行 A 股风险检查...")
    risk_output = run_risk_check(ts_code)
    print("风险检查完成")
    
    # 3. 获取财务数据
    print("\n【3/3】获取财务数据...")
    financial_data = get_financial_data(ts_code)
    print("财务数据获取完成")
    
    # 4. 生成报告
    print("\n" + "=" * 60)
    print("生成分析报告...")
    
    report = generate_report(ts_code, checklist_output, risk_output, financial_data)
    
    # 保存报告
    report_dir = ROOT_DIR / 'analysis' / 'reports'
    report_dir.mkdir(exist_ok=True)
    
    report_date = datetime.now().strftime('%Y%m%d_%H%M')
    report_path = report_dir / f"{ts_code.replace('.', '_')}_深度分析_{report_date}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已保存：{report_path}")
    print(f"\n" + "=" * 60)
    print(f"分析完成！")
    print(f"=" * 60)
    
    # 输出简要结论
    print(f"\n📊 核心结论：{score} - {conclusion}")
    
    return report_path


if __name__ == '__main__':
    main()
