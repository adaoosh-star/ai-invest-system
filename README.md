# 🦀 AI 价值投资系统 v2.0

> **把《投资宪法》的原则，翻译成 AI 可执行的自动化流程**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/adaoosh-star/ai-invest-system)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-stable-success.svg)]()

**作者：** 李哲（i 云保创始人）  
**开源时间：** 2026-03-27  
**GitHub：** https://github.com/adaoosh-star/ai-invest-system

---

## 💭 前言

虽是不务正业，但非常想分享给大家。

昨晚熬了一夜，用 OpenClaw 手搓了一个"AI 价值投资系统"，全程 0 代码（咱也不会），就靠聊天。

当测试完成，系统跑通，上传代码时，真的感觉这个世界太美好了——只要你努力，就有那么多种可能。

把朋友圈李路路老师的一句话送给大家：

> **"你并非在发现自己，而是在重新创造自己"**

朋友们，拥抱 AI 吧，创造自己的新世界。

—— 李哲  2026-03-26

---

---

## 🆕 v2.0 新增功能 (2026-04-07)

### P0: 推送优化 + 记忆系统
- ✅ **智能推送** - 仅预警时推送（红色/橙色/绿色机会），推送量减少 95%
- ✅ **记忆系统** - 30 天 TTL 自动清理，分析/决策/承诺追踪可追溯

### P1: 报告摘要化 + LLM 深度分析
- ✅ **摘要模式** - 3-5 行摘要 + 详细报告链接，阅读效率提升 80%
- ✅ **LLM 语义分析** - 千问 API 承诺分析、MD&A 解读、造假风险识别
- ✅ **成本管控** - 每日上限¥10，自动记录和限制

### P2: 投资宪法 2.0（决策引擎）
- ✅ **量化评分** - 5 维评分系统（检查清单 30% + ROE 25% + 现金流 20% + 估值 15% + 增长 10%）
- ✅ **决策规则** - 买入/卖出/补仓/减仓/持仓监控量化触发条件
- ✅ **仓位管理** - 单只股票 10-30%，单一行业≤40%

### P3: 年报深度解读
- ✅ **MD&A 分析** - 情感倾向、管理层语气、可信度评分
- ✅ **趋势分析** - 跨年度 CAGR、波动率、趋势方向判断
- ✅ **财报附注** - 关联交易、资产减值、或有负债提取框架

---

## 📖 项目简介

AI 价值投资系统是一个**基于规则的股票分析框架**，将价值投资原则转化为可执行的自动化流程。

**核心理念：**
- 🤖 **AI 是效率工具** —— 不改变投资逻辑，只提升执行效率
- 📜 **遵循投资宪法** —— 20 项检查清单是核心，不可妥协
- 🔍 **数据驱动决策** —所有结论来自真实 API 数据，禁止编造
- ⚠️ **人机协作** —— AI 提供分析，人类做最终判断

**适合人群：**
- ✅ 价值投资者（遵循巴菲特/段永平原则）
- ✅ A 股投资者（系统针对 A 股市场设计）
- ✅ 长期主义者（系统为低频交易设计，不适合短线）
- ❌ 短线交易者（系统不支持技术分析/量化交易）

---

## 🎯 核心功能

### 1️⃣ 股票深度分析（v1.0 + v2.0 增强）

**20 项投资宪法检查清单：**

| 类别 | 检查项 |
|------|--------|
| **盈利能力** | ROE 连续 5 年>15%、毛利率稳定性、现金流/净利润 |
| **财务健康** | 负债率<60%、应收账款/营收、存货/营收 |
| **估值水平** | PE 历史分位、PB 历史分位、PEG |
| **成长性** | 营收增长率、净利润增长率 |
| **管理层诚信** | 关联交易、大股东减持、承诺兑现率 |
| **行业对比** | ROE vs 行业、毛利率 vs 行业 |
| **风险检查** | ST/退市风险、质押风险、流动性风险 |

**输出：** 完整的 Markdown 分析报告，包含评级建议和风险提示。

**v2.0 增强:**
- 🤖 LLM 深度分析（承诺语义分析、MD&A 解读、造假风险识别）
- 📊 决策引擎量化评分（买入/卖出/补仓/减仓建议）
- 📝 年报深度解读（情感分析、趋势分析、跨年度对比）

---

### 2️⃣ 自动化选股（v1.0）

**全市场扫描流程：**

```bash
python3 run.py select
```

**步骤：**
1. 获取全 A 股列表（约 5000 只）
2. 流动性过滤（日均成交>5000 万）
3. 执行 20 项检查清单
4. 输出通过率高的股票列表

**耗时：** 约 30-60 分钟（取决于网络）

---

### 3️⃣ 持仓监控（v1.0 + v2.0 优化）

**实时监控预警：**

```bash
python3 run.py monitor
```

**7 大预警规则：**
1. 盈利预警（涨幅>5%）
2. 亏损预警（跌幅>5%）
3. 均线金叉/死叉
4. RSI 超买/超卖
5. 成交量异动
6. 跳空缺口
7. 动态止盈

**推送方式：** 钉钉消息通知

**v2.0 优化:**
- 🔕 智能推送 - 仅预警时推送（红色/橙色/绿色机会），无预警不推送
- 🧠 记忆系统 - 分析历史、决策记录、承诺追踪（30 天 TTL）

---

### 4️⃣ 定期复盘（v1.0）

**自动化复盘报告：**

| 报告类型 | 执行时间 | 内容 |
|---------|---------|------|
| 盘前预判 | 交易日 8:30 | 隔夜市场、操作计划 |
| 集合竞价 | 交易日 9:25 | 竞价结果、最终计划 |
| 盘后复盘 | 交易日 15:30 | 收盘数据、技术分析 |
| 周复盘 | 每周五 20:00 | 本周总结、下周计划 |
| 月复盘 | 每月末 20:00 | 月度回顾、持仓调整 |
| 年复盘 | 每年末 | 年度总结、策略优化 |

---

### 5️⃣ 事实一致性校验（NLP）

**管理层承诺兑现率分析：**

```bash
# 分析单只股票的承诺兑现情况
python3 run.py analyze 002270.SZ
```

**功能：**
- 获取近 1 年公司公告（232 条）
- 筛选承诺相关公告（11 条）
- 分类：明确承诺 / 模糊承诺 / 长期规划
- 计算兑现率（藏格矿业：100%）

**意义：** 验证管理层"本分"程度，避免诚信风险。

---

### 6️⃣ 决策引擎 v2.0（新增）

**量化评分系统：**

```bash
python3 run.py decision-test
```

**评分权重：**
| 指标 | 权重 |
|------|------|
| 20 项检查通过率 | 30% |
| ROE 评分 | 25% |
| 现金流评分 | 20% |
| 估值评分 | 15% |
| 增长评分 | 10% |

**决策阈值：**
| 评分 | 决策 | 等级 | 建议仓位 |
|------|------|------|---------|
| ≥0.85 | 买入 | 强烈推荐 | 25% |
| ≥0.70 | 买入 | 推荐买入 | 20% |
| ≥0.50 | 观望 | 观望 | 10% |

**卖出触发条件：**
- 🔴 ST 风险、质押率>50% → 立即卖出
- 🟠 PE 分位>95%、PEG>2 → 尽快卖出
- 🟡 ROE 连续 2 年下降 → 考虑卖出

---

### 7️⃣ 年报深度解读（新增）

**MD&A 深度分析：**

```bash
python3 run.py annual-test
```

**分析能力：**
- 📖 MD&A 情感分析 - 积极/中性/消极，管理层语气，可信度评分
- 📈 跨年度趋势 - CAGR、波动率、趋势方向（3 年 + 数据）
- 📋 财报附注提取 - 关联交易、资产减值、或有负债框架

**输出：** Markdown 格式年报解读报告（7 个章节）

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Linux / macOS（Windows 需 WSL）
- Tushare Pro 账号（免费，注册地址：https://tushare.pro）

### 1. 克隆项目

```bash
git clone git@github.com:adaoosh-star/ai-invest-system.git
cd ai-invest-system
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

**主要依赖：**
- `tushare` - A 股数据 API
- `akshare` - 备用数据源
- `pandas` - 数据处理
- `pdfplumber` - PDF 解析（NLP 功能）
- `requests` - HTTP 请求

### 3. 配置 Tushare Token

```bash
# 创建 Token 文件
echo "your_tushare_token" > ~/.tushare_token
chmod 600 ~/.tushare_token
```

**获取 Token：**
1. 注册 https://tushare.pro
2. 登录后进入"个人中心"
3. 复制 API TOKEN

### 4. 测试运行

**分析单只股票：**

```bash
python3 run.py analyze 002270.SZ
```

**预期输出：**
```
📊 002270.SZ 完整分析报告
✅ 核心结论
- 评级：✅ 通过
- 通过率：85%
- 风险等级：低
```

**报告位置：** `cache/002270_SZ_完整报告_YYYYMMDD_HHMMSS.md`

---

### 5. v2.0 新功能测试

**测试所有 v2.0 模块：**

```bash
# 持仓监控 v2（仅预警推送）
python3 run.py monitor-v2

# 记忆系统统计
python3 run.py memory-stats

# 报告摘要生成测试
python3 run.py summary-test

# LLM 深度分析测试
python3 run.py llm-test

# 决策引擎测试
python3 run.py decision-test

# 年报解读测试
python3 run.py annual-test
```

---

## 📂 项目结构

```
ai-invest-system/
├── run.py                     # 统一入口（推荐使用）
├── requirements.txt           # Python 依赖
├── README.md                  # 本文档
│
├── data/                      # 数据层
│   ├── tushare_client.py      # Tushare API 客户端
│   ├── data_fetcher.py        # 通用数据获取
│   ├── clean_rules.py         # 数据清洗规则
│   ├── cross_validate.py      # 交叉验证机制
│   ├── ocr_verify.py          # OCR 置信度校验
│   ├── liquidity_filter.py    # 流动性前置过滤
│   └── incremental_update.py  # 增量更新机制
│
├── model/                     # 模型层
│   ├── dual_threshold.py      # 双轨阈值（v1.0）
│   ├── safety_margin.py       # 安全边际动态校准（v1.0）
│   ├── integrity_score.py     # 管理层诚信评分（v1.0）
│   └── decision_engine_v2.py  # 决策引擎 v2.0（新增）
│
├── analysis/                  # 分析层（v2.0 新增）
│   ├── deep_analysis.py       # 个股深度分析
│   ├── llm_enhanced.py        # LLM 深度分析
│   └── annual_report_analyzer.py  # 年报深度解读
│
├── report/                    # 报告层（v2.0 新增）
│   └── summary_generator.py   # 报告摘要生成器
│
├── selection/                 # 选股层
│   ├── checklist_20.py        # 20 项检查清单
│   ├── complete_analysis.py   # 完整分析流程
│   └── auto_select.py         # 自动化选股
│
├── monitor/                   # 监控层
│   ├── holding_monitor.py     # 持仓监控（v1.0）
│   ├── holding_monitor_v2.py  # 持仓监控 v2（新增）
│   └── real_time_monitor.py   # 实时监控
│
├── utils/                     # 工具类
│   ├── logger.py              # 日志系统
│   ├── report_generator.py    # 报告生成
│   ├── view_logs.py           # 日志查看
│   └── session_memory.py      # 记忆系统（v2.0 新增）
│
├── review/                    # 复盘层
│   ├── weekly_review.py       # 周复盘
│   ├── monthly_review.py      # 月复盘
│   ├── quarterly_review.py    # 季复盘
│   └── annual_review.py       # 年复盘
│
├── nlp/                       # NLP 层
│   ├── announcement_analyzer.py  # 公告分析器
│   └── promise_analyzer.py       # 承诺兑现分析
│
├── risk/                      # 风险层
│   └── a_share_risks.py       # A 股特有风险检查
│
├── notify/                    # 通知层
│   └── dingtalk_alert.py      # 钉钉预警推送
│
├── config/                    # 配置层
│   ├── thresholds.yaml        # 双轨阈值配置
│   ├── holdings.yaml          # 持仓配置
│   ├── p0_config.yaml         # P0 阶段配置（v2.0 新增）
│   └── investment_constitution_v2.yaml  # 投资宪法 2.0（v2.0 新增）
│
├── cache/                     # 缓存（自动生成）
│   ├── 分析报告 *.md
│   └── 临时数据 *.pkl
│
├── memory/                    # 记忆系统（v2.0 新增）
│   ├── analysis_history.jsonl    # 分析历史
│   ├── decision_log.jsonl        # 决策记录
│   └── promise_tracking.jsonl    # 承诺追踪
│
├── scripts/                   # 脚本（v2.0 新增）
│   └── test_llm_full.py       # LLM 完整测试
│
├── tests/                     # 测试
│   ├── test_p0.py             # P0 验收测试
│   └── *_report.md            # 测试报告
│
└── docs/                      # 文档（v2.0 新增）
    ├── 投资宪法 2.0 决策规则.md
    └── ...
```

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    用户交互层                        │
│         run.py / CLI / 钉钉通知 / Canvas            │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│                    业务逻辑层                        │
│   选股 (selection) │ 监控 (monitor) │ 复盘 (review)  │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│                    模型层                            │
│   20 项检查 │ 双阈值 │ 诚信评分 │ 安全边际 │ NLP     │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│                    数据层                            │
│   Tushare │ Akshare │ 新浪财经 │ 东方财富 │ 公告    │
└─────────────────────────────────────────────────────┘
```

---

## 🎓 投资哲学

### 与投资宪法的关系

| 文档 | 定位 | 变更频率 |
|------|------|---------|
| 《投资宪法》 | **道**：投资哲学与原则 | 不变 |
| 系统架构设计 | **术**：原则的自动化落地 | 每季度复盘后优化 |
| 本系统 | **器**：具体实现 | 持续迭代 |

### 核心原则

1. **AI 架构可以优化，但必须遵循《投资宪法》的原则**
2. **回测结果可以指导阈值微调，但不能改变核心底线**
3. **效率可以提升，但投资决策的最终判断权在人工**
4. **数据必须真实，禁止编造**（2026-03-26 确立）

---

## 📈 使用示例

### 示例 1：分析单只股票

```bash
# 完整分析（20 项+A 股风险+NLP）
python3 run.py analyze 002270.SZ

# 快速分析（仅 20 项检查）
python3 run.py analyze 002270.SZ --quick
```

**输出报告：** `cache/002270_SZ_完整报告_20260327_194432.md`

---

### 示例 2：全市场选股

```bash
python3 run.py select
```

**输出：** 通过 20 项检查的股票列表（按通过率排序）

---

### 示例 3：持仓监控

```bash
python3 run.py monitor
```

**输出：** 持仓股票实时数据 + 预警信息（钉钉推送）

---

### 示例 4：周复盘

```bash
# 手动运行
python3 run.py review weekly

# 自动运行（cron 配置）
# 每周五 20:00 自动执行，钉钉通知结果
```

---

## ⚠️ 免责声明

**重要提示：**

1. **本系统不构成投资建议** —— 所有分析仅供参考，不构成买卖建议
2. **数据延迟风险** —— 行情数据可能延迟 15 分钟，请以交易所实时数据为准
3. **投资有风险** —— A 股市场波动较大，请独立判断，谨慎决策
4. **系统无保证** —— 按"原样"提供，不保证准确性、完整性、及时性

**使用本系统即表示你同意：**
- 独立承担所有投资风险
- 不向作者追究任何法律责任
- 将本系统作为辅助工具，而非决策依据

---

## 🤝 贡献指南

**欢迎提交：**
- 🐛 Bug 报告
- 💡 功能建议
- 📝 文档改进
- 🔧 代码 PR

**提交方式：**
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 更新日志

### v2.0.0 (2026-04-07) - P0+P1+P2+P3 完整实施

**P0: 推送优化 + 记忆系统**
- ✅ 智能推送 - 仅预警时推送（红色/橙色/绿色机会），推送量减少 95%
- ✅ 记忆系统 - 30 天 TTL 自动清理，分析/决策/承诺追踪可追溯

**P1: 报告摘要化 + LLM 深度分析**
- ✅ 报告摘要 - 3-5 行摘要 + 详细报告链接，阅读效率提升 80%
- ✅ LLM 语义分析 - 千问 API 承诺分析、MD&A 解读、造假风险识别
- ✅ 成本管控 - 每日上限¥10，自动记录和限制

**P2: 投资宪法 2.0（决策引擎）**
- ✅ 量化评分 - 5 维评分系统（检查清单 30% + ROE 25% + 现金流 20% + 估值 15% + 增长 10%）
- ✅ 决策规则 - 买入/卖出/补仓/减仓/持仓监控量化触发条件
- ✅ 仓位管理 - 单只股票 10-30%，单一行业≤40%

**P3: 年报深度解读**
- ✅ MD&A 分析 - 情感倾向、管理层语气、可信度评分
- ✅ 趋势分析 - 跨年度 CAGR、波动率、趋势方向判断
- ✅ 财报附注 - 关联交易、资产减值、或有负债提取框架

**新增文件：**
- `monitor/holding_monitor_v2.py` - 持仓监控 v2
- `utils/session_memory.py` - 记忆系统
- `report/summary_generator.py` - 报告摘要生成器
- `analysis/llm_enhanced.py` - LLM 深度分析
- `model/decision_engine_v2.py` - 决策引擎 v2.0
- `analysis/annual_report_analyzer.py` - 年报深度解读
- `config/p0_config.yaml` - P0 阶段配置
- `config/investment_constitution_v2.yaml` - 投资宪法 2.0

**新增命令：**
- `python3 run.py monitor-v2` - 持仓监控 v2
- `python3 run.py memory-stats` - 记忆系统统计
- `python3 run.py summary-test` - 报告摘要测试
- `python3 run.py llm-test` - LLM 深度分析测试
- `python3 run.py decision-test` - 决策引擎测试
- `python3 run.py annual-test` - 年报解读测试

**文档更新：**
- ✅ P0_COMPLETION_REPORT.md - P0 阶段完成报告
- ✅ P1_FINAL_REPORT.md - P1 阶段最终报告
- ✅ P2_COMPLETION_REPORT.md - P2 阶段完成报告
- ✅ P3_COMPLETION_REPORT.md - P3 阶段完成报告
- ✅ V2_FINAL_SUMMARY.md - v2.0 最终总结
- ✅ IMPLEMENTATION_PLAN_V2.md - v2.0 实施计划

**稳定性保障：**
- ✅ 向后兼容 - v1.0 命令保持可用
- ✅ 配置开关 - 所有新功能可独立控制
- ✅ 降级方案 - LLM 失败时自动切换规则分析
- ✅ 回滚方案 - 可一键回滚到 v1.0

---

### v1.0.0 (2026-03-27)

**新增功能：**
- ✅ 20 项投资宪法检查清单
- ✅ A 股特有风险检查（ST/质押/流动性/融资盘）
- ✅ NLP 事实一致性校验（公告分析+承诺兑现率）
- ✅ 自动化选股（全市场扫描）
- ✅ 持仓监控（7 大预警规则）
- ✅ 定期复盘（周/月/季/年）
- ✅ 钉钉预警推送

**修复问题：**
- ✅ Tushare 接口字段名错误（2026-03-26）
- ✅ 数据编造问题（确立"数据真实性原则"）
- ✅ NLP full 模式限制说明

**文档更新：**
- ✅ 完善 README.md
- ✅ 新增 USER_GUIDE.md
- ✅ 新增 SYSTEM_OVERVIEW.md

---

## 📧 联系方式

- **作者：** 李哲
- **GitHub：** https://github.com/adaoosh-star
- **邮箱：** adaoo.sh@gmail.com
- **公司：** i 云保（创始人）

---

## 📜 许可证

MIT License

---

**最后更新：** 2026-04-07  
**版本：** v2.0.0  
**状态：** ✅ Stable

---

<div align="center">

**🦀 AI 价值投资系统 v2.0 - 让投资更简单**

**P0+P1+P2+P3 完整实施 | 8 个新模块 | 向后兼容 | 稳定性保障**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/adaoosh-star/ai-invest-system)
[![Star](https://img.shields.io/github/stars/adaoosh-star/ai-invest-system?style=social)](https://github.com/adaoosh-star/ai-invest-system/stargazers)
[![Fork](https://img.shields.io/github/forks/adaoosh-star/ai-invest-system?style=social)](https://github.com/adaoosh-star/ai-invest-system/network/members)

</div>
