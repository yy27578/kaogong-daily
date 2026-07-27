#!/bin/bash
# GitHub Actions 自动更新脚本
# 每天用AI生成晨读内容并推送到GitHub Pages

set -e

echo "🔍 搜索今日时政热点..."
# 生成今日晨读内容
CONTENT=$(curl -s https://api.deepseek.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "system", "content": "你是一位资深的公务员考试教研专家。请基于最新时政热点，生成《考公晨读·每日精粹》内容。格式必须是JSON，不要加其他文字。字段：date(当天日期带星期), issue(递增期数), topic(精选话题), quoteSource(金句来源), quoteText(金句内容), quoteScene(适用场景), caseEvent(案例), caseApply(应用论证), conceptName(概念名), conceptDesc(概念解释), conceptQuick(一句话速记), tipText(背诵提示), questions(12道选择题，含type/question/options/answer/analysis，答案用0-3索引)"},
      {"role": "user", "content": "请搜索今日最新时政热点，生成高质量的考公晨读内容。题目覆盖常识判断、言语理解、判断推理、数量关系。"}
    ],
    "temperature": 0.7,
    "max_tokens": 8000
  }' | python3 -c "
import json,sys
data = json.load(sys.stdin)
print(data['choices'][0]['message']['content'])
")

# 先读取旧的 data.js 获取上期期数
OLD_ISSUE=$(grep -oP '"issue":\s*\K\d+' data.js 2>/dev/null || echo "0")
NEW_ISSUE=$((OLD_ISSUE + 1))

# 保存为 data.js
echo "📝 写入 data.js..."
echo "// 每日晨读数据 - 由GitHub Actions每日自动更新" > data.js
echo "window.DAILY_DATA = $CONTENT;" >> data.js

# 构建自包含HTML
echo "🔨 构建HTML..."
python3 build.py

# 复制为首页
cp index.v2.html index.html

echo "✅ 更新完成，第 $NEW_ISSUE 期"
