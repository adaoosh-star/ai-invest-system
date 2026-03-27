"""
研发费用获取测试
"""
import tushare as ts
from pathlib import Path

TOKEN_PATH = Path.home() / '.tushare_token'
with open(TOKEN_PATH, 'r') as f:
    token = f.read().strip()

pro = ts.pro_api(token)

ts_code = '002270.SZ'

print("获取研发费用...")

# 尝试 income 接口
df = pro.income(ts_code=ts_code, start_date='20240101', end_date='20251231')
print(f"income 接口字段：{len(df.columns)}个")

if 'rd_exp' in df.columns:
    print(f"✅ 找到 rd_exp")
    rd_data = df[['end_date', 'rd_exp']].sort_values('end_date', ascending=False)
    print(rd_data.head(5).to_string())
    
    # 获取营收
    rev_df = pro.income(ts_code=ts_code, start_date='20240101', end_date='20251231')
    if 'total_revenue' in rev_df.columns:
        rev_data = rev_df[['end_date', 'total_revenue']].sort_values('end_date', ascending=False)
        print(f"\n营收数据:")
        print(rev_data.head(5).to_string())
        
        # 计算比率
        if len(rd_data) > 0 and len(rev_data) > 0:
            latest_rd = rd_data.iloc[0]['rd_exp']
            latest_rev = rev_data.iloc[0]['total_revenue']
            if latest_rev > 0:
                ratio = latest_rd / latest_rev
                print(f"\n研发费用/营收 = {ratio:.1%}")
