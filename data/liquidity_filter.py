"""
流动性前置过滤
改进点 3：近 20 日日均成交额≥5000 万，直接排除流动性差的小票
"""

import yaml
from pathlib import Path

# 加载配置
CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'thresholds.yaml'
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

def filter_liquidity(stocks: list, get_avg_volume_func) -> list:
    """
    改进点 3：流动性前置过滤
    
    在初选阶段就筛掉日均成交<5000 万的股票
    避免后续做无用的分析
    """
    min_volume = config['hard_bottom']['avg_volume_min']  # 5000 万
    
    passed = []
    filtered_out = []
    
    for stock in stocks:
        ts_code = stock['ts_code']
        avg_volume = get_avg_volume_func(ts_code, days=20)
        
        if avg_volume >= min_volume:
            passed.append({
                **stock,
                'avg_volume': avg_volume,
            })
        else:
            filtered_out.append({
                **stock,
                'avg_volume': avg_volume,
                'reason': f"日均成交{avg_volume/1e8:.2f}亿 < {min_volume/1e8:.2f}亿",
            })
    
    return {
        'passed': passed,
        'filtered_out': filtered_out,
        'summary': {
            'total': len(stocks),
            'passed': len(passed),
            'filtered_out': len(filtered_out),
            'pass_rate': len(passed) / len(stocks) if len(stocks) > 0 else 0,
        }
    }

# 测试
if __name__ == '__main__':
    # 模拟股票列表
    stocks = [
        {'ts_code': '002270.SZ', 'name': '华明装备'},
        {'ts_code': '000001.SZ', 'name': '平安银行'},
        {'ts_code': '600519.SH', 'name': '贵州茅台'},
        {'ts_code': '000858.SZ', 'name': '五粮液'},
    ]
    
    # 模拟获取日均成交额函数
    def mock_get_avg_volume(ts_code, days=20):
        volumes = {
            '002270.SZ': 1e8,  # 1 亿
            '000001.SZ': 5e8,  # 5 亿
            '600519.SH': 20e8,  # 20 亿
            '000858.SZ': 15e8,  # 15 亿
        }
        return volumes.get(ts_code, 0)
    
    result = filter_liquidity(stocks, mock_get_avg_volume)
    
    print(f"流动性过滤结果：")
    print(f"  总计：{result['summary']['total']}")
    print(f"  通过：{result['summary']['passed']}")
    print(f"  过滤：{result['summary']['filtered_out']}")
    print(f"  通过率：{result['summary']['pass_rate']:.1%}")
    
    if result['filtered_out']:
        print(f"\n过滤掉的股票：")
        for stock in result['filtered_out']:
            print(f"  - {stock['name']} ({stock['ts_code']}): {stock['reason']}")
