"""
报告摘要生成器 v2.0

功能：
- 生成 3-5 行摘要报告
- 支持盘前/盘后/持仓监控报告
- 附带完整报告链接

稳定性保障：
- 独立新模块，不影响现有报告生成
- 配置开关控制
- 可降级为详细报告
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
logger = get_logger('summary_generator')


class ReportSummarizer:
    """报告摘要生成器"""
    
    def __init__(self):
        """初始化摘要生成器"""
        self.max_summary_lines = 5  # 最多 5 行
        self.enabled = True
    
    def summarize_portfolio(self, report: dict) -> str:
        """
        生成持仓监控摘要
        
        Args:
            report: 持仓监控报告数据
        
        Returns:
            str: 3-5 行摘要
        """
        if not report:
            return "⚠️ 报告数据为空"
        
        summary = report.get('summary', {})
        alerts = report.get('alerts', [])
        portfolio = report.get('portfolio', [])
        
        # 第 1 行：标题 + 时间
        timestamp = datetime.now().strftime('%H:%M')
        lines = [f"【持仓监控】{timestamp}"]
        
        # 第 2 行：状态 + 总市值
        total_mv = summary.get('total_market_value', 0)
        total_pnl_ratio = summary.get('total_pnl_ratio', 0)
        
        if alerts:
            # 有预警
            red_count = sum(1 for a in alerts if a.get('level') == '🔴 红色')
            orange_count = sum(1 for a in alerts if a.get('level') == '🟠 橙色')
            green_count = sum(1 for a in alerts if a.get('level') == '🟢 机会')
            
            status_parts = []
            if red_count > 0:
                status_parts.append(f"🔴{red_count}")
            if orange_count > 0:
                status_parts.append(f"🟠{orange_count}")
            if green_count > 0:
                status_parts.append(f"🟢{green_count}")
            
            status = " ".join(status_parts)
        else:
            status = "✅ 正常"
        
        lines[0] += f" {status} | 总市值¥{total_mv:,.0f} ({total_pnl_ratio:+.2f}%) |"
        
        # 第 3 行：持仓摘要（标的名 + 市值）
        if portfolio:
            holdings_summary = " ".join([
                f"{p['name']}¥{p['market_value']/10000:.0f}万"
                for p in portfolio[:3]  # 最多显示 3 个
            ])
            lines.append(holdings_summary)
        
        # 第 4 行：预警摘要（如有）
        if alerts:
            top_alert = alerts[0]
            lines.append(f"⚠️ {top_alert.get('stock', '')}: {top_alert.get('message', '')[:30]}")
        
        # 第 5 行：详细报告链接
        lines.append(f"📎 详细：cache/monitor/{datetime.now().strftime('%Y%m%d_%H%M')}.json")
        
        result = " | ".join(lines[:1]) + "\n"
        if len(lines) > 1:
            result += "\n".join(lines[1:])
        
        return result
    
    def summarize_analysis(self, analysis_result: dict) -> str:
        """
        生成个股分析摘要
        
        Args:
            analysis_result: 个股分析结果
        
        Returns:
            str: 3-5 行摘要
        """
        if not analysis_result:
            return "⚠️ 分析数据为空"
        
        conclusion = analysis_result.get('conclusion', {})
        ts_code = analysis_result.get('ts_code', 'N/A')
        stock_name = analysis_result.get('stock_name', 'N/A')
        
        # 第 1 行：标题
        lines = [f"【个股分析】{stock_name} ({ts_code})"]
        
        # 第 2 行：评级 + 通过率
        recommendation = conclusion.get('recommendation', 'N/A')
        pass_rate = conclusion.get('pass_rate', 0)
        risk_level = conclusion.get('risk_level', 'N/A')
        
        lines.append(f"评级：{recommendation} | 通过率：{pass_rate:.0%} | 风险：{risk_level}")
        
        # 第 3 行：核心亮点（如有）
        highlights = conclusion.get('highlights', [])
        if highlights:
            lines.append(f"亮点：{highlights[0][:40]}")
        
        # 第 4 行：主要风险（如有）
        risks = conclusion.get('risks', [])
        if risks:
            lines.append(f"风险：{risks[0][:40]}")
        
        # 第 5 行：完整报告链接
        report_path = analysis_result.get('report_path', 'N/A')
        lines.append(f"📎 详细：{report_path}")
        
        return "\n".join(lines[:self.max_summary_lines])
    
    def summarize_review(self, review_result: dict, review_type: str = 'weekly') -> str:
        """
        生成复盘报告摘要
        
        Args:
            review_result: 复盘报告结果
            review_type: 复盘类型（weekly/monthly/quarterly）
        
        Returns:
            str: 3-5 行摘要
        """
        if not review_result:
            return "⚠️ 复盘数据为空"
        
        # 第 1 行：标题
        type_names = {
            'weekly': '周复盘',
            'monthly': '月复盘',
            'quarterly': '季复盘',
            'annual': '年复盘'
        }
        type_name = type_names.get(review_type, '复盘')
        
        period = review_result.get('period', 'N/A')
        lines = [f"【{type_name}】{period}"]
        
        # 第 2 行：市场表现
        market_summary = review_result.get('market_summary', {})
        index_change = market_summary.get('index_change', 0)
        lines.append(f"市场：{market_summary.get('index_name', '上证指数')} {index_change:+.2f}%")
        
        # 第 3 行：持仓表现
        portfolio_summary = review_result.get('portfolio_summary', {})
        portfolio_return = portfolio_summary.get('return', 0)
        lines.append(f"持仓：{portfolio_return:+.2f}% | 跑赢：{portfolio_return - index_change:+.2f}%")
        
        # 第 4 行：操作总结
        operations = review_result.get('operations', [])
        if operations:
            lines.append(f"操作：{len(operations)} 笔 | 详情见报告")
        
        # 第 5 行：完整报告链接
        report_path = review_result.get('report_path', 'N/A')
        lines.append(f"📎 详细：{report_path}")
        
        return "\n".join(lines[:self.max_summary_lines])
    
    def format_for_dingtalk(self, summary: str, title: str = None) -> dict:
        """
        格式化为钉钉消息
        
        Args:
            summary: 摘要文本
            title: 消息标题
        
        Returns:
            dict: 钉钉消息 payload
        """
        if not title:
            title = "AI 价值投资系统"
        
        # 钉钉 Markdown 格式
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": summary.replace('\n', '\n\n')  # 钉钉需要双换行
            },
            "at": {
                "isAtAll": False  # 默认不@所有人
            }
        }
        
        return payload


# 全局实例
_summarizer_instance = None


def get_summarizer() -> ReportSummarizer:
    """获取摘要生成器实例"""
    global _summarizer_instance
    if _summarizer_instance is None:
        _summarizer_instance = ReportSummarizer()
    return _summarizer_instance


# CLI 测试入口
if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"报告摘要生成器 v2.0 - 测试")
    print(f"{'='*60}\n")
    
    summarizer = get_summarizer()
    
    # 测试持仓摘要
    print("测试 1: 持仓监控摘要")
    test_portfolio_report = {
        'summary': {
            'total_market_value': 314160,
            'total_pnl_ratio': -0.0012,
        },
        'portfolio': [
            {'name': '华明装备', 'market_value': 164400},
            {'name': '电网设备 ETF', 'market_value': 149760},
        ],
        'alerts': [
            {'level': '🟢 机会', 'stock': '华明装备', 'message': '现价 26.37 接近补仓位 26.0'}
        ]
    }
    summary = summarizer.summarize_portfolio(test_portfolio_report)
    print(summary)
    print()
    
    # 测试个股分析摘要
    print("测试 2: 个股分析摘要")
    test_analysis = {
        'ts_code': '002270.SZ',
        'stock_name': '华明装备',
        'conclusion': {
            'recommendation': '可买入',
            'pass_rate': 0.85,
            'risk_level': '低',
            'highlights': ['ROE 连续 5 年>15%', 'PE 分位 30%'],
            'risks': ['应收账款增长较快']
        },
        'report_path': 'cache/analysis/002270_20260407.md'
    }
    summary = summarizer.summarize_analysis(test_analysis)
    print(summary)
    print()
    
    # 测试钉钉格式化
    print("测试 3: 钉钉消息格式化")
    payload = summarizer.format_for_dingtalk(summary, "个股分析摘要")
    print(f"消息类型：{payload['msgtype']}")
    print(f"标题：{payload['markdown']['title']}")
    print()
    
    print(f"{'='*60}")
    print(f"✅ 摘要生成器测试完成")
    print(f"{'='*60}\n")
