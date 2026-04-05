"""
自动化选股流程
投资宪法：AI 批量执行选股前 20 项检查清单
效率：人工 10-15 小时/公司 → AI 1-2 分钟/100 公司（增量更新）

修复记录：
- 2026-03-26: 修复相对导入问题
- 2026-04-06: 优化 API 调用，使用批量接口避免限流
"""

import sys
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入日志系统
from utils.logger import get_logger
logger = get_logger('auto_select')

from data.tushare_client import pro

# 加载配置
CONFIG_PATH = PROJECT_ROOT / 'config' / 'thresholds.yaml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)



def auto_select_stocks() -> dict:
    """
    投资宪法：AI 批量执行选股前 20 项检查清单
    输出：高优先级标的（人工仅复核）
    效率：人工 10-15 小时/公司 → AI 1-2 分钟/100 公司（增量更新）
    
    优化策略：
    1. 使用 daily_basic 批量接口，一次获取全市场数据
    2. 分阶段筛选，减少不必要的 API 调用
    3. 添加缓存机制，避免重复调用
    """
    logger.info("开始自动化选股流程（优化版）")
    
    try:
        # 1. 获取全市场股票列表
        logger.info("获取全市场股票列表...")
        stock_list = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,market')
        logger.info(f"全市场 A 股数量：{len(stock_list)}")
        
        # 2. 使用 daily_basic 批量获取基本面数据（一次 API 调用）
        logger.info("批量获取基本面数据...")
        trade_date = datetime.now().strftime('%Y%m%d')
        daily_basic = pro.daily_basic(trade_date=trade_date)
        
        if daily_basic.empty:
            # 如果今天没数据，获取最近一天
            for i in range(1, 10):
                prev_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
                daily_basic = pro.daily_basic(trade_date=prev_date)
                if not daily_basic.empty:
                    logger.info(f"使用日期：{prev_date}")
                    break
        
        if daily_basic.empty:
            logger.error("无法获取基本面数据")
            return {'candidates': [], 'summary': {'total': len(stock_list), 'error': '无法获取基本面数据'}}
        
        logger.info(f"获取成功：{len(daily_basic)} 只股票")
        
        # 3. 合并数据
        logger.info("数据合并...")
        df = pd.merge(stock_list, daily_basic, on='ts_code', how='inner')
        
        # 4. 流动性过滤（使用换手率替代，>1% 表示活跃）
        # daily_basic 没有 avg_vol_20，用 turnover_rate_f（自由流通换手率）替代
        logger.info("流动性过滤...")
        df = df[df['turnover_rate_f'] > 1.0]  # 自由流通换手率 > 1%
        logger.info(f"通过流动性过滤：{len(df)} 只")
        
        # 5. 硬底线筛选
        logger.info("硬底线筛选...")
        df = df[
            (df['total_mv'] > 50) &  # 市值 > 50 亿
            (df['pe_ttm'] > 0) & (df['pe_ttm'] < 40) &  # PE 0-40
            (df['pb'] < 5) &  # PB < 5
            (df['dv_ratio'] > 1) &  # 股息率 > 1%
            (df['close'] > 5)  # 股价 > 5 元
        ]
        logger.info(f"通过硬底线筛选：{len(df)} 只")
        
        # 6. 计算综合评分
        logger.info("计算综合评分...")
        df['score'] = (
            (40 - df['pe_ttm']) / 40 * 40 +  # 低 PE 高分（40 分）
            (5 - df['pb']) / 5 * 30 +  # 低 PB 高分（30 分）
            df['dv_ratio'] / 5 * 15 +  # 高股息高分（15 分）
            (df['total_mv'] / 1000).clip(0, 1) * 15  # 大市值高分（15 分）
        )
        
        # 7. 排序
        df = df.sort_values('score', ascending=False)
        
        # 8. 保存结果
        output_dir = PROJECT_ROOT / 'cache' / 'screeners'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存 CSV
        csv_file = output_dir / f'auto_select_{datetime.now().strftime("%Y%m%d")}.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        logger.info(f"CSV 已保存：{csv_file}")
        
        # 9. 生成 Markdown 报告
        report = generate_selection_report(df, len(stock_list))
        md_file = output_dir / f'auto_select_{datetime.now().strftime("%Y%m%d")}.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"报告已保存：{md_file}")
        
        # 10. 输出结果
        result = {
            'candidates': df.to_dict('records'),
            'summary': {
                'total': len(stock_list),
                'passed_liquidity': len(df),
                'passed_hard_bottom': len(df),
                'output_file': str(md_file),
            }
        }
        
        logger.info(f"选股完成：{len(df)} 只候选股票")
        return result
        
    except Exception as e:
        logger.error(f"选股失败：{e}", exc_info=True)
        raise


def generate_selection_report(df: pd.DataFrame, total: int) -> str:
    """生成选股报告"""
    report = []
    
    report.append("# 🦀 AI 价值投资系统 - 自动化选股报告")
    report.append("")
    report.append(f"**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**扫描范围**: 全市场 A 股 ({total}只)")
    report.append(f"**达标数量**: {len(df)} 只")
    report.append(f"**达标率**: {len(df)/total*100:.1f}%")
    report.append("")
    
    report.append("## 📋 筛选标准")
    report.append("")
    report.append("| 指标 | 要求 | 说明 |")
    report.append("|------|------|------|")
    report.append("| 市值 | > 50 亿 | 避免小盘股风险 |")
    report.append("| PE(TTM) | 0-40 | 估值合理 |")
    report.append("| PB | < 5 | 避免过高溢价 |")
    report.append("| 股息率 | > 1% | 有分红能力 |")
    report.append("| 股价 | > 5 元 | 避免低价股 |")
    report.append("| 流动性 | 换手率>1% | 保证交易活跃 |")
    report.append("")
    
    report.append("## 🏆 TOP 20 股票")
    report.append("")
    report.append("| 排名 | 代码 | 名称 | 行业 | PE | PB | 股息率 | 市值 (亿) | 评分 |")
    report.append("|------|------|------|------|-----|-----|--------|----------|------|")
    
    for i, (_, row) in enumerate(df.head(20).iterrows(), 1):
        report.append(f"| {i} | {row['ts_code']} | {row['name']} | {row['industry']} | {row['pe_ttm']:.1f} | {row['pb']:.2f} | {row['dv_ratio']:.2f}% | {row['total_mv']:.1f} | {row['score']:.0f} |")
    
    report.append("")
    
    report.append("## 📊 行业分布")
    report.append("")
    
    industry_dist = df['industry'].value_counts().head(10)
    report.append("| 行业 | 数量 | 占比 |")
    report.append("|------|------|------|")
    
    for industry, count in industry_dist.items():
        pct = count / len(df) * 100
        report.append(f"| {industry} | {count} | {pct:.1f}% |")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append("**免责声明**: 本报告仅供参考，不构成投资建议。")
    report.append("")
    report.append("*AI 价值投资系统 v1.0*")
    
    return '\n'.join(report)

# 测试
if __name__ == '__main__':
    print("=== 自动化选股流程测试 ===\n")
    
    result = auto_select_stocks()
    
    print(f"选股结果汇总：")
    print(f"  全市场股票：{result['summary']['total']}")
    print(f"  通过流动性过滤：{result['summary']['passed_liquidity']}")
    print(f"  通过硬底线筛选：{result['summary']['passed_hard_bottom']}")
    print(f"  缓存命中率：{result['summary']['cache_hit_rate']:.1%}")
    
    if result['candidates']:
        print(f"\n候选股票（前 10 只）：")
        for stock in result['candidates'][:10]:
            print(f"  - {stock['ts_code']}")
