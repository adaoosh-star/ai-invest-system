#!/usr/bin/env python3
"""
AI 价值投资系统 - 快速选股器（简化版）
使用 daily_basic 接口批量获取数据，快速筛选
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
logger = get_logger('quick_screener')
from data.tushare_client import pro

print("="*60)
print("🦀 AI 价值投资系统 - 全市场快速扫描")
print("="*60)

# 获取全市场股票
print("\n1️⃣ 获取全市场股票列表...")
stock_list = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,market')
print(f"   全市场 A 股数量：{len(stock_list)}")

# 获取最新交易日的每日基本面数据
print("\n2️⃣ 获取全市场基本面数据...")
try:
    # 获取最新交易日数据
    daily_basic = pro.daily_basic(trade_date=datetime.now().strftime('%Y%m%d'))
    
    if daily_basic.empty:
        # 如果今天没数据，获取最近一天
        from datetime import timedelta
        for i in range(1, 10):
            prev_date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            daily_basic = pro.daily_basic(trade_date=prev_date)
            if not daily_basic.empty:
                print(f"   使用日期：{prev_date}")
                break
    
    if daily_basic.empty:
        print("   ❌ 无法获取基本面数据")
        sys.exit(1)
    
    print(f"   获取成功：{len(daily_basic)} 只股票")
except Exception as e:
    print(f"   ❌ 获取失败：{e}")
    sys.exit(1)

# 合并数据
print("\n3️⃣ 数据合并与筛选...")
df = pd.merge(stock_list, daily_basic, on='ts_code', how='inner')

# 筛选标准
print("\n📋 筛选标准:")
print("   - 市值 > 50 亿")
print("   - PE(TTM) < 40 且 > 0")
print("   - PB < 5")
print("   - 股息率 > 1%")
print("   - 股价 > 5 元")

# 应用筛选
filtered = df[
    (df['total_mv'] > 50) &  # 市值>50 亿
    (df['pe_ttm'] > 0) & (df['pe_ttm'] < 40) &  # PE 0-40
    (df['pb'] < 5) &  # PB<5
    (df['dv_ratio'] > 1) &  # 股息率>1%
    (df['close'] > 5)  # 股价>5 元
].copy()

print(f"\n✅ 达标股票数量：{len(filtered)} 只")

# 计算综合评分
print("\n4️⃣ 计算综合评分...")
filtered['score'] = (
    (40 - filtered['pe_ttm']) / 40 * 40 +  # 低 PE 高分（40 分）
    (5 - filtered['pb']) / 5 * 30 +  # 低 PB 高分（30 分）
    filtered['dv_ratio'] / 5 * 15 +  # 高股息高分（15 分）
    (filtered['total_mv'] / 1000).clip(0, 1) * 15  # 大市值高分（15 分）
)

# 排序
filtered = filtered.sort_values('score', ascending=False)

# 显示 TOP 20
print("\n" + "="*60)
print("🏆 TOP 20 价值股")
print("="*60)
print(f"{'排名':<4} {'代码':<10} {'名称':<10} {'行业':<12} {'PE':<6} {'PB':<6} {'股息':<6} {'市值':<8} {'评分':<6}")
print("-"*70)

for i, (_, row) in enumerate(filtered.head(20).iterrows(), 1):
    print(f"{i:<4} {row['ts_code']:<10} {row['name']:<10} {row['industry']:<12} {row['pe_ttm']:<6.1f} {row['pb']:<6.2f} {row['dv_ratio']:<6.2f}% {row['total_mv']:<8.1f}亿 {row['score']:<6.0f}")

# 保存结果
output_dir = PROJECT_ROOT / 'cache' / 'screeners'
output_dir.mkdir(parents=True, exist_ok=True)

# 保存 CSV
csv_file = output_dir / f'quick_screen_{datetime.now().strftime("%Y%m%d")}.csv'
filtered.to_csv(csv_file, index=False, encoding='utf-8-sig')
print(f"\n✅ CSV 已保存：{csv_file}")

# 生成 Markdown 报告
report = []
report.append("# 🦀 AI 价值投资系统 - 全市场扫描报告")
report.append("")
report.append(f"**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
report.append(f"**扫描范围**: 全市场 A 股 ({len(stock_list)}只)")
report.append(f"**达标数量**: {len(filtered)} 只")
report.append(f"**达标率**: {len(filtered)/len(stock_list)*100:.1f}%")
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
report.append("")

report.append("## 🏆 TOP 20 股票")
report.append("")
report.append("| 排名 | 代码 | 名称 | 行业 | PE | PB | 股息率 | 市值 (亿) | 评分 |")
report.append("|------|------|------|------|-----|-----|--------|----------|------|")

for i, (_, row) in enumerate(filtered.head(20).iterrows(), 1):
    report.append(f"| {i} | {row['ts_code']} | {row['name']} | {row['industry']} | {row['pe_ttm']:.1f} | {row['pb']:.2f} | {row['dv_ratio']:.2f}% | {row['total_mv']:.1f} | {row['score']:.0f} |")

report.append("")
report.append("## 📊 行业分布")
report.append("")

industry_dist = filtered['industry'].value_counts().head(10)
report.append("| 行业 | 数量 | 占比 |")
report.append("|------|------|------|")

for industry, count in industry_dist.items():
    pct = count / len(filtered) * 100
    report.append(f"| {industry} | {count} | {pct:.1f}% |")

report.append("")
report.append("---")
report.append("")
report.append("**免责声明**: 本报告仅供参考，不构成投资建议。")
report.append("")
report.append("*AI 价值投资系统 v1.0*")

md_file = output_dir / f'quick_screen_{datetime.now().strftime("%Y%m%d")}.md'
with open(md_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print(f"✅ 报告已保存：{md_file}")

print("\n" + "="*60)
print("✅ 扫描完成！")
print("="*60)
