# AI 价值投资系统 v1.0 - 数据层修复清单

**创建时间：** 2026-03-25 23:35  
**优先级：** P0（影响报告完整性）

---

## 问题描述

臻镭科技 (688270.SH) 分析报告中，20 项检查清单有 15 项显示"待查"，其中：
- **9 项** 是数据获取失败（系统缺陷）
- **7 项** 是需要人工查年报（设计如此）

---

## P0 修复项（自动获取失败）

### 1. 毛利率数据
**问题：** `get_gross_margin()` 调用 `pro.fina_income` 失败  
**错误：** `请指定正确的接口名`

**修复方案：**
```python
# 正确接口名：fina_mainbz（主营业务分析）或需要更新 tushare 库
# 方案 1：更新 tushare 库
pip install --upgrade tushare

# 方案 2：使用备用接口
df = pro.fina_mainbz(ts_code=ts_code, start_date=start_date, end_date=end_date)

# 方案 3：使用 akshare 作为备用数据源
import akshare as ak
```

**影响检查项：**
- 毛利率波动<5%

---

### 2. 现金流数据
**问题：** `get_cash_flow()` 调用 `pro.cashflow_obj` 失败  
**错误：** `请指定正确的接口名`

**修复方案：**
```python
# 正确接口名：cashflow
df = pro.cashflow(ts_code=ts_code, start_date=start_date, end_date=end_date)

# 关键字段：
# oper_cf: 经营活动产生的现金流量净额
# capex: 购建固定资产、无形资产和其他长期资产支付的现金
# fcf = oper_cf - capex
```

**影响检查项：**
- 现金流/净利润>0.8
- 自由现金流 5 年为正

---

### 3. 资产负债表数据
**问题：** `pro.balancesheet` 返回数据不完整

**修复方案：**
```python
# 需要获取的字段：
# total_assets: 总资产
# total_liab: 总负债
# accounts_receivable: 应收账款
# other_receivables: 其他应收款
# inventory: 存货

# 检查字段名是否正确
df = pro.balancesheet(ts_code=ts_code, start_date=start_date, end_date=end_date)
print(df.columns.tolist())
```

**影响检查项：**
- 应收账款/营收<30%
- 存货/营收<20%
- 其他应收款<3%

---

### 4. 利润表数据
**问题：** `pro.fina_income` 接口调用失败

**修复方案：**
```python
# 正确接口名：fina_mainbz
df = pro.fina_mainbz(ts_code=ts_code, start_date=start_date, end_date=end_date)

# 需要字段：
# revenue: 营业收入
# operating_cost: 营业成本
# rd_expense: 研发费用
# core_operating_income: 主营业务利润
```

**影响检查项：**
- 研发费用/营收>3%
- 主营收入占比>80%
- 毛利率计算

---

### 5. 行业对比数据
**问题：** 无行业平均数据接口

**修复方案：**
```python
# 方案 1：使用 tushare 行业分类 + 批量获取同行业数据
df = pro.stock_basic(ts_code=ts_code)
industry = df['industry']

# 获取同行业所有公司
peers = pro.stock_basic(industry=industry)

# 批量获取 ROE/毛利率，计算行业平均

# 方案 2：使用 akshare 行业数据
import akshare as ak
```

**影响检查项：**
- 毛利率 vs 行业
- ROE vs 行业

---

### 6. PEG 计算
**问题：** 需要盈利预测数据

**修复方案：**
```python
# 方案 1：使用券商一致预期（需要付费接口）
# 方案 2：用历史增长率代替
# 方案 3：跳过 PEG，用 PE+ 增长率分别评估

# 简化方案：
# PEG = PE / (净利润增长率*100)
# 增长率用最近 3 年复合增长率
```

**影响检查项：**
- PEG<2.0

---

## P1 完善项（需要人工核实）

这些数据**不适合自动获取**，需要人工查年报：

| 检查项 | 原因 | 建议 |
|--------|------|------|
| 关联交易 | 需要判断交易性质 | 年报"重大关联交易"章节 |
| 大股东减持 | 需要区分减持原因 | 公告/股东变动 |
| 诚信评分 | 需要 NLP 分析承诺 | 待 NLP 模块完善 |
| 承诺兑现率 | 需要对比承诺 vs 实际 | 待 NLP 模块完善 |

---

## 修复计划

| 优先级 | 任务 | 预计时间 |
|--------|------|---------|
| P0 | 修复 tushare 接口调用 | 1 小时 |
| P0 | 添加 akshare 备用数据源 | 2 小时 |
| P0 | 完善数据验证逻辑 | 1 小时 |
| P1 | 添加行业对比功能 | 2 小时 |
| P1 | 完善 NLP 承诺分析 | 4 小时 |
| P2 | 添加年报 PDF 解析 | 8 小时 |

---

## 临时解决方案

在数据层修复前，使用以下**备用方案**：

### 方案 1：东方财富网页抓取
```python
# 使用 web_fetch 获取东方财富数据
# 缺点：不稳定，可能反爬
```

### 方案 2：akshare 备用
```python
import akshare as ak

# 获取财务数据
df = ak.stock_financial_analysis_indicator(symbol="688270")
```

### 方案 3：人工输入
```yaml
# 在 config/holdings.yaml 中添加手动输入数据
manual_data:
  688270.SH:
    gross_margin: 0.55
    roe_avg: 0.20
    # ...
```

---

## 验收标准

修复后，臻镭科技报告应该：
- [ ] 20 项检查清单中，至少 15 项有明确数据（✅或❌）
- [ ] "待查"项不超过 5 项（仅限需要人工核实的数据）
- [ ] 所有自动获取的数据都有来源标注
- [ ] 数据获取失败时有明确错误提示

---

**责任人：** AI 价值投资系统开发团队  
**截止日期：** 2026-03-26 24:00
