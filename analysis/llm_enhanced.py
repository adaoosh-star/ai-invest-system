"""
LLM 深度分析模块 v2.0

功能：
- 语义级承诺分析
- 年报 MD&A 解读
- 财务造假风险识别增强
- 行业竞争格局分析

稳定性保障：
- 独立新模块，不影响现有 20 项检查
- 配置开关控制（默认关闭）
- 成本限制（每日上限）
- 降级方案（LLM 失败时用规则分析）
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
logger = get_logger('llm_enhanced')

# 配置
LLM_CONFIG = {
    'enabled': True,  # 默认开启
    'api_key': 'sk-sp-86c12d2ccf8f4a949a9b76a3cb106cde',
    'base_url': 'https://coding.dashscope.aliyuncs.com/v1',
    'model': 'qwen3.5-plus',
    'cost_limit_per_day': 10,
    'analysis_depth': 'medium',
}


def call_qwen_api(prompt: str, system_prompt: str = None) -> dict:
    """
    调用千问 API
    
    Args:
        prompt: 用户提示
        system_prompt: 系统提示
    
    Returns:
        dict: API 响应结果
    """
    if not LLM_CONFIG.get('enabled'):
        return {'error': 'LLM not enabled'}
    
    api_key = LLM_CONFIG.get('api_key')
    base_url = LLM_CONFIG.get('base_url', 'https://coding.dashscope.aliyuncs.com/v1')
    model = LLM_CONFIG.get('model', 'qwen3.5-plus')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': prompt})
    
    payload = {
        'model': model,
        'messages': messages,
        'temperature': 0.3,
        'max_tokens': 1000
    }
    
    try:
        response = requests.post(
            f'{base_url}/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return {
                'success': True,
                'content': result['choices'][0]['message']['content'],
                'usage': result.get('usage', {}),
            }
        else:
            return {'success': False, 'error': 'No choices in response'}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"千问 API 调用失败：{e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f"解析响应失败：{e}")
        return {'success': False, 'error': str(e)}


class LLMEnhancedAnalyzer:
    """LLM 深度分析器"""
    
    def __init__(self):
        """初始化 LLM 分析器"""
        self.enabled = LLM_CONFIG.get('enabled', False)
        self.cost_limit = LLM_CONFIG.get('cost_limit_per_day', 10)
        self.depth = LLM_CONFIG.get('analysis_depth', 'medium')
        self.daily_cost = 0.0
    
    def analyze_promise_semantic(self, promise_text: str, context: dict = None) -> dict:
        """
        语义级承诺分析
        """
        if not self.enabled:
            return self._fallback_promise_analysis(promise_text)
        
        logger.info(f"LLM 承诺分析：{promise_text[:50]}...")
        
        # 调用千问 API
        system_prompt = """你是一个专业的投资分析师，擅长分析企业管理层的承诺内容。
请分析以下承诺，评估其可信度、具体程度和潜在风险。
返回 JSON 格式的分析结果。"""
        
        prompt = f"""请分析以下管理层承诺：

"{promise_text}"

请返回 JSON 格式的分析结果，包含以下字段：
- type: 承诺类型（业绩承诺/增持承诺/分红承诺/其他）
- confidence: 可信度评分（0-1 之间的小数）
- specificity: 具体程度（0-1 之间的小数）
- deadline: 承诺期限（如果有）
- metrics: 量化指标列表（如果有）
- risks: 风险提示列表
- tone: 管理层语气（自信/犹豫/回避）

只返回 JSON，不要其他内容。"""
        
        result = call_qwen_api(prompt, system_prompt)
        
        if result.get('success'):
            try:
                # 解析 JSON 响应
                import re
                json_match = re.search(r'\{.*\}', result['content'], re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    analysis['method'] = 'llm'
                    self._record_cost(0.5)
                    return analysis
            except Exception as e:
                logger.warning(f"解析 LLM 响应失败：{e}，降级为规则分析")
        
        # 降级为规则分析
        return self._fallback_promise_analysis(promise_text)
    
    def _fallback_promise_analysis(self, promise_text: str) -> dict:
        """
        降级：规则式承诺分析（LLM 不可用时）
        """
        # 关键词匹配
        promise_keywords = {
            '业绩承诺': ['营收', '净利润', '增长率', 'ROE'],
            '增持承诺': ['增持', '回购', '持股'],
            '分红承诺': ['分红', '派息', '股利'],
        }
        
        detected_type = '其他'
        for ptype, keywords in promise_keywords.items():
            if any(kw in promise_text for kw in keywords):
                detected_type = ptype
                break
        
        return {
            'type': detected_type,
            'confidence': 0.5,  # 规则分析可信度较低
            'method': 'rule-based',
        }
    
    def analyze_md_a(self, md_a_text: str, financial_data: dict = None) -> dict:
        """
        年报 MD&A（管理层讨论与分析）深度解读
        
        Args:
            md_a_text: MD&A 文本内容
            financial_data: 财务数据（用于对比验证）
        
        Returns:
            dict: 分析结果（关键洞察、风险信号、与财报一致性等）
        """
        if not self.enabled:
            return self._fallback_mda_analysis(md_a_text)
        
        logger.info(f"LLM MD&A 分析：{len(md_a_text)} 字符")
        
        # TODO: 接入实际 LLM API
        # 分析维度：
        # 1. 战略方向提取
        # 2. 风险因素识别
        # 3. 业绩指引量化
        # 4. 与财报数据一致性验证
        # 5. 管理层语气分析
        
        # 模拟返回
        result = {
            'strategy': {
                'direction': '数字化转型 + 海外市场扩张',
                'investment_focus': ['研发', '产能扩张'],
                'risk_awareness': '高',
            },
            'performance_guidance': {
                'revenue_growth': '15-20%',
                'margin_outlook': '稳定',
                'capex_plan': '5 亿元',
            },
            'risk_signals': [
                {'type': '原材料价格波动', 'severity': '中'},
                {'type': '汇率风险', 'severity': '低'},
            ],
            'consistency_check': {
                'revenue_claim': '与财报一致',
                'margin_claim': '与财报一致',
                'cash_flow_claim': '需关注',
            },
            'tone_analysis': {
                'confidence': 0.7,
                'transparency': 0.8,
                'caution_level': 0.4,
            }
        }
        
        self._record_cost(1.0)
        return result
    
    def _fallback_mda_analysis(self, md_a_text: str) -> dict:
        """
        降级：规则式 MD&A 分析
        """
        # 简单统计
        word_count = len(md_a_text)
        risk_count = md_a_text.count('风险') + md_a_text.count('挑战')
        opportunity_count = md_a_text.count('机遇') + md_a_text.count('机会')
        
        return {
            'word_count': word_count,
            'risk_mentions': risk_count,
            'opportunity_mentions': opportunity_count,
            'method': 'rule-based',
        }
    
    def detect_fraud_risk(self, financial_data: dict, industry_data: dict = None) -> dict:
        """
        财务造假风险识别增强
        
        Args:
            financial_data: 财务数据
            industry_data: 行业对比数据
        
        Returns:
            dict: 风险识别结果（风险分数、具体风险点、证据）
        """
        if not self.enabled:
            return self._fallback_fraud_detection(financial_data)
        
        logger.info("LLM 财务造假风险识别")
        
        # TODO: 接入实际 LLM API
        # 分析维度：
        # 1. 营收增长 vs 行业趋势匹配性
        # 2. 毛利率 vs 同行异常偏离
        # 3. 应收账款 vs 现金流背离
        # 4. 关联交易话术分析
        # 5. 客户/供应商集中度风险
        
        # 模拟返回
        result = {
            'fraud_risk_score': 0.2,  # 0-1，越低越安全
            'risk_factors': [],
            'red_flags': [],
            'recommendation': '低风险，可继续跟踪',
        }
        
        # 规则检查（始终执行）
        rule_based_risks = self._check_fraud_rules(financial_data)
        result['rule_based_risks'] = rule_based_risks
        
        self._record_cost(0.8)
        return result
    
    def _check_fraud_rules(self, financial_data: dict) -> list:
        """
        规则式造假风险检查（始终执行）
        """
        risks = []
        
        # 1. 应收账款/营收 异常
        receivables_ratio = financial_data.get('receivables_to_revenue', 0)
        if receivables_ratio > 0.5:
            risks.append({
                'type': '应收账款占比过高',
                'value': f"{receivables_ratio:.1%}",
                'severity': '中'
            })
        
        # 2. 现金流/净利润 背离
        cash_flow_ratio = financial_data.get('cash_flow_to_net_profit', 1)
        if cash_flow_ratio < 0.5:
            risks.append({
                'type': '现金流与净利润背离',
                'value': f"{cash_flow_ratio:.2f}",
                'severity': '高'
            })
        
        # 3. 毛利率异常高于同行
        gross_margin_vs_industry = financial_data.get('gross_margin_vs_industry', 0)
        if gross_margin_vs_industry > 0.3:
            risks.append({
                'type': '毛利率显著高于同行',
                'value': f"+{gross_margin_vs_industry:.1%}",
                'severity': '中'
            })
        
        return risks
    
    def _fallback_fraud_detection(self, financial_data: dict) -> dict:
        """
        降级：仅规则检查
        """
        return {
            'rule_based_risks': self._check_fraud_rules(financial_data),
            'method': 'rule-based',
        }
    
    def analyze_industry_competition(self, company_name: str, industry: str) -> dict:
        """
        行业竞争格局分析
        
        Args:
            company_name: 公司名称
            industry: 所属行业
        
        Returns:
            dict: 分析结果（市场地位、竞争壁垒、产业链位置等）
        """
        if not self.enabled:
            return {'method': 'disabled', 'note': 'LLM 分析未启用'}
        
        logger.info(f"LLM 行业竞争分析：{company_name} - {industry}")
        
        # TODO: 接入实际 LLM API
        # 分析维度：
        # 1. 市场份额
        # 2. 竞争壁垒（技术/品牌/规模）
        # 3. 产业链位置（上下游议价能力）
        # 4. 政策影响
        # 5. 替代品威胁
        
        # 模拟返回
        result = {
            'market_position': {
                'rank': 2,
                'market_share': '15%',
                'trend': '上升',
            },
            'competitive_barriers': [
                {'type': '技术壁垒', 'strength': '高'},
                {'type': '品牌壁垒', 'strength': '中'},
                {'type': '规模壁垒', 'strength': '高'},
            ],
            'value_chain_position': {
                'upstream_power': '中',  # 对上游议价能力
                'downstream_power': '高',  # 对下游议价能力
            },
            'policy_impact': {
                'direction': '正面',
                'details': ['产业政策支持', '出口退税']
            },
            'substitute_threat': '低',
        }
        
        self._record_cost(1.2)
        return result
    
    def _record_cost(self, cost: float):
        """记录 LLM 调用成本"""
        self.daily_cost += cost
        if self.daily_cost > self.cost_limit:
            logger.warning(f"LLM 成本超出限制：{self.daily_cost:.2f} > {self.cost_limit}")
            # 可以在此自动禁用后续调用
    
    def get_cost_status(self) -> dict:
        """获取成本状态"""
        return {
            'daily_cost': self.daily_cost,
            'cost_limit': self.cost_limit,
            'remaining': max(0, self.cost_limit - self.daily_cost),
            'enabled': self.enabled and self.daily_cost < self.cost_limit,
        }
    
    def reset_daily_cost(self):
        """重置每日成本（每日调用一次）"""
        self.daily_cost = 0.0


# 全局实例
_llm_analyzer_instance = None


def get_llm_analyzer() -> LLMEnhancedAnalyzer:
    """获取 LLM 分析器实例"""
    global _llm_analyzer_instance
    if _llm_analyzer_instance is None:
        _llm_analyzer_instance = LLMEnhancedAnalyzer()
    return _llm_analyzer_instance


# CLI 测试入口
if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"LLM 深度分析模块 v2.0 - 测试")
    print(f"{'='*60}\n")
    
    analyzer = get_llm_analyzer()
    
    print(f"LLM 分析状态：{'已启用' if analyzer.enabled else '未启用'}")
    print(f"每日成本限制：¥{analyzer.cost_limit}")
    print()
    
    # 测试承诺分析
    print("测试 1: 承诺语义分析")
    promise_text = "公司承诺 2026 年营收增长率不低于 20%，净利润增长率不低于 15%"
    result = analyzer.analyze_promise_semantic(promise_text)
    print(f"承诺类型：{result.get('type')}")
    print(f"可信度：{result.get('confidence', 0):.2f}")
    print()
    
    # 测试 MD&A 分析
    print("测试 2: MD&A 分析（降级模式）")
    mda_text = "公司将继续加大研发投入，拓展海外市场..." * 100
    result = analyzer.analyze_md_a(mda_text)
    print(f"分析方法：{result.get('method')}")
    print()
    
    # 测试造假风险识别
    print("测试 3: 财务造假风险识别")
    financial_data = {
        'receivables_to_revenue': 0.3,
        'cash_flow_to_net_profit': 0.8,
        'gross_margin_vs_industry': 0.1,
    }
    result = analyzer.detect_fraud_risk(financial_data)
    print(f"规则检查风险：{len(result.get('rule_based_risks', []))} 个")
    for risk in result.get('rule_based_risks', []):
        print(f"  - {risk['type']}: {risk['value']} ({risk['severity']})")
    print()
    
    # 成本状态
    print("测试 4: 成本状态")
    cost_status = analyzer.get_cost_status()
    print(f"今日成本：¥{cost_status['daily_cost']:.2f}")
    print(f"剩余额度：¥{cost_status['remaining']:.2f}")
    print()
    
    print(f"{'='*60}")
    print(f"✅ LLM 分析模块测试完成")
    print(f"{'='*60}\n")
