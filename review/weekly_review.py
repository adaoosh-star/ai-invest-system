"""
周复盘自动化
- 每周自动生成持仓复盘报告
- 检查价格异动、估值变化、重大公告
- 预警是否触发卖出条件
- 输出：cache/review/weekly_review_YYYYMMDD.md
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入日志系统
from utils.logger import get_logger
logger = get_logger('weekly_review')

from data.tushare_client import pro, get_pe_pb_percentile, get_roe, get_gross_margin


class WeeklyReview:
    """周复盘引擎"""
    
    def __init__(self, holdings_file: str = None):
        """
        初始化周复盘引擎
        
        参数：
        - holdings_file: 持仓配置文件路径
        """
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
                # 兼容两种格式：直接是列表 或 包含 holdings 键
                if isinstance(data, list):
                    holdings = {'stocks': data}
                elif isinstance(data, dict):
                    # 如果有 holdings 键，使用它；否则直接使用
                    if 'holdings' in data:
                        holdings = {'stocks': data['holdings']}
                    else:
                        holdings = data
                else:
                    holdings = {'stocks': []}
                
                logger.info(f"持仓数量：{len(holdings.get('stocks', []))}")
                return holdings
        except Exception as e:
            logger.error(f"加载持仓配置失败：{e}")
            return {'stocks': []}
    
    def get_weekly_price(self, ts_code: str):
        """获取周度价格数据"""
        try:
            # 获取最近 2 周数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')
            
            df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return None
            
            # 按日期排序
            df = df.sort_values('trade_date')
            
            # 本周数据（最新）
            this_week = df.iloc[-1]
            # 上周数据（7 天前）
            last_week = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
            
            return {
                'this_week_close': this_week['close'],
                'last_week_close': last_week['close'],
                'week_change_pct': (this_week['close'] - last_week['close']) / last_week['close'] * 100,
                'week_high': df['high'].max(),
                'week_low': df['low'].min(),
                'week_avg_vol': df['vol'].mean() / 10000,  # 万股
            }
        except Exception as e:
            print(f"获取{ts_code}周度价格失败：{e}")
            return None
    
    def get_weekly_valuation(self, ts_code: str):
        """获取周度估值数据"""
        try:
            pe_pb = get_pe_pb_percentile(ts_code)
            if not pe_pb:
                return None
            
            return {
                'pe_ttm': pe_pb.get('pe_ttm'),
                'pe_percentile': pe_pb.get('pe_percentile'),
                'pb': pe_pb.get('pb'),
                'pb_percentile': pe_pb.get('pb_percentile'),
            }
        except Exception as e:
            print(f"获取{ts_code}估值失败：{e}")
            return None
    
    def check_alerts(self, ts_code: str, price_data: dict, valuation_data: dict):
        """检查预警条件"""
        alerts = []
        
        # 1. 价格异动（周涨跌幅>10%）
        if price_data:
            week_change = price_data.get('week_change_pct', 0)
            if week_change > 10:
                alerts.append({
                    'type': '🔴 价格大涨',
                    'level': 'warning',
                    'message': f'周涨幅 {week_change:.1f}% > 10%'
                })
            elif week_change < -10:
                alerts.append({
                    'type': '🟢 价格大跌',
                    'level': 'warning',
                    'message': f'周跌幅 {week_change:.1f}% < -10%'
                })
        
        # 2. 估值高估（PE 分位>80%）
        if valuation_data:
            pe_pct = valuation_data.get('pe_percentile', 0)
            if pe_pct and pe_pct > 80:
                alerts.append({
                    'type': '⚠️ 估值高估',
                    'level': 'warning',
                    'message': f'PE 分位 {pe_pct:.1f}% > 80%'
                })
            
            pb_pct = valuation_data.get('pb_percentile', 0)
            if pb_pct and pb_pct > 80:
                alerts.append({
                    'type': '⚠️ PB 高估',
                    'level': 'warning',
                    'message': f'PB 分位 {pb_pct:.1f}% > 80%'
                })
        
        return alerts
    
    def generate_report(self):
        """生成周复盘报告"""
        report = []
        
        # 报告头部
        report.append(f"# 🦀 AI 价值投资系统 v1.0 - 周复盘报告")
        report.append(f"")
        report.append(f"**复盘周期：** {self.review_week}")
        report.append(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**持仓数量：** {len(self.holdings.get('stocks', []))}")
        report.append(f"")
        
        # 本周概览
        report.append(f"## 📊 本周概览")
        report.append(f"")
        
        total_alerts = 0
        stocks_with_alerts = 0
        
        for stock in self.holdings.get('stocks', []):
            # 兼容两种字段名：ts_code 或 code
            ts_code = stock.get('ts_code') or stock.get('code')
            stock_name = stock.get('name', ts_code)
            
            # 获取数据
            price_data = self.get_weekly_price(ts_code)
            valuation_data = self.get_weekly_valuation(ts_code)
            
            # 检查预警
            alerts = self.check_alerts(ts_code, price_data, valuation_data)
            
            if alerts:
                stocks_with_alerts += 1
                total_alerts += len(alerts)
        
        report.append(f"| 指标 | 数值 |")
        report.append(f"|------|------|")
        report.append(f"| 持仓数量 | {len(self.holdings.get('stocks', []))} 只 |")
        report.append(f"| 有预警股票 | {stocks_with_alerts} 只 |")
        report.append(f"| 预警总数 | {total_alerts} 项 |")
        report.append(f"| 整体状态 | {'⚠️ 需关注' if total_alerts > 0 else '✅ 一切正常'} |")
        report.append(f"")
        
        # 预警详情
        if total_alerts > 0:
            report.append(f"## 🚨 预警详情")
            report.append(f"")
            
            for stock in self.holdings.get('stocks', []):
                # 兼容两种字段名：ts_code 或 code
                ts_code = stock.get('ts_code') or stock.get('code')
                stock_name = stock.get('name', ts_code)
                
                price_data = self.get_weekly_price(ts_code)
                valuation_data = self.get_weekly_valuation(ts_code)
                alerts = self.check_alerts(ts_code, price_data, valuation_data)
                
                if alerts:
                    report.append(f"### {stock_name} ({ts_code})")
                    report.append(f"")
                    for alert in alerts:
                        report.append(f"- {alert['type']}: {alert['message']}")
                    report.append(f"")
        else:
            report.append(f"## ✅ 无预警")
            report.append(f"")
            report.append(f"本周所有持仓股票均无预警，一切正常。")
            report.append(f"")
        
        # 持仓详情
        report.append(f"## 📈 持仓详情")
        report.append(f"")
        report.append(f"| 代码 | 名称 | 周涨跌幅 | 周最高 | 周最低 | PE 分位 | PB 分位 | 状态 |")
        report.append(f"|------|------|---------|--------|--------|-------|-------|------|")
        
        for stock in self.holdings.get('stocks', []):
            # 兼容两种字段名：ts_code 或 code
            ts_code = stock.get('ts_code') or stock.get('code')
            stock_name = stock.get('name', ts_code)
            
            price_data = self.get_weekly_price(ts_code)
            valuation_data = self.get_weekly_valuation(ts_code)
            
            if price_data and price_data.get('week_change_pct') is not None:
                week_change = price_data.get('week_change_pct', 0) or 0
                week_high = price_data.get('week_high', 0) or 0
                week_low = price_data.get('week_low', 0) or 0
                
                pe_pct = valuation_data.get('pe_percentile', 0) if valuation_data and valuation_data.get('pe_percentile') else 0
                pb_pct = valuation_data.get('pb_percentile', 0) if valuation_data and valuation_data.get('pb_percentile') else 0
                
                # 状态判断
                if week_change > 10 or week_change < -10:
                    status = '⚠️ 异动'
                elif pe_pct and pe_pct > 80:
                    status = '⚠️ 高估'
                else:
                    status = '✅ 正常'
                
                report.append(f"| {ts_code} | {stock_name} | {week_change:+.1f}% | {week_high:.2f} | {week_low:.2f} | {pe_pct:.1f}% | {pb_pct:.1f}% | {status} |")
            else:
                report.append(f"| {ts_code} | {stock_name} | 数据获取失败 | - | - | - | - | ❌ |")
        
        report.append(f"")
        
        # 下周关注
        report.append(f"## 📅 下周关注")
        report.append(f"")
        report.append(f"- [ ] 检查是否有财报发布")
        report.append(f"- [ ] 关注大股东减持公告")
        report.append(f"- [ ] 跟踪持仓股价格异动")
        report.append(f"")
        
        # 免责声明
        report.append(f"---")
        report.append(f"")
        report.append(f"**免责声明：** 本报告仅供参考，不构成投资建议。投资需谨慎，决策需自主。")
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
            # 生成报告
            logger.info("生成复盘报告...")
            report = self.generate_report()
            
            # 保存报告
            output_file = self.save_report(report)
            
            logger.info(f"周复盘报告已保存：{output_file}")
            print(f"✅ 周复盘报告已生成：{output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"周复盘失败：{e}", exc_info=True)
            raise


if __name__ == '__main__':
    review = WeeklyReview()
    review.run()
