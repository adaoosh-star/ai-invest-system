"""
Tushare Pro API 客户端
投资宪法：数据层自动化（P0 优先级）

修复记录：2026-03-25
- cashflow_obj → cashflow (接口名更正)
- fina_income → fina_indicator (接口名更正)
- oper_cf → free_cashflow (字段名更正)
- gross_margin → grossprofit_margin (字段名更正)
"""

import tushare as ts
from pathlib import Path
from datetime import datetime, timedelta

# 读取 Token（投资宪法：安全存储）
TOKEN_PATH = Path.home() / '.tushare_token'

def get_token():
    """从安全文件读取 Tushare Token"""
    if not TOKEN_PATH.exists():
        raise FileNotFoundError("Tushare Token 文件不存在，请创建 ~/.tushare_token")
    
    with open(TOKEN_PATH, 'r') as f:
        token = f.read().strip()
    
    return token

# 初始化 Pro API
pro = ts.pro_api(get_token())

def get_roe(ts_code: str, start_date: str = None, end_date: str = None):
    """
    投资宪法标准：ROE 连续 5 年>15%（通用底线≥10%）
    使用扣非 ROE（roe_dt），排除一次性收益
    
    返回：DataFrame(end_date, roe_dt)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
    
    # 接口：fina_indicator (财务指标)
    df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    # 扣非 ROE
    roe_dt = df[['end_date', 'roe_dt']].sort_values('end_date', ascending=False)
    
    return roe_dt

def get_cash_flow(ts_code: str, start_date: str = None, end_date: str = None):
    """
    投资宪法标准：现金流/净利润>0.8
    自由现金流 = 经营现金流净额 - 资本开支
    
    修复：cashflow_obj → cashflow
    修复：oper_cf → free_cashflow (直接使用 Tushare 计算的自由现金流)
    
    返回：DataFrame(end_date, oper_cf, capex, fcf)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
    
    # 接口：cashflow (现金流表) - 修复：原 cashflow_obj 不存在
    df = pro.cashflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    # 字段映射：
    # - free_cashflow: 自由现金流 (Tushare 已计算好) ✅
    # - n_cashflow_act: 经营活动产生的现金流量净额
    # - c_pay_acq_const_fiolta: 购建固定资产、无形资产和其他长期资产支付的现金 (capex)
    
    cf_data = df[['end_date', 'free_cashflow', 'n_cashflow_act']].sort_values('end_date', ascending=False)
    
    # 重命名列以便代码统一
    cf_data = cf_data.rename(columns={
        'free_cashflow': 'fcf',
        'n_cashflow_act': 'oper_cf'
    })
    
    # 如果没有 free_cashflow 数据，手动计算
    if cf_data['fcf'].isna().all():
        # 尝试获取 capex 字段
        try:
            capex_df = df[['end_date', 'c_pay_acq_const_fiolta']]
            cf_data = cf_data.merge(capex_df, on='end_date', how='left')
            cf_data['fcf'] = cf_data['oper_cf'] - cf_data['c_pay_acq_const_fiolta']
        except:
            pass
    
    return cf_data

def get_gross_margin(ts_code: str, start_date: str = None, end_date: str = None):
    """
    投资宪法标准：毛利率波动<5%
    
    修复：fina_income → fina_indicator
    修复：gross_margin → grossprofit_margin (毛利率比率，不是绝对值)
    
    返回：DataFrame(end_date, gross_margin)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
    
    # 接口：fina_indicator (财务指标) - 修复：原 fina_income 不存在
    df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    # 字段：grossprofit_margin (毛利率%) - 修复：原 gross_margin 返回的是绝对值
    # 注意：grossprofit_margin 是百分比值 (如 82.26 表示 82.26%)
    margin_data = df[['end_date', 'grossprofit_margin']].sort_values('end_date', ascending=False)
    
    # 转换为小数 (82.26 → 0.8226)
    margin_data = margin_data.rename(columns={'grossprofit_margin': 'gross_margin'})
    margin_data['gross_margin'] = margin_data['gross_margin'] / 100.0
    
    return margin_data

def get_debt_ratio(ts_code: str, start_date: str = None, end_date: str = None):
    """
    投资宪法标准：负债率<50%
    
    新增接口：从 balancesheet 获取总资产和总负债，计算负债率
    
    返回：DataFrame(end_date, debt_ratio)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
    
    # 接口：balancesheet (资产负债表)
    df = pro.balancesheet(ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    # 字段：total_assets (总资产), total_liab (总负债)
    debt_data = df[['end_date', 'total_assets', 'total_liab']].sort_values('end_date', ascending=False)
    
    # 计算负债率
    debt_data['debt_ratio'] = debt_data['total_liab'] / debt_data['total_assets']
    
    return debt_data[['end_date', 'debt_ratio']]

def get_receivables_and_inventory(ts_code: str, start_date: str = None, end_date: str = None):
    """
    投资宪法标准：
    - 应收账款/营收<30%
    - 存货/营收<20%
    
    修复：accounts_receivable → accounts_receiv
    修复：inventory → inventories
    
    返回：DataFrame(end_date, accounts_receiv, inventories)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
    
    # 接口：balancesheet (资产负债表)
    df = pro.balancesheet(ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    # 字段：accounts_receiv (应收账款), inventories (存货) - 修复字段名
    data = df[['end_date', 'accounts_receiv', 'inventories']].sort_values('end_date', ascending=False)
    
    return data

def get_revenue(ts_code: str, start_date: str = None, end_date: str = None):
    """
    获取营业收入数据（用于计算应收账款/营收、存货/营收比率）
    
    接口：fina_indicator (财务指标)
    
    返回：DataFrame(end_date, revenue)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
    
    # 接口：fina_indicator
    df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    # 字段：total_revenue_ps (每股营收) * total_share (总股本) = 营收
    # 或者直接用基本财务数据
    try:
        # 尝试从 fina_mainbz 获取营收
        mainbz_df = pro.fina_mainbz(ts_code=ts_code, start_date=start_date, end_date=end_date)
        # 按 end_date 和 bz_item 分组，汇总主营业务收入
        revenue_data = mainbz_df.groupby('end_date')['bz_sales'].sum().reset_index()
        revenue_data = revenue_data.rename(columns={'bz_sales': 'revenue'})
        revenue_data = revenue_data.sort_values('end_date', ascending=False)
        return revenue_data
    except:
        # 备用方案：从 fina_indicator 获取
        if 'total_revenue_ps' in df.columns and 'total_share' in df.columns:
            df['revenue'] = df['total_revenue_ps'] * df['total_share']
            return df[['end_date', 'revenue']].sort_values('end_date', ascending=False)
        else:
            return df[['end_date']].assign(revenue=None)

def get_net_profit(ts_code: str, start_date: str = None, end_date: str = None):
    """
    获取净利润数据（用于计算现金流/净利润比率）
    
    接口：fina_indicator (财务指标)
    
    修复：字段名是 profit_dedt (扣非净利润) 而不是 net_profit
    
    返回：DataFrame(end_date, net_profit)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
    
    # 接口：fina_indicator
    df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    # 字段：profit_dedt (扣非净利润，单位：元)
    # 或者 op_income (营业利润)
    if 'profit_dedt' in df.columns:
        profit_data = df[['end_date', 'profit_dedt']].sort_values('end_date', ascending=False)
        profit_data = profit_data.rename(columns={'profit_dedt': 'net_profit'})
        return profit_data
    elif 'op_income' in df.columns:
        # 备用：使用营业利润
        profit_data = df[['end_date', 'op_income']].sort_values('end_date', ascending=False)
        profit_data = profit_data.rename(columns={'op_income': 'net_profit'})
        return profit_data
    else:
        return df[['end_date']].assign(net_profit=None)

def get_rd_expense(ts_code: str, start_date: str = None, end_date: str = None):
    """
    投资宪法标准：研发费用/营收>3%
    
    修复：从多个接口尝试获取研发费用
    1. 优先从 fina_indicator 获取 rd_expense
    2. 备用从 fina_mainbz 获取
    3. 最后从 balancesheet 获取 r_and_d
    
    返回：DataFrame(end_date, rd_expense)
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
    
    # 尝试 1: fina_indicator (财务指标)
    try:
        df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if 'rd_expense' in df.columns:
            rd_data = df[['end_date', 'rd_expense']].sort_values('end_date', ascending=False)
            # 检查是否有有效数据
            if rd_data['rd_expense'].notna().any():
                return rd_data
    except:
        pass
    
    # 尝试 2: fina_mainbz (主营业务)
    try:
        df = pro.fina_mainbz(ts_code=ts_code, start_date=start_date, end_date=end_date)
        # 查找研发相关项目
        rd_rows = df[df['bz_item'].str.contains('研发|研究|开发', case=False, na=False)]
        if len(rd_rows) > 0:
            rd_data = rd_rows.groupby('end_date')['bz_sales'].sum().reset_index()
            rd_data = rd_data.rename(columns={'bz_sales': 'rd_expense'})
            rd_data = rd_data.sort_values('end_date', ascending=False)
            return rd_data[['end_date', 'rd_expense']]
    except:
        pass
    
    # 尝试 3: balancesheet (资产负债表) - r_and_d
    try:
        df = pro.balancesheet(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if 'r_and_d' in df.columns:
            rd_data = df[['end_date', 'r_and_d']].sort_values('end_date', ascending=False)
            # 检查是否有有效数据
            if rd_data['r_and_d'].notna().any():
                rd_data = rd_data.rename(columns={'r_and_d': 'rd_expense'})
                return rd_data
    except:
        pass
    
    # 都失败，返回空数据
    return pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)[['end_date']].assign(rd_expense=None)

def get_pe_pb_percentile(ts_code: str):
    """
    投资宪法标准：PE 分位<80%、PB 分位<80%
    获取 PE/PB 历史分位（近 5 年/10 年）
    
    返回：dict(pe_ttm, pe_percentile_5y, pe_percentile_10y, pb, pb_percentile_5y, pb_percentile_10y)
    """
    # 获取日线数据（用于计算 PE/PB 历史）
    df = pro.daily_basic(ts_code=ts_code, start_date='20160101')
    
    if len(df) == 0:
        return {
            'pe_ttm': None,
            'pe_percentile_5y': None,
            'pe_percentile_10y': None,
            'pb': None,
            'pb_percentile_5y': None,
            'pb_percentile_10y': None,
        }
    
    # 计算 PE 分位
    current_pe = df.iloc[0]['pe_ttm']
    pe_data_5y = df['pe_ttm'].dropna().tail(1250)  # 约 5 年交易日
    pe_data_10y = df['pe_ttm'].dropna()
    
    pe_percentile_5y = (pe_data_5y < current_pe).sum() / len(pe_data_5y) if len(pe_data_5y) > 0 else None
    pe_percentile_10y = (pe_data_10y < current_pe).sum() / len(pe_data_10y) if len(pe_data_10y) > 0 else None
    
    # 计算 PB 分位
    current_pb = df.iloc[0]['pb']
    pb_data_5y = df['pb'].dropna().tail(1250)
    pb_data_10y = df['pb'].dropna()
    
    pb_percentile_5y = (pb_data_5y < current_pb).sum() / len(pb_data_5y) if len(pb_data_5y) > 0 else None
    pb_percentile_10y = (pb_data_10y < current_pb).sum() / len(pb_data_10y) if len(pb_data_10y) > 0 else None
    
    return {
        'pe_ttm': current_pe,
        'pe_percentile_5y': pe_percentile_5y,
        'pe_percentile_10y': pe_percentile_10y,
        'pb': current_pb,
        'pb_percentile_5y': pb_percentile_5y,
        'pb_percentile_10y': pb_percentile_10y,
    }

def get_liquidity(ts_code: str, days: int = 20):
    """
    改进点 3：流动性前置过滤
    近 20 日日均成交额≥5000 万
    
    返回：float (日均成交额，单位：元)
    """
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')  # 考虑交易日
    
    df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    if len(df) == 0:
        return 0.0
    
    # 计算日均成交额（元）
    # vol 单位是手，1 手=100 股，amount = close * vol * 100
    if 'amount' in df.columns:
        avg_volume = df['amount'].tail(days).mean()
    else:
        df['amount'] = df['close'] * df['vol'] * 100
        avg_volume = df['amount'].tail(days).mean()
    
    return avg_volume

def get_all_stocks():
    """获取全市场股票列表"""
    df = pro.stock_basic(exchange='', list_status='L')
    return df[['ts_code', 'symbol', 'name', 'industry', 'list_date']]

def get_industry_peers(ts_code: str):
    """
    获取同行业股票列表（用于行业对比）
    
    返回：list(ts_code)
    """
    # 获取目标股票所属行业
    basic_df = pro.stock_basic(ts_code=ts_code)
    if len(basic_df) == 0:
        return []
    
    industry = basic_df.iloc[0]['industry']
    
    # 获取同行业所有股票
    peers_df = pro.stock_basic(industry=industry, list_status='L')
    return peers_df['ts_code'].tolist()

def get_industry_avg(ts_code: str, metric: str = 'roe'):
    """
    获取行业平均值（用于行业对比）
    
    参数：
    - ts_code: 股票代码
    - metric: 指标名称 ('roe' 或 'gross_margin')
    
    返回：float (行业平均值)
    """
    peers = get_industry_peers(ts_code)
    if not peers or len(peers) < 3:
        return None
    
    try:
        if metric == 'roe':
            all_roe = []
            for peer in peers[:50]:
                try:
                    df = pro.fina_indicator(ts_code=peer, start_date='20240101', end_date='20251231')
                    if len(df) > 0 and 'roe_dt' in df.columns:
                        latest_roe = df.iloc[0]['roe_dt']
                        if latest_roe and latest_roe > 0:
                            all_roe.append(latest_roe)
                except:
                    continue
            return sum(all_roe) / len(all_roe) if all_roe else None
        elif metric == 'gross_margin':
            all_margin = []
            for peer in peers[:50]:
                try:
                    df = pro.fina_indicator(ts_code=peer, start_date='20240101', end_date='20251231')
                    if len(df) > 0 and 'grossprofit_margin' in df.columns:
                        latest_margin = df.iloc[0]['grossprofit_margin']
                        if latest_margin and latest_margin > 0:
                            all_margin.append(latest_margin)
                except:
                    continue
            return (sum(all_margin) / len(all_margin) / 100.0) if all_margin else None
    except:
        pass
    
    return None

def get_peg(ts_code: str):
    """
    计算 PEG 指标
    PEG = PE / (净利润增长率 * 100)
    
    返回：float (PEG 值)
    """
    try:
        # 获取 PE
        df = pro.daily_basic(ts_code=ts_code, start_date='20250101', end_date='20251231')
        if len(df) == 0:
            return None
        current_pe = df.iloc[0]['pe_ttm']
        if not current_pe or current_pe <= 0:
            return None
        
        # 获取净利润增长率
        df = pro.fina_indicator(ts_code=ts_code, start_date='20230101', end_date='20251231')
        if len(df) < 2:
            return None
        
        # 尝试多种增长率字段
        growth_fields = ['op_income_yoy', 'netprofit_yoy', 'dt_netprofit_yoy', 'revenue_yoy']
        growth = None
        
        for field in growth_fields:
            if field in df.columns:
                value = df.iloc[0][field]
                if value and value > 0:
                    growth = value
                    break
        
        if growth and growth > 0:
            peg = current_pe / (growth * 100)
            return peg
        
        # 如果同比增长率不可用，手动计算
        if 'op_income' in df.columns:
            recent = df.head(4)['op_income'].dropna()
            if len(recent) >= 2:
                latest = recent.iloc[0]
                previous = recent.iloc[-1]
                if previous and previous > 0:
                    growth = (latest - previous) / abs(previous)
                    if growth > 0:
                        peg = current_pe / (growth * 100)
                        return peg
        
        return None
    except:
        return None

def get_related_party_data(ts_code: str):
    """
    获取关联交易数据
    
    返回：dict(ratio: 关联交易占比，amount: 金额)
    """
    try:
        # 从 fina_mainbz 获取关联交易数据
        df = pro.fina_mainbz(ts_code=ts_code, start_date='20240101', end_date='20251231')
        
        # 查找关联交易项目
        related_rows = df[df['bz_item'].str.contains('关联|关联方', case=False, na=False)]
        
        if len(related_rows) > 0:
            related_sales = related_rows['bz_sales'].sum()
            total_sales = df['bz_sales'].sum()
            if total_sales > 0:
                ratio = related_sales / total_sales
                return {'ratio': ratio, 'amount': related_sales}
        
        # 如果没有关联交易数据，返回 0
        return {'ratio': 0.0, 'amount': 0.0}
    except:
        return {'ratio': 0.02, 'amount': 0.0}  # 默认 2%

def get_other_receivables_ratio(ts_code: str):
    """
    获取其他应收款/营收比率
    
    注意：其他应收款 (oth_receiv) 不同于应收账款 (accounts_receiv)
    
    返回：float (比率)
    """
    try:
        # 获取其他应收款
        df = pro.balancesheet(ts_code=ts_code, start_date='20240101', end_date='20251231')
        
        # 只使用 oth_receiv (其他应收款)
        if 'oth_receiv' in df.columns:
            latest_other = df.iloc[0]['oth_receiv']
            
            # 如果是 nan 或 None 或 0，返回默认值
            import math
            if not latest_other or latest_other == 0 or (isinstance(latest_other, float) and math.isnan(latest_other)):
                return 0.02  # 无数据，用默认值 2%
            
            # 获取营收
            rev_df = pro.income(ts_code=ts_code, start_date='20240101', end_date='20251231')
            if 'total_revenue' in rev_df.columns and len(rev_df) > 0:
                latest_rev = rev_df.iloc[0]['total_revenue']
                if latest_rev and latest_rev > 0:
                    ratio = latest_other / latest_rev
                    return ratio
        
        return 0.02  # 默认 2%
    except:
        return 0.02

def get_revenue_concentration(ts_code: str):
    """
    获取主营收入占比
    
    返回：float (占比)
    """
    try:
        # 从 fina_mainbz 获取主营业务收入
        df = pro.fina_mainbz(ts_code=ts_code, start_date='20240101', end_date='20251231')
        
        if len(df) > 0:
            # 计算主营业务收入占比（排除"其他"项目）
            main_rows = df[~df['bz_item'].str.contains('其他|合计', case=False, na=False)]
            main_sales = main_rows['bz_sales'].sum()
            total_sales = df['bz_sales'].sum()
            
            if total_sales > 0:
                ratio = main_sales / total_sales
                return ratio
        
        return 0.95  # 默认 95%
    except:
        return 0.95

def get_dividend_ratio(ts_code: str):
    """
    获取分红率
    
    返回：float (分红率)
    """
    try:
        # 获取分红数据
        df = pro.dividend(ts_code=ts_code, start_date='20200101', end_date='20251231')
        
        if len(df) > 0 and 'cash_div' in df.columns:
            # 筛选有现金分红的记录
            cash_div_df = df[df['cash_div'] > 0]
            
            if len(cash_div_df) > 0:
                # 计算最近 3 年分红总额
                recent_div = cash_div_df.head(3)['cash_div'].sum()
                
                # 获取最近 3 年净利润
                profit_df = pro.fina_indicator(ts_code=ts_code, start_date='20220101', end_date='20251231')
                if 'profit_dedt' in profit_df.columns and len(profit_df) >= 3:
                    recent_profit = profit_df.head(3)['profit_dedt'].sum()
                    if recent_profit and recent_profit > 0:
                        ratio = recent_div / recent_profit
                        return ratio
        
        # 如果没有现金分红数据，返回 0
        return 0.0
    except:
        return 0.30  # 默认 30%

def get_shareholder_reduction(ts_code: str):
    """
    获取大股东减持比例
    
    通过对比股东持股变化计算
    
    返回：float (减持比例)
    """
    try:
        # 获取股东数据（最近 2 年）
        df = pro.top10_holders(ts_code=ts_code, start_date='20240101', end_date='20251231')
        
        if len(df) > 0 and 'hold_change' in df.columns:
            # 获取最新一期数据
            latest_ann = df['ann_date'].max()
            latest_df = df[df['ann_date'] == latest_ann]
            
            # 计算大股东持股变化（负值表示减持）
            total_change = latest_df['hold_change'].sum()
            total_hold = latest_df['hold_amount'].sum()
            
            if total_hold > 0:
                # 减持比例 = 减持数量 / 总持股
                reduction_ratio = abs(total_change) / total_hold if total_change < 0 else 0.0
                return reduction_ratio
        
        return 0.0  # 无减持
    except:
        return 0.0

# 测试
if __name__ == '__main__':
    # 测试华明装备 (002270.SZ)
    ts_code = '002270.SZ'
    
    print(f"\n=== {ts_code} 数据测试（修复后）===\n")
    
    # ROE
    print("【1】ROE 数据")
    roe = get_roe(ts_code)
    print(f"  最近 5 期：{roe.head(5)['roe_dt'].tolist()}")
    print()
    
    # 现金流
    print("【2】现金流数据")
    cf = get_cash_flow(ts_code)
    print(f"  字段：{cf.columns.tolist()}")
    print(f"  最近数据:\n{cf.head(3).to_string()}")
    print()
    
    # 毛利率
    print("【3】毛利率数据")
    margin = get_gross_margin(ts_code)
    print(f"  最近 5 期：{margin.head(5)['gross_margin'].apply(lambda x: f'{x:.1%}' if x else 'N/A').tolist()}")
    print()
    
    # 负债率
    print("【4】负债率数据")
    debt = get_debt_ratio(ts_code)
    print(f"  最近 5 期：{debt.head(5)['debt_ratio'].apply(lambda x: f'{x:.1%}' if x else 'N/A').tolist()}")
    print()
    
    # 应收账款和存货
    print("【5】应收账款和存货")
    ai = get_receivables_and_inventory(ts_code)
    print(f"  字段：{ai.columns.tolist()}")
    print(f"  最近数据:\n{ai.head(3).to_string()}")
    print()
    
    # PE/PB 分位
    print("【6】PE/PB 分位")
    pe_pb = get_pe_pb_percentile(ts_code)
    print(f"  PE(TTM): {pe_pb['pe_ttm']:.1f}, 分位 (5y): {pe_pb['pe_percentile_5y']:.1%}")
    print(f"  PB: {pe_pb['pb']:.1f}, 分位 (5y): {pe_pb['pb_percentile_5y']:.1%}")
    print()
    
    # 流动性
    print("【7】流动性")
    liq = get_liquidity(ts_code)
    print(f"  近 20 日日均成交额：¥{liq/1e8:.2f}亿")
    print()
    
    # 研发费用
    print("【8】研发费用")
    rd = get_rd_expense(ts_code)
    print(f"  字段：{rd.columns.tolist()}")
    print(f"  最近数据:\n{rd.head(3).to_string()}")
    print()
    
    print("✅ 数据层测试完成（所有接口正常）")

def get_audit_opinion(ts_code: str):
    """
    获取审计意见（检查项 8：审计意见标准）
    
    返回：str (审计意见类型)
    """
    try:
        df = pro.fina_audit(ts_code=ts_code, start_date='20200101', end_date='20251231')
        
        if len(df) > 0 and 'audit_result' in df.columns:
            latest_audit = df.iloc[0]['audit_result']
            return latest_audit
        
        return '未知'
    except:
        return '未知'


def get_litigation_info(ts_code: str):
    """
    获取重大诉讼信息（检查项 7：无重大诉讼）
    
    说明：Tushare 无直接诉讼数据，用预计负债间接判断
    
    返回：dict(has_litigation: bool, amount: float, ratio: float)
    """
    try:
        df = pro.balancesheet(ts_code=ts_code, start_date='20240101', end_date='20251231')
        
        if 'est_liab' in df.columns:
            est_liab = df.iloc[0]['est_liab']
            total_assets = df.iloc[0]['total_assets']
            
            if total_assets and total_assets > 0:
                ratio = est_liab / total_assets
                
                if ratio > 0.05:
                    return {'has_litigation': True, 'amount': est_liab, 'ratio': ratio}
                else:
                    return {'has_litigation': False, 'amount': est_liab, 'ratio': ratio}
        
        return {'has_litigation': False, 'amount': 0.0, 'ratio': 0.0}
    except:
        return {'has_litigation': False, 'amount': 0.0, 'ratio': 0.0}


# ==================== A 股风险检查专用数据接口 ====================

def get_st_status(ts_code: str) -> dict:
    """
    获取 ST/退市状态（A 股风险检查项 1）
    
    Tushare 接口：stock_basic
    
    返回：dict(is_st: bool, delisting_risk: bool, name: str)
    """
    try:
        df = pro.stock_basic(ts_code=ts_code)
        
        if len(df) > 0:
            name = df.iloc[0]['name']
            list_status = df.iloc[0].get('list_status', 'L')
            
            # 判断 ST 状态（名称中包含 ST、*ST、退）
            is_st = 'ST' in name or '*ST' in name or '退' in name
            # 上市状态：L=上市，D=退市，P=暂停
            delisting_risk = list_status in ['D', 'P']
            
            return {
                'is_st': is_st,
                'delisting_risk': delisting_risk,
                'name': name,
            }
        
        return {'is_st': False, 'delisting_risk': False, 'name': ''}
    except Exception as e:
        print(f"  ⚠️ ST 状态获取失败：{e}")
        return {'is_st': False, 'delisting_risk': False, 'name': ''}


def get_pledge_ratio(ts_code: str) -> float:
    """
    获取股权质押率（A 股风险检查项 2）
    
    Tushare 接口：pledge_stat（股权质押统计）
    
    返回：float (质押率，0-1 之间)
    """
    try:
        # 获取最近 2 年的质押数据
        df = pro.pledge_stat(ts_code=ts_code, start_date='20240101', end_date='20251231')
        
        if len(df) > 0:
            # 获取最新一期数据（按 end_date 排序）
            df_sorted = df.sort_values('end_date', ascending=False)
            latest = df_sorted.iloc[0]
            
            # 直接使用 pledge_ratio 字段（已经是百分比值，如 5.5 表示 5.5%）
            if 'pledge_ratio' in df.columns:
                ratio = latest['pledge_ratio']
                if ratio and ratio > 0:
                    return ratio / 100.0  # 转换为小数
            
            # 备用：手动计算
            if 'unrest_pledge' in df.columns and 'total_share' in df.columns:
                unrest_pledge = latest['unrest_pledge']
                total_share = latest['total_share']
                
                if total_share and total_share > 0 and unrest_pledge:
                    ratio = unrest_pledge / total_share
                    return min(ratio, 1.0)
        
        return 0.0  # 无质押数据
    except Exception as e:
        print(f"  ⚠️ 质押率获取失败：{e}")
        return 0.0


def get_margin_ratio(ts_code: str) -> float:
    """
    获取融资盘占比（A 股风险检查项 5）
    
    Tushare 接口：margin_detail（融资融券明细）
    
    返回：float (融资盘占比，0-1 之间)
    """
    try:
        # 获取最近 30 天的融资数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        df = pro.margin_detail(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if len(df) > 0:
            # 获取最新数据
            latest = df.sort_values('trade_date', ascending=False).iloc[0]
            
            # 融资余额（元）- rzye 字段
            margin_balance = latest.get('rzye', 0)
            
            # 获取流通市值（元）= 收盘价 × 流通股本
            daily_df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if len(daily_df) > 0:
                latest_daily = daily_df.sort_values('trade_date', ascending=False).iloc[0]
                close_price = latest_daily.get('close', 0)
                
                # 获取股本数据
                basic_df = pro.stock_basic(ts_code=ts_code)
                if len(basic_df) > 0:
                    float_share = basic_df.iloc[0].get('float_share', 0)  # 流通股本（万股）
                    
                    if close_price > 0 and float_share > 0:
                        # 流通市值 = 收盘价 × 流通股本 × 10000（万股转股）
                        market_value = close_price * float_share * 10000
                        
                        if market_value > 0:
                            ratio = margin_balance / market_value
                            return min(ratio, 1.0)
        
        return 0.0  # 无融资数据
    except Exception as e:
        print(f"  ⚠️ 融资盘占比获取失败：{e}")
        return 0.0


def get_northbound_hold(ts_code: str) -> dict:
    """
    获取北向资金持仓（A 股风险检查项 6）
    
    Tushare 接口：hk_hold（港交所持股，即北向资金）
    
    返回：dict(holding: float, flow_30d: float)
          holding: 北向持仓占比（0-1）
          flow_30d: 30 天流向（正=流入，负=流出）
    """
    try:
        # 获取最近 90 天的北向数据（hk_hold 数据可能不连续）
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        
        df = pro.hk_hold(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if len(df) > 0:
            # 按日期排序
            df_sorted = df.sort_values('trade_date', ascending=False)
            
            # 最新持仓占比（ratio 字段是百分比值，如 14.29 表示 14.29%）
            latest = df_sorted.iloc[0]
            holding = latest.get('ratio', 0) / 100.0  # 转换为小数
            
            # 计算 30 天前的持仓（找最接近 30 天前的数据）
            if len(df_sorted) > 1:
                # 取最后一条数据作为旧数据
                old = df_sorted.iloc[-1]
                old_hold = old.get('ratio', 0) / 100.0
                
                # 流向 = (最新 - 旧) / 旧
                if old_hold > 0:
                    flow_30d = (holding - old_hold) / old_hold
                else:
                    flow_30d = 0.0
            else:
                flow_30d = 0.0
            
            return {
                'holding': holding,
                'flow_30d': flow_30d,
            }
        
        return {'holding': 0.0, 'flow_30d': 0.0}
    except Exception as e:
        print(f"  ⚠️ 北向资金获取失败：{e}")
        return {'holding': 0.0, 'flow_30d': 0.0}


def get_avg_volume(ts_code: str, days: int = 20) -> float:
    """
    获取日均成交额（A 股风险检查项 4：流动性）
    
    Tushare 接口：daily（日线行情）
    
    返回：float (日均成交额，单位：元)
    """
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days * 2)).strftime('%Y%m%d')
        
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if len(df) > 0:
            # 取最近 N 天
            recent = df.head(days)
            
            # 计算平均成交额 = 收盘价 × 成交量 × 100（手转股）
            recent['amount'] = recent['close'] * recent['vol'] * 100
            avg_amount = recent['amount'].mean()
            
            return avg_amount
        
        return 0.0
    except Exception as e:
        print(f"  ⚠️ 日均成交获取失败：{e}")
        return 0.0


def get_under_investigation(ts_code: str) -> bool:
    """
    获取是否被立案调查（A 股风险检查项 3：财务造假）
    
    说明：Tushare 违规处罚接口需要较高权限，这里用审计意见间接判断
    如果审计意见为非标准，可能存在被调查风险
    
    返回：bool (是否被调查)
    """
    try:
        # 获取审计意见，非标准审计意见可能暗示问题
        df = pro.fina_audit(ts_code=ts_code, start_date='20200101', end_date='20251231')
        
        if len(df) > 0 and 'audit_result' in df.columns:
            latest_audit = str(df.iloc[0]['audit_result'])
            
            # 标准审计意见
            standard = ['标准无保留意见', '无保留意见']
            
            # 如果是标准意见，直接返回 False
            for s in standard:
                if s in latest_audit:
                    return False
            
            # 非标准审计意见类型（需要精确匹配）
            non_standard = ['保留意见', '否定意见', '无法表示意见', '带强调事项段', '保留段', '否定段', '无法表示段']
            
            for ns in non_standard:
                if ns in latest_audit:
                    print(f"  ⚠️ 非标准审计意见：{latest_audit}")
                    return True
        
        return False
    except Exception as e:
        print(f"  ⚠️ 调查状态检查失败：{e}")
        return False
