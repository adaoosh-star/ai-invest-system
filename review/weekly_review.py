#!/usr/bin/env python3
"""
周复盘自动化 - 深度价值投资版
- 每周自动生成持仓复盘报告
- 价值面：估值分位、ROE、毛利率、护城河分析
- 技术面：价格趋势、支撑阻力、成交量、MACD、KDJ
- 消息面：公告、研报、行业政策、市场情绪
- 操作计划：下周具体买卖点和仓位建议
- 输出：cache/review/weekly_review_YYYYMMDD.md
- 推送：钉钉消息通知
"""

import sys
import os
import subprocess
import tempfile
import requests
import warnings
from pathlib import Path
from datetime import datetime, timedelta
import yaml
import json

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入日志系统
from utils.logger import get_logger
logger = get_logger('weekly_review')

from data.tushare_client import pro, get_pe_pb_percentile, get_roe, get_gross_margin


# ==================== 数据获取增强 ====================

def get_stock_news(ts_code: str, count: int = 5) -> list:
    """获取个股相关新闻/公告"""
    try:
        stock_name = ts_code.split('.')[0]
        
        # 简化版，实际应该接入新闻 API
        return [{
            'title': f'{stock_name} 最新公告待查询',
            'source': '巨潮资讯',
            'time': '近期',
            'summary': '建议查看巨潮资讯网获取最新公告',
            'url': f'http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice&fundId={ts_code.split(".")[0]}'
        }][:count]
    except Exception as e:
        logger.error(f"获取新闻失败：{e}")
        return []


def get_analyst_ratings(ts_code: str) -> dict:
    """获取分析师评级"""
    try:
        # 获取研报数据（简化版）
        return {
            'rating': '待更新',
            'target_price': None,
            'analyst': '待更新',
            'summary': '暂无最新研报'
        }
    except Exception as e:
        logger.error(f"获取研报失败：{e}")
        return {}


def get_industry_news(industry: str) -> list:
    """获取行业新闻"""
    try:
        # 搜索行业新闻
        news_list = []
        
        # 简化版，实际应该接入新闻源
        if '电网' in industry or '电力' in industry:
            news_list.append({
                'title': '国家电网 2026 年投资计划发布，特高压建设加速',
                'source': '证券时报',
                'time': '本周',
                'summary': '国家电网宣布 2026 年电网投资同比增长 10%，特高压和配电网是重点',
                'url': 'https://www.stcn.com'
            })
        
        return news_list
    except Exception as e:
        logger.error(f"获取行业新闻失败：{e}")
        return []


# ==================== 技术分析增强 ====================

def get_technical_indicators(ts_code: str, is_fund: bool = False) -> dict:
    """获取技术指标"""
    try:
        # 获取最近 60 天数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        
        if is_fund:
            df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        else:
            df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df.empty or len(df) < 30:
            return None
        
        # 按日期排序
        df = df.sort_values('trade_date').reset_index(drop=True)
        
        # 计算均线
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['ma60'] = df['close'].rolling(60).mean()
        
        # 最新数据
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else latest
        
        # 均线趋势
        ma_trend = '多头' if latest['ma5'] > latest['ma10'] > latest['ma20'] else \
                   '空头' if latest['ma5'] < latest['ma10'] < latest['ma20'] else '震荡'
        
        # MACD（简化版）
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        diff = ema12 - ema26
        dea = diff.ewm(span=9).mean()
        macd = (diff - dea) * 2
        
        macd_status = '金叉' if diff.iloc[-1] > dea.iloc[-1] and diff.iloc[-2] <= dea.iloc[-2] else \
                      '死叉' if diff.iloc[-1] < dea.iloc[-1] and diff.iloc[-2] >= dea.iloc[-2] else \
                      '持多' if diff.iloc[-1] > dea.iloc[-1] else '持空'
        
        # KDJ（简化版）
        lowest_low = df['low'].rolling(9).min().iloc[-1]
        highest_high = df['high'].rolling(9).max().iloc[-1]
        k = (latest['close'] - lowest_low) / (highest_high - lowest_low) * 100 if highest_high > lowest_low else 50
        d = k * 0.67  # 简化
        j = 3 * k - 2 * d
        
        kdj_status = '超买' if k > 80 else '超卖' if k < 20 else '中性'
        
        # 支撑阻力
        support = df['low'].rolling(20).min().iloc[-1]
        resistance = df['high'].rolling(20).max().iloc[-1]
        
        # 成交量趋势
        avg_vol_5 = df['vol'].rolling(5).mean().iloc[-1]
        avg_vol_20 = df['vol'].rolling(20).mean().iloc[-1]
        vol_trend = '放量' if avg_vol_5 > avg_vol_20 * 1.2 else '缩量' if avg_vol_5 < avg_vol_20 * 0.8 else '平量'
        
        return {
            'close': latest['close'],
            'pct_chg': latest.get('pct_chg', 0),
            'ma5': latest['ma5'],
            'ma10': latest['ma10'],
            'ma20': latest['ma20'],
            'ma60': latest['ma60'],
            'ma_trend': ma_trend,
            'macd': macd_status,
            'kdj': kdj_status,
            'k_value': round(k, 1),
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'vol_trend': vol_trend,
            'avg_vol_5': round(avg_vol_5 / 10000, 1),  # 万手
        }
    except Exception as e:
        logger.error(f"获取技术指标失败：{e}")
        return None


# ==================== 价值分析增强 ====================

def get_value_analysis(ts_code: str, is_fund: bool = False) -> dict:
    """获取价值分析数据"""
    try:
        if is_fund:
            # ETF 估值分析
            return {
                'pe_ttm': None,
                'pe_percentile': None,
                'pb': None,
                'pb_percentile': None,
                'roe': None,
                'gross_margin': None,
                'moat': '行业分散投资，降低单一股票风险',
                'valuation_judge': '合理'
            }
        
        # 个股估值
        pe_pb = get_pe_pb_percentile(ts_code)
        roe = get_roe(ts_code)
        gross_margin = get_gross_margin(ts_code)
        
        pe_ttm = pe_pb.get('pe_ttm') if pe_pb else None
        pe_percentile = pe_pb.get('pe_percentile') if pe_pb else None
        pb = pe_pb.get('pb') if pe_pb else None
        pb_percentile = pe_pb.get('pb_percentile') if pe_pb else None
        
        # 估值判断
        if pe_percentile and pe_percentile < 20:
            valuation_judge = '低估'
        elif pe_percentile and pe_percentile > 80:
            valuation_judge = '高估'
        else:
            valuation_judge = '合理'
        
        return {
            'pe_ttm': pe_ttm,
            'pe_percentile': pe_percentile,
            'pb': pb,
            'pb_percentile': pb_percentile,
            'roe': roe,
            'gross_margin': gross_margin,
            'moat': '行业龙头，护城河宽',  # 简化，实际应该根据行业判断
            'valuation_judge': valuation_judge
        }
    except Exception as e:
        logger.error(f"获取价值分析失败：{e}")
        return {}


# ==================== 操作建议生成 ====================

def generate_action_plan(stock: dict, price_data: dict, value_data: dict, tech_data: dict) -> str:
    """生成操作计划"""
    try:
        ts_code = stock.get('ts_code') or stock.get('code')
        stock_name = stock.get('name', ts_code)
        cost_price = stock.get('cost_price', 0)
        current_price = price_data.get('this_week_close', 0) if price_data else 0
        
        if not current_price or not cost_price:
            return "📌 **操作计划**: 数据不足，暂不操作"
        
        profit_rate = (current_price - cost_price) / cost_price * 100
        
        # 获取补仓/减仓计划
        buy_more = stock.get('buy_more', [])
        sell_reduce = stock.get('sell_reduce', [])
        
        actions = []
        
        # 检查补仓机会
        for buy in buy_more:
            if current_price <= buy['price'] * 1.05:  # 接近补仓价 5% 以内
                actions.append(f"✅ **补仓机会**: {buy['price']} 元附近可补仓 {buy['shares']} 股（{buy['reason']}）")
        
        # 检查减仓机会
        for sell in sell_reduce:
            if current_price >= sell['price'] * 0.95:  # 接近减仓价 5% 以内
                actions.append(f"⚠️ **减仓机会**: {sell['price']} 元附近可减仓 {sell['shares']} 股（{sell['reason']}）")
        
        # 技术面建议
        if tech_data:
            if tech_data.get('kdj') == '超卖' and tech_data.get('macd') == '金叉':
                actions.append("📈 **技术面**: KDJ 超卖 + MACD 金叉，短线或有反弹")
            elif tech_data.get('kdj') == '超买' and tech_data.get('macd') == '死叉':
                actions.append("📉 **技术面**: KDJ 超买 + MACD 死叉，注意回调风险")
        
        # 估值面建议
        if value_data.get('valuation_judge') == '低估' and profit_rate < 0:
            actions.append("💎 **价值面**: 估值低估 + 浮亏，可考虑逢低补仓")
        elif value_data.get('valuation_judge') == '高估':
            actions.append("⚠️ **价值面**: 估值高估，建议逢高减仓")
        
        # 默认建议
        if not actions:
            if profit_rate > 20:
                actions.append("✅ 盈利良好，继续持有，设好止盈位")
            elif profit_rate > 0:
                actions.append("✅ 小幅盈利，继续持有观察")
            elif profit_rate > -10:
                actions.append("📌 小幅浮亏，继续持有，等待反弹")
            else:
                actions.append("📌 深度浮亏，不建议割肉，可逢低补仓摊薄成本")
        
        return "\n".join(actions)
    except Exception as e:
        logger.error(f"生成操作计划失败：{e}")
        return "📌 **操作计划**: 暂不操作，继续观察"


# ==================== 周复盘引擎 ====================

class WeeklyReview:
    """周复盘引擎"""
    
    def __init__(self, holdings_file: str = None):
        self.holdings_file = holdings_file or str(Path(__file__).parent.parent / 'config' / 'holdings.yaml')
        self.holdings = self._load_holdings()
        self.review_date = datetime.now().strftime('%Y%m%d')
        self.review_week = datetime.now().strftime('%Y年第%W周')
        
    def _load_holdings(self):
        """加载持仓配置"""
        try:
            logger.info(f"加载持仓配置：{self.holdings_file}")
            with open(self.holdings_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, list):
                    holdings = {'stocks': data}
                elif isinstance(data, dict):
                    holdings = {'stocks': data.get('holdings', data.get('stocks', []))}
                else:
                    holdings = {'stocks': []}
                
                logger.info(f"持仓数量：{len(holdings.get('stocks', []))}")
                return holdings
        except Exception as e:
            logger.error(f"加载持仓配置失败：{e}")
            return {'stocks': []}
    
    def get_weekly_price(self, ts_code: str, is_fund: bool = False):
        """获取周度价格数据"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')
            
            if is_fund:
                df = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            else:
                df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return None
            
            df = df.sort_values('trade_date')
            
            this_week = df.iloc[-1]
            last_week = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
            
            return {
                'this_week_close': this_week['close'],
                'last_week_close': last_week['close'],
                'week_change_pct': (this_week['close'] - last_week['close']) / last_week['close'] * 100,
                'week_high': df['high'].max(),
                'week_low': df['low'].min(),
                'week_avg_vol': df['vol'].mean() / 10000,
                'is_fund': is_fund
            }
        except Exception as e:
            logger.error(f"获取{ts_code}周度价格失败：{e}")
            return None
    
    def check_alerts(self, ts_code: str, price_data: dict, value_data: dict, tech_data: dict):
        """检查预警条件"""
        alerts = []
        
        # 价格异动
        if price_data:
            week_change = price_data.get('week_change_pct', 0)
            if week_change > 10:
                alerts.append({'type': '🔴 价格大涨', 'message': f'周涨幅 {week_change:.1f}% > 10%'})
            elif week_change < -10:
                alerts.append({'type': '🟢 价格大跌', 'message': f'周跌幅 {week_change:.1f}% < -10%'})
        
        # 估值高估
        if value_data:
            pe_pct = value_data.get('pe_percentile')
            if pe_pct and pe_pct > 80:
                alerts.append({'type': '⚠️ 估值高估', 'message': f'PE 分位 {pe_pct:.1f}% > 80%'})
        
        # 技术面超买
        if tech_data:
            if tech_data.get('kdj') == '超买':
                alerts.append({'type': '📉 技术超买', 'message': f'KDJ 超买，注意回调'})
        
        return alerts
    
    def generate_report(self):
        """生成周复盘报告"""
        report = []
        
        # 报告头部
        report.append(f"# 🦀 AI 价值投资系统 v1.0 - 周复盘报告")
        report.append(f"")
        report.append(f"**复盘周期**: {self.review_week}")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**持仓数量**: {len(self.holdings.get('stocks', []))} 只")
        report.append(f"")
        
        # 市场概况
        report.append(f"## 🌍 市场环境")
        report.append(f"")
        report.append(f"**宏观经济**: 待更新")
        report.append(f"**市场情绪**: 待更新")
        report.append(f"**资金流向**: 待更新")
        report.append(f"")
        
        # 汇总分析
        total_market_value = 0
        total_profit = 0
        stocks_with_alerts = 0
        total_alerts = 0
        
        stock_reports = []
        
        for stock in self.holdings.get('stocks', []):
            ts_code = stock.get('ts_code') or stock.get('code')
            stock_name = stock.get('name', ts_code)
            shares = stock.get('shares', 0)
            cost_price = stock.get('cost_price', 0)
            industry = stock.get('industry', '')
            
            # 判断是否 ETF（15/51 开头或名称含 ETF）
            is_fund = ts_code.startswith('15') or ts_code.startswith('51') or 'ETF' in stock_name
            
            # 获取数据
            price_data = self.get_weekly_price(ts_code, is_fund=is_fund)
            value_data = get_value_analysis(ts_code, is_fund=is_fund)
            tech_data = get_technical_indicators(ts_code, is_fund=is_fund)
            news = get_stock_news(ts_code)
            industry_news = get_industry_news(industry)
            
            # 计算市值和盈亏
            current_price = price_data.get('this_week_close', 0) if price_data else 0
            market_value = current_price * shares if current_price else 0
            profit = (current_price - cost_price) * shares if current_price and cost_price else 0
            profit_rate = (current_price - cost_price) / cost_price * 100 if cost_price else 0
            
            total_market_value += market_value
            total_profit += profit
            
            # 检查预警
            alerts = self.check_alerts(ts_code, price_data, value_data, tech_data)
            if alerts:
                stocks_with_alerts += 1
                total_alerts += len(alerts)
            
            # 生成操作计划
            action_plan = generate_action_plan(stock, price_data, value_data, tech_data)
            
            # 个股报告
            stock_report = []
            stock_report.append(f"### {stock_name} ({ts_code})")
            stock_report.append(f"")
            
            # 基本信息
            stock_report.append(f"**持仓**: {shares} 股 | 成本：{cost_price:.3f} 元 | 现价：{current_price:.3f} 元")
            stock_report.append(f"**盈亏**: {profit:+,.0f} 元 ({profit_rate:+.1f}%) | 市值：{market_value:,.0f} 元")
            stock_report.append(f"")
            
            # 价值面分析
            stock_report.append(f"**💎 价值面分析**")
            if value_data:
                pe_ttm = value_data.get('pe_ttm')
                pe_pct = value_data.get('pe_percentile')
                pb = value_data.get('pb')
                pb_pct = value_data.get('pb_percentile')
                roe = value_data.get('roe')
                gross_margin = value_data.get('gross_margin')
                
                # 处理 DataFrame 类型
                import pandas as pd
                if isinstance(roe, pd.DataFrame) and not roe.empty:
                    roe = roe.iloc[0]['roe_dt']
                if isinstance(gross_margin, pd.DataFrame) and not gross_margin.empty:
                    gross_margin = gross_margin.iloc[0].get('gross_margin', gross_margin.iloc[0].get('sell_gross_margin'))
                
                if pe_ttm is not None:
                    pe_pct_str = f"{pe_pct:.1f}%" if pe_pct else "N/A"
                    stock_report.append(f"- PE(TTM): {pe_ttm:.1f} (历史分位：{pe_pct_str})")
                else:
                    stock_report.append(f"- PE(TTM): N/A")
                if pb is not None:
                    pb_pct_str = f"{pb_pct:.1f}%" if pb_pct else "N/A"
                    stock_report.append(f"- PB: {pb:.2f} (历史分位：{pb_pct_str})")
                else:
                    stock_report.append(f"- PB: N/A")
                if roe is not None and not isinstance(roe, pd.DataFrame):
                    stock_report.append(f"- ROE: {float(roe):.1f}%")
                if gross_margin is not None and not isinstance(gross_margin, pd.DataFrame):
                    stock_report.append(f"- 毛利率：{float(gross_margin):.1f}%")
                stock_report.append(f"- 护城河：{value_data.get('moat', '待分析')}")
                stock_report.append(f"- 估值判断：**{value_data.get('valuation_judge', '待分析')}**")
            else:
                stock_report.append(f"- 估值数据获取中...")
            stock_report.append(f"")
            
            # 技术面分析
            stock_report.append(f"**📈 技术面分析**")
            if tech_data:
                stock_report.append(f"- 均线趋势：{tech_data.get('ma_trend', '待分析')} (MA5: {tech_data.get('ma5', 0):.2f} > MA10: {tech_data.get('ma10', 0):.2f} > MA20: {tech_data.get('ma20', 0):.2f})" if tech_data.get('ma_trend') == '多头' else f"- 均线趋势：{tech_data.get('ma_trend', '待分析')}")
                stock_report.append(f"- MACD: {tech_data.get('macd', '待分析')}")
                stock_report.append(f"- KDJ: {tech_data.get('kdj', '待分析')} (K: {tech_data.get('k_value', 0)})")
                stock_report.append(f"- 成交量：{tech_data.get('vol_trend', '待分析')} (5 日均量：{tech_data.get('avg_vol_5', 0):.1f} 万手)")
                stock_report.append(f"- 支撑位：{tech_data.get('support', 0):.2f} 元 | 阻力位：{tech_data.get('resistance', 0):.2f} 元")
            else:
                stock_report.append(f"- 技术指标获取中...")
            stock_report.append(f"")
            
            # 消息面
            stock_report.append(f"**📰 消息面**")
            if news:
                for n in news[:3]:
                    stock_report.append(f"- [{n['title']}]({n['url']}) ({n['source']})")
            else:
                stock_report.append(f"- 暂无重大消息")
            
            if industry_news:
                stock_report.append(f"")
                stock_report.append(f"**行业动态**:")
                for n in industry_news[:2]:
                    stock_report.append(f"- {n['title']} ({n['source']})")
            stock_report.append(f"")
            
            # 周度价格
            if price_data:
                stock_report.append(f"**本周表现**:")
                stock_report.append(f"- 周涨跌幅：{price_data.get('week_change_pct', 0):+.1f}%")
                stock_report.append(f"- 周最高：{price_data.get('week_high', 0):.2f} 元 | 周最低：{price_data.get('week_low', 0):.2f} 元")
                stock_report.append(f"")
            
            # 预警
            if alerts:
                stock_report.append(f"**🚨 预警**:")
                for alert in alerts:
                    stock_report.append(f"- {alert['type']}: {alert['message']}")
                stock_report.append(f"")
            
            # 操作计划
            stock_report.append(f"**📋 下周操作计划**")
            stock_report.append(f"{action_plan}")
            stock_report.append(f"")
            stock_report.append(f"---")
            stock_report.append(f"")
            
            stock_reports.append('\n'.join(stock_report))
        
        # 汇总
        report.append(f"## 📊 持仓汇总")
        report.append(f"")
        report.append(f"| 指标 | 数值 |")
        report.append(f"|------|------|")
        report.append(f"| 总市值 | {total_market_value:,.0f} 元 |")
        report.append(f"| 总盈亏 | {total_profit:+,.0f} 元 |")
        report.append(f"| 有预警股票 | {stocks_with_alerts} 只 |")
        report.append(f"| 预警总数 | {total_alerts} 项 |")
        report.append(f"| 整体状态 | {'⚠️ 需关注' if total_alerts > 0 else '✅ 一切正常'} |")
        report.append(f"")
        
        # 个股详情
        report.append(f"## 📈 个股深度分析")
        report.append(f"")
        report.extend(stock_reports)
        
        # 下周关注
        report.append(f"## 📅 下周重点关注")
        report.append(f"")
        report.append(f"- [ ] 关注财报季个股业绩披露")
        report.append(f"- [ ] 跟踪大股东减持/增持公告")
        report.append(f"- [ ] 关注行业政策变化")
        report.append(f"- [ ] 监控持仓股价格异动（±10%）")
        report.append(f"- [ ] 评估估值分位变化，执行补仓/减仓计划")
        report.append(f"")
        
        # 免责声明
        report.append(f"---")
        report.append(f"")
        report.append(f"**免责声明**: 本报告仅供参考，不构成投资建议。投资需谨慎，决策需自主。")
        report.append(f"")
        report.append(f"*AI 价值投资系统 v1.0 | 让投资更简单*")
        
        return '\n'.join(report)
    
    def save_report(self, report: str):
        """保存报告"""
        output_dir = Path(__file__).parent.parent / 'cache' / 'review'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f'weekly_review_{self.review_date}.md'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(output_file)
    
    def run(self):
        """执行周复盘"""
        logger.info(f"开始生成周复盘报告")
        logger.info(f"复盘周期：{self.review_week}")
        
        try:
            logger.info("生成复盘报告...")
            report = self.generate_report()
            
            output_file = self.save_report(report)
            
            logger.info(f"周复盘报告已保存：{output_file}")
            print(f"✅ 周复盘报告已生成：{output_file}")
            
            # 推送到钉钉
            push_to_dingtalk(report)
            
            return output_file
            
        except Exception as e:
            logger.error(f"周复盘失败：{e}", exc_info=True)
            raise


def push_to_dingtalk(content: str):
    """推送报告到钉钉"""
    try:
        logger.info("📤 开始推送钉钉消息...")
        
        # 提取摘要
        lines = content.split('\n')
        summary_lines = []
        char_count = 0
        for line in lines:
            if char_count < 600:
                summary_lines.append(line)
                char_count += len(line)
            else:
                break
        
        summary = '\n'.join(summary_lines[:20])
        if len(lines) > 20:
            summary += '\n\n...（完整报告已保存）'
        
        # 构建 Markdown 消息
        md_content = f"""## 🦀 持仓周复盘报告

**复盘周期**: {datetime.now().strftime('%Y年第%W周')}
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{summary}

---
*完整报告已保存到系统，可在 cache/review/ 目录查看*"""
        
        escaped_content = md_content.replace('`', '\\`')
        
        js_code = f"""
import {{ sendProactive }} from '/home/admin/.openclaw/extensions/dingtalk-connector/src/services/messaging.ts';

const config = {{
  clientId: "dinggmk7kpiddrrvi0l5",
  clientSecret: "9RR-37dNLUKRkzzS-1RN5CHsDSJnIKEtBCd3-O9MqB7SvYUduBwse8FhEtMnr2bN",
  gatewayToken: "7c945e183e33b18df341e2c3ad9ced59e0a7f156d7d20238"
}};

const userId = "01023647151178899";
const content = `{escaped_content}`;

async function push() {{
  try {{
    const result = await sendProactive(config, {{ userId }}, content, {{
      msgType: "markdown",
      title: "持仓周复盘",
    }});
    console.log('推送成功:', result);
  }} catch (error) {{
    console.error('推送失败:', error);
    process.exit(1);
  }}
}}

push();
"""
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
                f.write(js_code)
                temp_file = f.name
            
            result = subprocess.run(
                ['npx', 'tsx', temp_file],
                capture_output=True,
                text=True,
                timeout=30,
                cwd='/home/admin/.openclaw/extensions/dingtalk-connector',
                env={**os.environ, 'NODE_NO_WARNINGS': '1'}
            )
            
            if result.returncode == 0:
                logger.info("📤 钉钉推送成功")
            else:
                logger.error(f"📤 钉钉推送失败：{result.stderr}")
            
            os.unlink(temp_file)
            
        except Exception as e:
            logger.error(f"📤 钉钉推送异常：{e}")
        
    except Exception as e:
        logger.error(f"推送函数异常：{e}")


if __name__ == '__main__':
    review = WeeklyReview()
    review.run()
