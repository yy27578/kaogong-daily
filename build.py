#!/usr/bin/env python3
"""
将 data.js 合并到 index.v2.html，生成自包含的 HTML。
修复 data.js 中字符串值包含未转义 ASCII 双引号的问题。
"""
import json
import re
import sys
import os

DATA_JS = os.path.join(os.path.dirname(__file__), 'data.js')
TEMPLATE = os.path.join(os.path.dirname(__file__), 'index.v2.html')
OUTPUT = os.path.join(os.path.dirname(__file__), 'index.v2.html')


def fix_json_quotes(raw):
    """修复 JSON 字符串值中未转义的 ASCII 双引号"""
    result = []
    i = 0
    in_string = False
    while i < len(raw):
        ch = raw[i]
        if ch == '"' and (i == 0 or raw[i-1] != '\\'):
            if not in_string:
                in_string = True
                result.append(ch)
            else:
                # 检查下一个非空白字符是否是 , ] } : 
                # 如果是，则这是 JSON 结构引号（字符串结束）
                j = i + 1
                while j < len(raw) and raw[j] in ' \t\n\r':
                    j += 1
                if j < len(raw) and raw[j] in ',:;]}':
                    in_string = False
                    result.append(ch)
                else:
                    # 这是字符串内部的引号，替换为中文右引号
                    result.append('\u201d')
        else:
            result.append(ch)
        i += 1
    return ''.join(result)


def parse_data_js(filepath):
    """解析 data.js 并返回字典"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # 提取 window.DAILY_DATA = { ... }
    match = re.search(r'window\.DAILY_DATA\s*=\s*(\{.*?\});?\s*$', content, re.DOTALL)
    if not match:
        print('❌ 未找到 DAILY_DATA')
        sys.exit(1)
    
    raw = match.group(1)
    
    # 修复引号问题
    fixed = fix_json_quotes(raw)
    
    # 再修复一下：中文左引号被替换为右引号后可能导致的不平衡
    # 以及问题数组中的引号
    try:
        data = json.loads(fixed)
        return data
    except json.JSONDecodeError as e:
        print(f'❌ 修复后 JSON 仍解析失败: {e}')
        print(f'问题位置: {fixed[max(0, e.pos-40):e.pos+40]}')
        sys.exit(1)


def build_html(data, template_path, output_path):
    """将数据嵌入 HTML 模板"""
    with open(template_path, 'r') as f:
        html = f.read()
    
    # 用 JSON.stringify 兼容所有特殊字符
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # 在 HTML 中使用 JSON.parse 来安全地解析数据
    escaped = json_str.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    replacement = "var DATA = JSON.parse('" + escaped + "');\n\n"
    
    # 找到 DATA 对象的起止位置
    marker_start = 'var DATA = JSON.parse(\''
    marker_end = '// ===== 加载首页'
    data_start = html.find(marker_start)
    data_end = html.find(marker_end, data_start)
    
    if data_start == -1 or data_end == -1:
        # fallback: 尝试旧格式
        marker_start = 'var DATA = {'
        data_start = html.find(marker_start)
        if data_start == -1 or data_end == -1:
            print('❌ 无法在 HTML 中找到 DATA 对象位置')
            sys.exit(1)
    
    new_html = html[:data_start] + replacement + html[data_end:]
    
    with open(output_path, 'w') as f:
        f.write(new_html)
    
    print(f'✅ 已生成自包含 HTML（第 {data["issue"]} 期 - {data["date"]}）')
    print(f'📁 {output_path}')
    print(f'📊 题数: {len(data.get("questions", []))}')


if __name__ == '__main__':
    data = parse_data_js(DATA_JS)
    build_html(data, TEMPLATE, OUTPUT)
