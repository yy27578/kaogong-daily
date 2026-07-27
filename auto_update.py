#!/usr/bin/env python3
import json, os, re, subprocess, urllib.request, urllib.error
from datetime import datetime

REPO_DIR = "/home/runner/work/kaogong-daily/kaogong-daily"
DATA_JS = os.path.join(REPO_DIR, 'data.js')
BUILD_PY = os.path.join(REPO_DIR, 'build.py')

try:
    with open(DATA_JS) as f:
        old = f.read()
    m = re.search(r'"issue":\s*(\d+)', old)
    old_issue = int(m.group(1)) if m else 0
except:
    old_issue = 0
new_issue = old_issue + 1

today = datetime.now()
weekday_map = {0:'星期一',1:'星期二',2:'星期三',3:'星期四',4:'星期五',5:'星期六',6:'星期日'}
date_str = f"{today.year}年{today.month}月{today.day}日·{weekday_map[today.weekday()]}"

print(f"📝 第{old_issue}期 → 第{new_issue}期 ({date_str})")

api_key = os.environ['DEEPSEEK_API_KEY']
print("🤖 调用DeepSeek API...")

payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": f"日期：{date_str}，第{new_issue}期。请基于最新时政热点生成《考公晨读·每日精粹》，输出纯JSON，不要加其他文字。字段：date, issue, topic, quoteSource, quoteText, quoteScene, caseEvent, caseApply, conceptName, conceptDesc, conceptQuick, tipText, questions(12道选择题，含id,type,question,options,answer,analysis)，答案用0-3索引。字符串中的双引号请转义或用中文引号"},
        {"role": "user", "content": f"搜索{date_str}前后最新时政热点，生成考公晨读内容。12道题覆盖常识判断、言语理解、判断推理、数量关系各3道。"}
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
result = json.loads(resp.read().decode('utf-8'))
content = result["choices"][0]["message"]["content"].strip()
content = re.sub(r'^```.*?\n', '', content)
content = re.sub(r'\n```\s*$', '', content)
data = json.loads(content)

print(f"✅ 第{data['issue']}期 - {data['date']}，{len(data.get('questions',[]))}道题")

with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write("// 每日晨读数据 - 由GitHub Actions每日自动更新\n")
    f.write(f"window.DAILY_DATA = {json.dumps(data, ensure_ascii=False, indent=2)};\n")

subprocess.run(['python3', BUILD_PY], cwd=REPO_DIR, check=True)
subprocess.run(['cp', 'index.v2.html', 'index.html'], cwd=REPO_DIR)
print("✅ 完成！")
