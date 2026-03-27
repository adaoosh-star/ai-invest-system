"""
历史全量股票池（改进点 2）
投资宪法：回测时纳入当年的全量股票，包括后续退市的股票
避免幸存者偏差导致结果虚高

修复记录：2026-03-26
- 对接 Tushare API 获取真实历史股票池
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.tushare_client import pro

def get_stocks_listed_on_date(target_date: str) -> pd.DataFrame:
    """
    改进点 2：获取某日期所有上市的股票（包括后续退市的）
    
    避免只拿当前还在上市的股票回测导致结果虚高
    
    修复：对接 Tushare stock_basic 接口
    """
    try:
        # 获取所有股票（包括已退市）
        df = pro.stock_basic(fields='ts_code,symbol,name,area,industry,list_date,delist_date')
        
        # 转换日期格式
        df['list_date'] = pd.to_datetime(df['list_date'], format='%Y%m%d', errors='coerce')
        df['delist_date'] = pd.to_datetime(df['delist_date'], format='%Y%m%d', errors='coerce')
        
        # 筛选：目标日期已上市且未退市
        target_dt = pd.to_datetime(target_date)
        listed = df[
            (df['list_date'] <= target_dt) & 
            ((df['delist_date'].isna()) | (df['delist_date'] > target_dt))
        ]
        
        return listed[['ts_code', 'symbol', 'name', 'list_date', 'delist_date']]
    except Exception as e:
        print(f"⚠️ 获取历史股票池失败：{e}")
        # 降级：返回空 DataFrame
        return pd.DataFrame(columns=['ts_code', 'symbol', 'name', 'list_date', 'delist_date'])

def get_delisted_stocks(after_date: str) -> pd.DataFrame:
    """
    改进点 2：获取某日期后退市的股票列表
    
    回测时这些股票要按实际退市收益计入（通常 -100%）
    
    修复：对接 Tushare stock_basic 接口（list_status='D'）
    """
    try:
        # 获取所有已退市股票
        df = pro.stock_basic(list_status='D', fields='ts_code,symbol,name,delist_date,delist_reason')
        
        if len(df) == 0:
            return pd.DataFrame(columns=['ts_code', 'symbol', 'name', 'delist_date', 'delist_reason'])
        
        # 转换日期格式
        df['delist_date'] = pd.to_datetime(df['delist_date'], format='%Y%m%d', errors='coerce')
        
        # 筛选：指定日期后退市
        after_dt = pd.to_datetime(after_date)
        delisted = df[df['delist_date'] > after_dt]
        
        return delisted[['ts_code', 'symbol', 'name', 'delist_date', 'delist_reason']]
    except Exception as e:
        print(f"⚠️ 获取退市股票失败：{e}")
        # 降级：返回空 DataFrame
        return pd.DataFrame(columns=['ts_code', 'symbol', 'name', 'delist_date', 'delist_reason'])

def build_historical_universe(start_date: str, end_date: str) -> Dict:
    """
    构建历史全量股票池（包含退市股）
    
    用于回测，避免幸存者偏差
    """
    # 获取起始日已上市的股票
    listed_stocks = get_stocks_listped_on_date(start_date)
    
    # 获取期间退市的股票
    delisted_stocks = get_delisted_stocks(after_date=start_date)
    
    # 合并
    all_stocks = pd.concat([listed_stocks, delisted_stocks], ignore_index=True).drop_duplicates(subset=['ts_code'])
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'listed_count': len(listed_stocks),
        'delisted_count': len(delisted_stocks),
        'total_count': len(all_stocks),
        'delisted_ratio': len(delisted_stocks) / len(all_stocks) if len(all_stocks) > 0 else 0,
        'stocks': all_stocks,
    }

def calculate_delist_return(delist_reason: str) -> float:
    """
    计算退市收益
    
    吸收合并/私有化：可能有一定收益
    强制退市：通常 -100%
    """
    if '吸收合并' in delist_reason or '私有化' in delist_reason:
        return -0.30  # 假设 -30%
    else:
        return -1.00  # 强制退市 -100%

# 测试
if __name__ == '__main__':
    print("=== 历史全量股票池测试（改进点 2）===\n")
    
    # 测试获取某日期上市股票
    print("1. 获取 2020-01-01 上市股票：")
    listed = get_stocks_listped_on_date('2020-01-01')
    print(f"   上市股票数量：{len(listed)}")
    print(f"   股票列表：{', '.join(listed['name'].tolist())}")
    print()
    
    # 测试获取退市股票
    print("2. 获取 2020-01-01 后退市股票：")
    delisted = get_delisted_stocks(after_date='2020-01-01')
    print(f"   退市股票数量：{len(delisted)}")
    print(f"   股票列表：{', '.join(delisted['name'].tolist())}")
    print()
    
    # 测试构建历史全量股票池
    print("3. 构建 2020-2023 年历史全量股票池：")
    result = build_historical_universe('2020-01-01', '2023-12-31')
    print(f"   起始日上市：{result['listed_count']}只")
    print(f"   期间退市：{result['delisted_count']}只")
    print(f"   总计：{result['total_count']}只")
    print(f"   退市占比：{result['delisted_ratio']:.1%}")
    print()
    
    # 测试退市收益计算
    print("4. 退市收益计算：")
    print(f"   吸收合并：{calculate_delist_return('吸收合并'):.0%}")
    print(f"   强制退市：{calculate_delist_return('强制退市'):.0%}")
    print()
    
    print("✅ 历史全量股票池测试完成（改进点 2：幸存者偏差规避）")
