"""
实时价格获取模块 - 多数据源冗余设计

设计原则：
1. 盘中必须用实时价格（Tushare 只有盘后数据）
2. 多数据源冗余，主数据源失败自动降级
3. 数据源健康检查，动态选择最优源
4. 统一接口，调用方无需关心数据源

数据源优先级：
1. 腾讯财经 (qt.gtimg.cn) - 最稳定，A 股/ETF 全覆盖
2. 东方财富 (push2his.eastmoney.com) - 备用，数据丰富
3. 新浪财经 (hq.sinajs.cn) - 备用，有时被限
4. AKShare - 最后备用，依赖第三方

修复记录：2026-03-26
- 初始版本：多数据源实时价格获取
"""

import requests
import time
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

# 数据源配置
DATA_SOURCES = [
    {
        'name': 'qq',
        'url_template': 'http://qt.gtimg.cn/q={market}{code}',
        'timeout': 3,
        'priority': 1,
        'parser': '_parse_qq'
    },
    {
        'name': 'eastmoney',
        'url_template': 'https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60',
        'timeout': 5,
        'priority': 2,
        'parser': '_parse_em'
    },
    {
        'name': 'sina',
        'url_template': 'https://hq.sinajs.cn/list={market}{code}',
        'timeout': 5,
        'priority': 3,
        'parser': '_parse_sina'
    }
]

# 数据源健康状态（运行时动态更新）
SOURCE_HEALTH = {src['name']: {'healthy': True, 'last_fail': None, 'fail_count': 0} for src in DATA_SOURCES}


class RealtimePriceFetcher:
    """实时价格获取器 - 多数据源冗余"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._cache = {}  # 简单缓存，避免短时间内重复请求
        self._cache_ttl = 10  # 缓存 10 秒
    
    def _convert_code(self, ts_code: str) -> Dict[str, str]:
        """
        转换股票代码格式
        
        输入：002270.SZ, 159326.SZ, 600519.SH
        输出：{'market': 'sz/sh', 'code': '002270/159326/600519'}
        """
        parts = ts_code.split('.')
        if len(parts) != 2:
            raise ValueError(f"无效的代码格式：{ts_code}")
        
        code, exchange = parts
        exchange = exchange.lower()
        
        # 市场代码映射
        market_map = {
            'sz': 'sz',  # 深交所
            'sh': 'sh',  # 上交所
        }
        
        market = market_map.get(exchange)
        if not market:
            raise ValueError(f"不支持的交易所：{exchange}")
        
        return {'market': market, 'code': code}
    
    def _parse_qq(self, text: str, ts_code: str) -> Optional[Dict]:
        """解析腾讯财经数据"""
        try:
            # 格式：v_sz002270="51~名称~代码~当前价~收盘价~...
            if '=' not in text or '"' not in text:
                return None
            
            data_str = text.split('=')[1].strip('"')
            p = data_str.split('~')
            
            if len(p) < 5:
                return None
            
            # 字段映射（腾讯财经）
            # [3]=当前价，[4]=昨收，[5]=开盘，[33]=最高，[34]=最低，[6]=成交量
            price = float(p[3]) if p[3] else 0
            if price <= 0:
                return None
            
            # 腾讯时间格式：20260326115233 (YYYYMMDDHHMMSS) - 字段 [30]
            time_str = p[30] if len(p) > 30 and p[30] else datetime.now().strftime('%Y%m%d%H%M%S')
            if len(time_str) >= 14:
                time_display = f"{time_str[:8]} {time_str[8:10]}:{time_str[10:12]}:{time_str[12:14]}"
            elif len(time_str) >= 12:
                time_display = f"{time_str[:8]} {time_str[8:10]}:{time_str[10:12]}"
            elif len(time_str) >= 8:
                time_display = time_str[:8]
            else:
                time_display = time_str
            
            return {
                'price': price,
                'prev_close': float(p[4]) if len(p) > 4 and p[4] else price,
                'open': float(p[5]) if len(p) > 5 and p[5] else price,
                'high': float(p[33]) if len(p) > 33 and p[33] else price,
                'low': float(p[34]) if len(p) > 34 and p[34] else price,
                'volume': int(float(p[6])) if len(p) > 6 and p[6] else 0,
                'amount': float(p[37]) if len(p) > 37 and p[37] else 0,
                'change_pct': float(p[32]) if len(p) > 32 and p[32] else 0,
                'time_display': time_display,
                'time_raw': time_str,
                'source': 'qq'
            }
        except Exception as e:
            print(f"解析腾讯数据失败：{e}")
            return None
    
    def _parse_em(self, text: str, ts_code: str) -> Optional[Dict]:
        """解析东方财富数据"""
        try:
            data = text.get('data', {})
            if not data:
                return None
            
            price = data.get('f43', 0)  # 当前价
            if price <= 0:
                return None
            
            return {
                'price': price,
                'prev_close': data.get('f60', price),  # 昨收
                'open': data.get('f46', price),  # 开盘
                'high': data.get('f44', price),  # 最高
                'low': data.get('f45', price),  # 最低
                'volume': data.get('f47', 0),  # 成交量
                'amount': data.get('f48', 0),  # 成交额
                'change_pct': data.get('f49', 0),  # 涨跌幅
                'time': datetime.now().strftime('%Y%m%d%H%M%S'),
                'source': 'eastmoney'
            }
        except Exception as e:
            print(f"解析东财数据失败：{e}")
            return None
    
    def _parse_sina(self, text: str, ts_code: str) -> Optional[Dict]:
        """解析新浪财经数据"""
        try:
            if '"' not in text:
                return None
            
            data_str = text[text.index('"')+1 : text.rindex('"')]
            p = data_str.split(',')
            
            if len(p) < 4:
                return None
            
            price = float(p[3]) if p[3] else 0
            if price <= 0:
                return None
            
            return {
                'price': price,
                'prev_close': float(p[2]) if len(p) > 2 and p[2] else price,
                'open': float(p[1]) if len(p) > 1 and p[1] else price,
                'high': float(p[4]) if len(p) > 4 and p[4] else price,
                'low': float(p[5]) if len(p) > 5 and p[5] else price,
                'volume': int(float(p[8])) if len(p) > 8 and p[8] else 0,
                'amount': float(p[9]) if len(p) > 9 and p[9] else 0,
                'change_pct': float(p[32]) if len(p) > 32 and p[32] else 0,
                'date': p[30] if len(p) > 30 else '',
                'time': p[31] if len(p) > 31 else '',
                'source': 'sina'
            }
        except Exception as e:
            print(f"解析新浪数据失败：{e}")
            return None
    
    def _fetch_from_source(self, source: Dict, market: str, code: str, ts_code: str) -> Optional[Dict]:
        """从指定数据源获取数据"""
        try:
            url = source['url_template'].format(market=market, code=code)
            resp = self.session.get(url, timeout=source['timeout'])
            
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}")
            
            text = resp.text
            
            # 检查数据有效性
            if not text or 'Forbidden' in text or 'error' in text.lower():
                raise Exception("数据无效")
            
            # 调用对应的解析器
            parser = getattr(self, source['parser'])
            result = parser(text, ts_code)
            
            if result and result.get('price', 0) > 0:
                return result
            else:
                raise Exception("解析失败或价格为 0")
                
        except Exception as e:
            # 更新健康状态
            SOURCE_HEALTH[source['name']]['healthy'] = False
            SOURCE_HEALTH[source['name']]['last_fail'] = datetime.now()
            SOURCE_HEALTH[source['name']]['fail_count'] += 1
            print(f"数据源 {source['name']} 失败：{e}")
            return None
    
    def _is_cache_valid(self, ts_code: str) -> bool:
        """检查缓存是否有效"""
        if ts_code not in self._cache:
            return False
        
        cache_time, _ = self._cache[ts_code]
        return (time.time() - cache_time) < self._cache_ttl
    
    def fetch(self, ts_code: str, use_cache: bool = True) -> Optional[Dict]:
        """
        获取实时价格（多数据源自动降级）
        
        参数：
        - ts_code: 股票代码 (如：002270.SZ)
        - use_cache: 是否使用缓存（默认 True）
        
        返回：
        {
            'price': float,       # 当前价
            'prev_close': float,  # 昨收
            'open': float,        # 开盘
            'high': float,        # 最高
            'low': float,         # 最低
            'volume': int,        # 成交量
            'amount': float,      # 成交额
            'change_pct': float,  # 涨跌幅
            'time': str,          # 时间戳
            'source': str         # 数据来源
        }
        """
        # 检查缓存
        if use_cache and self._is_cache_valid(ts_code):
            return self._cache[ts_code][1]
        
        # 转换代码格式
        try:
            code_info = self._convert_code(ts_code)
        except Exception as e:
            print(f"代码转换失败 {ts_code}: {e}")
            return None
        
        market = code_info['market']
        code = code_info['code']
        
        # 按优先级尝试各数据源
        # 优先使用健康的数据源
        sorted_sources = sorted(
            DATA_SOURCES,
            key=lambda s: (
                0 if SOURCE_HEALTH[s['name']]['healthy'] else 1,  # 健康的优先
                s['priority']  # 同健康度按优先级
            )
        )
        
        for source in sorted_sources:
            result = self._fetch_from_source(source, market, code, ts_code)
            
            if result:
                # 成功获取，更新健康状态
                SOURCE_HEALTH[source['name']]['healthy'] = True
                SOURCE_HEALTH[source['name']]['fail_count'] = 0
                
                # 更新缓存
                self._cache[ts_code] = (time.time(), result)
                
                # 静默成功，不输出（避免 cron 推送时噪音）
                pass
                return result
        
        # 所有数据源都失败
        print(f"❌ {ts_code} 所有数据源都失败")
        return None
    
    def fetch_batch(self, ts_codes: List[str], use_cache: bool = True) -> Dict[str, Dict]:
        """
        批量获取实时价格
        
        参数：
        - ts_codes: 股票代码列表
        - use_cache: 是否使用缓存
        
        返回：
        {ts_code: price_data, ...}
        """
        results = {}
        for ts_code in ts_codes:
            result = self.fetch(ts_code, use_cache)
            if result:
                results[ts_code] = result
        return results
    
    def get_source_health(self) -> Dict:
        """获取数据源健康状态"""
        return SOURCE_HEALTH.copy()
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()


# 全局单例
_realtime_fetcher = None

def get_realtime_fetcher() -> RealtimePriceFetcher:
    """获取实时价格获取器单例"""
    global _realtime_fetcher
    if _realtime_fetcher is None:
        _realtime_fetcher = RealtimePriceFetcher()
    return _realtime_fetcher


# ========== 便捷函数 ==========

def fetch_realtime_price(ts_code: str, use_cache: bool = True) -> Optional[Dict]:
    """获取实时价格（便捷函数）"""
    return get_realtime_fetcher().fetch(ts_code, use_cache)

def fetch_batch_realtime(ts_codes: List[str], use_cache: bool = True) -> Dict[str, Dict]:
    """批量获取实时价格"""
    return get_realtime_fetcher().fetch_batch(ts_codes, use_cache)

def get_source_health() -> Dict:
    """获取数据源健康状态"""
    return get_realtime_fetcher().get_source_health()


# ========== 测试 ==========

if __name__ == '__main__':
    print("=" * 60)
    print("🧪 实时价格获取测试")
    print("=" * 60)
    
    fetcher = get_realtime_fetcher()
    
    # 测试单个股票
    print("\n📈 测试华明装备 (002270.SZ)...")
    hm = fetcher.fetch('002270.SZ')
    if hm:
        print(f"✅ 获取成功 (数据源：{hm['source']})")
        print(f"  当前价：¥{hm['price']:.2f}")
        print(f"  涨跌幅：{hm['change_pct']:+.2f}%")
        print(f"  成交量：{hm['volume']:,}手")
    else:
        print("❌ 获取失败")
    
    # 测试 ETF
    print("\n📈 测试电网设备 ETF (159326.SZ)...")
    etf = fetcher.fetch('159326.SZ')
    if etf:
        print(f"✅ 获取成功 (数据源：{etf['source']})")
        print(f"  当前价：¥{etf['price']:.3f}")
        print(f"  涨跌幅：{etf['change_pct']:+.2f}%")
        print(f"  成交量：{etf['volume']:,}手")
    else:
        print("❌ 获取失败")
    
    # 测试批量获取
    print("\n📊 批量获取测试...")
    batch = fetcher.fetch_batch(['002270.SZ', '159326.SZ'])
    for ts_code, data in batch.items():
        print(f"  {ts_code}: ¥{data['price']:.3f} ({data['change_pct']:+.2f}%) [{data['source']}]")
    
    # 显示数据源健康状态
    print("\n💚 数据源健康状态:")
    health = fetcher.get_source_health()
    for name, status in health.items():
        icon = "✅" if status['healthy'] else "❌"
        print(f"  {icon} {name}: {'健康' if status['healthy'] else '异常'} (失败次数：{status['fail_count']})")
    
    print("\n" + "=" * 60)
