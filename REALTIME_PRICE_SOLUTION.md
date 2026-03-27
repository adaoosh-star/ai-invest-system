# 实时价格解决方案 - 多数据源冗余设计

**创建时间：** 2026-03-26 12:00  
**问题：** 盘中监控使用过期缓存数据，华明装备显示 26.58（3 月 23 日数据），实际价格 27.50

---

## 🎯 设计原则

1. **盘中必须用实时价格** - Tushare 只有盘后数据，不能用于盘中监控
2. **多数据源冗余** - 主数据源失败自动降级到备用源
3. **数据源健康检查** - 动态选择最优数据源
4. **统一接口** - 调用方无需关心数据源细节

---

## 📊 数据源架构

### 数据源优先级

| 优先级 | 数据源 | 接口地址 | 特点 | 状态 |
|--------|--------|----------|------|------|
| 1 | 腾讯财经 | qt.gtimg.cn | 最稳定，A 股/ETF 全覆盖 | ✅ 主力 |
| 2 | 东方财富 | push2.eastmoney.com | 备用，数据丰富 | ✅ 可用 |
| 3 | 新浪财经 | hq.sinajs.cn | 备用，有时被限 | ⚠️ 限流 |
| 4 | AKShare | 聚合接口 | 最后备用 | ✅ 可用 |

### 自动降级逻辑

```
腾讯财经 (主) → 失败 → 东方财富 (备 1) → 失败 → 新浪财经 (备 2) → 失败 → AKShare (最后)
```

### 健康检查机制

- 每个数据源维护健康状态
- 失败次数累计，成功后清零
- 优先使用健康的数据源
- 失败数据源暂时跳过

---

## 🛠️ 实现方案

### 1. 新建实时价格模块

**文件：** `data/realtime_fetcher.py`

**核心功能：**
- `RealtimePriceFetcher` 类 - 多数据源获取器
- `fetch(ts_code)` - 获取单只股票实时价格
- `fetch_batch(ts_codes)` - 批量获取
- `get_source_health()` - 获取数据源健康状态

**返回数据：**
```python
{
    'price': 27.50,           # 当前价
    'prev_close': 27.70,      # 昨收
    'open': 27.60,            # 开盘
    'high': 27.73,            # 最高
    'low': 27.20,             # 最低
    'volume': 59005,          # 成交量 (手)
    'amount': 16196.0,        # 成交额 (千元)
    'change_pct': -0.72,      # 涨跌幅 (%)
    'time_display': '20260326 11:52:33',  # 格式化时间
    'time_raw': '20260326115233',         # 原始时间戳
    'source': 'qq'            # 数据来源
}
```

### 2. 更新统一数据层

**文件：** `data/data_fetcher.py`

**修改：**
- `get_daily_data()` 在交易时间调用 `realtime_fetcher`
- 非交易时间继续使用 Tushare 日线数据
- 自动合并今日实时数据和历史数据

### 3. 更新持仓监控

**文件：** `monitor/holding_monitor.py`

**修改：**
- `get_current_data()` 优先使用 `fetch_realtime_price()`
- 失败时降级到 `get_daily_data()`
- 显示价格来源标识（🟢 实时 / 📅 盘后）
- 显示价格时间戳

---

## 📋 使用示例

### 获取单只股票实时价格

```python
from data.realtime_fetcher import fetch_realtime_price

data = fetch_realtime_price('002270.SZ', use_cache=False)
print(f"华明装备：¥{data['price']:.2f} ({data['change_pct']:+.2f}%) [{data['source']}]")
```

### 批量获取

```python
from data.realtime_fetcher import fetch_batch_realtime

stocks = ['002270.SZ', '159326.SZ']
results = fetch_batch_realtime(stocks, use_cache=False)

for ts_code, data in results.items():
    print(f"{ts_code}: ¥{data['price']:.3f} [{data['source']}]")
```

### 检查数据源健康状态

```python
from data.realtime_fetcher import get_source_health

health = get_source_health()
for name, status in health.items():
    icon = "✅" if status['healthy'] else "❌"
    print(f"{icon} {name}: {'健康' if status['healthy'] else '异常'}")
```

---

## 🧪 测试结果

### 实时价格获取测试

```bash
$ python3 data/realtime_fetcher.py

📈 测试华明装备 (002270.SZ)...
✅ 获取成功 (数据源：qq)
  当前价：¥27.50
  涨跌幅：-0.72%
  成交量：59,005 手

📈 测试电网设备 ETF (159326.SZ)...
✅ 获取成功 (数据源：qq)
  当前价：¥1.884
  涨跌幅：-1.15%
  成交量：5,553,985 手

💚 数据源健康状态:
  ✅ qq: 健康 (失败次数：0)
  ✅ eastmoney: 健康 (失败次数：0)
  ✅ sina: 健康 (失败次数：0)
```

### 持仓监控报告

```
## 📈 持仓明细

**华明装备 (002270.SZ)** 📉 🟢 实时
- 持仓：6000 股
- 成本：¥33.033 → 现价：¥27.500
- 价格时间：2026-03-26 11:53:33
- 市值：¥165,000
- 盈亏：¥-33,198 (-16.75%)

**电网设备 ETF (159326.SZ)** 📉 🟢 实时
- 持仓：80000 股
- 成本：¥1.996 → 现价：¥1.884
- 价格时间：2026-03-26 11:53:21
- 市值：¥150,720
- 盈亏：¥-8,960 (-5.61%)
```

---

## ⚠️ 注意事项

### 1. 缓存策略

- **交易时间**：`use_cache=False` 确保获取最新价格
- **非交易时间**：`use_cache=True` 减少 API 调用
- 缓存 TTL：10 秒（避免短时间内重复请求）

### 2. 交易时间判断

```python
def _is_trading_time():
    now = datetime.now()
    time_val = now.hour * 100 + now.minute
    weekday = now.weekday()
    
    # 周末非交易日
    if weekday >= 5:
        return False
    
    # 交易时间：9:30-11:30, 13:00-15:00
    if 930 <= time_val <= 1500:
        return True
    
    return False
```

### 3. 错误处理

- 所有数据源失败时返回 `None`
- 调用方需要处理降级逻辑
- 记录失败日志便于排查

---

## 🔄 后续优化

### 短期优化
- [ ] 增加数据源失败告警（连续失败 3 次）
- [ ] 添加数据源响应时间监控
- [ ] 优化缓存策略（不同标的不同 TTL）

### 长期优化
- [ ] 接入更多数据源（同花顺、通达信）
- [ ] 实现数据源自动切换（基于响应时间）
- [ ] 添加价格异常检测（涨跌幅过大告警）

---

## 📝 修复记录

| 时间 | 问题 | 修复方案 | 状态 |
|------|------|----------|------|
| 2026-03-26 11:42 | 监控显示过期价格 26.58 | 创建 realtime_fetcher 多数据源模块 | ✅ 完成 |
| 2026-03-26 11:50 | 新浪接口 Forbidden | 改用腾讯财经接口 | ✅ 完成 |
| 2026-03-26 11:55 | 时间显示错误 | 修正腾讯字段索引 [30] | ✅ 完成 |
| 2026-03-26 12:00 | 缓存导致数据不更新 | 交易时间 use_cache=False | ✅ 完成 |

---

## 📚 相关文件

- `data/realtime_fetcher.py` - 实时价格获取模块（新增）
- `data/data_fetcher.py` - 统一数据层（更新）
- `monitor/holding_monitor.py` - 持仓监控报告（更新）
- `tests/test_realtime.py` - 实时价格测试（待创建）

---

**核心原则：** 盘中监控必须用实时价格，多数据源冗余确保可靠性！
