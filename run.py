#!/usr/bin/env python3
"""
AI 价值投资系统 v1.0 - 统一入口

用法：
    python run.py analyze 002969.SZ    # 分析单只股票
    python run.py select               # 全市场选股
    python run.py monitor              # 持仓监控
    python run.py review               # 周复盘

投资宪法：所有分析必须通过本系统执行，禁止临时写脚本
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def analyze_stock(ts_code: str, full: bool = True):
    """
    分析单只股票（标准流程）
    
    参数：
    - ts_code: 股票代码（如 002969.SZ）
    - full: 是否执行完整分析（20 项+A 股风险+NLP）
    
    输出：
    - 关键结论 + 完整报告 + 文件路径（供 cron 推送钉钉）
    """
    from utils.logger import get_logger
    logger = get_logger('complete_analysis')
    
    logger.info(f"开始分析股票：{ts_code}")
    logger.info(f"分析模式：{'完整分析' if full else '20 项检查'}")
    
    try:
        if full:
            # 完整分析（20 项 + A 股风险 + NLP）
            from selection.complete_analysis import run_complete_analysis
            result = run_complete_analysis(ts_code, output_report=True, nlp_mode='simple')
        else:
            # 仅 20 项检查
            from selection.checklist_20 import fetch_financial_data, run_full_checklist
            financial_data = fetch_financial_data(ts_code)
            result = run_full_checklist(ts_code, financial_data)
        
        # 记录分析结果
        if result.get('conclusion'):
            conclusion = result.get('conclusion', {})
            if isinstance(conclusion, dict):
                logger.info(f"分析完成：{ts_code} - 评级={conclusion.get('recommendation', '未知')}, 通过率={conclusion.get('pass_rate', 0):.0%}")
            else:
                logger.info(f"分析完成：{ts_code}")
        
        # 如果有完整报告，输出：关键结论 + 完整报告 + 文件路径
        if result.get('report') and result.get('filepath'):
            conclusion = result.get('conclusion', {})
            recommendation = conclusion.get('recommendation', '未知')
            pass_rate = conclusion.get('pass_rate', 0)
            risk_level = conclusion.get('risk_level', '未知')
            
            logger.info(f"报告已保存：{result['filepath']}")
            
            # 关键结论（5 行）
            print(f"📊 {ts_code} 完整分析报告")
            print(f"")
            print(f"✅ 核心结论")
            print(f"- 评级：{recommendation}")
            print(f"- 通过率：{pass_rate:.0%}")
            print(f"- 风险等级：{risk_level}")
            print(f"")
            print(f"---")
            print(f"")
            # 完整报告
            print(result['report'])
            print(f"")
            print(f"---")
            print(f"")
            print(f"📁 报告已保存：{result['filepath']}")
        
        return result
        
    except Exception as e:
        logger.error(f"分析失败 {ts_code}: {e}", exc_info=True)
        raise

def select_stocks():
    """全市场自动化选股"""
    print(f"\n{'='*60}")
    print(f"AI 价值投资系统 v1.0 - 自动化选股")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    from selection.auto_select import auto_select_stocks
    result = auto_select_stocks()
    
    print(f"\n选股结果汇总：")
    print(f"  全市场股票：{result['summary']['total']}")
    print(f"  通过筛选：{result['summary']['passed_hard_bottom']}")
    print(f"  报告路径：{result['summary'].get('output_file', 'N/A')}")
    
    if result['candidates']:
        print(f"\n候选股票 TOP 10：")
        for stock in result['candidates'][:10]:
            print(f"  - {stock['ts_code']} {stock['name']} (评分：{stock.get('score', 0):.0f})")
    
    return result

def monitor_portfolio():
    """持仓监控（v1.0 兼容）"""
    print(f"\n{'='*60}")
    print(f"AI 价值投资系统 v1.0 - 持仓监控")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    from monitor.holding_monitor import generate_report, format_report
    
    report = generate_report()
    print(format_report(report, verbose=True))
    return report

def monitor_portfolio_v2():
    """持仓监控 v2.0（推送优化 + 记忆系统）"""
    print(f"\n{'='*60}")
    print(f"AI 价值投资系统 v2.0 - 持仓监控（推送优化）")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    from monitor.holding_monitor_v2 import run_monitoring_v2, format_push_message
    
    result = run_monitoring_v2(verbose=True)
    
    # 输出推送决策
    print(f"推送决策：{'推送' if result['push_decision']['should_push'] else '不推送'}")
    print(f"预警数量：{result['push_decision']['alert_count']}")
    print(f"原因：{result['push_decision']['reason']}")
    print()
    
    if result['push_decision']['should_push']:
        # 有预警，输出推送消息
        message = format_push_message(result['report'])
        print(message)
    else:
        # 无预警，输出摘要
        summary = result['report']['summary']
        print(f"✅ 持仓正常，无预警")
        print(f"总市值：¥{summary['total_market_value']:,.0f} ({summary['total_pnl_ratio']:+.2f}%)")
    
    # 保存记忆
    try:
        from utils.session_memory import get_memory
        memory = get_memory()
        memory.save_analysis(
            ts_code='portfolio',
            stock_name='持仓组合',
            conclusion={
                'status': 'normal' if not result['push_decision']['should_push'] else 'alert',
                'alert_count': result['push_decision']['alert_count'],
            },
            metadata=result['push_decision']
        )
        print(f"\n🧠 记忆已保存")
    except Exception as e:
        print(f"\n⚠️ 记忆保存失败：{e}")
    
    print(f"\n{'='*60}\n")
    return result

def weekly_review():
    """周复盘"""
    print(f"\n{'='*60}")
    print(f"AI 价值投资系统 v1.0 - 周复盘")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    from review.weekly_review import run_weekly_review
    result = run_weekly_review()
    return result

def main():
    parser = argparse.ArgumentParser(
        description='AI 价值投资系统 v1.0/v2.0 - 统一入口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py analyze 002969.SZ          # 分析嘉美包装
  python run.py analyze 002270.SZ --quick  # 快速分析（仅 20 项检查）
  python run.py select                     # 全市场选股
  python run.py monitor                    # 持仓监控（v1.0）
  python run.py monitor-v2                 # 持仓监控（v2.0 推送优化）
  python run.py review                     # 周复盘
  python run.py memory-stats               # 记忆系统统计
        """
    )
    
    parser.add_argument(
        'command',
        choices=['analyze', 'select', 'monitor', 'monitor-v2', 'review', 'memory-stats', 'summary-test', 'llm-test', 'decision-test', 'annual-test'],
        help='命令类型'
    )
    
    parser.add_argument(
        'target',
        nargs='?',
        default=None,
        help='目标（股票代码或其他）'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='快速模式（仅 20 项检查，跳过 NLP）'
    )
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        if not args.target:
            print("❌ 错误：analyze 命令需要指定股票代码")
            print("用法：python run.py analyze 002969.SZ")
            sys.exit(1)
        analyze_stock(args.target, full=not args.quick)
    
    elif args.command == 'select':
        select_stocks()
    
    elif args.command == 'monitor':
        monitor_portfolio()
    
    elif args.command == 'monitor-v2':
        monitor_portfolio_v2()
    
    elif args.command == 'review':
        weekly_review()
    
    elif args.command == 'memory-stats':
        from utils.session_memory import get_memory
        memory = get_memory()
        stats = memory.get_memory_stats()
        print(f"\n{'='*60}")
        print(f"投资系统记忆统计")
        print(f"{'='*60}")
        print(f"状态：{'已启用' if stats.get('enabled') else '未启用'}")
        if stats.get('enabled'):
            print(f"目录：{stats['memory_dir']}")
            print(f"保留期：{stats['retention_days']} 天")
            print(f"总记录数：{stats['total_entries']}")
            print(f"分类统计:")
            for mem_type, data in stats['files'].items():
                print(f"  - {mem_type}: {data['entries']} 条 ({data['files']} 个文件)")
        print(f"{'='*60}\n")
    
    elif args.command == 'summary-test':
        print(f"\n{'='*60}")
        print(f"报告摘要生成器 - 测试")
        print(f"{'='*60}\n")
        from report.summary_generator import get_summarizer
        summarizer = get_summarizer()
        
        # 测试摘要生成
        test_report = {
            'summary': {'total_market_value': 314160, 'total_pnl_ratio': -0.0012},
            'portfolio': [
                {'name': '华明装备', 'market_value': 164400},
                {'name': '电网设备 ETF', 'market_value': 149760},
            ],
            'alerts': [{'level': '🟢 机会', 'stock': '华明装备', 'message': '现价 26.37 接近补仓位 26.0'}]
        }
        summary = summarizer.summarize_portfolio(test_report)
        print(f"持仓监控摘要:\n{summary}\n")
        print(f"{'='*60}\n")
    
    elif args.command == 'llm-test':
        print(f"\n{'='*60}")
        print(f"LLM 深度分析模块 - 测试")
        print(f"{'='*60}\n")
        from analysis.llm_enhanced import get_llm_analyzer
        analyzer = get_llm_analyzer()
        
        print(f"LLM 状态：{'已启用' if analyzer.enabled else '未启用'}")
        print(f"成本限制：¥{analyzer.cost_limit}/天")
        print(f"剩余额度：¥{analyzer.get_cost_status()['remaining']:.2f}")
        print()
        
        # 测试造假风险识别（规则式）
        financial_data = {
            'receivables_to_revenue': 0.3,
            'cash_flow_to_net_profit': 0.8,
        }
        result = analyzer.detect_fraud_risk(financial_data)
        print(f"造假风险识别（规则式）:")
        for risk in result.get('rule_based_risks', []):
            print(f"  - {risk['type']}: {risk['value']} ({risk['severity']})")
        if not result.get('rule_based_risks'):
            print("  ✅ 无风险信号")
        print()
        print(f"{'='*60}\n")
    
    elif args.command == 'annual-test':
        print(f"\n{'='*60}")
        print(f"年报深度解读模块 - 测试")
        print(f"{'='*60}\n")
        from analysis.annual_report_analyzer import get_annual_analyzer
        analyzer = get_annual_analyzer()
        
        print(f"年报分析器状态：已启用")
        print()
        
        # 测试 MD&A 分析
        print("测试 1: MD&A 分析")
        sample_mda = """
        2025 年，公司实现营业收入 50 亿元，同比增长 25%。
        净利润 8 亿元，同比增长 30%。
        公司继续加大研发投入，研发费用占营收比例达到 8%。
        主要产品市场份额进一步提升，竞争优势巩固。
        
        面临挑战：原材料价格波动风险、行业竞争加剧、宏观经济不确定性
        
        展望未来，公司将继续坚持创新驱动发展战略，深耕主业。
        """
        result = analyzer.analyze_mda(sample_mda, 2025)
        print(f"  字数：{result['word_count']}")
        print(f"  摘要：{result['summary']}")
        print(f"  情感倾向：{result['rule_based']['sentiment']}")
        print()
        
        # 测试趋势分析
        print("测试 2: 跨年度趋势分析")
        historical_data = [
            {'revenue': 30, 'net_profit': 5, 'roe': 0.15, 'gross_margin': 0.40},
            {'revenue': 38, 'net_profit': 6.5, 'roe': 0.18, 'gross_margin': 0.42},
            {'revenue': 50, 'net_profit': 8, 'roe': 0.22, 'gross_margin': 0.45},
        ]
        result = analyzer.analyze_trend(historical_data)
        print(f"  分析年数：{result['years']}")
        print(f"  整体趋势：{result['overall_trend']}")
        print()
        
        # 测试完整报告
        print("测试 3: 完整报告生成")
        report = analyzer.generate_full_report(
            ts_code='002270.SZ',
            stock_name='华明装备',
            mda_text=sample_mda,
            financial_notes={},
            historical_data=historical_data
        )
        print(f"  报告长度：{len(report)} 字符")
        print(f"  报告章节：{report.count('## ')} 个")
        print()
        
        print(f"{'='*60}")
        print(f"✅ 年报深度解读模块测试完成")
        print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
