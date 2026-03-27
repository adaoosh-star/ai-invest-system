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
    print(f"  通过流动性过滤：{result['summary']['passed_liquidity']}")
    print(f"  通过硬底线筛选：{result['summary']['passed_hard_bottom']}")
    print(f"  缓存命中率：{result['summary']['cache_hit_rate']:.1%}")
    
    if result['candidates']:
        print(f"\n候选股票（前 10 只）：")
        for stock in result['candidates'][:10]:
            print(f"  - {stock['ts_code']}")
    
    return result

def monitor_portfolio():
    """持仓监控"""
    print(f"\n{'='*60}")
    print(f"AI 价值投资系统 v1.0 - 持仓监控")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # TODO: 实现持仓监控
    print("⚠️ 持仓监控功能开发中...")
    return None

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
        description='AI 价值投资系统 v1.0 - 统一入口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py analyze 002969.SZ          # 分析嘉美包装
  python run.py analyze 002270.SZ --quick  # 快速分析（仅 20 项检查）
  python run.py select                     # 全市场选股
  python run.py monitor                    # 持仓监控
  python run.py review                     # 周复盘
        """
    )
    
    parser.add_argument(
        'command',
        choices=['analyze', 'select', 'monitor', 'review'],
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
    
    elif args.command == 'review':
        weekly_review()

if __name__ == '__main__':
    main()
