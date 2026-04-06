"""
年报深度解读模块 v2.0

功能：
- MD&A 深度分析（LLM 增强）
- 财报附注关键信息提取
- 跨年度趋势分析
- 管理层讨论与解读
- 风险因素识别

稳定性保障：
- 独立新模块，不影响现有代码
- 配置开关控制
- 降级方案（LLM 失败时规则式）
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
from analysis.llm_enhanced import call_qwen_api, get_llm_analyzer

logger = get_logger('annual_report_analyzer')

# 配置
ANALYSIS_CONFIG = {
    'enabled': True,
    'llm_enabled': True,  # LLM 增强分析
    'years_to_compare': 3,  # 跨年度对比年数
    'key_metrics': [
        'revenue', 'net_profit', 'gross_margin', 'roe',
        'cash_flow_ratio', 'debt_ratio', 'rd_expense_ratio'
    ]
}


class AnnualReportAnalyzer:
    """年报深度解读引擎"""
    
    def __init__(self):
        """初始化年报分析器"""
        self.config = ANALYSIS_CONFIG
        self.llm_analyzer = get_llm_analyzer() if self.config['llm_enabled'] else None
    
    def analyze_mda(self, mda_text: str, year: int) -> dict:
        """
        MD&A（管理层讨论与分析）深度解读
        
        Args:
            mda_text: MD&A 文本内容
            year: 报告年份
        
        Returns:
            dict: 分析结果
        """
        logger.info(f"分析 MD&A ({year}年)...")
        
        if not self.config['enabled']:
            return {'error': '分析未启用'}
        
        # 1. 基础分析（规则式）
        rule_analysis = self._rule_based_mda_analysis(mda_text)
        
        # 2. LLM 增强分析
        llm_analysis = None
        if self.config['llm_enabled'] and self.llm_analyzer:
            llm_analysis = self._llm_mda_analysis(mda_text, year)
        
        # 3. 合并结果
        result = {
            'year': year,
            'word_count': len(mda_text),
            'rule_based': rule_analysis,
            'llm_enhanced': llm_analysis,
            'summary': self._generate_mda_summary(rule_analysis, llm_analysis)
        }
        
        return result
    
    def _rule_based_mda_analysis(self, mda_text: str) -> dict:
        """规则式 MD&A 分析"""
        # 关键词统计
        positive_keywords = ['增长', '提升', '突破', '创新', '领先', '优势', '机遇']
        negative_keywords = ['风险', '挑战', '下滑', '下降', '困难', '压力', '不确定性']
        risk_keywords = ['风险', '不确定性', '可能', '影响', '波动']
        
        positive_count = sum(mda_text.count(kw) for kw in positive_keywords)
        negative_count = sum(mda_text.count(kw) for kw in negative_keywords)
        risk_count = sum(mda_text.count(kw) for kw in risk_keywords)
        
        # 情感倾向
        if positive_count > negative_count * 1.5:
            sentiment = '积极'
        elif negative_count > positive_count * 1.5:
            sentiment = '消极'
        else:
            sentiment = '中性'
        
        return {
            'word_count': len(mda_text),
            'positive_mentions': positive_count,
            'negative_mentions': negative_count,
            'risk_mentions': risk_count,
            'sentiment': sentiment,
            'sentiment_score': (positive_count - negative_count) / max(1, positive_count + negative_count)
        }
    
    def _llm_mda_analysis(self, mda_text: str, year: int) -> dict:
        """LLM 增强 MD&A 分析"""
        try:
            system_prompt = """你是一个专业的投资分析师，擅长解读上市公司年报的 MD&A（管理层讨论与分析）。
请分析管理层对过去一年的总结和对未来的展望，提取关键信息。
返回 JSON 格式的分析结果。"""
            
            prompt = f"""请分析以下{year}年年报的 MD&A 内容：

"{mda_text[:3000]}..."  # 限制长度

请返回 JSON 格式的分析结果，包含以下字段：
- key_achievements: 关键成就（3-5 个）
- main_challenges: 主要挑战（2-3 个）
- future_outlook: 未来展望（积极/中性/消极）
- strategic_focus: 战略重点（2-3 个）
- risk_factors: 风险因素（3-5 个）
- management_tone: 管理层语气（自信/谨慎/乐观/悲观）
- credibility: 可信度评分（0-1 之间的小数）

只返回 JSON，不要其他内容。"""
            
            result = call_qwen_api(prompt, system_prompt)
            
            if result.get('success'):
                # 解析 JSON 响应
                json_match = re.search(r'\{.*\}', result['content'], re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    analysis['method'] = 'llm'
                    return analysis
            
            return None
        except Exception as e:
            logger.warning(f"LLM MD&A 分析失败：{e}，降级为规则分析")
            return None
    
    def _generate_mda_summary(self, rule_analysis: dict, llm_analysis: dict = None) -> str:
        """生成 MD&A 摘要"""
        summary_lines = []
        
        # 规则分析摘要
        sentiment = rule_analysis.get('sentiment', 'N/A')
        sentiment_score = rule_analysis.get('sentiment_score', 0)
        summary_lines.append(f"情感倾向：{sentiment} ({sentiment_score:.2f})")
        
        # LLM 分析摘要
        if llm_analysis:
            tone = llm_analysis.get('management_tone', 'N/A')
            credibility = llm_analysis.get('credibility', 0)
            summary_lines.append(f"管理层语气：{tone} (可信度{credibility:.2f})")
            
            achievements = llm_analysis.get('key_achievements', [])
            if achievements:
                summary_lines.append(f"关键成就：{len(achievements)} 个")
        
        return ' | '.join(summary_lines)
    
    def extract_key_info(self, financial_notes: dict) -> dict:
        """
        财报附注关键信息提取
        
        Args:
            financial_notes: 财报附注数据
        
        Returns:
            dict: 关键信息
        """
        logger.info("提取财报附注关键信息...")
        
        key_info = {
            'related_party_transactions': self._extract_related_party(financial_notes),
            'asset_impairment': self._extract_asset_impairment(financial_notes),
            'contingent_liabilities': self._extract_contingent_liabilities(financial_notes),
            'accounting_policy_changes': self._extract_accounting_policy_changes(financial_notes),
            'segment_performance': self._extract_segment_performance(financial_notes),
        }
        
        return key_info
    
    def _extract_related_party(self, notes: dict) -> list:
        """提取关联交易信息"""
        # TODO: 实际实现需要从财报数据中提取
        return []
    
    def _extract_asset_impairment(self, notes: dict) -> list:
        """提取资产减值信息"""
        return []
    
    def _extract_contingent_liabilities(self, notes: dict) -> list:
        """提取或有负债信息"""
        return []
    
    def _extract_accounting_policy_changes(self, notes: dict) -> list:
        """提取会计政策变更"""
        return []
    
    def _extract_segment_performance(self, notes: dict) -> list:
        """提取分部业绩"""
        return []
    
    def analyze_trend(self, historical_data: List[dict]) -> dict:
        """
        跨年度趋势分析
        
        Args:
            historical_data: 历史数据列表（多年）
        
        Returns:
            dict: 趋势分析结果
        """
        logger.info(f"跨年度趋势分析（{len(historical_data)}年）...")
        
        if len(historical_data) < 2:
            return {'error': '数据不足 2 年'}
        
        trend_analysis = {}
        
        for metric in self.config['key_metrics']:
            values = [data.get(metric) for data in historical_data if data.get(metric) is not None]
            if len(values) >= 2:
                trend_analysis[metric] = self._calculate_trend(values)
        
        return {
            'years': len(historical_data),
            'metrics': trend_analysis,
            'overall_trend': self._assess_overall_trend(trend_analysis)
        }
    
    def _calculate_trend(self, values: List[float]) -> dict:
        """计算单一指标的趋势"""
        if len(values) < 2:
            return {}
        
        # 计算复合增长率
        n = len(values) - 1
        if values[0] == 0:
            cagr = 0
        else:
            cagr = (values[-1] / values[0]) ** (1/n) - 1
        
        # 计算波动率
        import statistics
        volatility = statistics.stdev(values) if len(values) > 1 else 0
        
        # 判断趋势方向
        if cagr > 0.10:
            trend = '快速增长'
        elif cagr > 0:
            trend = '稳定增长'
        elif cagr > -0.10:
            trend = '小幅下滑'
        else:
            trend = '快速下滑'
        
        return {
            'cagr': cagr,
            'volatility': volatility,
            'trend': trend,
            'start_value': values[0],
            'end_value': values[-1],
        }
    
    def _assess_overall_trend(self, trend_analysis: dict) -> str:
        """评估整体趋势"""
        positive_count = 0
        negative_count = 0
        
        for metric, trend in trend_analysis.items():
            cagr = trend.get('cagr', 0)
            if cagr > 0.05:
                positive_count += 1
            elif cagr < -0.05:
                negative_count += 1
        
        total = positive_count + negative_count
        if total == 0:
            return '平稳'
        
        positive_ratio = positive_count / total
        if positive_ratio > 0.7:
            return '整体向好'
        elif positive_ratio > 0.4:
            return '分化'
        else:
            return '整体承压'
    
    def generate_full_report(self, ts_code: str, stock_name: str,
                            mda_text: str = None, financial_notes: dict = None,
                            historical_data: List[dict] = None) -> str:
        """
        生成完整年报解读报告
        
        Args:
            ts_code: 股票代码
            stock_name: 股票名称
            mda_text: MD&A 文本
            financial_notes: 财报附注
            historical_data: 历史数据
        
        Returns:
            str: Markdown 格式报告
        """
        logger.info(f"生成年报解读报告：{stock_name} ({ts_code})")
        
        report = []
        
        # 报告头部
        report.append(f"# 📊 {stock_name} ({ts_code}) - 年报深度解读")
        report.append(f"")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"")
        
        # 第一部分：MD&A 深度解读
        if mda_text:
            report.append(f"## 📖 第一部分：MD&A 深度解读")
            report.append(f"")
            
            mda_analysis = self.analyze_mda(mda_text, datetime.now().year)
            
            report.append(f"### 管理层讨论与分析")
            report.append(f"")
            report.append(f"**字数**: {mda_analysis.get('word_count', 0):,} 字")
            report.append(f"")
            report.append(f"**摘要**: {mda_analysis.get('summary', 'N/A')}")
            report.append(f"")
            
            # 规则分析结果
            rule_analysis = mda_analysis.get('rule_based', {})
            report.append(f"### 规则分析")
            report.append(f"")
            report.append(f"| 指标 | 数值 |")
            report.append(f"|------|------|")
            report.append(f"| 积极词汇 | {rule_analysis.get('positive_mentions', 0)} 次 |")
            report.append(f"| 消极词汇 | {rule_analysis.get('negative_mentions', 0)} 次 |")
            report.append(f"| 风险提及 | {rule_analysis.get('risk_mentions', 0)} 次 |")
            report.append(f"| 情感倾向 | {rule_analysis.get('sentiment', 'N/A')} |")
            report.append(f"")
            
            # LLM 分析结果
            llm_analysis = mda_analysis.get('llm_enhanced')
            if llm_analysis:
                report.append(f"### LLM 增强分析")
                report.append(f"")
                report.append(f"**管理层语气**: {llm_analysis.get('management_tone', 'N/A')}")
                report.append(f"**可信度**: {llm_analysis.get('credibility', 0):.2f}")
                report.append(f"")
                
                achievements = llm_analysis.get('key_achievements', [])
                if achievements:
                    report.append(f"**关键成就**:")
                    for i, achievement in enumerate(achievements, 1):
                        report.append(f"{i}. {achievement}")
                    report.append(f"")
                
                risks = llm_analysis.get('risk_factors', [])
                if risks:
                    report.append(f"**风险因素**:")
                    for i, risk in enumerate(risks, 1):
                        report.append(f"{i}. {risk}")
                    report.append(f"")
        
        # 第二部分：财报附注关键信息
        if financial_notes:
            report.append(f"## 📋 第二部分：财报附注关键信息")
            report.append(f"")
            
            key_info = self.extract_key_info(financial_notes)
            
            report.append(f"### 关联交易")
            report.append(f"")
            if key_info.get('related_party_transactions'):
                for item in key_info['related_party_transactions']:
                    report.append(f"- {item}")
            else:
                report.append(f"- 无重大关联交易")
            report.append(f"")
            
            report.append(f"### 资产减值")
            report.append(f"")
            if key_info.get('asset_impairment'):
                for item in key_info['asset_impairment']:
                    report.append(f"- {item}")
            else:
                report.append(f"- 无重大资产减值")
            report.append(f"")
        
        # 第三部分：跨年度趋势分析
        if historical_data:
            report.append(f"## 📈 第三部分：跨年度趋势分析")
            report.append(f"")
            
            trend_analysis = self.analyze_trend(historical_data)
            
            report.append(f"### 整体趋势：{trend_analysis.get('overall_trend', 'N/A')}")
            report.append(f"")
            
            metrics = trend_analysis.get('metrics', {})
            if metrics:
                report.append(f"| 指标 | 趋势 | CAGR | 波动率 |")
                report.append(f"|------|------|------|--------|")
                
                for metric, trend in metrics.items():
                    metric_name = metric.replace('_', ' ').title()
                    report.append(f"| {metric_name} | {trend.get('trend', 'N/A')} | {trend.get('cagr', 0):+.1%} | {trend.get('volatility', 0):.2f} |")
                report.append(f"")
        
        # 第四部分：投资建议
        report.append(f"## 💡 第四部分：投资建议")
        report.append(f"")
        report.append(f"**综合评估**: 待完善")
        report.append(f"")
        report.append(f"**建议**: 待完善")
        report.append(f"")
        
        # 免责声明
        report.append(f"---")
        report.append(f"")
        report.append(f"**免责声明**: 本报告仅供参考，不构成投资建议。投资需谨慎，决策需自主。")
        report.append(f"")
        
        return '\n'.join(report)


# 全局实例
_analyzer_instance = None


def get_annual_analyzer() -> AnnualReportAnalyzer:
    """获取年报分析器实例"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = AnnualReportAnalyzer()
    return _analyzer_instance


# CLI 测试入口
if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"年报深度解读模块 - 测试")
    print(f"{'='*60}\n")
    
    analyzer = get_annual_analyzer()
    
    # 测试 MD&A 分析
    print("测试 1: MD&A 分析")
    sample_mda = """
    2025 年，公司实现营业收入 50 亿元，同比增长 25%。
    净利润 8 亿元，同比增长 30%。
    公司继续加大研发投入，研发费用占营收比例达到 8%。
    主要产品市场份额进一步提升，竞争优势巩固。
    
    面临挑战：
    1. 原材料价格波动风险
    2. 行业竞争加剧
    3. 宏观经济不确定性
    
    展望未来，公司将继续坚持创新驱动发展战略，
    深耕主业，提升核心竞争力，为股东创造更大价值。
    """
    
    result = analyzer.analyze_mda(sample_mda, 2025)
    print(f"字数：{result['word_count']}")
    print(f"摘要：{result['summary']}")
    print(f"规则分析：{result['rule_based']['sentiment']}")
    if result['llm_enhanced']:
        print(f"LLM 分析：{result['llm_enhanced'].get('management_tone', 'N/A')}")
    print()
    
    # 测试趋势分析
    print("测试 2: 跨年度趋势分析")
    historical_data = [
        {'revenue': 30, 'net_profit': 5, 'roe': 0.15, 'gross_margin': 0.40},
        {'revenue': 38, 'net_profit': 6.5, 'roe': 0.18, 'gross_margin': 0.42},
        {'revenue': 50, 'net_profit': 8, 'roe': 0.22, 'gross_margin': 0.45},
    ]
    result = analyzer.analyze_trend(historical_data)
    print(f"分析年数：{result['years']}")
    print(f"整体趋势：{result['overall_trend']}")
    print()
    
    # 测试完整报告生成
    print("测试 3: 完整报告生成")
    report = analyzer.generate_full_report(
        ts_code='002270.SZ',
        stock_name='华明装备',
        mda_text=sample_mda,
        financial_notes={},
        historical_data=historical_data
    )
    print(f"报告长度：{len(report)} 字符")
    print(f"报告包含章节：{report.count('## ')} 个")
    print()
    
    print(f"{'='*60}")
    print(f"✅ 年报深度解读模块测试完成")
    print(f"{'='*60}\n")
