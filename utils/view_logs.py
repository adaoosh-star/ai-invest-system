#!/usr/bin/env python3
"""
日志查看工具

用法：
    python3 utils/view_logs.py              # 查看所有日志文件
    python3 utils/view_logs.py holding      # 查看持仓监控日志
    python3 utils/view_logs.py --tail 50    # 查看最后 50 行
    python3 utils/view_logs.py --clean      # 清理 30 天前的日志
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import LOG_DIR, cleanup_old_logs


def list_logs():
    """列出所有日志文件"""
    print(f"📁 日志目录：{LOG_DIR}\n")
    
    log_files = sorted(LOG_DIR.glob('*.log*'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not log_files:
        print("暂无日志文件")
        return
    
    print(f"{'文件名':<40} {'大小':<10} {'修改时间'}")
    print("-" * 70)
    
    for log_file in log_files:
        size = log_file.stat().st_size
        size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        print(f"{log_file.name:<40} {size_str:<10} {mtime}")


def view_log(name: str, lines: int = 50):
    """查看指定日志文件"""
    log_file = LOG_DIR / f'{name}.log'
    
    if not log_file.exists():
        # 尝试查找匹配的日志文件
        matches = list(LOG_DIR.glob(f'{name}*.log*'))
        if matches:
            log_file = matches[0]
        else:
            print(f"❌ 日志文件不存在：{name}")
            print("\n可用日志：")
            list_logs()
            return
    
    print(f"📄 查看日志：{log_file.name}\n")
    print("-" * 70)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            for line in last_lines:
                print(line, end='')
            
            print("-" * 70)
            print(f"\n共 {len(all_lines)} 行，显示最后 {min(lines, len(all_lines))} 行")
    
    except Exception as e:
        print(f"❌ 读取失败：{e}")


def clean_logs(days: int = 30):
    """清理旧日志"""
    print(f"🧹 清理 {days} 天前的日志...\n")
    cleanup_old_logs(days)
    print("\n✅ 清理完成")


def main():
    parser = argparse.ArgumentParser(
        description='日志查看工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 utils/view_logs.py              # 查看所有日志文件
  python3 utils/view_logs.py holding      # 查看持仓监控日志
  python3 utils/view_logs.py --tail 100   # 查看最后 100 行
  python3 utils/view_logs.py --clean      # 清理 30 天前的日志
        """
    )
    
    parser.add_argument(
        'name',
        nargs='?',
        default=None,
        help='日志文件名（不含扩展名）'
    )
    
    parser.add_argument(
        '--tail', '-n',
        type=int,
        default=50,
        help='显示最后 N 行（默认 50）'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='清理 30 天前的日志'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='清理 N 天前的日志（默认 30）'
    )
    
    args = parser.parse_args()
    
    if args.clean:
        clean_logs(args.days)
    elif args.name:
        view_log(args.name, args.tail)
    else:
        list_logs()


if __name__ == '__main__':
    main()
