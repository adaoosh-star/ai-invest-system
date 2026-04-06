"""
决策引擎 v2.0 - 投资宪法 2.0 核心

功能：
- 买入决策（量化评分）
- 卖出决策（触发条件）
- 补仓/减仓决策
- 持仓监控决策

稳定性保障：
- 独立新模块，不影响现有 dual_threshold.py
- 配置开关控制
- 降级方案（评分失败时用规则）
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
logger = get_logger('decision_engine_v2')

# 加载配置
CONFIG_PATH = PROJECT_ROOT / 'config' / 'investment_constitution_v2.yaml'


class DecisionEngine:
    """决策引擎 v2.0"""
    
    def __init__(self):
        """初始化决策引擎"""
        self.config = self._load_config()
        self.enabled = self.config.get('enabled', True)
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            # 默认配置
            return self._default_config()
    
    def _default_config(self) -> dict:
        """默认配置"""
        return {
            'enabled': True,
            'buy': {
                'checklist_pass_rate_min': 0.75,
                'hard_bottom_required': True,
                'pe_percentile_max': 0.80,
                'safety_margin_discount': 0.80,
            },
            'sell': {
                'pe_percentile_sell': 0.95,
                'peg_sell': 2.0,
                'roe_decline_years': 2,
            },
            'scoring': {
                'weights': {
                    'checklist_pass_rate': 0.30,
                    'roe_score': 0.25,
                    'cash_flow_score': 0.20,
                    'valuation_score': 0.15,
                    'growth_score': 0.10,
                },
                'thresholds': {
                    'strong_buy': 0.85,
                    'buy': 0.70,
                    'hold': 0.50,
                }
            }
        }
    
    def make_buy_decision(self, ts_code: str, stock_name: str, industry: str,
                          financial_data: dict, checklist_result: dict,
                          risk_check_result: dict, current_pe_percentile: float,
                          current_price: float, target_buy_price: float) -> dict:
        """
        买入决策
        
        Args:
            ts_code: 股票代码
            stock_name: 股票名称
            industry: 所属行业
            financial_data: 财务数据
            checklist_result: 20 项检查结果
            risk_check_result: A 股风险检查结果
            current_pe_percentile: 当前 PE 分位
            current_price: 当前价格
            target_buy_price: 目标买入价
        
        Returns:
            dict: 决策结果
        """
        if not self.enabled:
            return {'decision': '观望', 'reason': '决策引擎未启用'}
        
        logger.info(f"买入决策：{stock_name} ({ts_code})")
        
        # 1. 前置条件检查
        prereq_result = self._check_buy_prerequisites(
            checklist_result, risk_check_result, financial_data
        )
        if not prereq_result['passed']:
            return {
                'decision': '避免',
                'score': 0.0,
                'level': '避免',
                'reasons': prereq_result['issues'],
                'risks': []
            }
        
        # 2. 估值检查
        valuation_ok = self._check_valuation(
            current_pe_percentile,
            self.config['buy'].get('pe_percentile_max', 0.80)
        )
        if not valuation_ok:
            return {
                'decision': '观望',
                'score': 0.5,
                'level': '观望',
                'reasons': ['估值过高'],
                'risks': [f'PE 分位{current_pe_percentile:.0%} > 80%']
            }
        
        # 3. 决策评分
        score = self._calculate_buy_score(
            checklist_result, financial_data, current_pe_percentile
        )
        
        # 4. 决策阈值
        thresholds = self.config['scoring']['thresholds']
        if score >= thresholds['strong_buy']:
            decision = '买入'
            level = '强烈推荐'
        elif score >= thresholds['buy']:
            decision = '买入'
            level = '推荐买入'
        elif score >= thresholds['hold']:
            decision = '观望'
            level = '观望'
        else:
            decision = '避免'
            level = '避免'
        
        # 5. 生成原因
        reasons = self._generate_buy_reasons(checklist_result, financial_data)
        risks = self._generate_buy_risks(financial_data)
        
        # 6. 建议仓位
        recommended_position = self._calculate_recommended_position(score, level)
        
        return {
            'decision': decision,
            'score': score,
            'level': level,
            'reasons': reasons,
            'risks': risks,
            'recommended_position': recommended_position,
            'target_price': target_buy_price,
            'current_price': current_price,
        }
    
    def _check_buy_prerequisites(self, checklist_result: dict,
                                  risk_check_result: dict,
                                  financial_data: dict) -> dict:
        """前置条件检查"""
        issues = []
        passed = True
        
        # 1. 20 项检查通过率
        pass_rate = checklist_result.get('pass_rate', 0)
        min_pass_rate = self.config['buy'].get('checklist_pass_rate_min', 0.75)
        if pass_rate < min_pass_rate:
            issues.append(f"20 项检查通过率{pass_rate:.0%} < {min_pass_rate:.0%}")
            passed = False
        
        # 2. A 股风险检查
        if risk_check_result.get('has_red_risk', False):
            issues.append("存在红色风险")
            passed = False
        
        # 3. 流动性检查
        avg_volume = financial_data.get('avg_volume', 0)
        if avg_volume < 50000000:
            issues.append(f"日均成交{avg_volume/10000:.0f}万 < 5000 万")
            passed = False
        
        return {'passed': passed, 'issues': issues}
    
    def _check_valuation(self, pe_percentile: float, max_pe: float) -> bool:
        """估值检查"""
        return pe_percentile <= max_pe
    
    def _calculate_buy_score(self, checklist_result: dict, financial_data: dict,
                             pe_percentile: float) -> float:
        """
        买入决策评分（0-1）
        """
        weights = self.config['scoring']['weights']
        score = 0.0
        
        # 1. 20 项检查通过率（30%）
        checklist_score = checklist_result.get('pass_rate', 0)
        score += checklist_score * weights['checklist_pass_rate']
        
        # 2. ROE 评分（25%）
        roe_avg = financial_data.get('roe_avg_5y', 0)
        roe_score = min(1.0, roe_avg / 0.20)  # 20% 为满分
        score += roe_score * weights['roe_score']
        
        # 3. 现金流评分（20%）
        cf_ratio = financial_data.get('cash_flow_ratio', 0)
        cf_score = min(1.0, cf_ratio / 1.0)  # 1.0 为满分
        score += cf_score * weights['cash_flow_score']
        
        # 4. 估值评分（15%）
        valuation_score = 1.0 - pe_percentile  # PE 分位越低越好
        score += valuation_score * weights['valuation_score']
        
        # 5. 增长评分（10%）
        revenue_growth = financial_data.get('revenue_growth_3y', 0)
        growth_score = min(1.0, revenue_growth / 0.20)  # 20% 为满分
        score += growth_score * weights['growth_score']
        
        return score
    
    def _generate_buy_reasons(self, checklist_result: dict, financial_data: dict) -> list:
        """生成买入原因"""
        reasons = []
        
        # 20 项检查通过率
        pass_rate = checklist_result.get('pass_rate', 0)
        reasons.append(f"20 项检查通过率{pass_rate:.0%}")
        
        # ROE
        roe_avg = financial_data.get('roe_avg_5y', 0)
        if roe_avg > 0.15:
            reasons.append(f"ROE 连续 5 年>{roe_avg:.0%}")
        
        # 现金流
        cf_ratio = financial_data.get('cash_flow_ratio', 0)
        if cf_ratio > 0.8:
            reasons.append(f"现金流/净利润{cf_ratio:.2f}")
        
        return reasons[:3]  # 最多 3 个原因
    
    def _generate_buy_risks(self, financial_data: dict) -> list:
        """生成风险提示"""
        risks = []
        
        # 应收账款
        receivables_ratio = financial_data.get('receivables_to_revenue', 0)
        if receivables_ratio > 0.30:
            risks.append("应收账款增长较快")
        
        # 负债率
        debt_ratio = financial_data.get('debt_ratio', 0)
        if debt_ratio > 0.50:
            risks.append(f"负债率{debt_ratio:.0%}偏高")
        
        return risks[:2]  # 最多 2 个风险
    
    def _calculate_recommended_position(self, score: float, level: str) -> float:
        """计算建议仓位"""
        if level == '强烈推荐':
            return 0.25  # 25%
        elif level == '推荐买入':
            return 0.20  # 20%
        else:
            return 0.10  # 10%
    
    def make_sell_decision(self, ts_code: str, stock_name: str,
                           financial_data: dict, current_pe_percentile: float,
                           current_price: float, position_ratio: float) -> dict:
        """
        卖出决策
        
        Returns:
            dict: 决策结果（decision, urgency, reasons, recommended_action）
        """
        if not self.enabled:
            return {'decision': '持有', 'urgency': 'hold', 'reason': '决策引擎未启用'}
        
        logger.info(f"卖出决策：{stock_name} ({ts_code})")
        
        triggers = self.config['sell']
        urgency = 'hold'
        reasons = []
        decision = '持有'
        
        # 1. 红色风险（立即卖出）
        if financial_data.get('is_st', False):
            urgency = 'immediate'
            reasons.append("被 ST")
            decision = '卖出'
        
        if financial_data.get('pledge_ratio', 0) > 0.50:
            urgency = 'immediate'
            reasons.append("质押率>50%")
            decision = '卖出'
        
        # 2. 高估（尽快卖出）
        if current_pe_percentile > triggers.get('pe_percentile_sell', 0.95):
            if urgency not in ['immediate']:
                urgency = 'soon'
            reasons.append(f"PE 分位{current_pe_percentile:.0%} > 95%")
            decision = '卖出'
        
        if financial_data.get('peg', 0) > triggers.get('peg_sell', 2.0):
            if urgency not in ['immediate']:
                urgency = 'soon'
            reasons.append(f"PEG>{financial_data.get('peg', 0):.1f}")
            decision = '卖出'
        
        # 3. 基本面恶化（尽快卖出）
        roe_decline = financial_data.get('roe_decline_consecutive_2y', False)
        if roe_decline:
            if urgency not in ['immediate']:
                urgency = 'soon'
            reasons.append("ROE 连续 2 年下降")
            decision = '卖出'
        
        # 4. 仓位管理（考虑卖出）
        if position_ratio > 0.30:
            if urgency == 'hold':
                urgency = 'consider'
            reasons.append(f"单一持仓{position_ratio:.0%} > 30%")
            if decision == '持有':
                decision = '考虑卖出'
        
        # 生成行动建议
        action_map = {
            'immediate': '立即卖出',
            'soon': '分批卖出',
            'consider': '考虑减仓',
            'hold': '继续持有'
        }
        
        return {
            'decision': decision,
            'urgency': urgency,
            'reasons': reasons,
            'recommended_action': action_map.get(urgency, '继续持有'),
            'current_price': current_price,
        }
    
    def make_monitor_decision(self, ts_code: str, stock_name: str,
                              current_price: float, buy_position: float,
                              sell_position: float, alerts: list,
                              position_ratio: float) -> dict:
        """
        持仓监控决策
        
        Returns:
            dict: 决策结果（decision, alert_level, push_required, action, message）
        """
        if not self.enabled:
            return {'decision': '持有', 'push_required': False}
        
        logger.info(f"持仓监控决策：{stock_name} ({ts_code})")
        
        # 1. 检查预警
        if alerts:
            # 有预警
            top_alert = alerts[0]
            alert_level = top_alert.get('level', '')
            
            # 决策
            if '🔴' in alert_level or '🟠' in alert_level:
                decision = '预警'
                push_required = True
                action = f"关注：{top_alert.get('message', '')}"
            elif '🟢' in alert_level:
                decision = '补仓'
                push_required = True
                action = f"准备补仓"
            else:
                decision = '持有'
                push_required = False
                action = '继续持有'
            
            return {
                'decision': decision,
                'alert_level': alert_level,
                'push_required': push_required,
                'action': action,
                'message': top_alert.get('message', ''),
            }
        
        # 2. 检查价格位置
        if current_price <= buy_position * 1.02:
            return {
                'decision': '补仓',
                'alert_level': '🟢 机会',
                'push_required': True,
                'action': '准备补仓',
                'message': f'{stock_name} 现价{current_price:.2f} 接近补仓位{buy_position:.2f}'
            }
        
        if current_price >= sell_position * 0.98:
            return {
                'decision': '减仓',
                'alert_level': '🟠 预警',
                'push_required': True,
                'action': '准备减仓',
                'message': f'{stock_name} 现价{current_price:.2f} 接近减仓位{sell_position:.2f}'
            }
        
        # 3. 正常持有
        return {
            'decision': '持有',
            'alert_level': '✅ 正常',
            'push_required': False,
            'action': '继续持有',
            'message': f'{stock_name} 运行正常'
        }
    
    def reload_config(self):
        """重新加载配置"""
        self.config = self._load_config()
        logger.info("决策引擎配置已重新加载")


# 全局实例
_engine_instance = None


def get_decision_engine() -> DecisionEngine:
    """获取决策引擎实例"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DecisionEngine()
    return _engine_instance


# CLI 测试入口
if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"决策引擎 v2.0 - 测试")
    print(f"{'='*60}\n")
    
    engine = get_decision_engine()
    
    # 测试买入决策
    print("测试 1: 买入决策")
    result = engine.make_buy_decision(
        ts_code='002270.SZ',
        stock_name='华明装备',
        industry='制造业',
        financial_data={
            'roe_avg_5y': 0.22,
            'cash_flow_ratio': 1.16,
            'revenue_growth_3y': 0.15,
            'avg_volume': 100000000,
        },
        checklist_result={'pass_rate': 0.85},
        risk_check_result={'has_red_risk': False},
        current_pe_percentile=0.30,
        current_price=26.37,
        target_buy_price=26.00
    )
    print(f"决策：{result['decision']}")
    print(f"评分：{result['score']:.2f}")
    print(f"等级：{result['level']}")
    print(f"原因：{result['reasons']}")
    print(f"建议仓位：{result['recommended_position']:.0%}")
    print()
    
    # 测试卖出决策
    print("测试 2: 卖出决策（高估场景）")
    result = engine.make_sell_decision(
        ts_code='002270.SZ',
        stock_name='华明装备',
        financial_data={'peg': 1.5, 'is_st': False, 'pledge_ratio': 0.20},
        current_pe_percentile=0.96,
        current_price=35.00,
        position_ratio=0.25
    )
    print(f"决策：{result['decision']}")
    print(f"紧急程度：{result['urgency']}")
    print(f"原因：{result['reasons']}")
    print(f"行动：{result['recommended_action']}")
    print()
    
    # 测试持仓监控决策
    print("测试 3: 持仓监控决策（补仓机会）")
    result = engine.make_monitor_decision(
        ts_code='002270.SZ',
        stock_name='华明装备',
        current_price=26.37,
        buy_position=26.00,
        sell_position=34.00,
        alerts=[],
        position_ratio=0.20
    )
    print(f"决策：{result['decision']}")
    print(f"预警级别：{result['alert_level']}")
    print(f"推送：{result['push_required']}")
    print(f"行动：{result['action']}")
    print(f"消息：{result['message']}")
    print()
    
    print(f"{'='*60}")
    print(f"✅ 决策引擎 v2.0 测试完成")
    print(f"{'='*60}\n")
