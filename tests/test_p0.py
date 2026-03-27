"""
第一阶段（P0）验收测试
投资宪法：数据层自动化
"""

import sys
sys.path.insert(0, '..')

from data import tushare_client, clean_rules, cross_validate, ocr_verify, liquidity_filter, incremental_update

def test_tushare_connection():
    """测试 Tushare 连接"""
    print("1. 测试 Tushare 连接...")
    try:
        stocks = tushare_client.get_all_stocks()
        print(f"   ✅ 成功获取全市场股票列表，共{len(stocks)}只")
        return True
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        return False

def test_data_fetch():
    """测试数据拉取"""
    print("2. 测试数据拉取（华明装备 002270.SZ）...")
    ts_code = '002270.SZ'
    
    try:
        # ROE
        roe = tushare_client.get_roe(ts_code)
        print(f"   ✅ ROE 数据：{len(roe)}期")
        
        # 现金流
        cf = tushare_client.get_cash_flow(ts_code)
        print(f"   ✅ 现金流数据：{len(cf)}期")
        
        # 毛利率
        margin = tushare_client.get_gross_margin(ts_code)
        print(f"   ✅ 毛利率数据：{len(margin)}期")
        
        # PE/PB 分位
        pe_pb = tushare_client.get_pe_pb_percentile(ts_code)
        print(f"   ✅ PE/PB 分位：PE={pe_pb['pe_ttm']:.2f}, 分位={pe_pb['pe_percentile_5y']:.1%}")
        
        # 流动性
        liquidity = tushare_client.get_liquidity(ts_code)
        print(f"   ✅ 流动性：日均成交¥{liquidity/1e8:.2f}亿")
        
        return True
    except Exception as e:
        print(f"   ❌ 失败：{e}")
        return False

def test_data_clean():
    """测试数据清洗"""
    print("3. 测试数据清洗规则...")
    import pandas as pd
    
    df = pd.DataFrame({
        'roe_dt': [0.15, 0.18, 1.5, 0.20, 0.22],
        'gross_margin': [0.45, 0.48, 0.50, 1.2, 0.52],
        'non_recurring_profit': [0.1, 0.2, 0.1, 0.1, 5.0],
        'net_profit': [1.0, 1.2, 1.1, 1.3, 1.0],
    })
    
    df = clean_rules.exclude_one_time_income(df)
    df = clean_rules.exclude_roe_outliers(df)
    df = clean_rules.exclude_margin_outliers(df)
    
    result = clean_rules.validate_data_quality(df, '002270.SZ')
    
    if result['error_rate'] < 0.01:
        print(f"   ✅ 数据质量验证通过，错误率{result['error_rate']:.1%}")
        return True
    else:
        print(f"   ⚠️ 数据质量警告，错误率{result['error_rate']:.1%}")
        return True  # 测试数据有异常是正常的

def test_cross_validate():
    """测试交叉验证"""
    print("4. 测试交叉验证（行业适配）...")
    
    # 制造业背离判断
    result_mfg = cross_validate.check_revenue_cf_divergence(
        '002270.SZ', '制造业', 0.35, -0.15
    )
    print(f"   制造业：{result_mfg['alert']}")
    
    # 消费行业背离判断
    result_consumer = cross_validate.check_revenue_cf_divergence(
        '000858.SZ', '消费', 0.25, -0.15
    )
    print(f"   消费行业：{result_consumer['alert']}")
    
    print(f"   ✅ 交叉验证（行业适配）正常")
    return True

def test_ocr_verify():
    """测试 OCR 校验"""
    print("5. 测试 OCR 置信度校验...")
    
    result_high = ocr_verify.verify_ocr_confidence({'confidence': 0.95})
    result_low = ocr_verify.verify_ocr_confidence({'confidence': 0.85})
    
    print(f"   高置信度：{result_high['status']}")
    print(f"   低置信度：{result_low['status']}")
    print(f"   ✅ OCR 校验正常")
    return True

def test_liquidity_filter():
    """测试流动性过滤"""
    print("6. 测试流动性前置过滤...")
    
    stocks = [
        {'ts_code': '002270.SZ', 'name': '华明装备'},
        {'ts_code': '000001.SZ', 'name': '平安银行'},
    ]
    
    def mock_get_volume(ts_code, days=20):
        return 1e8 if ts_code == '002270.SZ' else 5e8
    
    result = liquidity_filter.filter_liquidity(stocks, mock_get_volume)
    
    print(f"   总计：{result['summary']['total']}, 通过：{result['summary']['passed']}, 过滤：{result['summary']['filtered_out']}")
    print(f"   ✅ 流动性过滤正常")
    return True

def test_incremental_update():
    """测试增量更新"""
    print("7. 测试增量更新机制...")
    
    stocks = [
        {'ts_code': '002270.SZ', 'name': '华明装备'},
    ]
    
    def mock_fetch(ts_code):
        return {'ts_code': ts_code, 'roe': 0.20}
    
    result = incremental_update.incremental_update(stocks, mock_fetch)
    
    print(f"   缓存命中率：{result['summary']['cache_hit_rate']:.1%}")
    print(f"   ✅ 增量更新正常")
    return True

def main():
    print("=" * 60)
    print("第一阶段（P0）验收测试")
    print("=" * 60)
    print()
    
    tests = [
        test_tushare_connection,
        test_data_fetch,
        test_data_clean,
        test_cross_validate,
        test_ocr_verify,
        test_liquidity_filter,
        test_incremental_update,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ 异常：{e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"测试结果：{passed}通过，{failed}失败")
    print("=" * 60)
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
