"""
数据清洗规则
投资宪法：统一财务口径，排除异常值
"""

import pandas as pd
import numpy as np

def exclude_one_time_income(df: pd.DataFrame) -> pd.DataFrame:
    """
    排除一次性收益（资产处置、政府补助等）
    投资宪法：如果非经常性损益/净利润 > 20%，标记为异常
    """
    if 'non_recurring_profit' in df.columns and 'net_profit' in df.columns:
        df['one_time_ratio'] = df['non_recurring_profit'] / df['net_profit'].abs()
        df['is_abnormal'] = df['one_time_ratio'] > 0.2
    return df

def exclude_roe_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    排除 ROE 异常值（>100% 或 <-50%）
    投资宪法：ROE 异常值排除
    """
    if 'roe_dt' in df.columns:
        df['is_roe_abnormal'] = (df['roe_dt'] > 1.0) | (df['roe_dt'] < -0.5)
    return df

def exclude_margin_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    排除毛利率异常值（>100% 或 <0%）
    """
    if 'gross_margin' in df.columns:
        df['is_margin_abnormal'] = (df['gross_margin'] > 1.0) | (df['gross_margin'] < 0)
    return df

def forward_fill_missing(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    缺失值处理：前向填充
    投资宪法：数据完整性保证
    """
    df[columns] = df[columns].fillna(method='ffill')
    return df

def validate_data_quality(df: pd.DataFrame, ts_code: str) -> dict:
    """
    数据质量验证
    返回：错误率、异常标记
    """
    issues = []
    error_count = 0
    total_records = len(df)
    
    # ROE 异常
    if 'is_roe_abnormal' in df.columns:
        roe_abnormal = df['is_roe_abnormal'].sum()
        if roe_abnormal > 0:
            issues.append(f"ROE 异常 {roe_abnormal} 条")
            error_count += roe_abnormal
    
    # 毛利率异常
    if 'is_margin_abnormal' in df.columns:
        margin_abnormal = df['is_margin_abnormal'].sum()
        if margin_abnormal > 0:
            issues.append(f"毛利率异常 {margin_abnormal} 条")
            error_count += margin_abnormal
    
    # 一次性收益过高
    if 'is_abnormal' in df.columns:
        one_time_abnormal = df['is_abnormal'].sum()
        if one_time_abnormal > 0:
            issues.append(f"一次性收益过高 {one_time_abnormal} 条")
            error_count += one_time_abnormal
    
    error_rate = error_count / total_records if total_records > 0 else 0
    
    return {
        'ts_code': ts_code,
        'total_records': total_records,
        'error_count': error_count,
        'error_rate': error_rate,
        'issues': issues,
        'is_valid': error_rate < 0.01,  # 错误率<1% 为有效
    }

# 测试
if __name__ == '__main__':
    # 模拟数据测试
    df = pd.DataFrame({
        'roe_dt': [0.15, 0.18, 1.5, 0.20, 0.22],  # 第 3 条异常
        'gross_margin': [0.45, 0.48, 0.50, 1.2, 0.52],  # 第 4 条异常
        'non_recurring_profit': [0.1, 0.2, 0.1, 0.1, 5.0],  # 第 5 条异常
        'net_profit': [1.0, 1.2, 1.1, 1.3, 1.0],
    })
    
    df = exclude_one_time_income(df)
    df = exclude_roe_outliers(df)
    df = exclude_margin_outliers(df)
    
    result = validate_data_quality(df, '002270.SZ')
    
    print(f"数据质量验证结果：{result}")
