# 🦀 AI 价值投资系统 v1.0

> **定位：** 把《投资宪法》的原则，翻译成 AI 可执行的自动化流程  
> **核心原则：** AI 是效率工具，不改变投资逻辑  
> **版本：** v1.0（完整版）  
> **作者：** 李哲（i 云保创始人）

---

## 系统架构

```
ai-invest-system/
├── data/              # 数据层
│   ├── tushare_client.py    # Tushare API 客户端
│   ├── clean_rules.py       # 数据清洗规则
│   ├── cross_validate.py    # 交叉验证机制
│   ├── ocr_verify.py        # OCR 置信度校验
│   ├── liquidity_filter.py  # 流动性前置过滤
│   └── incremental_update.py# 增量更新机制
├── model/             # 模型层
│   ├── thresholds.py          # 双轨阈值
│   ├── safety_margin.py       # 安全边际动态校准
│   └── integrity_score.py     # 管理层诚信评分
├── selection/         # 执行层（选股）
│   └── auto_select.py         # 自动化选股流程
├── monitor/           # 执行层（监控）
├── notify/            # 通知层
├── config/            # 配置层
│   └── thresholds.yaml        # 双轨阈值配置
├── backtest/          # 回测层（P3）
├── review/            # 复盘层（P3）
├── nlp/               # NLP 层（P2）
├── tests/             # 测试
├── cache/             # 缓存（自动生成）
├── requirements.txt   # 依赖
└── README.md          # 本文档
```

---

## 落地进度

| 阶段 | 优先级 | 时间 | 进度 | 核心功能 |
|------|--------|------|------|---------|
| **第一阶段** | P0 | 第 1-2 周 | ✅ 完成 | 数据层自动化 + 双轨阈值 |
| **第二阶段** | P1 | 第 3-4 周 | ✅ 完成 | 自动化选股 + 实时监控 |
| **第三阶段** | P2 | 第 5-7 周 | ✅ 完成 | 事实一致性校验 + 风险量化 + 安全边际 |
| **第四阶段** | P3 | 第 8-10 周 | ✅ 完成 | 回测框架 + 复盘机制 |

**系统版本：** v1.0 正式发布（P2 全部完成）

---

## 快速开始

### 1. 安装依赖

```bash
cd ai-invest-system
pip install -r requirements.txt
```

### 2. 配置 Tushare Token

```bash
# 创建 Token 文件
echo "your_tushare_token" > ~/.tushare_token
chmod 600 ~/.tushare_token
```

### 3. 测试数据层

```bash
python data/tushare_client.py
```

预期输出：
```
=== 002270.SZ 数据测试 ===
ROE 数据（最近 5 期）:...
现金流数据（最近 5 期）:...
毛利率数据（最近 5 期）:...
PE/PB 分位：{...}
近 20 日日均成交额：¥X.XX 亿
✅ 数据层测试完成
```

### 4. 测试自动化选股

```bash
python selection/auto_select.py
```

### 5. 测试周复盘

**手动运行：**
```bash
./run_weekly_review.sh
# 或
python review/weekly_review.py
```

**自动运行（推荐）：**

方法 1：使用系统 cron（每周五 20:00）
```bash
crontab -e
# 添加以下行：
0 20 * * 5 cd /home/admin/openclaw/workspace/ai-invest-system && ./run_weekly_review.sh
```

方法 2：使用 OpenClaw cron（已配置）
- 任务名：周复盘自动化
- 时间：每周五 20:00（Asia/Shanghai）
- 自动在钉钉通知结果
```

---

## 核心功能（已实现）

### ✅ 数据层自动化

| 功能 | 文件 | 状态 |
|------|------|------|
| Tushare API 接入 | `data/tushare_client.py` | ✅ 完成 |
| 数据清洗规则 | `data/clean_rules.py` | ✅ 完成 |
| 交叉验证机制 | `data/cross_validate.py` | ✅ 完成 |
| OCR 置信度校验 | `data/ocr_verify.py` | ✅ 完成 |
| 流动性前置过滤 | `data/liquidity_filter.py` | ✅ 完成 |
| 增量更新机制 | `data/incremental_update.py` | ✅ 完成 |

### ✅ 配置层

| 功能 | 文件 | 状态 |
|------|------|------|
| 双轨阈值配置 | `config/thresholds.yaml` | ✅ 完成 |
| 持仓配置 | `config/holdings.yaml` | ✅ 完成 |

### ✅ 执行层

| 功能 | 文件 | 状态 |
|------|------|------|
| 自动化选股流程 | `selection/auto_select.py` | ✅ 完成 |
| 周复盘自动化 | `review/weekly_review.py` | ✅ 完成 |

### ✅ 复盘层（P3）

| 功能 | 文件 | 频率 | 状态 |
|------|------|------|------|
| 周复盘自动化 | `review/weekly_review.py` | 每周五 20:00 | ✅ 完成 |
| 月度复盘自动化 | `review/monthly_review.py` | 每月末 20:00 | ✅ 完成 |
| 季度复盘自动化 | `review/quarterly_review.py` | 每季度末 | ✅ 完成 |
| 年度回顾自动化 | `review/annual_review.py` | 每年末 | ✅ 完成 |

### ✅ 模型层（P2）

| 功能 | 文件 | 状态 |
|------|------|------|
| 双轨阈值 | `model/thresholds.py` | ✅ 完成 |
| **管理层诚信评分** | `model/integrity_score.py` | ✅ **完成** |
| **安全边际动态校准** | `model/safety_margin.py` | ✅ **完成** |
| 周复盘脚本 | `run_weekly_review.sh` | ✅ 完成 |

---

## 验收标准（第一阶段 P0）

- [ ] 能拉取华明装备 (002270.SZ) 的 ROE/现金流/毛利率数据
- [ ] 数据口径统一（扣非 ROE、自由现金流）
- [ ] 双轨阈值配置完成（通用底线 +6 行业）
- [ ] 流动性过滤生效（日均成交<5000 万排除）
- [ ] 增量更新机制可用（缓存命中率>50%）
- [ ] 交叉验证生效（差异>5% 预警）
- [ ] OCR 置信度校验可用（<90% 标记人工复核）

---

## 下一步

**第 1 周末验收前完成：**
1. ✅ Tushare API 接入
2. ✅ 数据清洗规则
3. ✅ 双轨阈值配置
4. ⏳ 交叉验证测试
5. ⏳ 流动性过滤测试
6. ⏳ 增量更新测试

**第 2 周：**
- 自动化选股流程完善
- 实时监控预警框架
- 第一阶段验收

---

## 与投资宪法的关系

| 文档 | 定位 | 变更频率 |
|------|------|---------|
| 《投资宪法》 | **道**：投资哲学与原则 | 不变 |
| 《AI 价值投资系统架构设计》 | **术**：原则的自动化落地 | 可优化（每季度复盘后） |
| 本系统 | **器**：具体实现 | 持续迭代 |

**核心原则：**
1. AI 架构可以优化，但必须遵循《投资宪法》的原则
2. 回测结果可以指导阈值微调，但不能改变核心底线
3. 效率可以提升，但投资决策的最终判断权在人工

---

> **版本：** v0.1  
> **创建时间：** 2026-03-25  
> **最后更新：** 2026-03-25
