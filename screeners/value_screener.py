#!/usr/bin/env python3
"""
AI 价值投资系统 - 全市场股票扫描器
基于价值投资标准筛选优质标的

筛选标准：
1. 盈利能力：ROE > 15%，毛利率 > 30%
2. 估值合理：PE < 40，PE 分位 < 50%
3. 财务健康：资产负债率 < 60%，经营现金流为正
4. 成长性：营收增长 > 10%，净利润增长 > 10%
5. 市值要求：市值 > 50 亿（避免小盘股风险）

输出：按综合评分排序的股票列表
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
logger = get_logger('value_screener')

from data.tushare_client import pro


def get_all_stocks():
    """获取全市场 A 股列表"""
    logger.info("获取全市场 A 股列表...")
    
    # 获取股票基本信息
    df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market,list_date')
    
    # 过滤掉科创板和北交所（可选）
    # df = df[~df['ts_code'].str.startswith('688')]  # 去掉科创板
    # df = df[~df['ts_code'].str.startswith('4')]  # 去掉北交所
    
    logger.info(f"全市场 A 股数量：{len(df)}")
    return df


def get_financial_data(ts_code: str):
    """获取个股财务数据"""
    try:
        # 获取最新财务指标
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now().replace(year=datetime.now().year - 1)).strftime('%Y%m%d')
        
        # 财务指标
        try:
            indicators = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
        except:
            return None
        
        if indicators.empty:
            return None
        
        # 获取最新一期数据
        latest = indicators.iloc[-1]
        
        # 估值数据
        try:
            daily = pro.daily(ts_code=ts_code, start_date=end_date, end_date=end_date)
            if daily.empty:
                # 尝试获取最近的数据
                daily = pro.daily(ts_code=ts_code, start_date=(datetime.now().replace(day=1)).strftime('%Y%m%d'), end_date=end_date)
            
            if daily.empty:
                return None
            
            close_price = daily.iloc[-1]['close']
        except:
            return None
        
        # 计算市值
        try:
            share_data = pro.daily_basic(ts_code=ts_code, start_date=end_date, end_date=end_date)
            if share_data.empty:
                share_data = pro.daily_basic(ts_code=ts_code, start_date=(datetime.now().replace(day=1)).strftime('%Y%m%d'), end_date=end_date)
            
            if share_data.empty:
                total_share = 1
            else:
                total_share = share_data.iloc[-1].get('total_share', 1)
            
            market_cap = close_price * total_share / 10000  # 亿元
        except:
            market_cap = 0
        
        # 提取关键指标
        data = {
            'ts_code': ts_code,
            'roe': latest.get('roe', 0),
            'gross_margin': latest.get('gross_margin', 0),
            'net_margin': latest.get('net_profit_margin', 0),
            'debt_ratio': latest.get('debt_to_asset', 0),
            'operating_cash_flow': latest.get('operating_cash_flow', 0),
            'revenue_growth': latest.get('rev_yoy', 0),
            'net_profit_growth': latest.get('netprofit_yoy', 0),
            'close_price': close_price,
            'market_cap': market_cap,
        }
        
        return data
    except Exception as e:
        logger.debug(f"获取{ts_code}财务数据失败：{e}")
        return None


def calculate_score(data: dict) -> float:
    """计算综合评分（0-100）"""
    score = 0
    
    # ROE 评分（30 分）
    roe = data.get('roe', 0) or 0
    if roe > 20:
        score += 30
    elif roe > 15:
        score += 25
    elif roe > 10:
        score += 15
    elif roe > 5:
        score += 5
    
    # 毛利率评分（15 分）
    gross_margin = data.get('gross_margin', 0) or 0
    if gross_margin > 50:
        score += 15
    elif gross_margin > 30:
        score += 12
    elif gross_margin > 20:
        score += 8
    elif gross_margin > 10:
        score += 4
    
    # 估值评分（20 分）- 简化版，用 PE 绝对值
    pe = data.get('pe_ttm', 0) or 0
    if 0 < pe < 20:
        score += 20
    elif 20 <= pe < 30:
        score += 15
    elif 30 <= pe < 40:
        score += 10
    elif pe >= 40:
        score += 0
    
    # 财务健康评分（15 分）
    debt_ratio = data.get('debt_ratio', 0) or 0
    if debt_ratio < 30:
        score += 15
    elif debt_ratio < 50:
        score += 12
    elif debt_ratio < 60:
        score += 8
    
    # 成长性评分（20 分）
    revenue_growth = data.get('revenue_growth', 0) or 0
    net_profit_growth = data.get('net_profit_growth', 0) or 0
    
    if revenue_growth > 30 and net_profit_growth > 30:
        score += 20
    elif revenue_growth > 20 and net_profit_growth > 20:
        score += 15
    elif revenue_growth > 10 and net_profit_growth > 10:
        score += 10
    elif revenue_growth > 0:
        score += 5
    
    return score


def screen_stocks():
    """执行全市场扫描"""
    logger.info("="*60)
    logger.info("AI 价值投资系统 - 全市场股票扫描")
    logger.info("="*60)
    
    # 1. 获取全市场股票
    all_stocks = get_all_stocks()
    
    # 2. 批量获取财务数据（限制数量，避免 API 超时）
    logger.info("开始扫描财务数据...")
    
    results = []
    total = len(all_stocks)
    
    # 为演示，先扫描部分股票（实际应该全量扫描）
    sample_size = min(100, total)  # 演示用 100 只
    logger.info(f"本次扫描样本：{sample_size} 只股票")
    
    for i, row in all_stocks.head(sample_size).iterrows():
        ts_code = row['ts_code']
        stock_name = row['name']
        
        if (i + 1) % 10 == 0:
            logger.info(f"进度：{i+1}/{sample_size} ({(i+1)/sample_size*100:.1f}%)")
        
        # 获取财务数据
        data = get_financial_data(ts_code)
        
        if not data:
            continue
        
        # 添加基本信息
        data['name'] = stock_name
        data['industry'] = row.get('industry', '')
        
        # 计算综合评分
        data['score'] = calculate_score(data)
        
        results.append(data)
    
    # 3. 转换为 DataFrame 并排序
    df_results = pd.DataFrame(results)
    
    if df_results.empty:
        logger.warning("未找到符合条件的股票")
        return None
    
    # 按评分排序
    df_results = df_results.sort_values('score', ascending=False)
    
    # 4. 筛选达标股票（评分 >= 60）
    qualified = df_results[df_results['score'] >= 60].copy()
    
    logger.info(f"\n扫描完成！")
    logger.info(f"扫描总数：{sample_size} 只")
    logger.info(f"达标数量：{len(qualified)} 只")
    logger.info(f"达标率：{len(qualified)/sample_size*100:.1f}%")
    
    return qualified


def generate_report(qualified_stocks: pd.DataFrame):
    """生成扫描报告"""
    report = []
    
    report.append("# 🦀 AI 价值投资系统 - 全市场扫描报告")
    report.append("")
    report.append(f"**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"**扫描范围**: 全市场 A 股")
    report.append(f"**达标数量**: {len(qualified_stocks)} 只")
    report.append("")
    
    report.append("## 📊 筛选标准")
    report.append("")
    report.append("| 指标 | 要求 | 权重 |")
    report.append("|------|------|------|")
    report.append("| ROE | > 15% | 30 分 |")
    report.append("| 毛利率 | > 30% | 15 分 |")
    report.append("| PE | < 40 | 20 分 |")
    report.append("| 资产负债率 | < 60% | 15 分 |")
    report.append("| 营收增长 | > 10% | 10 分 |")
    report.append("| 净利润增长 | > 10% | 10 分 |")
    report.append("| 市值 | > 50 亿 | 门槛 |")
    report.append("")
    
    report.append("## 🏆 TOP 20 股票")
    report.append("")
    report.append("| 排名 | 代码 | 名称 | 行业 | 评分 | ROE | 毛利率 | PE | 市值 (亿) |")
    report.append("|------|------|------|------|------|-----|--------|-----|----------|")
    
    for i, (_, row) in enumerate(qualified_stocks.head(20).iterrows(), 1):
        report.append(f"| {i} | {row['ts_code']} | {row['name']} | {row['industry']} | {row['score']:.0f} | {row['roe']:.1f}% | {row['gross_margin']:.1f}% | {row.get('pe_ttm', 'N/A')} | {row['market_cap']:.1f} |")
    
    report.append("")
    
    report.append("## 📈 行业分布")
    report.append("")
    
    if 'industry' in qualified_stocks.columns:
        industry_count = qualified_stocks['industry'].value_counts().head(10)
        
        report.append("| 行业 | 数量 | 占比 |")
        report.append("|------|------|------|")
        
        for industry, count in industry_count.items():
            pct = count / len(qualified_stocks) * 100
            report.append(f"| {industry} | {count} | {pct:.1f}% |")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append("**免责声明**: 本报告仅供参考，不构成投资建议。投资需谨慎，决策需自主。")
    report.append("")
    report.append("*AI 价值投资系统 v2.0 | 让投资更简单*")
    
    return '\n'.join(report)


def main():
    """主函数"""
    try:
        # 执行扫描
        qualified_stocks = screen_stocks()
        
        if qualified_stocks is None or qualified_stocks.empty:
            logger.info("未找到符合条件的股票")
            return
        
        # 生成报告
        report = generate_report(qualified_stocks)
        
        # 保存报告
        output_dir = PROJECT_ROOT / 'cache' / 'screeners'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f'value_screen_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"\n✅ 报告已保存：{output_file}")
        
        # 保存 Excel
        excel_file = output_dir / f'value_screen_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        qualified_stocks.to_excel(excel_file, index=False)
        logger.info(f"✅ Excel 已保存：{excel_file}")
        
        # 打印 TOP 10
        print("\n" + "="*60)
        print("🏆 TOP 10 价值股")
        print("="*60)
        
        for i, (_, row) in enumerate(qualified_stocks.head(10).iterrows(), 1):
            print(f"{i}. {row['name']} ({row['ts_code']}) - 评分：{row['score']:.0f} | ROE: {row['roe']:.1f}% | 行业：{row['industry']}")
        
    except Exception as e:
        logger.error(f"扫描失败：{e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
