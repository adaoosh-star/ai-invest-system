"""
公告下载子代理
- 全量下载上市公司公告
- 遵守 Tushare 规则（单次最大 2000 条）
- 保存到本地固定文件夹
- 支持增量下载
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import time
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.tushare_client import pro

# 配置
DOWNLOAD_DIR = Path(__file__).parent.parent.parent / 'data' / 'announcements'
STATE_FILE = DOWNLOAD_DIR / 'download_state.json'
BATCH_SIZE = 2000  # Tushare 限制单次最大 2000 条
DELAY_SECONDS = 1  # 请求间隔，避免触发限流


def get_download_state():
    """获取下载状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'last_update': None,
        'last_date': None,
        'total_downloaded': 0,
        'stocks_processed': [],
    }


def save_download_state(state):
    """保存下载状态"""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def download_announcements(ts_code: str, start_date: str, end_date: str, download_pdf: bool = False):
    """
    下载公告（分批下载，遵守 Tushare 限制）
    
    参数：
    - ts_code: 股票代码
    - start_date: 开始日期 YYYYMMDD
    - end_date: 结束日期 YYYYMMDD
    - download_pdf: 是否下载 PDF 文件
    
    返回：dict
    """
    result = {
        'ts_code': ts_code,
        'status': 'success',
        'total': 0,
        'batches': 0,
        'pdf_downloaded': 0,
    }
    
    # 创建股票专属文件夹
    stock_dir = DOWNLOAD_DIR / ts_code.replace('.', '_')
    stock_dir.mkdir(parents=True, exist_ok=True)
    
    # 计算日期范围
    start = datetime.strptime(start_date, '%Y%m%d')
    end = datetime.strptime(end_date, '%Y%m%d')
    total_days = (end - start).days + 1
    
    # 分批下载（按日期分，避免超过 2000 条限制）
    # 假设每天最多 5 条公告，每批最多 400 天
    batch_days = 400
    current_start = start
    
    while current_start <= end:
        batch_end = min(current_start + timedelta(days=batch_days-1), end)
        
        try:
            # 获取公告列表
            df = pro.anns_d(
                ts_code=ts_code,
                start_date=current_start.strftime('%Y%m%d'),
                end_date=batch_end.strftime('%Y%m%d')
            )
            
            if len(df) > 0:
                result['total'] += len(df)
                result['batches'] += 1
                
                # 保存公告元数据
                metadata_file = stock_dir / f'announcements_{current_start.strftime("%Y%m%d")}_{batch_end.strftime("%Y%m%d")}.csv'
                df.to_csv(metadata_file, index=False, encoding='utf-8-sig')
                
                # 下载 PDF（可选）
                if download_pdf and 'pdf_url' in df.columns:
                    pdf_dir = stock_dir / 'pdfs'
                    pdf_dir.mkdir(exist_ok=True)
                    
                    for _, row in df.iterrows():
                        if row.get('pdf_url'):
                            pdf_path = download_pdf_file(row['pdf_url'], pdf_dir)
                            if pdf_path:
                                result['pdf_downloaded'] += 1
                
                print(f"  ✅ 下载 {current_start.strftime('%Y%m%d')}-{batch_end.strftime('%Y%m%d')}: {len(df)} 条公告")
            
            # 等待，避免触发限流
            time.sleep(DELAY_SECONDS)
            
        except Exception as e:
            print(f"  ❌ 下载失败 {current_start.strftime('%Y%m%d')}-{batch_end.strftime('%Y%m%d')}: {e}")
            result['status'] = 'partial'
        
        current_start = batch_end + timedelta(days=1)
    
    return result


def download_pdf_file(pdf_url: str, save_dir: Path):
    """
    下载单个 PDF 文件
    
    参数：
    - pdf_url: PDF 下载地址
    - save_dir: 保存目录
    
    返回：str (保存路径) 或 None
    """
    try:
        import requests
        
        filename = pdf_url.split('/')[-1]
        # 清理文件名
        filename = filename.replace('?download=1', '').replace('?download=true', '')
        save_path = save_dir / filename
        
        # 如果已存在，跳过
        if save_path.exists():
            return str(save_path)
        
        response = requests.get(pdf_url, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return str(save_path)
        else:
            return None
    except Exception as e:
        print(f"    ⚠️ PDF 下载失败：{e}")
        return None


def run_full_download(ts_codes: list = None, download_pdf: bool = True):
    """
    全量下载公告
    
    参数：
    - ts_codes: 股票代码列表，None 表示全市场
    - download_pdf: 是否下载 PDF（默认 True，充分利用已开通的权限）
    
    注意：anns_d 接口已开通权限，API 调用不再产生额外费用
    本地存储 PDF 可提高系统运行效率，避免重复调用 API
    """
    print("=" * 60)
    print("公告下载子代理 - 全量下载")
    print("=" * 60)
    print()
    print(f"PDF 下载：{'✅ 启用' if download_pdf else '❌ 禁用'}")
    if download_pdf:
        print("说明：anns_d 接口权限已开通，本地存储 PDF 可提高系统效率")
    print()
    
    # 获取下载状态
    state = get_download_state()
    print(f"上次更新：{state.get('last_update', '从未')}")
    print(f"已下载公告：{state.get('total_downloaded', 0)} 条")
    print()
    
    # 如果没有指定股票列表，获取全市场
    if ts_codes is None:
        print("获取全市场股票列表...")
        try:
            df = pro.stock_basic(list_status='L')
            ts_codes = df['ts_code'].tolist()
            print(f"全市场股票：{len(ts_codes)} 只")
        except Exception as e:
            print(f"获取股票列表失败：{e}")
            return
    
    # 下载公告
    for i, ts_code in enumerate(ts_codes, 1):
        print(f"\n[{i}/{len(ts_codes)}] 下载 {ts_code} 公告...")
        
        # 下载最近 1 年公告
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        result = download_announcements(ts_code, start_date, end_date, download_pdf)
        
        # 更新状态
        state['total_downloaded'] += result['total']
        if ts_code not in state['stocks_processed']:
            state['stocks_processed'].append(ts_code)
        state['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        state['last_date'] = end_date
        
        # 每 10 只股票保存一次状态
        if i % 10 == 0:
            save_download_state(state)
    
    # 保存最终状态
    save_download_state(state)
    
    print()
    print("=" * 60)
    print("✅ 全量下载完成")
    print(f"总公告数：{state['total_downloaded']} 条")
    print(f"处理股票：{len(state['stocks_processed'])} 只")
    print(f"保存位置：{DOWNLOAD_DIR}")
    print("=" * 60)


def run_incremental_download(ts_codes: list = None, download_pdf: bool = True):
    """
    增量下载公告（只下载上次之后的新公告）
    
    参数：
    - ts_codes: 股票代码列表
    - download_pdf: 是否下载 PDF（默认 True，充分利用已开通的权限）
    """
    print("=" * 60)
    print("公告下载子代理 - 增量下载")
    print("=" * 60)
    print()
    print(f"PDF 下载：{'✅ 启用' if download_pdf else '❌ 禁用'}")
    print()
    
    # 获取下载状态
    state = get_download_state()
    last_date = state.get('last_date')
    
    if not last_date:
        print("⚠️ 无上次下载记录，执行全量下载")
        run_full_download(ts_codes, download_pdf)
        return
    
    print(f"上次下载日期：{last_date}")
    start_date = last_date
    end_date = datetime.now().strftime('%Y%m%d')
    print(f"下载范围：{start_date} - {end_date}")
    print()
    
    # 如果没有指定股票列表，使用上次处理过的
    if ts_codes is None:
        ts_codes = state.get('stocks_processed', [])
    
    # 增量下载
    for i, ts_code in enumerate(ts_codes, 1):
        print(f"\n[{i}/{len(ts_codes)}] 下载 {ts_code} 新公告...")
        
        result = download_announcements(ts_code, start_date, end_date, download_pdf)
        
        # 更新状态
        state['total_downloaded'] += result['total']
        state['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        state['last_date'] = end_date
    
    # 保存状态
    save_download_state(state)
    
    print()
    print("=" * 60)
    print("✅ 增量下载完成")
    print(f"总公告数：{state['total_downloaded']} 条")
    print("=" * 60)


# 主程序
if __name__ == '__main__':
    import sys
    
    # 默认下载华明装备（测试用）
    if len(sys.argv) > 1:
        if sys.argv[1] == 'full':
            # 全量下载
            ts_codes = sys.argv[2:] if len(sys.argv) > 2 else None
            run_full_download(ts_codes, download_pdf=False)
        elif sys.argv[1] == 'incremental':
            # 增量下载
            ts_codes = sys.argv[2:] if len(sys.argv) > 2 else None
            run_incremental_download(ts_codes, download_pdf=False)
        else:
            # 下载指定股票
            ts_codes = sys.argv[1:]
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            for ts_code in ts_codes:
                print(f"\n下载 {ts_code} 公告...")
                result = download_announcements(ts_code, start_date, end_date, download_pdf=False)
                print(f"✅ 下载完成：{result['total']} 条公告")
    else:
        # 默认测试：下载华明装备
        ts_code = '002270.SZ'
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        print(f"测试下载 {ts_code} 公告...")
        result = download_announcements(ts_code, start_date, end_date, download_pdf=False)
        print(f"✅ 测试完成：{result['total']} 条公告")
        print(f"保存位置：{DOWNLOAD_DIR / ts_code.replace('.', '_')}")
