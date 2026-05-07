#!/usr/bin/env python3
# 简单留言板后端 - 存储留言到留言.txt
from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)  # 允许跨域

MESSAGE_FILE = "/home/claw/桌面/留言.txt"

@app.route("/api/messages", methods=["GET"])
def get_messages():
    try:
        with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
            lines = f.read().strip().split("\n---\n")
            messages = []
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    parts = line.split("\n", 2)
                    if len(parts) >= 3:
                        # 去掉标签前缀 "名称：" 和 "内容："
                        name = parts[1].replace("名称：", "").strip()
                        content = parts[2].replace("内容：", "").strip()
                        messages.append({
                            "time": parts[0],
                            "name": name,
                            "content": content
                        })
                    elif len(parts) == 2:
                        name = parts[1].replace("名称：", "").strip() if "名称：" in parts[1] else parts[1]
                        messages.append({
                            "time": parts[0],
                            "name": name if name else "匿名",
                            "content": ""
                        })
            return jsonify({"messages": list(reversed(messages))})
    except FileNotFoundError:
        return jsonify({"messages": []})

@app.route("/api/messages", methods=["POST"])
def add_message():
    data = request.get_json()
    name = data.get("name", "匿名").strip()
    content = data.get("content", "").strip()
    
    if not content:
        return jsonify({"success": False, "error": "留言内容不能为空"})
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    with open(MESSAGE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp}\n名称：{name}\n内容：{content}\n---\n")
    
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
