#!/usr/bin/env python3
import json, os, re, urllib.request
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
DATA_JS = 'data.js'
INDEX_HTML = 'index.html'
TEMPLATE = 'index.v2.html'

def fix_json(s):
    s = re.sub(r'(?<=[,\[{])\s*"', '\u201c', s)
    s = re.sub(r'"(?=\s*[,\}\]])', '\u201d', s)
    return s

try:
    with open(DATA_JS) as f:
        old = f.read()
    m = re.search(r'"issue":\s*(\d+)', old)
    old_issue = int(m.group(1)) if m else 0
except:
    old_issue = 0
new_issue = old_issue + 1

today = datetime.now()
wd = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
ds = f"{today.year}年{today.month}月{today.day}日·{wd[today.weekday()]}"
print(f"📝 第{old_issue}期 → 第{new_issue}期 ({ds})")

api_key = os.environ['DEEPSEEK_API_KEY']
print("🤖 调用DeepSeek...")

payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": f"你是一位公考教研专家。日期{ds}，第{new_issue}期。输出纯JSON。字段：date(今天的日期带星期), issue({new_issue}), topic, quoteSource, quoteText, quoteScene, caseEvent, caseApply, conceptName, conceptDesc, conceptQuick, tipText, questions(12道选择题，含id,type,question,options（4个选项数组）,answer（0-3）,analysis）。字符串中双引号用中文引号"},
        {"role": "user", "content": "搜索今日最新时政热点，生成晨读内容。12道题覆盖常识判断、言语理解、判断推理、数量关系各3道。"}
    ],
    "temperature": 0.7,
    "max_tokens": 8000
}
req = urllib.request.Request(
    "https://api.deepseek.com/v1/chat/completions",
    data=json.dumps(payload).encode('utf-8'),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
)
resp = urllib.request.urlopen(req, timeout=120)
content = json.loads(resp.read())["choices"][0]["message"]["content"]
content = re.sub(r'^```.*?\n', '', content)
content = re.sub(r'\n```\s*$', '', content)
data = json.loads(content)

print(f"✅ 第{data['issue']}期 - {data['date']}，{len(data.get('questions',[]))}道题")

json_str = json.dumps(data, ensure_ascii=False, indent=2)
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write("// 每日晨读数据\n")
    f.write(f"window.DAILY_DATA = {json_str};\n")

# 直接读取模板并替换DATA部分
with open(TEMPLATE, 'r', encoding='utf-8') as f:
    html = f.read()

escaped = json_str.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
replacement = "var DATA = JSON.parse('" + escaped + "');\n\n"
start = html.find('var DATA =')
end = html.find('// ===== 加载首页', start)
if start >= 0 and end >= 0:
    html = html[:start] + replacement + html[end:]

with open(INDEX_HTML, 'w', encoding='utf-8') as f:
    f.write(html)
with open('index.v2.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ 完成！")
