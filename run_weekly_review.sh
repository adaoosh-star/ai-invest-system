#!/bin/bash
# 周复盘自动化运行脚本
# 用法：./run_weekly_review.sh
# 定时任务：每周五 20:00 运行（Tushare 数据更新后）

set -e

# 切换到项目目录
cd "$(dirname "$0")"

# 激活虚拟环境（如果有）
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 运行周复盘
echo "🦀 开始生成周复盘报告..."
python3 review/weekly_review.py

# 输出结果
echo ""
echo "✅ 周复盘完成！"
echo "报告位置：cache/review/weekly_review_$(date +%Y%m%d).md"
