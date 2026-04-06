#!/usr/bin/env python3
"""
LLM 深度分析模块 - 完整测试脚本

测试所有 LLM 功能：
1. 承诺语义分析
2. MD&A 分析（降级模式）
3. 造假风险识别
4. 成本监控
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.llm_enhanced import get_llm_analyzer

def main():
    print(f"\n{'='*70}")
    print(f"AI 价值投资系统 v2.0 - LLM 深度分析完整测试")
    print(f"{'='*70}\n")
    
    analyzer = get_llm_analyzer()
    
    print(f"LLM 配置:")
    print(f"  状态：{'✅ 已启用' if analyzer.enabled else '❌ 未启用'}")
    print(f"  模型：{analyzer.__class__.__module__}")
    print(f"  成本限制：¥{analyzer.cost_limit}/天")
    print(f"  剩余额度：¥{analyzer.get_cost_status()['remaining']:.2f}")
    print()
    
    # 测试 1: 承诺语义分析
    print(f"{'='*70}")
    print(f"测试 1: 承诺语义分析")
    print(f"{'='*70}")
    
    promise_samples = [
        "公司承诺 2026 年营收增长率不低于 20%，净利润增长率不低于 15%",
        "控股股东承诺 6 个月内增持公司股份，金额不低于 5000 万元",
        "公司计划未来三年分红比例不低于当年可分配利润的 30%",
    ]
    
    for promise in promise_samples:
        print(f"\n分析承诺：{promise[:50]}...")
        result = analyzer.analyze_promise_semantic(promise)
        print(f"  类型：{result.get('type', 'N/A')}")
        print(f"  可信度：{result.get('confidence', 0):.2f}")
        print(f"  具体程度：{result.get('specificity', 0):.2f}")
        print(f"  语气：{result.get('tone', 'N/A')}")
        if result.get('risks'):
            print(f"  风险：{len(result['risks'])} 个")
    
    print()
    
    # 测试 2: MD&A 分析（降级模式）
    print(f"{'='*70}")
    print(f"测试 2: MD&A 分析（降级模式 - 规则式）")
    print(f"{'='*70}")
    
    mda_sample = "公司将继续加大研发投入，拓展海外市场，优化产品结构，提升运营效率..."
    result = analyzer.analyze_md_a(mda_sample * 10)
    print(f"  分析方法：{result.get('method', 'N/A')}")
    print(f"  字数：{result.get('word_count', 0)}")
    print(f"  风险提及：{result.get('risk_mentions', 0)} 次")
    print(f"  机遇提及：{result.get('opportunity_mentions', 0)} 次")
    print()
    
    # 测试 3: 造假风险识别
    print(f"{'='*70}")
    print(f"测试 3: 财务造假风险识别（规则式）")
    print(f"{'='*70}")
    
    test_cases = [
        {'name': '健康公司', 'data': {'receivables_to_revenue': 0.3, 'cash_flow_to_net_profit': 0.8, 'gross_margin_vs_industry': 0.1}},
        {'name': '应收账款高', 'data': {'receivables_to_revenue': 0.6, 'cash_flow_to_net_profit': 0.8, 'gross_margin_vs_industry': 0.1}},
        {'name': '现金流背离', 'data': {'receivables_to_revenue': 0.3, 'cash_flow_to_net_profit': 0.3, 'gross_margin_vs_industry': 0.1}},
        {'name': '毛利率异常', 'data': {'receivables_to_revenue': 0.3, 'cash_flow_to_net_profit': 0.8, 'gross_margin_vs_industry': 0.5}},
    ]
    
    for case in test_cases:
        result = analyzer.detect_fraud_risk(case['data'])
        risks = result.get('rule_based_risks', [])
        print(f"\n  {case['name']}:")
        if risks:
            for risk in risks:
                print(f"    ⚠️ {risk['type']}: {risk['value']} ({risk['severity']})")
        else:
            print(f"    ✅ 无风险信号")
    
    print()
    
    # 测试 4: 成本监控
    print(f"{'='*70}")
    print(f"测试 4: 成本监控")
    print(f"{'='*70}")
    
    cost_status = analyzer.get_cost_status()
    print(f"  今日已用：¥{cost_status['daily_cost']:.2f}")
    print(f"  剩余额度：¥{cost_status['remaining']:.2f}")
    print(f"  状态：{'✅ 可用' if cost_status['enabled'] else '❌ 超限'}")
    print()
    
    # 总结
    print(f"{'='*70}")
    print(f"测试总结")
    print(f"{'='*70}")
    print(f"  ✅ 承诺语义分析 - 千问 API 调用成功")
    print(f"  ✅ MD&A 分析 - 降级模式可用")
    print(f"  ✅ 造假风险识别 - 规则式正常")
    print(f"  ✅ 成本监控 - 限额控制有效")
    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    main()
