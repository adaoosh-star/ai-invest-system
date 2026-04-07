"""
管理层诚信评分模型
- 承诺兑现分析
- 信息披露质量评估
- 历史记录查询
- 综合评分计算

评分标准：
- 90-100: 优秀（诚信记录良好）
- 75-89: 良好（基本诚信）
- 60-74: 中等（有待观察）
- <60: 高风险（诚信问题）
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import re
import csv

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.tushare_client import pro


class IntegrityScore:
    """管理层诚信评分"""
    
    def __init__(self, ts_code: str):
        """
        初始化诚信评分
        
        参数：
        - ts_code: 股票代码
        """
        self.ts_code = ts_code
        self.stock_name = self._get_stock_name()
        self.score = 100  # 初始满分
        self.deductions = []  # 扣分记录
        self.evidence = []  # 证据列表
        self.announcements = self._load_announcements()  # 加载本地公告库
    
    def _load_announcements(self):
        """加载本地公告库"""
        announcements = []
        
        # 公告库路径
        ann_dir = Path(__file__).parent.parent.parent / 'data' / 'announcements'
        stock_dir = ann_dir / self.ts_code.replace('.', '_')
        
        if not stock_dir.exists():
            return announcements
        
        # 读取 CSV 文件
        csv_files = list(stock_dir.glob('*.csv'))
        for csv_file in csv_files:
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        announcements.append(row)
            except Exception as e:
                print(f"读取公告文件失败：{e}")
        
        # 按日期排序（最新的在前）
        announcements.sort(key=lambda x: x.get('ann_date', ''), reverse=True)
        
        return announcements
        
    def _get_stock_name(self):
        """获取股票名称"""
        try:
            df = pro.stock_basic(ts_code=self.ts_code)
            if not df.empty:
                return df.iloc[0]['name']
        except Exception as e:
            print(f"获取股票名称失败：{e}")
        return self.ts_code
    
    def check_commitment_fulfillment(self):
        """检查承诺兑现情况"""
        print(f"📋 检查{self.stock_name}承诺兑现情况...")
        
        try:
            if not self.announcements:
                self.evidence.append("✅ 无公告记录")
                return
            
            # 检查是否有"承诺未履行"相关公告
            keywords = ['承诺未履行', '承诺未兑现', '承诺延期', '承诺变更']
            
            for ann in self.announcements:
                title = ann.get('title', '')
                if any(keyword in title for keyword in keywords):
                    self.score -= 20
                    self.deductions.append({
                        'type': '承诺未兑现',
                        'score': -20,
                        'evidence': title,
                        'date': ann.get('ann_date', '')
                    })
                    self.evidence.append(f"❌ 承诺未履行：{title}")
            
            if not any('承诺未兑现' in d['type'] for d in self.deductions):
                self.evidence.append("✅ 未发现承诺未兑现记录")
                
        except Exception as e:
            print(f"检查承诺兑现失败：{e}")
            self.evidence.append(f"⚠️ 数据获取失败：{e}")
    
    def check_disclosure_violations(self):
        """检查信息披露违规"""
        print(f"📢 检查{self.stock_name}信息披露违规...")
        
        try:
            if not self.announcements:
                self.evidence.append("✅ 无公告记录")
                return
            
            # 检查是否有"问询函"、"监管措施"、"警示函"等
            violation_keywords = ['问询函', '监管措施', '警示函', '责令改正', '通报批评', '公开谴责']
            
            for ann in self.announcements:
                title = ann.get('title', '')
                for keyword in violation_keywords:
                    if keyword in title:
                        self.score -= 10
                        self.deductions.append({
                            'type': '信息披露违规',
                            'score': -10,
                            'evidence': f"{keyword}: {title}",
                            'date': ann.get('ann_date', '')
                        })
                        self.evidence.append(f"❌ 信息披露违规：{title}")
            
            if not any('信息披露违规' in d['type'] for d in self.deductions):
                self.evidence.append("✅ 未发现信息披露违规记录")
                
        except Exception as e:
            print(f"检查信息披露违规失败：{e}")
            self.evidence.append(f"⚠️ 数据获取失败：{e}")
    
    def check_regulatory_penalties(self):
        """查询监管处罚记录"""
        print(f"⚖️ 检查{self.stock_name}监管处罚...")
        
        try:
            if not self.announcements:
                self.evidence.append("✅ 无公告记录")
                return
            
            # 检查是否有"行政处罚"、"立案调查"等
            penalty_keywords = ['行政处罚', '立案调查', '公开谴责', '严重失信', '违规处罚']
            
            for ann in self.announcements:
                title = ann.get('title', '')
                for keyword in penalty_keywords:
                    if keyword in title:
                        self.score -= 30
                        self.deductions.append({
                            'type': '监管处罚',
                            'score': -30,
                            'evidence': f"{keyword}: {title}",
                            'date': ann.get('ann_date', '')
                        })
                        self.evidence.append(f"❌ 监管处罚：{title}")
            
            if not any('监管处罚' in d['type'] for d in self.deductions):
                self.evidence.append("✅ 未发现监管处罚记录")
                
        except Exception as e:
            print(f"检查监管处罚失败：{e}")
            self.evidence.append(f"⚠️ 数据获取失败：{e}")
    
    def check_shareholder_reduction(self):
        """检查大股东违规减持"""
        print(f"💰 检查{self.stock_name}大股东减持...")
        
        try:
            if not self.announcements:
                self.evidence.append("✅ 无公告记录")
                return
            
            # 检查是否有"减持"相关公告
            reduction_keywords = ['减持', '股份减持', '股东减持', '减持计划']
            
            total_reduction = 0
            for ann in self.announcements:
                title = ann.get('title', '')
                for keyword in reduction_keywords:
                    if keyword in title:
                        total_reduction += 1
                        self.evidence.append(f"⚠️ 减持公告：{title}")
            
            # 如果减持公告过多（>3 次），扣分
            if total_reduction > 3:
                self.score -= 15
                self.deductions.append({
                    'type': '大股东减持',
                    'score': -15,
                    'evidence': f'减持公告次数：{total_reduction} 次',
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
                self.evidence.append(f"❌ 大股东频繁减持：{total_reduction} 次")
            elif total_reduction > 0:
                self.evidence.append(f"✅ 有减持公告但频率正常：{total_reduction} 次")
            else:
                self.evidence.append("✅ 无减持公告")
                
        except Exception as e:
            print(f"检查大股东减持失败：{e}")
            self.evidence.append(f"⚠️ 数据获取失败：{e}")
    
    def calculate_score(self):
        """计算最终评分"""
        # 确保分数不低于 0
        self.score = max(0, self.score)
        
        # 评级
        if self.score >= 90:
            self.rating = '优秀'
            self.level = 'A'
        elif self.score >= 75:
            self.rating = '良好'
            self.level = 'B'
        elif self.score >= 60:
            self.rating = '中等'
            self.level = 'C'
        else:
            self.rating = '高风险'
            self.level = 'D'
        
        return self.score
    
    def generate_report(self):
        """生成诚信评分报告"""
        # 先执行所有检查
        self.check_commitment_fulfillment()
        self.check_disclosure_violations()
        self.check_regulatory_penalties()
        self.check_shareholder_reduction()
        
        # 计算评分
        self.calculate_score()
        
        # 生成报告
        report = []
        report.append(f"# 🦀 AI 价值投资系统 v2.0 - 管理层诚信评分报告")
        report.append(f"")
        report.append(f"**股票代码：** {self.ts_code}")
        report.append(f"**股票名称：** {self.stock_name}")
        report.append(f"**评分时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"")
        
        # 评分结果
        report.append(f"## 📊 评分结果")
        report.append(f"")
        report.append(f"| 项目 | 结果 |")
        report.append(f"|------|------|")
        report.append(f"| **诚信评分** | **{self.score} 分** |")
        report.append(f"| **评级** | **{self.level} - {self.rating}** |")
        report.append(f"| **扣分项数** | {len(self.deductions)} 项 |")
        report.append(f"")
        
        # 评分标准
        report.append(f"### 评分标准")
        report.append(f"")
        report.append(f"| 分数 | 评级 | 说明 |")
        report.append(f"|------|------|------|")
        report.append(f"| 90-100 | A - 优秀 | 诚信记录良好，可信任 |")
        report.append(f"| 75-89 | B - 良好 | 基本诚信，无明显问题 |")
        report.append(f"| 60-74 | C - 中等 | 有待观察，注意风险 |")
        report.append(f"| <60 | D - 高风险 | 诚信问题，建议规避 |")
        report.append(f"")
        
        # 扣分详情
        if self.deductions:
            report.append(f"## ❌ 扣分详情")
            report.append(f"")
            report.append(f"| 类型 | 扣分 | 证据 | 日期 |")
            report.append(f"|------|------|------|------|")
            for d in self.deductions:
                report.append(f"| {d['type']} | {d['score']} | {d['evidence'][:50]}... | {d['date']} |")
            report.append(f"")
        else:
            report.append(f"## ✅ 无扣分项")
            report.append(f"")
            report.append(f"未发现承诺未兑现、信息披露违规、监管处罚或大股东违规减持记录。")
            report.append(f"")
        
        # 证据列表
        report.append(f"## 📋 证据列表")
        report.append(f"")
        for e in self.evidence:
            report.append(f"- {e}")
        report.append(f"")
        
        # 投资建议
        report.append(f"## 💡 投资建议")
        report.append(f"")
        if self.score >= 90:
            report.append(f"**诚信记录优秀，可以信任。** 管理层诚信度高，信息披露规范，无不良记录。")
        elif self.score >= 75:
            report.append(f"**诚信记录良好。** 未发现重大诚信问题，可正常投资。")
        elif self.score >= 60:
            report.append(f"**诚信记录中等。** 存在一些瑕疵，建议保持关注，谨慎投资。")
        else:
            report.append(f"**诚信高风险。** 存在严重诚信问题，**建议规避**该股票。")
        report.append(f"")
        
        # 免责声明
        report.append(f"---")
        report.append(f"")
        report.append(f"**数据来源：** Tushare Pro、巨潮资讯网公开数据")
        report.append(f"**免责声明：** 本报告仅供参考，不构成投资建议。投资需谨慎，决策需自主。")
        report.append(f"")
        report.append(f"*AI 价值投资系统 v2.0 | 让投资更简单*")
        
        return '\n'.join(report)
    
    def save_report(self, report: str):
        """保存报告"""
        output_dir = Path(__file__).parent.parent / 'cache' / 'integrity'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{self.ts_code.replace('.', '_')}_integrity_{datetime.now().strftime('%Y%m%d')}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(output_file)
    
    def run(self):
        """执行诚信评分"""
        print(f"🦀 开始评估{self.stock_name}管理层诚信...")
        
        # 生成报告
        report = self.generate_report()
        
        # 保存报告
        output_file = self.save_report(report)
        
        print(f"✅ 诚信评分已完成：{self.score}分 ({self.rating})")
        print(f"报告已保存：{output_file}")
        
        return {
            'ts_code': self.ts_code,
            'stock_name': self.stock_name,
            'score': self.score,
            'rating': self.rating,
            'level': self.level,
            'report_file': output_file
        }


if __name__ == '__main__':
    # 测试：华明装备
    ts_code = '002270.SZ'
    integrity = IntegrityScore(ts_code)
    result = integrity.run()
    
    print(f"\n📊 评分结果：{result['score']}分 - {result['rating']}")
