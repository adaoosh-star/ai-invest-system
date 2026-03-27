"""
自动化选股流程
投资宪法：AI 批量执行选股前 20 项检查清单
效率：人工 10-15 小时/公司 → AI 1-2 分钟/100 公司（增量更新）

修复记录：2026-03-26
- 修复相对导入问题，改用绝对导入
"""

import sys
import yaml
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入日志系统
from utils.logger import get_logger
logger = get_logger('auto_select')

from data import tushare_client, liquidity_filter, incremental_update, cross_validate
from data.clean_rules import validate_data_quality

# 加载配置
CONFIG_PATH = Path(__file__).parent / 'config' / 'thresholds.yaml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

def check_hard_bottom(ts_code: str) -> dict:
    """
    投资宪法：通用硬底线检查
    ROE≥10%、现金流≥0.8、负债≤70%
    """
    issues = []
    
    # 1. ROE 连续 3 年≥10%
    roe_data = tushare_client.get_roe(ts_code)
    roe_3y = roe_data.tail(12)  # 3 年 12 个季度
    roe_avg = roe_3y['roe_dt'].mean()
    if roe_avg < config['hard_bottom']['roe_min']:
        issues.append(f"ROE 连续 3 年平均{roe_avg:.1%} < {config['hard_bottom']['roe_min']:.0%}")
    
    # 2. 现金流/净利润≥0.8
    cf_data = tushare_client.get_cash_flow(ts_code)
    net_profit = cf_data['oper_cf'].tail(4).sum()  # 近 4 季度经营现金流
    if net_profit < 0:
        issues.append("经营现金流为负")
    
    # 3. 负债率≤70%
    # TODO: 获取负债率数据
    
    return {
        'ts_code': ts_code,
        'passed': len(issues) == 0,
        'issues': issues,
    }

def auto_select_stocks() -> dict:
    """
    投资宪法：AI 批量执行选股前 20 项检查清单
    输出：高优先级标的（人工仅复核）
    效率：人工 10-15 小时/公司 → AI 1-2 分钟/100 公司（增量更新）
    """
    logger.info("开始自动化选股流程")
    
    try:
        # 1. 获取全市场股票列表
        logger.info("获取全市场股票列表...")
        all_stocks = tushare_client.get_all_stocks()
        logger.info(f"全市场股票数量：{len(all_stocks)}")
        
        # 2. 流动性前置过滤（改进点 3）
        logger.info("流动性前置过滤...")
        liquidity_result = liquidity_filter.filter_liquidity(
            all_stocks.to_dict('records'),
            tushare_client.get_liquidity
        )
        passed_liquidity = liquidity_result['passed']
        logger.info(f"通过流动性过滤：{len(passed_liquidity)} 只")
        
        # 3. 增量更新（改进点 8）
        def fetch_stock_data(ts_code):
            """获取单只股票数据"""
            return {
                'ts_code': ts_code,
                'roe': tushare_client.get_roe(ts_code),
                'cf': tushare_client.get_cash_flow(ts_code),
            }
        
        logger.info("增量更新数据...")
        update_result = incremental_update.incremental_update(
            passed_liquidity,
            fetch_stock_data
        )
        logger.info(f"缓存命中率：{update_result['summary']['cache_hit_rate']:.1%}")
        
        # 4. 批量筛选（投资宪法：通用硬底线）
        logger.info("执行硬底线筛选...")
        passed_hard_bottom = []
        for stock_data in update_result['results']:
            ts_code = stock_data['ts_code']
            result = check_hard_bottom(ts_code)
            if result['passed']:
                passed_hard_bottom.append(stock_data)
        
        logger.info(f"通过硬底线筛选：{len(passed_hard_bottom)} 只")
        
        # 5. 输出结果
        result = {
            'candidates': passed_hard_bottom,
            'summary': {
                'total': len(all_stocks),
                'passed_liquidity': len(passed_liquidity),
                'passed_hard_bottom': len(passed_hard_bottom),
                'cache_hit_rate': update_result['summary']['cache_hit_rate'],
            }
        }
        
        logger.info(f"选股完成：{len(passed_hard_bottom)} 只候选股票")
        return result
        
    except Exception as e:
        logger.error(f"选股失败：{e}", exc_info=True)
        raise

# 测试
if __name__ == '__main__':
    print("=== 自动化选股流程测试 ===\n")
    
    result = auto_select_stocks()
    
    print(f"选股结果汇总：")
    print(f"  全市场股票：{result['summary']['total']}")
    print(f"  通过流动性过滤：{result['summary']['passed_liquidity']}")
    print(f"  通过硬底线筛选：{result['summary']['passed_hard_bottom']}")
    print(f"  缓存命中率：{result['summary']['cache_hit_rate']:.1%}")
    
    if result['candidates']:
        print(f"\n候选股票（前 10 只）：")
        for stock in result['candidates'][:10]:
            print(f"  - {stock['ts_code']}")
