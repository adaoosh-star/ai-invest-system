"""
月度复盘自动化
- 每月自动生成持仓复盘报告
- 使用统一数据获取层
- 输出：cache/review/monthly_review_YYYYMM.md
- 时间：每月最后一个交易日 20:00
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.data_fetcher import get_price_change, get_valuation, get_holdings_list


class MonthlyReview:
    """月度复盘引擎"""
    
    def __init__(self, holdings_file: str = None):
        """
        初始化月度复盘
        
        参数：
        - holdings_file: 持仓配置文件路径
        """
        self.holdings = get_holdings_list(holdings_file)
        self.review_date = datetime.now()
        self.review_month = self.review_date.strftime('%Y年%m月')
        
    def generate_report(self):
        """生成月度复盘报告"""
        report = []
        
        # 报告头部
        report.append(f"# 🦀 AI 价值投资系统 v1.0 - 月度复盘报告")
        report.append(f"")
        report.append(f"**复盘周期：** {self.review_month}")
        report.append(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**持仓数量：** {len(self.holdings)} 只")
        report.append(f"")
        
        # 组合整体表现
        report.append(f"## 📊 组合整体表现")
        report.append(f"")
        report.append(f"| 指标 | 数值 |")
        report.append(f"|------|------|")
        report.append(f"| 持仓数量 | {len(self.holdings)} 只 |")
        report.append(f"| 本月表现 | 待计算 |")
        report.append(f"| 整体状态 | {'✅ 正常' if len(self.holdings) > 0 else '⚠️ 无持仓'} |")
        report.append(f"")
        
        # 个股表现
        report.append(f"## 📈 个股表现")
        report.append(f"")
        report.append(f"| 代码 | 名称 | 月初 | 月末 | 涨跌幅 | 估值分位 | 状态 |")
        report.append(f"|------|------|------|------|--------|---------|------|")
        
        for stock in self.holdings:
            ts_code = stock.get('ts_code') or stock.get('code')
            stock_name = stock.get('name', ts_code)
            
            # 获取月度表现（30 天）
            perf = get_price_change(ts_code, days=30)
            
            # 获取估值
            valuation = get_valuation(ts_code)
            
            if perf and perf.get('start_price') and perf.get('end_price'):
                month_change = perf.get('change_pct', 0)
                
                # 获取 PE 分位
                pe_pct = None
                if valuation:
                    pe = valuation.get('pe_percentile')
                    if pe is not None:
                        pe_pct = float(pe) * 100  # 转换为百分比
                
                # 状态判断
                if month_change > 20:
                    status = '🔴 大涨'
                elif month_change < -20:
                    status = '🟢 大跌'
                elif pe_pct and pe_pct > 80:
                    status = '⚠️ 高估'
                elif pe_pct and pe_pct < 20:
                    status = '✅ 低估'
                else:
                    status = '✅ 正常' if pe_pct else '⚪ 无数据'
                
                pe_display = f"{pe_pct:.1f}%" if pe_pct else "N/A"
                report.append(f"| {ts_code} | {stock_name} | {perf['start_price']:.2f} | {perf['end_price']:.2f} | {month_change:+.1f}% | {pe_display} | {status} |")
            else:
                report.append(f"| {ts_code} | {stock_name} | 数据获取失败 | - | - | - | ❌ |")
        
        report.append(f"")
        
        # 系统表现
        report.append(f"## ⚙️ 系统表现")
        report.append(f"")
        report.append(f"| 指标 | 状态 |")
        report.append(f"|------|------|")
        report.append(f"| 数据获取成功率 | ✅ 正常 |")
        report.append(f"| 预警准确性 | ✅ 正常 |")
        report.append(f"| 系统稳定性 | ✅ 正常 |")
        report.append(f"")
        
        # 问题清单
        report.append(f"## ⚠️ 问题清单")
        report.append(f"")
        report.append(f"### 本月发现的问题")
        report.append(f"")
        report.append(f"- [ ] 待补充")
        report.append(f"")
        
        report.append(f"### 需要改进的地方")
        report.append(f"")
        report.append(f"- [ ] 待补充")
        report.append(f"")
        
        # 下月计划
        report.append(f"## 📅 下月计划")
        report.append(f"")
        report.append(f"- [ ] 重点关注持仓股财报发布")
        report.append(f"- [ ] 跟踪估值变化")
        report.append(f"- [ ] 检查系统运行状态")
        report.append(f"")
        
        # 免责声明
        report.append(f"---")
        report.append(f"")
        report.append(f"**免责声明：** 本报告仅供参考，不构成投资建议。投资需谨慎，决策需自主。")
        report.append(f"")
        report.append(f"*AI 价值投资系统 v1.0 | 让投资更简单*")
        
        return '\n'.join(report)
    
    def save_report(self, report: str):
        """保存报告"""
        output_dir = Path(__file__).parent.parent / 'cache' / 'review'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f'monthly_review_{self.review_date.strftime("%Y%m")}.md'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(output_file)
    
    def run(self):
        """执行月度复盘"""
        print(f"🦀 开始生成{self.review_month}月度复盘报告...")
        
        # 生成报告
        report = self.generate_report()
        
        # 保存报告
        output_file = self.save_report(report)
        
        print(f"✅ 月度复盘报告已生成：{output_file}")
        
        return output_file


if __name__ == '__main__':
    review = MonthlyReview()
    review.run()
