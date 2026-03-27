"""
日志系统配置

功能：
- 按日期自动分割日志文件
- 支持不同级别（DEBUG/INFO/WARNING/ERROR）
- 自动清理 30 天前的日志
- 统一日志格式
"""

import logging
import os
from pathlib import Path
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler

# 日志目录
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

class LoggerConfig:
    """日志配置类"""
    
    @staticmethod
    def get_logger(name: str, level=logging.INFO) -> logging.Logger:
        """
        获取日志记录器
        
        参数：
        - name: 日志名称（通常是模块名）
        - level: 日志级别
        
        返回：
        - logging.Logger 实例
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重复添加 handler
        if logger.handlers:
            return logger
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. 文件日志（按天轮转，保留 30 天）
        log_file = LOG_DIR / f'{name}.log'
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='D',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.suffix = '%Y%m%d'
        logger.addHandler(file_handler)
        
        # 2. 控制台日志（仅 ERROR 级别）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    @staticmethod
    def cleanup_old_logs(days: int = 30):
        """
        清理旧日志文件
        
        参数：
        - days: 保留天数，默认 30 天
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        for log_file in LOG_DIR.glob('*.log*'):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff:
                    log_file.unlink()
                    print(f"已删除旧日志：{log_file}")
            except Exception as e:
                print(f"删除日志失败 {log_file}: {e}")


# 快捷函数
def get_logger(name: str, level=logging.INFO) -> logging.Logger:
    """获取日志记录器（快捷方式）"""
    return LoggerConfig.get_logger(name, level)


def cleanup_old_logs(days: int = 30):
    """清理旧日志（快捷方式）"""
    LoggerConfig.cleanup_old_logs(days)


# 测试
if __name__ == '__main__':
    logger = get_logger('test')
    logger.debug('调试信息')
    logger.info('普通信息')
    logger.warning('警告信息')
    logger.error('错误信息')
    print(f"日志文件位置：{LOG_DIR}")
