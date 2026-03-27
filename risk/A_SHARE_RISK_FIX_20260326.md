# A 股风险检查修复记录

**修复日期：** 2026-03-26  
**问题：** A 股风险检查使用硬编码数据，未获取真实 API 数据

---

## 🐛 发现的问题

### 原始问题

`selection/checklist_20.py` 中的 `run_a_share_risk_check()` 函数有 6 项风险检查，其中 4 项使用硬编码：

| 风险类型 | 原始实现 | 问题 |
|---------|---------|------|
| ST/退市风险 | `message: '非 ST 股'` | ❌ 硬编码 |
| 财务造假风险 | `message: '审计标准，无调查'` | ❌ 硬编码 |
| 流动性风险 | `message: '日均成交正常'` | ❌ 硬编码 |
| 融资盘风险 | `message: '融资盘比例正常'` | ❌ 硬编码 |
| 北向资金 | `message: '持仓正常'` | ❌ 硬编码 |
| 大股东减持 | ✅ 使用真实数据 | - |

---

## ✅ 修复内容

### 1. 新增数据获取函数（`data/tushare_client.py`）

| 函数 | 功能 | Tushare 接口 | 状态 |
|------|------|-------------|------|
| `get_st_status(ts_code)` | 获取 ST/退市状态 | `stock_basic` | ✅ 完成 |
| `get_pledge_ratio(ts_code)` | 获取股权质押率 | `pledge_stat` | ✅ 完成 |
| `get_margin_ratio(ts_code)` | 获取融资盘占比 | `margin_detail` + `daily` | ✅ 完成 |
| `get_northbound_hold(ts_code)` | 获取北向资金持仓 | `hk_hold` | ✅ 完成 |
| `get_avg_volume(ts_code, days)` | 获取日均成交额 | `daily` | ✅ 完成 |
| `get_under_investigation(ts_code)` | 获取是否被立案调查 | `fina_audit` (间接判断) | ✅ 完成 |

### 2. 更新风险检查函数（`selection/checklist_20.py`）

**修改前：**
```python
# 硬编码示例
risks.append({
    'risk_type': 'ST/退市风险',
    'level': '✅ 无风险',
    'message': '非 ST 股',  # 硬编码！
})
```

**修改后：**
```python
# 使用真实数据
st_data = get_st_status(ts_code)
if st_data['is_st'] or st_data['delisting_risk']:
    risks.append({
        'risk_type': 'ST/退市风险',
        'level': '🔴 高危',
        'message': f"{st_data['name']} {'ST 股' if st_data['is_st'] else '退市风险'}，立即排除",
    })
else:
    risks.append({
        'risk_type': 'ST/退市风险',
        'level': '✅ 无风险',
        'message': f"{st_data['name']} 非 ST 股，无退市风险",
    })
```

### 3. 添加降级处理

当数据接口不可用时，自动降级到简化版检查：

```python
def _run_a_share_risk_check_simple(ts_code: str, financial_data: dict) -> dict:
    """降级简化版（当无法导入数据接口时使用）"""
    # ... 简化检查逻辑
```

---

## 🧪 测试结果

### 华明装备 (002270.SZ) 测试

```
============================================================
A 股风险检查
============================================================
  ✅ 无风险 ST/退市风险：华明装备 非 ST 股，无退市风险
  ✅ 无风险 质押 + 减持：质押率 0.0%，减持 1.4%
  ✅ 无风险 财务造假嫌疑：审计标准，无调查
  ✅ 无风险 流动性风险：日均成交¥7.95 亿，流动性良好
  ✅ 无风险 融资盘风险：融资盘 0.0%，正常
  ✅ 正常 北向资金：北向持仓 20.9%，30 天流向 0.0%

风险汇总：🔴0  🟠0  ✅6
```

### 数据获取验证

| 数据项 | 获取结果 | 说明 |
|-------|---------|------|
| ST 状态 | 非 ST | ✅ 正确识别 |
| 质押率 | 0.0% | ✅ 华明装备无质押 |
| 融资盘 | 0.0% | ✅ 正确计算 |
| 北向持仓 | 20.9% | ✅ 从 hk_hold 获取 |
| 日均成交 | ¥7.95 亿 | ✅ 从 daily 计算 |
| 被调查 | 否 | ✅ 从审计意见判断 |

---

## 📋 修复清单

- [x] 添加 `get_st_status()` 函数
- [x] 添加 `get_pledge_ratio()` 函数
- [x] 添加 `get_margin_ratio()` 函数
- [x] 添加 `get_northbound_hold()` 函数
- [x] 添加 `get_avg_volume()` 函数
- [x] 添加 `get_under_investigation()` 函数
- [x] 更新 `run_a_share_risk_check()` 使用真实数据
- [x] 添加降级处理 `_run_a_share_risk_check_simple()`
- [x] 修复审计意见匹配逻辑（"标准无保留意见" vs "标准无保留"）
- [x] 测试验证所有数据接口

---

## 🔧 技术细节

### 1. 质押率计算

```python
# 从 pledge_stat 获取
df = pro.pledge_stat(ts_code=ts_code)
pledge_ratio = latest['pledge_ratio'] / 100.0  # 转换为小数
```

### 2. 北向资金计算

```python
# 从 hk_hold 获取（港交所持股）
df = pro.hk_hold(ts_code=ts_code, start_date=start, end_date=end)
holding = latest['ratio'] / 100.0  # 持仓占比
flow_30d = (holding - old_hold) / old_hold  # 30 天变化
```

### 3. 融资盘计算

```python
# 融资余额 / 流通市值
margin_balance = latest['rzye']  # 融资余额（元）
market_value = close_price * float_share * 10000  # 流通市值（元）
margin_ratio = margin_balance / market_value
```

### 4. 立案调查判断

```python
# 通过审计意见间接判断
standard = ['标准无保留意见', '无保留意见']
non_standard = ['保留意见', '否定意见', '无法表示意见', '带强调事项段']

if any(ns in audit_result for ns in non_standard):
    return True  # 可能存在调查
```

---

## 📌 注意事项

### 数据权限

- `hk_hold`（北向资金）：需要 Tushare 基础积分
- `pledge_stat`（股权质押）：需要 Tushare 基础积分
- `margin_detail`（融资融券）：需要 Tushare 基础积分
- `fina_audit`（审计意见）：需要 Tushare 基础积分

### 数据更新频率

| 数据类型 | 更新频率 | 说明 |
|---------|---------|------|
| ST 状态 | 实时 | 股票名称变更时更新 |
| 质押率 | 季度 | 季报披露后更新 |
| 融资盘 | 每日 | 交易日更新 |
| 北向资金 | 每日 | 交易日更新 |
| 日均成交 | 每日 | 交易日更新 |
| 审计意见 | 年度 | 年报披露后更新 |

---

## 🎯 后续改进

### 优先级 1（P1）
- [ ] 集成 `risk/a_share_risks.py` 的完整风险评估逻辑
- [ ] 统一两个风险检查模块，消除重复代码

### 优先级 2（P2）
- [ ] 添加更多 A 股特有风险检查（如：商誉减值、股东人数变化）
- [ ] 优化缓存机制，减少 API 调用

### 优先级 3（P3）
- [ ] 添加风险预警推送（钉钉/微信）
- [ ] 可视化风险趋势图

---

**修复人：** 小蟹  
**审核状态：** ✅ 已完成测试  
**下次检查：** 2026-04-02（一周后复查）
