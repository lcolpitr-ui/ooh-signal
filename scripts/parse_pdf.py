#!/usr/bin/env python3
"""PDF 解析脚本 - 将 PDF 文件转换为 JSON 格式

使用方法:
    python scripts/parse_pdf.py <pdf文件路径>

输出:
    会在同目录下生成同名的 .json 文件
"""

import sys
import os
import json
import re

def parse_pdf(pdf_path):
    """解析 PDF 文件"""
    try:
        import pdfplumber
        return parse_with_pdfplumber(pdf_path)
    except ImportError:
        pass

    try:
        import PyPDF2
        return parse_with_pypdf2(pdf_path)
    except ImportError:
        pass

    print("错误: 需要安装 PDF 解析库")
    print("请运行: pip install pdfplumber 或 pip install PyPDF2")
    sys.exit(1)

def parse_with_pdfplumber(pdf_path):
    """使用 pdfplumber 解析 PDF"""
    import pdfplumber

    all_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # 尝试提取表格
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if len(table) >= 2:
                        headers = [str(h).strip() if h else f'列{i}' for i, h in enumerate(table[0])]
                        for row in table[1:]:
                            if any(cell for cell in row):
                                row_data = {}
                                for i, cell in enumerate(row):
                                    if i < len(headers):
                                        row_data[headers[i]] = str(cell).strip() if cell else ''
                                all_data.append(row_data)

            # 如果没有表格，提取文本
            if not tables:
                text = page.extract_text()
                if text:
                    data = parse_text_to_data(text)
                    all_data.extend(data)

    return all_data

def parse_with_pypdf2(pdf_path):
    """使用 PyPDF2 解析 PDF"""
    import PyPDF2

    all_text = ''

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                all_text += text + '\n'

    return parse_text_to_data(all_text)

def parse_text_to_data(text):
    """从文本中提取结构化数据"""
    lines = text.split('\n')
    lines = [line.strip() for line in lines if line.strip()]

    if not lines:
        return []

    # 尝试检测表格分隔符
    separator = detect_separator(lines)

    if separator:
        return parse_table_data(lines, separator)
    else:
        return parse_key_value_data(lines)

def detect_separator(lines):
    """检测文本分隔符"""
    if not lines:
        return None

    first_line = lines[0]

    # 检查制表符
    if '\t' in first_line and first_line.count('\t') >= 2:
        return '\t'

    # 检查逗号
    if ',' in first_line and first_line.count(',') >= 2:
        return ','

    # 检查多个空格
    if re.search(r'\s{2,}', first_line):
        return r'\s{2,}'

    # 检查竖线
    if '|' in first_line and first_line.count('|') >= 2:
        return '|'

    return None

def parse_table_data(lines, separator):
    """解析表格格式数据"""
    if len(lines) < 2:
        return []

    headers = re.split(separator, lines[0])
    headers = [h.strip() for h in headers if h.strip()]

    if len(headers) < 2:
        return []

    data = []
    for line in lines[1:]:
        values = re.split(separator, line)
        values = [v.strip() for v in values]

        if len(values) >= 2:
            row = {}
            for i, header in enumerate(headers):
                if i < len(values):
                    row[header] = values[i]
            data.append(row)

    return data

def parse_key_value_data(lines):
    """解析键值对格式数据"""
    data = []
    current = {}

    for line in lines:
        # 检测新条目（数字开头或特定标记）
        if re.match(r'^\d+[.、]', line) or re.match(r'^[【\[]', line):
            if current:
                data.append(current)
            current = {'名称': re.sub(r'^\d+[.、]\s*', '', line).replace('【', '').replace('】', '').replace('[', '').replace(']', '')}
            continue

        # 解析键值对
        kv_match = re.match(r'^([^：:]+)[：:](.+)$', line)
        if kv_match:
            key = kv_match.group(1).strip()
            value = kv_match.group(2).strip()
            current[key] = value
        elif current.get('名称'):
            # 附加到描述
            current['描述'] = current.get('描述', '') + line

    if current:
        data.append(current)

    return data

def main():
    if len(sys.argv) < 2:
        print("使用方法: python scripts/parse_pdf.py <pdf文件路径>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"错误: 文件不存在: {pdf_path}")
        sys.exit(1)

    if not pdf_path.lower().endswith('.pdf'):
        print("错误: 请提供 PDF 文件")
        sys.exit(1)

    print(f"正在解析: {pdf_path}")

    data = parse_pdf(pdf_path)

    if not data:
        print("警告: 未能从 PDF 中提取到数据")
        print("请确保 PDF 包含表格或结构化数据")
        sys.exit(1)

    # 生成输出文件名
    output_path = os.path.splitext(pdf_path)[0] + '.json'

    # 保存为 JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"解析完成!")
    print(f"  提取到 {len(data)} 条数据")
    print(f"  列名: {', '.join(data[0].keys()) if data else '无'}")
    print(f"  输出文件: {output_path}")
    print(f"\n请将 {output_path} 上传到资源匹配页面")

if __name__ == '__main__':
    main()
