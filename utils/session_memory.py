"""
投资系统记忆模块 v2.0

功能：
- 分析历史记忆 - 记录每次分析的结论和依据
- 决策记忆 - 买入/卖出决策的逻辑和结果
- 承诺追踪记忆 - 跨年度的承诺兑现追踪

稳定性保障：
- 独立新模块，不影响现有功能
- 配置开关控制
- 自动清理过期记忆（30 天 TTL）
"""

import sys
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
logger = get_logger('memory_system')

# 加载 P0 配置
P0_CONFIG_PATH = PROJECT_ROOT / 'config' / 'p0_config.yaml'
with open(P0_CONFIG_PATH, 'r', encoding='utf-8') as f:
    p0_config = yaml.safe_load(f)

# 记忆目录
MEMORY_CONFIG = p0_config.get('memory_system', {})
MEMORY_DIR = PROJECT_ROOT / MEMORY_CONFIG.get('memory_dir', 'memory/')
RETENTION_DAYS = MEMORY_CONFIG.get('retention_days', 30)


class InvestmentMemory:
    """投资系统记忆管理类"""
    
    def __init__(self):
        """初始化记忆系统"""
        self.memory_dir = MEMORY_DIR
        self.retention_days = RETENTION_DAYS
        self.enabled = MEMORY_CONFIG.get('enabled', True)
        
        # 确保目录存在
        if self.enabled:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"记忆系统已初始化：{self.memory_dir}")
    
    def save_analysis(self, ts_code: str, stock_name: str, conclusion: dict, 
                      report_path: str = None, metadata: dict = None):
        """
        保存分析历史
        
        Args:
            ts_code: 股票代码
            stock_name: 股票名称
            conclusion: 分析结论（评级、通过率等）
            report_path: 完整报告路径
            metadata: 额外元数据
        """
        if not self.enabled:
            return
        
        memory_entry = {
            'type': 'analysis',
            'timestamp': datetime.now().isoformat(),
            'stock': {
                'code': ts_code,
                'name': stock_name,
            },
            'conclusion': conclusion,
            'report_path': report_path,
            'metadata': metadata or {},
        }
        
        # 保存到文件
        date_str = datetime.now().strftime('%Y-%m-%d')
        filepath = self.memory_dir / f"{date_str}_analysis.jsonl"
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(memory_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"分析记忆已保存：{ts_code} {stock_name}")
        return filepath
    
    def save_decision(self, ts_code: str, stock_name: str, decision_type: str,
                      decision: str, reasoning: str, expected_outcome: str = None):
        """
        保存决策记录
        
        Args:
            ts_code: 股票代码
            stock_name: 股票名称
            decision_type: 决策类型（买入/卖出/持仓/观望）
            decision: 具体决策
            reasoning: 决策逻辑
            expected_outcome: 预期结果
        """
        if not self.enabled:
            return
        
        memory_entry = {
            'type': 'decision',
            'timestamp': datetime.now().isoformat(),
            'stock': {
                'code': ts_code,
                'name': stock_name,
            },
            'decision': {
                'type': decision_type,
                'content': decision,
                'reasoning': reasoning,
                'expected_outcome': expected_outcome,
            },
        }
        
        # 保存到文件
        date_str = datetime.now().strftime('%Y-%m-%d')
        filepath = self.memory_dir / f"{date_str}_decision.jsonl"
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(memory_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"决策记忆已保存：{ts_code} {decision_type}")
        return filepath
    
    def save_promise(self, ts_code: str, stock_name: str, promise_text: str,
                     promise_date: str, expected_deadline: str = None, 
                     promise_type: str = '业绩承诺'):
        """
        保存承诺追踪
        
        Args:
            ts_code: 股票代码
            stock_name: 股票名称
            promise_text: 承诺内容
            promise_date: 承诺日期
            expected_deadline: 预期完成期限
            promise_type: 承诺类型（业绩承诺/增持承诺/其他）
        """
        if not self.enabled:
            return
        
        memory_entry = {
            'type': 'promise',
            'timestamp': datetime.now().isoformat(),
            'stock': {
                'code': ts_code,
                'name': stock_name,
            },
            'promise': {
                'text': promise_text,
                'date': promise_date,
                'deadline': expected_deadline,
                'type': promise_type,
                'status': 'pending',  # pending/fulfilled/failed
            },
        }
        
        # 保存到文件
        date_str = datetime.now().strftime('%Y-%m-%d')
        filepath = self.memory_dir / f"{date_str}_promise.jsonl"
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(memory_entry, ensure_ascii=False) + '\n')
        
        logger.info(f"承诺记忆已保存：{ts_code} {promise_type}")
        return filepath
    
    def get_analysis_history(self, ts_code: str, days: int = 30) -> list:
        """
        获取股票分析历史
        
        Args:
            ts_code: 股票代码
            days: 查询天数
        
        Returns:
            list: 分析历史记录
        """
        if not self.enabled:
            return []
        
        history = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 扫描记忆文件
        for filepath in self.memory_dir.glob('*_analysis.jsonl'):
            file_date = datetime.strptime(filepath.stem.split('_')[0], '%Y-%m-%d')
            if file_date < cutoff_date:
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('stock', {}).get('code') == ts_code:
                            history.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        # 按时间排序
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        logger.info(f"查询分析历史：{ts_code}，找到 {len(history)} 条记录")
        return history
    
    def get_decision_history(self, ts_code: str, days: int = 30) -> list:
        """
        获取股票决策历史
        """
        if not self.enabled:
            return []
        
        history = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for filepath in self.memory_dir.glob('*_decision.jsonl'):
            file_date = datetime.strptime(filepath.stem.split('_')[0], '%Y-%m-%d')
            if file_date < cutoff_date:
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('stock', {}).get('code') == ts_code:
                            history.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        logger.info(f"查询决策历史：{ts_code}，找到 {len(history)} 条记录")
        return history
    
    def get_pending_promises(self, ts_code: str = None) -> list:
        """
        获取待追踪承诺
        
        Args:
            ts_code: 可选，查询特定股票
        
        Returns:
            list: 待追踪承诺列表
        """
        if not self.enabled:
            return []
        
        promises = []
        
        for filepath in self.memory_dir.glob('*_promise.jsonl'):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('promise', {}).get('status') == 'pending':
                            if ts_code is None or entry.get('stock', {}).get('code') == ts_code:
                                promises.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        promises.sort(key=lambda x: x.get('promise', {}).get('deadline', ''))
        logger.info(f"查询待追踪承诺：找到 {len(promises)} 条记录")
        return promises
    
    def auto_purge(self):
        """
        自动清理过期记忆（TTL）
        """
        if not self.enabled:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        purged_count = 0
        
        for filepath in self.memory_dir.glob('*.jsonl'):
            try:
                file_date = datetime.strptime(filepath.stem.split('_')[0], '%Y-%m-%d')
                if file_date < cutoff_date:
                    filepath.unlink()
                    purged_count += 1
                    logger.info(f"清理过期记忆：{filepath.name}")
            except (ValueError, OSError) as e:
                logger.warning(f"清理失败 {filepath}: {e}")
        
        logger.info(f"记忆清理完成：清理 {purged_count} 个文件")
        return purged_count
    
    def get_memory_stats(self) -> dict:
        """
        获取记忆统计
        """
        if not self.enabled:
            return {'enabled': False}
        
        stats = {
            'enabled': True,
            'memory_dir': str(self.memory_dir),
            'retention_days': self.retention_days,
            'files': {},
            'total_entries': 0,
        }
        
        for filepath in self.memory_dir.glob('*.jsonl'):
            file_type = filepath.stem.split('_')[1] if '_' in filepath.stem else 'unknown'
            if file_type not in stats['files']:
                stats['files'][file_type] = {'files': 0, 'entries': 0}
            
            stats['files'][file_type]['files'] += 1
            
            # 统计条目数
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    entry_count = sum(1 for _ in f)
                stats['files'][file_type]['entries'] += entry_count
                stats['total_entries'] += entry_count
            except OSError:
                continue
        
        return stats


# 全局实例
_memory_instance = None


def get_memory() -> InvestmentMemory:
    """获取记忆系统实例"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = InvestmentMemory()
    return _memory_instance


# CLI 入口
if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"投资系统记忆模块 v2.0 - 测试")
    print(f"{'='*60}\n")
    
    memory = get_memory()
    
    # 测试保存分析
    print("测试：保存分析记忆...")
    memory.save_analysis(
        ts_code='002270.SZ',
        stock_name='华明装备',
        conclusion={'recommendation': '可买入', 'pass_rate': 0.85},
        report_path='cache/analysis/002270_20260407.md',
        metadata={'analyst': '小蟹'}
    )
    
    # 测试保存决策
    print("测试：保存决策记忆...")
    memory.save_decision(
        ts_code='002270.SZ',
        stock_name='华明装备',
        decision_type='买入',
        decision='建仓 1000 股',
        reasoning='20 项检查通过率 85%，PE 分位 30%，符合投资宪法',
        expected_outcome='长期持有，享受公司成长'
    )
    
    # 测试查询历史
    print("测试：查询分析历史...")
    history = memory.get_analysis_history('002270.SZ', days=30)
    print(f"找到 {len(history)} 条分析记录")
    
    # 测试统计
    print("测试：记忆统计...")
    stats = memory.get_memory_stats()
    print(f"记忆系统状态：{json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    print(f"\n{'='*60}")
    print(f"✅ 记忆模块测试完成")
    print(f"{'='*60}\n")
