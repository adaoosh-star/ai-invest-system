"""
安全边际动态校准模型
- 根据市场情绪、行业周期、个股风险动态调整安全边际
- 基础安全边际：30%（格雷厄姆标准）
- 动态调整范围：20% - 40%

核心逻辑：
安全边际 = 基础安全边际 × 动态调整系数
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.tushare_client import pro, get_pe_pb_percentile, get_roe
from model.integrity_score import IntegrityScore


class SafetyMargin:
    """安全边际动态校准"""
    
    # 基础安全边际（格雷厄姆标准）
    BASE_MARGIN = 0.30  # 30%
    
    # 调整范围
    MIN_MARGIN = 0.20  # 20%（市场极度乐观时）
    MAX_MARGIN = 0.40  # 40%（市场极度悲观时）
    
    def __init__(self, ts_code: str = None):
        """
        初始化安全边际校准
        
        参数：
        - ts_code: 股票代码（可选，不传则只计算市场整体）
        """
        self.ts_code = ts_code
        self.stock_name = self._get_stock_name() if ts_code else "市场整体"
        self.adjustments = []  # 调整记录
        
    def _get_stock_name(self):
        """获取股票名称"""
        try:
            df = pro.stock_basic(ts_code=self.ts_code)
            if not df.empty:
                return df.iloc[0]['name']
        except Exception as e:
            print(f"获取股票名称失败：{e}")
        return self.ts_code
    
    def calculate_market_sentiment(self):
        """
        计算市场情绪调整
        
        使用全市场 PE 分位判断市场情绪
        
        返回：调整幅度（-0.10 ~ +0.10）
        """
        print(f"📊 计算市场情绪调整...")
        
        try:
            # 获取上证指数 PE 分位
            # 简化：使用沪深 300 代表市场
            pe_data = get_pe_pb_percentile('000300.SH')
            
            if not pe_data:
                self.adjustments.append({
                    'factor': '市场情绪',
                    'adjustment': 0,
                    'reason': '数据获取失败，使用中性假设'
                })
                return 0
            
            pe_percentile = pe_data.get('pe_percentile', 50)
            
            # 根据 PE 分位调整
            if pe_percentile < 20:
                # 市场极度悲观，放宽安全边际
                adjustment = 0.10
                reason = f'市场 PE 分位{pe_percentile:.1f}% < 20%，极度悲观'
            elif pe_percentile < 40:
                # 市场偏悲观
                adjustment = 0.05
                reason = f'市场 PE 分位{pe_percentile:.1f}% < 40%，偏悲观'
            elif pe_percentile < 60:
                # 市场中性
                adjustment = 0
                reason = f'市场 PE 分位{pe_percentile:.1f}%，中性'
            elif pe_percentile < 80:
                # 市场偏乐观
                adjustment = -0.05
                reason = f'市场 PE 分位{pe_percentile:.1f}% > 60%，偏乐观'
            else:
                # 市场极度乐观
                adjustment = -0.10
                reason = f'市场 PE 分位{pe_percentile:.1f}% > 80%，极度乐观'
            
            self.adjustments.append({
                'factor': '市场情绪',
                'adjustment': adjustment,
                'reason': reason
            })
            
            return adjustment
            
        except Exception as e:
            print(f"计算市场情绪失败：{e}")
            self.adjustments.append({
                'factor': '市场情绪',
                'adjustment': 0,
                'reason': f'计算失败：{e}'
            })
            return 0
    
    def calculate_industry_cycle(self, industry: str = None):
        """
        计算行业周期调整
        
        使用行业 PE 分位判断行业周期
        
        参数：
        - industry: 行业名称（可选，自动获取）
        
        返回：调整幅度（-0.05 ~ +0.05）
        """
        print(f"🏭 计算行业周期调整...")
        
        if not self.ts_code:
            self.adjustments.append({
                'factor': '行业周期',
                'adjustment': 0,
                'reason': '无个股代码，跳过行业分析'
            })
            return 0
        
        try:
            # 获取股票所属行业
            if not industry:
                df = pro.stock_basic(ts_code=self.ts_code)
                if not df.empty:
                    industry = df.iloc[0].get('industry', '')
            
            if not industry:
                self.adjustments.append({
                    'factor': '行业周期',
                    'adjustment': 0,
                    'reason': '无法获取行业信息'
                })
                return 0
            
            # 获取行业 PE 分位（简化：使用行业中位数）
            # TODO: 完善行业对比数据获取
            industry_pe = 50  # 默认中性
            
            # 根据行业 PE 分位调整
            if industry_pe < 30:
                # 行业底部
                adjustment = 0.05
                reason = f'{industry} 处于周期底部'
            elif industry_pe < 50:
                # 行业偏底部
                adjustment = 0.02
                reason = f'{industry} 处于周期偏底部'
            elif industry_pe < 70:
                # 行业中性
                adjustment = 0
                reason = f'{industry} 处于周期中性'
            elif industry_pe < 90:
                # 行业偏顶部
                adjustment = -0.02
                reason = f'{industry} 处于周期偏顶部'
            else:
                # 行业顶部
                adjustment = -0.05
                reason = f'{industry} 处于周期顶部'
            
            self.adjustments.append({
                'factor': '行业周期',
                'adjustment': adjustment,
                'reason': reason
            })
            
            return adjustment
            
        except Exception as e:
            print(f"计算行业周期失败：{e}")
            self.adjustments.append({
                'factor': '行业周期',
                'adjustment': 0,
                'reason': f'计算失败：{e}'
            })
            return 0
    
    def calculate_individual_risk(self):
        """
        计算个股风险调整
        
        使用诚信评分、财务风险等
        
        返回：调整幅度（-0.05 ~ +0.05）
        """
        print(f"⚠️ 计算个股风险调整...")
        
        if not self.ts_code:
            self.adjustments.append({
                'factor': '个股风险',
                'adjustment': 0,
                'reason': '无个股代码，跳过个股分析'
            })
            return 0
        
        try:
            adjustment = 0
            reasons = []
            
            # 1. 诚信评分调整
            integrity = IntegrityScore(self.ts_code)
            integrity_result = integrity.run()
            score = integrity_result['score']
            
            if score >= 90:
                # 诚信优秀，降低风险溢价
                adjustment += 0.05
                reasons.append(f'诚信评分{score}分（优秀）')
            elif score >= 75:
                # 诚信良好
                adjustment += 0.02
                reasons.append(f'诚信评分{score}分（良好）')
            elif score >= 60:
                # 诚信中等
                adjustment += 0
                reasons.append(f'诚信评分{score}分（中等）')
            else:
                # 诚信高风险
                adjustment -= 0.05
                reasons.append(f'诚信评分{score}分（高风险）')
            
            # 2. 财务风险调整（简化：使用 ROE）
            roe_data = get_roe(self.ts_code)
            if not roe_data.empty:
                avg_roe = roe_data['roe_dt'].mean()
                if avg_roe > 15:
                    # ROE 优秀
                    adjustment += 0.03
                    reasons.append(f'ROE 平均{avg_roe:.1f}%（优秀）')
                elif avg_roe > 10:
                    # ROE 良好
                    adjustment += 0.01
                    reasons.append(f'ROE 平均{avg_roe:.1f}%（良好）')
                elif avg_roe > 5:
                    # ROE 中等
                    adjustment += 0
                    reasons.append(f'ROE 平均{avg_roe:.1f}%（中等）')
                else:
                    # ROE 较差
                    adjustment -= 0.03
                    reasons.append(f'ROE 平均{avg_roe:.1f}%（较差）')
            
            # 限制调整范围
            adjustment = max(-0.05, min(0.05, adjustment))
            
            self.adjustments.append({
                'factor': '个股风险',
                'adjustment': adjustment,
                'reason': '；'.join(reasons)
            })
            
            return adjustment
            
        except Exception as e:
            print(f"计算个股风险失败：{e}")
            self.adjustments.append({
                'factor': '个股风险',
                'adjustment': 0,
                'reason': f'计算失败：{e}'
            })
            return 0
    
    def calculate(self):
        """
        计算最终安全边际
        
        返回：dict
        """
        print(f"🦀 开始计算{self.stock_name}安全边际...")
        
        # 计算各项调整
        market_adj = self.calculate_market_sentiment()
        industry_adj = self.calculate_industry_cycle()
        risk_adj = self.calculate_individual_risk()
        
        # 计算总调整
        total_adjustment = market_adj + industry_adj + risk_adj
        
        # 计算最终安全边际
        final_margin = self.BASE_MARGIN + total_adjustment
        
        # 限制在合理范围内
        final_margin = max(self.MIN_MARGIN, min(self.MAX_MARGIN, final_margin))
        
        # 计算结果
        result = {
            'ts_code': self.ts_code,
            'stock_name': self.stock_name,
            'base_margin': self.BASE_MARGIN,
            'adjustments': {
                'market_sentiment': market_adj,
                'industry_cycle': industry_adj,
                'individual_risk': risk_adj,
                'total': total_adjustment
            },
            'final_margin': final_margin,
            'margin_type': self._get_margin_type(final_margin),
            'calculation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ {self.stock_name}安全边际：{final_margin:.1%} ({result['margin_type']})")
        
        return result
    
    def _get_margin_type(self, margin: float):
        """获取安全边际类型"""
        if margin >= 0.35:
            return '保守型（高安全边际）'
        elif margin >= 0.30:
            return '标准型（格雷厄姆标准）'
        else:
            return '积极型（低安全边际）'
    
    def generate_report(self, result: dict):
        """生成安全边际报告"""
        report = []
        
        report.append(f"# 🦀 AI 价值投资系统 v1.0 - 安全边际动态校准报告")
        report.append(f"")
        report.append(f"**股票代码：** {result.get('ts_code', 'N/A')}")
        report.append(f"**股票名称：** {result['stock_name']}")
        report.append(f"**计算时间：** {result['calculation_time']}")
        report.append(f"")
        
        # 计算结果
        report.append(f"## 📊 安全边际计算结果")
        report.append(f"")
        report.append(f"| 项目 | 数值 |")
        report.append(f"|------|------|")
        report.append(f"| **基础安全边际** | **{result['base_margin']:.1%}** |")
        report.append(f"| 市场情绪调整 | {result['adjustments']['market_sentiment']:+.1%} |")
        report.append(f"| 行业周期调整 | {result['adjustments']['industry_cycle']:+.1%} |")
        report.append(f"| 个股风险调整 | {result['adjustments']['individual_risk']:+.1%} |")
        report.append(f"| **总调整** | **{result['adjustments']['total']:+.1%}** |")
        report.append(f"| **最终安全边际** | **{result['final_margin']:.1%}** |")
        report.append(f"| **类型** | **{result['margin_type']}** |")
        report.append(f"")
        
        # 调整详情
        report.append(f"## 📋 调整详情")
        report.append(f"")
        for adj in self.adjustments:
            report.append(f"### {adj['factor']}")
            report.append(f"")
            report.append(f"- **调整幅度：** {adj['adjustment']:+.1%}")
            report.append(f"- **原因：** {adj['reason']}")
            report.append(f"")
        
        # 使用建议
        report.append(f"## 💡 使用建议")
        report.append(f"")
        if result['final_margin'] >= 0.35:
            report.append(f"**保守型安全边际（{result['final_margin']:.1%}）**")
            report.append(f"")
            report.append(f"当前市场环境或个股风险较高，建议采用更保守的安全边际。")
            report.append(f"")
            report.append(f"**买入条件：** 价格 < 内在价值 × {1 - result['final_margin']:.1%}")
        elif result['final_margin'] >= 0.30:
            report.append(f"**标准型安全边际（{result['final_margin']:.1%}）**")
            report.append(f"")
            report.append(f"市场环境正常，采用格雷厄姆标准安全边际。")
            report.append(f"")
            report.append(f"**买入条件：** 价格 < 内在价值 × {1 - result['final_margin']:.1%}")
        else:
            report.append(f"**积极型安全边际（{result['final_margin']:.1%}）**")
            report.append(f"")
            report.append(f"市场环境较好或个股质量优秀，可适当降低安全边际要求。")
            report.append(f"")
            report.append(f"**买入条件：** 价格 < 内在价值 × {1 - result['final_margin']:.1%}")
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
        output_dir = Path(__file__).parent.parent / 'cache' / 'margin'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        ts_code_part = self.ts_code.replace('.', '_') if self.ts_code else 'market'
        output_file = output_dir / f"{ts_code_part}_margin_{datetime.now().strftime('%Y%m%d')}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(output_file)
    
    def run(self):
        """执行安全边际计算"""
        # 计算
        result = self.calculate()
        
        # 生成报告
        report = self.generate_report(result)
        
        # 保存报告
        output_file = self.save_report(report)
        
        print(f"✅ 报告已保存：{output_file}")
        
        return result


if __name__ == '__main__':
    # 测试：华明装备
    ts_code = '002270.SZ'
    margin = SafetyMargin(ts_code)
    result = margin.run()
    
    print(f"\n📊 最终安全边际：{result['final_margin']:.1%} ({result['margin_type']})")
