"""
📋 Habitica To-Do 导出脚本
由 fingertiao 制作
最后更新：2025-06-27

功能说明：
- 导出 Habitica 中未完成和已完成的待办事项（含 子项checklist）
- 输出为 Markdown 文件
"""
import requests
import datetime

# === 用户配置 ===
USER_ID = "填写你的USER ID"
API_TOKEN = "填写你的API TOKEN令牌"
OUTPUT_FILE = "habitica待办事项存档.md"

HEADERS = {
    "x-api-user": USER_ID,
    "x-api-key": API_TOKEN
}

def format_datetime(dt_str):
    if not dt_str:
        return ""
    try:
        dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str or "(无时间)"


def format_task(task):
    lines = []
    status = "✅ 已完成" if task.get("completed") else "🕒 未完成"
    date = format_datetime(task.get("dateCompleted")) if task.get("completed") else ""
    title = task.get("text", "(无标题)")

    if date:
        lines.append(f"- **{title}** ({status}, {date})")
    else:
        lines.append(f"- **{title}** ({status})")

    checklist = task.get("checklist", [])
    for item in checklist:
        prefix = "☑️" if item.get("completed") else "⬜"
        lines.append(f"  - {prefix} {item.get('text')}")
    return lines


# === 拉取未完成 To-Do ===
print("📥 正在拉取未完成 To-Do（来自 /user -> tasksOrder.todos）...")
user_data = requests.get("https://habitica.com/api/v4/user", headers=HEADERS)

if user_data.status_code != 200:
    print("❌ 获取用户数据失败：", user_data.text)
    exit(1)

todo_ids = user_data.json().get("data", {}).get("tasksOrder", {}).get("todos", [])

unfinished_tasks = []

for i, task_id in enumerate(todo_ids):
    task_url = f"https://habitica.com/api/v4/tasks/{task_id}"
    resp = requests.get(task_url, headers=HEADERS)

    if resp.status_code != 200:
        print(f"[{i+1}/{len(todo_ids)}] ❌ 无法获取任务 {task_id}")
        continue

    task = resp.json().get("data", {})
    if task.get("type") == "todo" and not task.get("completed", False):
        unfinished_tasks.append(task)

    print(f"[{i+1}/{len(todo_ids)}] ✅ 检查任务：{task.get('text', '')}")

# === 拉取最近已完成 To-Do===
print("📥 正在拉取已完成 To-Do（最近）...")
url_finished = "https://habitica.com/api/v4/tasks/user?type=completedTodos"
res2 = requests.get(url_finished, headers=HEADERS)

if res2.status_code != 200:
    print("❌ 获取已完成 To-Do 失败：", res2.text)
    finished_tasks = []
else:
    finished_tasks = res2.json().get("data", [])

# === 排序已完成任务
finished_tasks.sort(key=lambda x: x.get("dateCompleted", ""), reverse=True)

# === 写入 Markdown
print("\n📝 正在写入 Markdown 文件...")
lines = ["# 📋 Habitica To-Do 导出记录\n"]

# 未完成
lines.append("## 🔸 当前进行中 To-Do（未完成）\n")
for task in unfinished_tasks:
    lines.extend(format_task(task))

# 已完成
lines.append("\n## ✅ 最近完成的 To-Do\n")
for task in finished_tasks:
    lines.extend(format_task(task))

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n✅ 导出完成：{len(unfinished_tasks)} 个未完成 + {len(finished_tasks)} 个已完成")
print(f"📄 保存至：{OUTPUT_FILE}")