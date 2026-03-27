# 日志系统使用说明

**创建日期：** 2026-03-27  
**版本：** v1.0

---

## 一、日志系统功能

| 功能 | 说明 |
|------|------|
| **自动分割** | 按日期自动分割日志文件 |
| **级别支持** | DEBUG/INFO/WARNING/ERROR |
| **自动清理** | 自动清理 30 天前的日志 |
| **统一格式** | 时间 \| 模块 \| 级别 \| 消息 |

---

## 二、日志文件位置

```
/home/admin/openclaw/workspace/ai-invest-system/logs/
├── holding_monitor.log    # 持仓监控日志
├── complete_analysis.log  # 个股分析日志（待集成）
├── auto_select.log        # 自动化选股日志（待集成）
└── ...
```

---

## 三、查看日志

### 3.1 查看所有日志文件

```bash
cd /home/admin/openclaw/workspace/ai-invest-system
python3 utils/view_logs.py
```

**输出示例：**
```
📁 日志目录：/home/admin/openclaw/workspace/ai-invest-system/logs

文件名                                      大小         修改时间
----------------------------------------------------------------------
holding_monitor.log                      0.6KB      2026-03-27 16:27
```

### 3.2 查看指定日志

```bash
# 查看持仓监控日志（最后 50 行）
python3 utils/view_logs.py holding_monitor

# 查看最后 100 行
python3 utils/view_logs.py holding_monitor --tail 100
```

**输出示例：**
```
📄 查看日志：holding_monitor.log

----------------------------------------------------------------------
2026-03-27 16:27:48 | holding_monitor | INFO | 持仓监控任务开始执行
2026-03-27 16:27:48 | holding_monitor | INFO | 持仓数量：2
2026-03-27 16:27:49 | holding_monitor | INFO | 预警汇总：红色=0, 橙色=0, 机会=0
2026-03-27 16:27:49 | holding_monitor | INFO | 报告已保存：...
2026-03-27 16:27:49 | holding_monitor | INFO | 持仓监控任务执行完成
----------------------------------------------------------------------

共 7 行，显示最后 7 行
```

### 3.3 清理旧日志

```bash
# 清理 30 天前的日志
python3 utils/view_logs.py --clean

# 清理 7 天前的日志
python3 utils/view_logs.py --clean --days 7
```

---

## 四、日志级别说明

| 级别 | 说明 | 何时使用 |
|------|------|---------|
| **DEBUG** | 调试信息 | 开发调试时使用 |
| **INFO** | 普通信息 | 任务开始/结束、关键步骤 |
| **WARNING** | 警告信息 | 降级处理、非关键错误 |
| **ERROR** | 错误信息 | 任务失败、关键错误 |

---

## 五、在代码中使用日志

### 5.1 导入日志

```python
from utils.logger import get_logger
logger = get_logger('模块名')
```

### 5.2 记录日志

```python
# 普通信息
logger.info("任务开始执行")

# 警告
logger.warning("API 调用失败，尝试降级方案")

# 错误
logger.error("任务执行失败", exc_info=True)  # 包含堆栈

# 调试
logger.debug(f"处理数据：{data}")
```

### 5.3 完整示例

```python
from utils.logger import get_logger
logger = get_logger('my_module')

def my_function():
    logger.info("函数开始执行")
    
    try:
        # 业务逻辑
        result = process_data()
        logger.info(f"处理完成：{result}")
        
    except Exception as e:
        logger.error(f"处理失败：{e}", exc_info=True)
        raise
```

---

## 六、已集成日志的模块

| 模块 | 日志文件 | 状态 |
|------|---------|------|
| **持仓监控** | `holding_monitor.log` | ✅ 已集成 |
| **个股分析** | `complete_analysis.log` | ⏳ 待集成 |
| **自动化选股** | `auto_select.log` | ⏳ 待集成 |
| **周复盘** | `weekly_review.log` | ⏳ 待集成 |

---

## 七、日志格式

```
YYYY-MM-DD HH:MM:SS | 模块名 | 级别 | 消息
```

**示例：**
```
2026-03-27 16:27:48 | holding_monitor | INFO | 持仓监控任务开始执行
2026-03-27 16:27:49 | holding_monitor | WARNING | 获取实时价格失败 002270.SZ: 连接超时
2026-03-27 16:27:50 | holding_monitor | ERROR | 持仓监控任务执行失败：数据异常
```

---

## 八、常见问题

### Q1: 日志文件太大怎么办？

**A:** 系统会自动清理 30 天前的日志。如需手动清理：
```bash
python3 utils/view_logs.py --clean
```

### Q2: 如何实时查看日志？

**A:** 使用 `tail -f` 命令：
```bash
tail -f logs/holding_monitor.log
```

### Q3: 如何查找特定错误？

**A:** 使用 `grep` 命令：
```bash
grep "ERROR" logs/holding_monitor.log
grep "002270" logs/holding_monitor.log
```

### Q4: 日志级别如何调整？

**A:** 修改 `get_logger()` 调用：
```python
# 默认 INFO 级别
logger = get_logger('my_module')

# DEBUG 级别（输出更多）
logger = get_logger('my_module', level=logging.DEBUG)
```

---

## 九、下一步计划

| 任务 | 状态 |
|------|------|
| 集成到个股分析模块 | ⏳ 待完成 |
| 集成到自动化选股模块 | ⏳ 待完成 |
| 集成到周复盘模块 | ⏳ 待完成 |
| 添加日志分析工具 | ⏳ 待完成 |

---

**文档位置：** `/home/admin/openclaw/workspace/ai-invest-system/docs/LOG_SYSTEM.md`
