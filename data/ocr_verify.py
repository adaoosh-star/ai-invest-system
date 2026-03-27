"""
OCR 准确率校验
改进点 6：老年报扫描版 OCR 置信度<90% 标记为待人工复核
"""

def verify_ocr_confidence(ocr_result: dict) -> dict:
    """
    改进点 6：OCR 准确率校验
    
    置信度<90% → 标记为「待人工复核」
    置信度≥90% → 可自动处理
    """
    confidence = ocr_result.get('confidence', 0)
    
    if confidence < 0.90:
        return {
            'is_valid': False,
            'confidence': confidence,
            'status': '⚠️ 待人工复核',
            'message': f"OCR 置信度{confidence:.1%} < 90%，需人工复核",
        }
    else:
        return {
            'is_valid': True,
            'confidence': confidence,
            'status': '✅ 可自动处理',
            'message': f"OCR 置信度{confidence:.1%} ≥ 90%，可自动处理",
        }

def extract_promises_from_ocr(ocr_text: str) -> dict:
    """
    改进点 1：承诺分类
    从 OCR 文本中提取承诺，并分类为明确/模糊/长期
    """
    clear_promises = []  # 明确承诺："计划"、"将实现"、"目标"
    vague_promises = []  # 模糊承诺："力争"、"争取"、"努力"
    long_term_plans = []  # 长期规划：3 年期
    
    lines = ocr_text.split('\n')
    
    for line in lines:
        # 明确承诺
        if any(keyword in line for keyword in ['计划', '将实现', '目标']):
            clear_promises.append(line)
        # 模糊承诺
        elif any(keyword in line for keyword in ['力争', '争取', '努力']):
            vague_promises.append(line)
        # 长期规划
        elif any(keyword in line for keyword in ['三年', '五年', '中长期']):
            long_term_plans.append(line)
    
    return {
        'clear_promises': clear_promises,
        'vague_promises': vague_promises,
        'long_term_plans': long_term_plans,
        'summary': {
            'clear_count': len(clear_promises),
            'vague_count': len(vague_promises),
            'long_term_count': len(long_term_plans),
        }
    }

# 测试
if __name__ == '__main__':
    # 测试 OCR 置信度校验
    ocr_result_high = {'confidence': 0.95}
    ocr_result_low = {'confidence': 0.85}
    
    print(f"高置信度：{verify_ocr_confidence(ocr_result_high)}")
    print(f"低置信度：{verify_ocr_confidence(ocr_result_low)}")
    
    # 测试承诺分类
    ocr_text = """
    2025 年经营计划：
    1. 计划实现营业收入增长 15%
    2. 力争实现净利润增长 20%
    3. 目标 ROE 达到 18%
    4. 争取扩大市场份额
    5. 三年发展规划：2025-2027 年营收 CAGR≥20%
    """
    
    promises = extract_promises_from_ocr(ocr_text)
    print(f"\n承诺分类结果：{promises}")
