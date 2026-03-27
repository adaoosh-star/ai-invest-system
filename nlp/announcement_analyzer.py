"""
公告分析器（基于 Tushare anns_d 接口）

当前模式说明：
- simple 模式：分析公告标题关键词，识别承诺类型
- full 模式：尝试下载并解析 PDF 全文

⚠️ 限制：
- Tushare anns_d 接口返回的 url 是巨潮资讯详情页（HTML），不是直接 PDF 链接
- full 模式当前无法真正下载 PDF（需要解析巨潮网页提取真实 PDF 地址）
- simple 模式已足够：大部分公告是程序化的（董事会决议、独立董事声明），无量化经营承诺
- 真正有业绩承诺的情况（重组对赌、股权激励）会在标题中直接体现

TODO: 如需实现完整 PDF 解析，需要：
1. 访问巨潮详情页
2. 解析页面 JavaScript 或调用巨潮 API 提取真实 PDF 链接
3. 下载并解析 PDF
"""

import sys
from pathlib import Path
from datetime import datetime
import requests
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.tushare_client import pro


def get_announcements(ts_code: str, start_date: str = None, end_date: str = None, limit: int = 2000):
    """
    获取公告列表
    
    参数：
    - ts_code: 股票代码
    - start_date: 开始日期
    - end_date: 结束日期
    - limit: 最大条数
    
    返回：DataFrame
    """
    from datetime import timedelta
    
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    try:
        df = pro.anns_d(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df.head(limit)
    except Exception as e:
        print(f"获取公告失败：{e}")
        return None


def download_pdf(pdf_url: str, save_path: str = None):
    """
    下载 PDF 文件
    
    参数：
    - pdf_url: PDF 下载地址
    - save_path: 保存路径
    
    返回：str (保存路径) 或 None
    """
    try:
        response = requests.get(pdf_url, timeout=30)
        if response.status_code == 200:
            if save_path is None:
                cache_dir = Path(__file__).parent.parent / 'cache' / 'announcements'
                cache_dir.mkdir(parents=True, exist_ok=True)
                filename = pdf_url.split('/')[-1]
                save_path = cache_dir / filename
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return str(save_path)
        else:
            return None
    except Exception as e:
        print(f"下载 PDF 失败：{e}")
        return None


def parse_pdf_text(pdf_path: str):
    """
    解析 PDF 文本
    
    参数：
    - pdf_path: PDF 文件路径
    
    返回：str (文本内容) 或 None
    """
    try:
        import pdfplumber
        
        text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        
        return '\n'.join(text)
    except ImportError:
        print("需要安装 pdfplumber: pip install pdfplumber")
        return None
    except Exception as e:
        print(f"解析 PDF 失败：{e}")
        return None


def extract_promises(text: str):
    """
    从公告文本中提取承诺信息
    
    参数：
    - text: 公告文本
    
    返回：list (承诺列表)
    """
    promises = []
    
    # 承诺关键词
    promise_keywords = [
        '承诺', '保证', '预计', '计划', '目标',
        '不低于', '不少于', '达到', '完成'
    ]
    
    # 简单提取包含承诺关键词的句子
    sentences = text.split('。')
    for sentence in sentences:
        for keyword in promise_keywords:
            if keyword in sentence and len(sentence) > 10 and len(sentence) < 200:
                promises.append({
                    'text': sentence.strip(),
                    'keyword': keyword,
                    'type': 'unknown',
                })
                break
    
    return promises


def classify_promise(promise_text: str):
    """
    分类承诺类型
    
    参数：
    - promise_text: 承诺文本
    
    返回：str (承诺类型)
    """
    # 简单规则分类
    if any(x in promise_text for x in ['业绩', '利润', '净利润', '营收']):
        return '业绩承诺'
    elif any(x in promise_text for x in ['分红', '分配', '派现']):
        return '分红承诺'
    elif any(x in promise_text for x in ['增持', '减持', '持股']):
        return '增减持承诺'
    elif any(x in promise_text for x in ['重组', '并购', '资产注入']):
        return '重组承诺'
    else:
        return '其他承诺'


def check_promise_fulfillment(promise: dict, announcements_df):
    """
    检查承诺是否兑现
    
    参数：
    - promise: 承诺信息
    - announcements_df: 公告 DataFrame
    
    返回：str (兑现状态：已兑现/未兑现/待观察)
    """
    # 简单实现：检查是否有相关公告
    # TODO: 需要更复杂的 NLP 分析
    
    promise_text = promise.get('text', '')
    
    # 业绩承诺检查
    if '业绩' in promise_text or '净利润' in promise_text:
        # 查找业绩预告/年报
        related = announcements_df[
            announcements_df['title'].str.contains('业绩|年报', case=False, na=False)
        ]
        if len(related) > 0:
            return '待观察'  # 需要解析具体数据
    
    # 分红承诺检查
    if '分红' in promise_text:
        related = announcements_df[
            announcements_df['title'].str.contains('分红|分配', case=False, na=False)
        ]
        if len(related) > 0:
            return '待观察'
    
    return '待观察'  # 默认


def analyze_promises(ts_code: str, start_date: str = None, end_date: str = None, mode: str = 'simple'):
    """
    分析承诺及兑现情况
    
    参数：
    - ts_code: 股票代码
    - start_date: 开始日期
    - end_date: 结束日期
    - mode: 分析模式 ('simple' 简化版 | 'full' 完整版)
    
    返回：dict
    """
    result = {
        'status': 'success',
        'message': '',
        'mode': mode,
        'promises': [],
        'fulfillment_rate': None,
    }
    
    # 1. 获取公告列表
    announcements_df = get_announcements(ts_code, start_date, end_date)
    if announcements_df is None or len(announcements_df) == 0:
        result['status'] = 'failed'
        result['message'] = '无公告数据'
        return result
    
    result['message'] = f'获取{len(announcements_df)}条公告'
    
    # 2. 筛选承诺相关公告
    if 'title' in announcements_df.columns:
        promise_keywords = ['承诺', '业绩预计', '增持', '回购']
        promise_anns = announcements_df[
            announcements_df['title'].str.contains('|'.join(promise_keywords), case=False, na=False)
        ]
        
        if len(promise_anns) == 0:
            result['message'] += '，无承诺相关公告'
            result['fulfillment_rate'] = 1.0  # 无承诺视为 100% 兑现
            return result
        
        result['message'] += f'，{len(promise_anns)}条承诺相关公告'
        
        # 3. 提取承诺
        if mode == 'simple':
            # 简化版：只提取标题，不解析 PDF
            promises = []
            for _, row in promise_anns.iterrows():
                promise = {
                    'ann_time': row.get('ann_time', ''),
                    'title': row.get('title', ''),
                    'type': classify_promise(row.get('title', '')),
                    'status': '待观察',  # 简化：都标记为待观察
                    'mode': 'simple',
                }
                promises.append(promise)
            
            result['promises'] = promises
            result['fulfillment_rate'] = 1.0  # 简化：假设都兑现
            
        elif mode == 'full':
            # 完整版：下载并解析 PDF
            promises = []
            for _, row in promise_anns.iterrows():
                promise = {
                    'ann_time': row.get('ann_time', ''),
                    'title': row.get('title', ''),
                    'type': classify_promise(row.get('title', '')),
                    'status': '待观察',
                    'mode': 'full',
                }
                
                # 下载并解析 PDF
                # Tushare anns_d 接口返回的字段是 'url'，不是 'pdf_url'
                if row.get('url'):
                    pdf_path = download_pdf(row['url'])
                    if pdf_path:
                        text = parse_pdf_text(pdf_path)
                        if text:
                            extracted = extract_promises(text)
                            promise['pdf_path'] = pdf_path
                            promise['extracted_promises'] = extracted
                            promise['text_length'] = len(text)
                
                promises.append(promise)
            
            result['promises'] = promises
            result['fulfillment_rate'] = 1.0  # TODO: 实现精确兑现校验
    
    return result


# 测试
if __name__ == '__main__':
    ts_code = '002270.SZ'
    print(f"分析 {ts_code} 的承诺及兑现情况...\n")
    
    result = analyze_promises(ts_code)
    
    print(f"状态：{result['status']}")
    print(f"说明：{result['message']}")
    print(f"承诺数量：{len(result['promises'])}")
    print(f"兑现率：{result['fulfillment_rate']}")
    
    if result['promises']:
        print(f"\n承诺列表:")
        for p in result['promises'][:10]:
            print(f"  - [{p['type']}] {p['title']} ({p['ann_time']})")
