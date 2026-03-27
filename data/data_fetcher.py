"""
统一数据获取层
- 整合所有 Tushare 数据获取函数
- 统一返回值格式
- 提供股票/ETF 自动识别
- 缓存机制提高效率
- 交易时间使用多数据源实时价格

所有模块应该使用本模块的函数，不要直接调用 pro.xxx

修复记录：
- 2026-03-26 11:50: 交易时间优先使用腾讯财经实时接口
- 2026-03-26 12:00: 集成 realtime_fetcher 多数据源模块
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from tushare_client import pro
from realtime_fetcher import fetch_realtime_price


class DataFetcher:
    """统一数据获取器"""
    
    # 缓存目录
    CACHE_DIR = Path(__file__).parent.parent / 'cache' / 'data_cache'
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def __init__(self):
        self.pro = pro
    
    def _is_trading_time(self):
        """判断是否在交易时间内（包括午休）"""
        now = datetime.now()
        time_val = now.hour * 100 + now.minute
        weekday = now.weekday()
        
        # 周末非交易日
        if weekday >= 5:
            return False
        
        # 交易时间：9:30-11:30, 13:00-15:00
        # 午休：11:30-13:00（也能获取实时价格）
        if 930 <= time_val <= 1500:
            return True
        
        return False
    
    def _is_etf(self, ts_code: str) -> bool:
        """判断是否为 ETF/基金"""
        return ts_code.startswith('15') or ts_code.startswith('51') or ts_code.startswith('16')
    
    def _get_cache_key(self, func_name: str, ts_code: str, **kwargs) -> str:
        """生成缓存键"""
        key = f"{func_name}_{ts_code}"
        for k, v in sorted(kwargs.items()):
            key += f"_{k}_{v}"
        return key
    
    def _load_cache(self, key: str, max_age_hours: int = 24) -> dict:
        """加载缓存"""
        cache_file = self.CACHE_DIR / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 检查缓存是否过期
                    cache_time = datetime.fromisoformat(data.get('_cache_time', ''))
                    if (datetime.now() - cache_time).total_seconds() < max_age_hours * 3600:
                        return data
            except:
                pass
        return None
    
    def _save_cache(self, key: str, data: dict):
        """保存缓存"""
        cache_file = self.CACHE_DIR / f"{key}.json"
        data['_cache_time'] = datetime.now().isoformat()
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    
    def get_daily_data(self, ts_code: str, start_date: str = None, end_date: str = None, days: int = 30):
        """
        获取日线数据（股票/ETF 自动识别）
        
        参数：
        - ts_code: 股票代码
        - start_date: 开始日期（可选，与 days 二选一）
        - end_date: 结束日期（可选）
        - days: 获取天数（默认 30 天）
        
        返回：DataFrame
        
        修复记录：2026-03-26
        - 交易时间使用 realtime_fetcher 多数据源获取实时价格
        """
        import pandas as pd
        
        # 交易时间使用实时价格模块（多数据源冗余）
        if self._is_trading_time():
            realtime_data = fetch_realtime_price(ts_code, use_cache=True)
            if realtime_data:
                # 创建今日数据行
                today_row = {
                    'ts_code': ts_code,
                    'trade_date': datetime.now().strftime('%Y%m%d'),
                    'close': realtime_data['price'],
                    'open': realtime_data['open'],
                    'high': realtime_data['high'],
                    'low': realtime_data['low'],
                    'pre_close': realtime_data['prev_close'],
                    'vol': realtime_data['volume'] / 100,  # 手
                    'amount': realtime_data['amount'] / 1000,  # 千元
                }
                
                # 获取历史数据（用于计算均线等）
                if not start_date:
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                
                try:
                    if self._is_etf(ts_code):
                        hist_df = self.pro.fund_daily(ts_code=ts_code, start_date=start_date, 
                                                      end_date=(datetime.now() - timedelta(days=1)).strftime('%Y%m%d'))
                    else:
                        hist_df = self.pro.daily(ts_code=ts_code, start_date=start_date,
                                                 end_date=(datetime.now() - timedelta(days=1)).strftime('%Y%m%d'))
                    
                    if not hist_df.empty:
                        # 合并今日数据
                        today_df = pd.DataFrame([today_row])
                        df = pd.concat([hist_df, today_df], ignore_index=True)
                        df = df.sort_values('trade_date')
                        return df
                    else:
                        return pd.DataFrame([today_row])
                except Exception as e:
                    print(f"获取历史数据失败 {ts_code}: {e}")
                    return pd.DataFrame([today_row])
        
        # 非交易时间使用 Tushare（盘后数据已更新）
        # 日期处理
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        # 缓存键
        cache_key = self._get_cache_key('daily', ts_code, start=start_date, end=end_date)
        cached = self._load_cache(cache_key)
        if cached and 'data' in cached:
            return pd.DataFrame(cached['data'])
        
        # 获取数据
        try:
            if self._is_etf(ts_code):
                df = self.pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            else:
                df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if not df.empty:
                df = df.sort_values('trade_date')
                # 缓存
                self._save_cache(cache_key, {'data': df.to_dict('records')})
            
            return df
        except Exception as e:
            print(f"获取日线数据失败 {ts_code}: {e}")
            return pd.DataFrame()
    
    def get_price_change(self, ts_code: str, days: int = 30):
        """
        获取价格变化（指定天数）
        
        参数：
        - ts_code: 股票代码
        - days: 天数（默认 30 天=月度）
        
        返回：dict
        {
            'start_price': 期初价格,
            'end_price': 期末价格,
            'change_pct': 涨跌幅（%）,
            'high': 期间最高,
            'low': 期间最低,
        }
        """
        df = self.get_daily_data(ts_code, days=days)
        
        if df.empty:
            return None
        
        start_price = float(df.iloc[0]['close'])
        end_price = float(df.iloc[-1]['close'])
        change_pct = (end_price - start_price) / start_price * 100
        
        return {
            'start_price': start_price,
            'end_price': end_price,
            'change_pct': change_pct,
            'high': float(df['high'].max()),
            'low': float(df['low'].min()),
            'avg_vol': float(df['vol'].mean()) / 10000,  # 万股
        }
    
    def get_valuation(self, ts_code: str):
        """
        获取估值数据（PE/PB 分位）
        
        参数：
        - ts_code: 股票代码
        
        返回：dict
        {
            'pe_ttm': PE TTM,
            'pe_percentile': PE 分位（5 年优先，否则 10 年）,
            'pb': PB,
            'pb_percentile': PB 分位（5 年优先，否则 10 年）,
        }
        """
        # 缓存键
        cache_key = self._get_cache_key('valuation', ts_code)
        cached = self._load_cache(cache_key, max_age_hours=6)  # 估值数据 6 小时更新
        if cached:
            return cached
        
        try:
            # 获取 daily_basic 数据
            df = self.pro.daily_basic(ts_code=ts_code, start_date='20160101')
            
            if df.empty:
                return None
            
            # 计算 PE/PB 分位
            pe_data = df['pe_ttm'].dropna()
            pb_data = df['pb'].dropna()
            
            if len(pe_data) == 0 or len(pb_data) == 0:
                return None
            
            current_pe = float(df.iloc[0]['pe_ttm'])
            current_pb = float(df.iloc[0]['pb'])
            
            # 5 年分位（约 1250 个交易日）
            pe_data_5y = pe_data.tail(1250)
            pb_data_5y = pb_data.tail(1250)
            
            pe_percentile_5y = (pe_data_5y < current_pe).sum() / len(pe_data_5y) if len(pe_data_5y) > 0 else None
            pb_percentile_5y = (pb_data_5y < current_pb).sum() / len(pb_data_5y) if len(pb_data_5y) > 0 else None
            
            # 10 年分位（全部数据）
            pe_percentile_10y = (pe_data < current_pe).sum() / len(pe_data) if len(pe_data) > 0 else None
            pb_percentile_10y = (pb_data < current_pb).sum() / len(pb_data) if len(pb_data) > 0 else None
            
            # 优先使用 5 年分位
            pe_percentile = pe_percentile_5y if pe_percentile_5y is not None else pe_percentile_10y
            pb_percentile = pb_percentile_5y if pb_percentile_5y is not None else pb_percentile_10y
            
            result = {
                'pe_ttm': current_pe,
                'pe_percentile': pe_percentile,
                'pb': current_pb,
                'pb_percentile': pb_percentile,
            }
            
            # 缓存
            self._save_cache(cache_key, result)
            
            return result
        except Exception as e:
            print(f"获取估值数据失败 {ts_code}: {e}")
            return None
    
    def get_roe(self, ts_code: str, years: int = 5):
        """
        获取 ROE 数据
        
        参数：
        - ts_code: 股票代码
        - years: 年数（默认 5 年）
        
        返回：DataFrame
        """
        try:
            # 获取财务指标
            df = self.pro.fina_indicator(ts_code=ts_code)
            
            if df.empty:
                import pandas as pd
                return pd.DataFrame()
            
            # 按报告期排序
            df = df.sort_values('ann_date', ascending=False)
            
            # 取最近 N 年数据（年报）
            df = df[df['end_type'] == '1231'].head(years)
            
            return df
        except Exception as e:
            print(f"获取 ROE 数据失败 {ts_code}: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def get_stock_name(self, ts_code: str) -> str:
        """
        获取股票名称
        
        参数：
        - ts_code: 股票代码
        
        返回：股票名称
        """
        try:
            df = self.pro.stock_basic(ts_code=ts_code)
            if not df.empty:
                return df.iloc[0]['name']
        except:
            pass
        return ts_code
    
    def get_holdings_list(self, holdings_file: str = None):
        """
        加载持仓配置
        
        参数：
        - holdings_file: 持仓配置文件路径
        
        返回：list of dict
        """
        import yaml
        
        if not holdings_file:
            holdings_file = Path(__file__).parent.parent / 'config' / 'holdings.yaml'
        
        try:
            with open(holdings_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
                # 兼容两种格式
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    if 'holdings' in data:
                        return data['holdings']
                    if 'stocks' in data:
                        return data['stocks']
        except Exception as e:
            print(f"加载持仓配置失败：{e}")
        
        return []


# 全局实例
fetcher = DataFetcher()


# ========== 便捷函数（供其他模块直接调用） ==========

def get_daily_data(ts_code: str, **kwargs):
    """获取日线数据"""
    return fetcher.get_daily_data(ts_code, **kwargs)

def get_price_change(ts_code: str, days: int = 30):
    """获取价格变化"""
    return fetcher.get_price_change(ts_code, days=days)

def get_valuation(ts_code: str):
    """获取估值数据"""
    return fetcher.get_valuation(ts_code)

def get_roe(ts_code: str, **kwargs):
    """获取 ROE 数据"""
    return fetcher.get_roe(ts_code, **kwargs)

def get_stock_name(ts_code: str):
    """获取股票名称"""
    return fetcher.get_stock_name(ts_code)

def get_holdings_list(**kwargs):
    """加载持仓配置"""
    return fetcher.get_holdings_list(**kwargs)
