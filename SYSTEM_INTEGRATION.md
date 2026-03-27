# AI 价值投资系统 v1.0 - 系统整合文档

**整合日期：** 2026-03-26  
**整合目标：** 统一数据获取、函数逻辑、消除重复代码

---

## 一、统一数据获取层

### 📁 文件位置

```
ai-invest-system/data/data_fetcher.py
```

### 🎯 核心功能

| 函数 | 功能 | 返回值 | 复用场景 |
|------|------|--------|---------|
| `get_daily_data(ts_code, days)` | 获取日线数据（股票/ETF 自动识别） | DataFrame | 所有需要价格数据的模块 |
| `get_price_change(ts_code, days)` | 获取价格变化 | dict（start_price, end_price, change_pct） | 月度/季度/年度复盘 |
| `get_valuation(ts_code)` | 获取估值数据（PE/PB 分位） | dict（pe_ttm, pe_percentile, pb, pb_percentile） | 选股、复盘、安全边际 |
| `get_roe(ts_code, years)` | 获取 ROE 数据 | DataFrame | 选股、诚信评分 |
| `get_stock_name(ts_code)` | 获取股票名称 | str | 所有报告生成 |
| `get_holdings_list()` | 加载持仓配置 | list | 所有需要持仓的模块 |

### ✅ 已解决问题

| 问题 | 解决方案 |
|------|---------|
| ETF 数据获取失败 | 自动识别 ETF，使用 `fund_daily` 接口 |
| PE 分位字段名不统一 | 统一返回 `pe_percentile`（5 年优先） |
| 重复调用 API | 添加缓存机制（24 小时） |
| 日期范围计算不一致 | 统一使用 `days` 参数 |

---

## 二、模块依赖关系

```
┌─────────────────────────────────────┐
│        data/data_fetcher.py         │
│     统一数据获取层（核心）           │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼────┐  ┌──▼────┐
│选股  │  │复盘   │  │模型   │
│模块  │  │模块   │  │模块   │
└───────┘  └───────┘  └───────┘
```

### 📦 模块清单

| 模块 | 文件 | 使用数据函数 |
|------|------|-------------|
| **选股模块** | `selection/checklist_20.py` | `get_valuation`, `get_roe` |
| **复盘模块** | `review/monthly_review.py` | `get_price_change`, `get_valuation` |
| **复盘模块** | `review/quarterly_review.py` | `get_price_change`, `get_valuation` |
| **复盘模块** | `review/annual_review.py` | `get_price_change`, `get_valuation` |
| **复盘模块** | `review/weekly_review.py` | 待更新 |
| **模型模块** | `model/integrity_score.py` | 待更新 |
| **模型模块** | `model/safety_margin.py` | `get_valuation`, `get_roe` |

---

## 三、函数命名规范

### 命名规则

| 类型 | 前缀 | 示例 |
|------|------|------|
| 数据获取 | `get_` | `get_valuation`, `get_roe` |
| 计算类 | `calculate_` | `calculate_score` |
| 检查类 | `check_` | `check_alerts` |
| 生成类 | `generate_` | `generate_report` |
| 保存类 | `save_` | `save_report` |

### 返回值规范

| 类型 | 成功 | 失败 |
|------|------|------|
| 数据获取 | DataFrame/dict | 空 DataFrame/None |
| 计算类 | dict/float | None |
| 检查类 | list（问题列表） | 空列表 |
| 生成类 | str（报告内容） | 空字符串 |

---

## 四、缓存机制

### 缓存策略

| 数据类型 | 缓存时间 | 说明 |
|---------|---------|------|
| 日线数据 | 24 小时 | 盘后更新 |
| 估值数据 | 6 小时 | Tushare 20:00 更新 |
| 财务数据 | 7 天 | 季报更新频率 |
| 公告数据 | 永久 | 本地公告库 |

### 缓存位置

```
ai-invest-system/cache/data_cache/
```

---

## 五、错误处理规范

### 统一错误处理

```python
try:
    data = get_valuation(ts_code)
    if not data:
        # 数据获取失败，使用默认值或跳过
        continue
except Exception as e:
    print(f"错误信息：{e}")
    # 记录日志，继续处理其他股票
    continue
```

### 错误日志

所有错误应该：
1. 打印错误信息（便于调试）
2. 不中断程序（继续处理其他数据）
3. 在报告中标注（如"数据获取失败"）

---

## 六、更新计划

### ✅ 已完成

| 模块 | 状态 | 日期 |
|------|------|------|
| 统一数据获取层 | ✅ 完成 | 2026-03-26 |
| 月度复盘模块 | ✅ 完成 | 2026-03-26 |

### ⏳ 待更新

| 模块 | 优先级 | 说明 |
|------|--------|------|
| 周复盘模块 | P1 | 使用 `get_price_change` 替代直接 API 调用 |
| 季度复盘模块 | P1 | 使用 `get_price_change` 替代直接 API 调用 |
| 年度回顾模块 | P1 | 使用 `get_price_change` 替代直接 API 调用 |
| 诚信评分模块 | P2 | 使用 `get_valuation` 替代直接 API 调用 |
| 安全边际模块 | P2 | 使用 `get_valuation`, `get_roe` 替代直接 API 调用 |
| 选股模块 | P2 | 使用 `get_valuation`, `get_roe` 替代直接 API 调用 |

---

## 七、测试验证

### 测试用例

| 测试项 | 测试方法 | 预期结果 |
|--------|---------|---------|
| 股票数据获取 | `get_price_change('002270.SZ', 30)` | 返回华明装备 30 天价格变化 |
| ETF 数据获取 | `get_price_change('159326.SZ', 30)` | 返回电网 ETF 30 天价格变化 |
| 估值数据获取 | `get_valuation('002270.SZ')` | 返回 PE/PB 分位（非 0） |
| 缓存机制 | 连续调用 2 次 | 第 2 次从缓存读取 |

### 测试结果

| 测试项 | 状态 | 日期 |
|--------|------|------|
| 股票数据获取 | ✅ 通过 | 2026-03-26 |
| ETF 数据获取 | ✅ 通过 | 2026-03-26 |
| 估值数据获取 | ✅ 通过 | 2026-03-26 |
| 月度复盘生成 | ✅ 通过 | 2026-03-26 |

---

## 八、最佳实践

### 1. 使用统一数据层

❌ **错误：**
```python
from data.tushare_client import pro
df = pro.daily(ts_code=ts_code)
```

✅ **正确：**
```python
from data.data_fetcher import get_daily_data
df = get_daily_data(ts_code, days=30)
```

### 2. 检查返回值

❌ **错误：**
```python
valuation = get_valuation(ts_code)
pe_pct = valuation['pe_percentile'] * 100  # 可能报错
```

✅ **正确：**
```python
valuation = get_valuation(ts_code)
if valuation and valuation.get('pe_percentile'):
    pe_pct = float(valuation['pe_percentile']) * 100
else:
    pe_pct = None
```

### 3. 复用已有函数

❌ **错误：** 重复编写价格变化计算逻辑

✅ **正确：**
```python
from data.data_fetcher import get_price_change
perf = get_price_change(ts_code, days=30)
```

---

## 九、维护说明

### 添加新数据源

1. 在 `data_fetcher.py` 中添加新函数
2. 遵循命名规范（`get_xxx`）
3. 添加缓存机制
4. 更新本文档

### 修改现有函数

1. 确保向后兼容
2. 更新所有调用方
3. 测试验证
4. 更新本文档

---

**最后更新：** 2026-03-26  
**维护人：** 小蟹（战略助理）

---

*AI 价值投资系统 v1.0 | 让投资更简单*
