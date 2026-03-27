"""
回测引擎
- 基于历史数据回测选股策略
- 计算收益率、夏普比率、最大回撤等指标
- 生成回测报告
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.tushare_client import pro, get_pe_pb_percentile, get_roe, get_gross_margin


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, ts_codes: list = None, start_date: str = None, end_date: str = None, initial_capital: float = 1000000):
        """
        初始化回测引擎
        
        参数：
        - ts_codes: 股票代码列表
        - start_date: 开始日期 YYYYMMDD
        - end_date: 结束日期 YYYYMMDD
        - initial_capital: 初始资金
        """
        self.ts_codes = ts_codes or ['002270.SZ']
        self.start_date = start_date or '20200101'
        self.end_date = end_date or datetime.now().strftime('%Y%m%d')
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}  # 持仓
        self.trades = []  # 交易记录
        self.portfolio_values = []  # 组合净值
    
    def get_trade_dates(self):
        """获取交易日历"""
        try:
            df = pro.trade_cal(exchange='SSE', start_date=self.start_date, end_date=self.end_date, is_open='1')
            return df['cal_date'].tolist()
        except Exception as e:
            print(f"获取交易日历失败：{e}")
            return []
    
    def get_stock_data(self, ts_code: str, trade_date: str):
        """
        获取股票数据
        
        参数：
        - ts_code: 股票代码
        - trade_date: 交易日期
        
        返回：dict (PE, PB, ROE, 毛利率等)
        """
        try:
            # 获取估值数据
            df = pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
            if len(df) == 0:
                return None
            
            data = {
                'close': df.iloc[0]['close'],
                'pe_ttm': df.iloc[0]['pe_ttm'],
                'pb': df.iloc[0]['pb'],
                'ps_ttm': df.iloc[0]['ps_ttm'],
                'total_mv': df.iloc[0]['total_mv'],
            }
            
            # 获取财务数据（季度更新，用最近一期）
            try:
                roe_df = get_roe(ts_code)
                if len(roe_df) > 0:
                    data['roe'] = roe_df.iloc[0]['roe_dt']
                else:
                    data['roe'] = None
            except:
                data['roe'] = None
            
            return data
        except Exception as e:
            print(f"获取股票数据失败：{e}")
            return None
    
    def check_buy_signal(self, ts_code: str, data: dict):
        """
        检查买入信号
        
        买入条件（简化版）：
        1. PE 分位 < 50%
        2. ROE > 10%
        3. 负债率 < 50%
        
        返回：bool
        """
        if data is None:
            return False
        
        # PE 条件
        pe = data.get('pe_ttm')
        if pe is None or pe < 0 or pe > 100:
            return False
        
        # ROE 条件
        roe = data.get('roe')
        if roe is None or roe < 0.10:
            return False
        
        # 简化：假设 PE < 25 且 ROE > 15% 时买入
        if pe < 25 and roe > 0.15:
            return True
        
        return False
    
    def check_sell_signal(self, ts_code: str, data: dict, cost_price: float, current_price: float):
        """
        检查卖出信号
        
        卖出条件：
        1. 止盈：涨幅 > 50%
        2. 止损：跌幅 > 20%
        3. PE 分位 > 80%
        
        返回：bool
        """
        if data is None or cost_price <= 0:
            return False
        
        # 计算收益率
        return_rate = (current_price - cost_price) / cost_price
        
        # 止盈
        if return_rate > 0.50:
            return True
        
        # 止损
        if return_rate < -0.20:
            return True
        
        # PE 过高
        pe = data.get('pe_ttm')
        if pe and pe > 50:
            return True
        
        return False
    
    def execute_backtest(self):
        """执行回测"""
        print("=" * 60)
        print("回测引擎 - 执行回测")
        print("=" * 60)
        print()
        print(f"回测区间：{self.start_date} - {self.end_date}")
        print(f"初始资金：¥{self.initial_capital:,.0f}")
        print(f"股票池：{len(self.ts_codes)} 只")
        print()
        
        # 获取交易日历
        trade_dates = self.get_trade_dates()
        if not trade_dates:
            print("❌ 无交易数据")
            return None
        
        print(f"交易天数：{len(trade_dates)}")
        print()
        
        # 初始化组合净值
        self.portfolio_values.append({
            'date': self.start_date,
            'value': self.initial_capital,
            'cash': self.initial_capital,
            'positions': 0,
        })
        
        # 遍历每个交易日
        for i, trade_date in enumerate(trade_dates, 1):
            if i % 100 == 0:
                print(f"  进度：{i}/{len(trade_dates)} 天")
            
            # 检查持仓股票是否卖出
            for ts_code in list(self.positions.keys()):
                position = self.positions[ts_code]
                data = self.get_stock_data(ts_code, trade_date)
                
                if data and data.get('close'):
                    current_price = data['close']
                    cost_price = position['cost_price']
                    
                    # 检查卖出信号
                    if self.check_sell_signal(ts_code, data, cost_price, current_price):
                        # 卖出
                        shares = position['shares']
                        sell_value = shares * current_price
                        self.capital += sell_value
                        
                        # 记录交易
                        self.trades.append({
                            'date': trade_date,
                            'ts_code': ts_code,
                            'action': 'sell',
                            'price': current_price,
                            'shares': shares,
                            'value': sell_value,
                            'reason': '止盈/止损/PE 过高',
                        })
                        
                        # 移除持仓
                        del self.positions[ts_code]
            
            # 检查是否有买入机会
            for ts_code in self.ts_codes:
                if ts_code in self.positions:
                    continue  # 已持仓
                
                data = self.get_stock_data(ts_code, trade_date)
                
                # 检查买入信号
                if self.check_buy_signal(ts_code, data):
                    # 买入（每只股票最多 10% 仓位）
                    buy_value = min(self.initial_capital * 0.10, self.capital * 0.95)
                    if buy_value < 10000:
                        continue  # 最小买入金额
                    
                    current_price = data['close']
                    shares = int(buy_value / current_price / 100) * 100  # 100 股的整数倍
                    
                    if shares > 0:
                        cost = shares * current_price
                        self.capital -= cost
                        
                        # 记录持仓
                        self.positions[ts_code] = {
                            'shares': shares,
                            'cost_price': current_price,
                            'buy_date': trade_date,
                        }
                        
                        # 记录交易
                        self.trades.append({
                            'date': trade_date,
                            'ts_code': ts_code,
                            'action': 'buy',
                            'price': current_price,
                            'shares': shares,
                            'value': cost,
                        })
            
            # 计算组合净值
            position_value = 0
            for ts_code, pos in self.positions.items():
                data = self.get_stock_data(ts_code, trade_date)
                if data and data.get('close'):
                    position_value += pos['shares'] * data['close']
            
            total_value = self.capital + position_value
            
            self.portfolio_values.append({
                'date': trade_date,
                'value': total_value,
                'cash': self.capital,
                'positions': position_value,
            })
        
        print()
        print("=" * 60)
        print("✅ 回测完成")
        print("=" * 60)
        
        # 计算回测指标
        return self.calculate_metrics()
    
    def calculate_metrics(self):
        """计算回测指标"""
        if not self.portfolio_values:
            return None
        
        # 最终净值
        final_value = self.portfolio_values[-1]['value']
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # 年化收益率
        start_date = datetime.strptime(self.portfolio_values[0]['date'], '%Y%m%d')
        end_date = datetime.strptime(self.portfolio_values[-1]['date'], '%Y%m%d')
        years = (end_date - start_date).days / 365.25
        annual_return = (final_value / self.initial_capital) ** (1 / years) - 1 if years > 0 else 0
        
        # 最大回撤
        max_drawdown = 0
        peak = self.initial_capital
        for pv in self.portfolio_values:
            value = pv['value']
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 夏普比率（简化：假设无风险利率 3%）
        daily_returns = []
        for i in range(1, len(self.portfolio_values)):
            prev_value = self.portfolio_values[i-1]['value']
            curr_value = self.portfolio_values[i]['value']
            if prev_value > 0:
                daily_returns.append((curr_value - prev_value) / prev_value)
        
        if daily_returns:
            import statistics
            avg_return = statistics.mean(daily_returns)
            std_return = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 1
            sharpe_ratio = (avg_return * 252 - 0.03) / (std_return * (252 ** 0.5)) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # 交易统计
        total_trades = len(self.trades)
        buy_trades = sum(1 for t in self.trades if t['action'] == 'buy')
        sell_trades = sum(1 for t in self.trades if t['action'] == 'sell')
        
        metrics = {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'trade_dates': len(self.portfolio_values),
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        
        # 打印回测结果
        print()
        print("=" * 60)
        print("回测结果")
        print("=" * 60)
        print(f"初始资金：¥{self.initial_capital:,.0f}")
        print(f"最终净值：¥{final_value:,.0f}")
        print(f"总收益率：{total_return:.1%}")
        print(f"年化收益率：{annual_return:.1%}")
        print(f"最大回撤：{max_drawdown:.1%}")
        print(f"夏普比率：{sharpe_ratio:.2f}")
        print(f"交易次数：{total_trades} 次（买入{buy_trades}次，卖出{sell_trades}次）")
        print(f"回测天数：{len(self.portfolio_values)} 天")
        print("=" * 60)
        
        return metrics
    
    def save_report(self, metrics: dict, output_path: str = None):
        """保存回测报告"""
        if output_path is None:
            output_dir = Path(__file__).parent.parent / 'cache' / 'backtest'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'metrics': metrics,
            'trades': self.trades[:100],  # 只保存前 100 条交易
            'portfolio_values': self.portfolio_values[-100:],  # 只保存最后 100 条净值
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"回测报告已保存：{output_path}")
        return output_path


# 主程序
if __name__ == '__main__':
    # 测试回测
    ts_codes = ['002270.SZ']  # 华明装备
    start_date = '20200101'
    end_date = '20251231'
    
    print(f"回测标的：{ts_codes}")
    print(f"回测区间：{start_date} - {end_date}")
    print()
    
    # 创建回测引擎
    engine = BacktestEngine(ts_codes=ts_codes, start_date=start_date, end_date=end_date)
    
    # 执行回测
    metrics = engine.execute_backtest()
    
    if metrics:
        # 保存报告
        engine.save_report(metrics)
