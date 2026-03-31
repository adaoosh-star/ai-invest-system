#!/bin/bash
# 测试三个交易日报告脚本
# 用法：./test_cron_reports.sh

echo "======================================"
echo "AI 价值投资系统 - 交易日报告测试"
echo "======================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "测试环境："
echo "- 工作目录：$(pwd)"
echo "- Python 版本：$(python3 --version)"
echo "- 测试时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 测试盘前报告
echo "======================================"
echo "1️⃣  测试盘前预判报告"
echo "======================================"
python3 agents/premarket_report.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 盘前报告 - 执行成功"
    echo "📁 报告位置：cache/premarket_*.md"
    ls -lt cache/premarket_*.md 2>/dev/null | head -1 | awk '{print "   最新文件:", $NF, "("$5, "bytes)")}'
else
    echo "❌ 盘前报告 - 执行失败"
fi
echo ""

# 测试集合竞价报告
echo "======================================"
echo "2️⃣  测试集合竞价报告"
echo "======================================"
python3 agents/auction_report.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 集合竞价报告 - 执行成功"
    echo "📁 报告位置：cache/auction_*.md"
    ls -lt cache/auction_*.md 2>/dev/null | head -1 | awk '{print "   最新文件:", $NF, "("$5, "bytes)")}'
else
    echo "❌ 集合竞价报告 - 执行失败"
fi
echo ""

# 测试盘后报告
echo "======================================"
echo "3️⃣  测试盘后复盘报告"
echo "======================================"
python3 agents/postmarket_report.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 盘后复盘报告 - 执行成功"
    echo "📁 报告位置：cache/postmarket_*.md"
    ls -lt cache/postmarket_*.md 2>/dev/null | head -1 | awk '{print "   最新文件:", $NF, "("$5, "bytes)")}'
else
    echo "❌ 盘后复盘报告 - 执行失败"
fi
echo ""

# 测试持仓监控（已有功能）
echo "======================================"
echo "4️⃣  测试持仓监控（已有功能）"
echo "======================================"
python3 monitor/holding_monitor.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 持仓监控 - 执行成功"
    echo "📁 报告位置：cache/holding_report_*.md"
    ls -lt cache/holding_report_*.md 2>/dev/null | head -1 | awk '{print "   最新文件:", $NF, "("$5, "bytes)")}'
else
    echo "❌ 持仓监控 - 执行失败"
fi
echo ""

# 汇总
echo "======================================"
echo "📊 测试汇总"
echo "======================================"
echo ""
echo "Cron 任务列表："
crontab -l | grep -E "^(30 8|25 9|0,30 9|30 15)" | sed 's/^/  /'
echo ""
echo "✅ 所有报告脚本测试完成！"
echo ""
echo "下次执行时间："
echo "  - 盘前报告：下一个交易日 08:30"
echo "  - 集合竞价：下一个交易日 09:25"
echo "  - 持仓监控：交易时间每 30 分钟"
echo "  - 盘后报告：下一个交易日 15:30"
echo ""
