"""
年度回顾自动化
- 每年自动生成年度回顾报告
- 投资宪法重读 + 系统校验 + 年度业绩 + 明年规划
- 输出：cache/review/annual_review_YYYY.md
- 时间：每年 12 月 31 日或次年 1 月 1 日
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.tushare_client import pro, get_pe_pb_percentile


class AnnualReview:
    """年度回顾引擎"""
    
    def __init__(self, holdings_file: str = None):
        """
        初始化年度回顾
        
        参数：
        - holdings_file: 持仓配置文件路径
        """
        self.holdings_file = holdings_file or str(Path(__file__).parent.parent / 'config' / 'holdings.yaml')
        self.holdings = self._load_holdings()
        self.review_date = datetime.now()
        self.review_year = self.review_date.year
        
    def _load_holdings(self):
        """加载持仓配置"""
        try:
            with open(self.holdings_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载持仓配置失败：{e}")
            return {}
    
    def get_annual_performance(self, ts_code: str):
        """获取年度表现数据"""
        try:
            # 获取本年度数据
            end_date = self.review_date.strftime('%Y%m%d')
            start_date = f'{self.review_year}0101'
            
            df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return None
            
            # 按日期排序
            df = df.sort_values('trade_date')
            
            # 年初 vs 年末
            year_start = df.iloc[0]['close']
            year_end = df.iloc[-1]['close']
            year_change = (year_end - year_start) / year_start * 100
            
            return {
                'year_start': year_start,
                'year_end': year_end,
                'year_change_pct': year_change,
                'year_high': df['high'].max(),
                'year_low': df['low'].min(),
            }
        except Exception as e:
            print(f"获取{ts_code}年度表现失败：{e}")
            return None
    
    def generate_report(self):
        """生成年度回顾报告"""
        report = []
        
        # 报告头部
        report.append(f"# 🦀 AI 价值投资系统 v1.0 - 年度回顾报告")
        report.append(f"")
        report.append(f"**回顾年度：** {self.review_year}年")
        report.append(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**持仓数量：** {len(self.holdings.get('stocks', []))} 只")
        report.append(f"")
        
        # 第一部分：重读投资宪法
        report.append(f"## 📖 第一部分：重读投资宪法")
        report.append(f"")
        report.append(f"### 本年度重读感悟")
        report.append(f"")
        report.append(f"**待补充：**")
        report.append(f"")
        report.append(f"- 重读《巴菲特致股东的信》的新理解")
        report.append(f"- 重读《段永平投资问答录》的新理解")
        report.append(f"- 重读《穷查理宝典》的新理解")
        report.append(f"")
        
        report.append(f"### 原则是否需要更新")
        report.append(f"")
        report.append(f"- [ ] 投资宪法原则无需更新")
        report.append(f"- [ ] 需要更新以下原则：待补充")
        report.append(f"")
        
        # 第二部分：系统校验
        report.append(f"## ⚙️ 第二部分：系统校验")
        report.append(f"")
        report.append(f"### 系统是否偏离投资宪法")
        report.append(f"")
        report.append(f"- [ ] 系统运行符合投资宪法")
        report.append(f"- [ ] 发现以下偏离：待补充")
        report.append(f"")
        
        report.append(f"### 需要调整的功能")
        report.append(f"")
        report.append(f"- [ ] 无需调整")
        report.append(f"- [ ] 需要调整：待补充")
        report.append(f"")
        
        report.append(f"### 需要强化的原则")
        report.append(f"")
        report.append(f"- [ ] 无需强化")
        report.append(f"- [ ] 需要强化：待补充")
        report.append(f"")
        
        # 第三部分：年度业绩回顾
        report.append(f"## 📊 第三部分：年度业绩回顾")
        report.append(f"")
        report.append(f"### 组合表现")
        report.append(f"")
        report.append(f"| 指标 | 数值 |")
        report.append(f"|------|------|")
        report.append(f"| 年度收益率 | 待计算 |")
        report.append(f"| 基准收益率（沪深 300） | 待计算 |")
        report.append(f"| 超额收益 | 待计算 |")
        report.append(f"")
        
        report.append(f"### 个股表现")
        report.append(f"")
        report.append(f"| 代码 | 名称 | 年初 | 年末 | 涨跌幅 | 状态 |")
        report.append(f"|------|------|------|------|--------|------|")
        
        for stock in self.holdings.get('stocks', []):
            ts_code = stock.get('ts_code') or stock.get('code')
            stock_name = stock.get('name', ts_code)
            
            perf = self.get_annual_performance(ts_code)
            
            if perf:
                year_change = perf.get('year_change_pct', 0)
                
                if year_change > 50:
                    status = '🔴 大涨'
                elif year_change > 20:
                    status = '✅ 上涨'
                elif year_change > -20:
                    status = '⚪ 震荡'
                elif year_change > -50:
                    status = '⚠️ 下跌'
                else:
                    status = '🟢 大跌'
                
                report.append(f"| {ts_code} | {stock_name} | {perf['year_start']:.2f} | {perf['year_end']:.2f} | {year_change:+.1f}% | {status} |")
            else:
                report.append(f"| {ts_code} | {stock_name} | - | - | 数据获取失败 | ❌ |")
        
        report.append(f"")
        
        report.append(f"### 重大决策回顾")
        report.append(f"")
        report.append(f"| 日期 | 股票 | 操作 | 理由 | 结果 | 反思 |")
        report.append(f"|------|------|------|------|------|--------|")
        report.append(f"| - | - | - | - | - | - |")
        report.append(f"")
        
        report.append(f"### 经验教训总结")
        report.append(f"")
        report.append(f"**成功经验：**")
        report.append(f"")
        report.append(f"- 待补充")
        report.append(f"")
        report.append(f"**失败教训：**")
        report.append(f"")
        report.append(f"- 待补充")
        report.append(f"")
        
        # 第四部分：明年规划
        report.append(f"## 📅 第四部分：明年规划")
        report.append(f"")
        report.append(f"### 系统优化方向")
        report.append(f"")
        report.append(f"- [ ] 待补充")
        report.append(f"")
        
        report.append(f"### 能力提升计划")
        report.append(f"")
        report.append(f"- [ ] 待补充")
        report.append(f"")
        
        report.append(f"### 目标设定")
        report.append(f"")
        report.append(f"| 目标类型 | 目标值 | 衡量标准 |")
        report.append(f"|---------|--------|---------|")
        report.append(f"| 投资目标 | 待设定 | 年化收益率 |")
        report.append(f"| 系统目标 | 待设定 | 功能完善度 |")
        report.append(f"| 学习目标 | 待设定 | 阅读量 |")
        report.append(f"")
        
        # 结语
        report.append(f"## 💭 结语")
        report.append(f"")
        report.append(f"{self.review_year}年是____的一年。")
        report.append(f"")
        report.append(f"感谢市场先生的馈赠，感谢自己的坚持。")
        report.append(f"")
        report.append(f"{self.review_year + 1}年，继续做难而正确的事。")
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
        
        output_file = output_dir / f'annual_review_{self.review_year}.md'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(output_file)
    
    def run(self):
        """执行年度回顾"""
        print(f"🦀 开始生成{self.review_year}年年度回顾报告...")
        
        # 生成报告
        report = self.generate_report()
        
        # 保存报告
        output_file = self.save_report(report)
        
        print(f"✅ 年度回顾报告已生成：{output_file}")
        
        return output_file


if __name__ == '__main__':
    review = AnnualReview()
    review.run()
