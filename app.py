import os
import re
from datetime import datetime

from flask import Flask, render_template_string, request

app = Flask(__name__)

LOG_FILE = os.environ.get("LOG_FILE", "/app/logs/log.txt")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

LINE_RE = re.compile(r"^\[(.+?)\]\s(.*)$")
MAX_LEN = 500

PAGE = """
<!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Message Logger</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg1: #eef2ff; --bg2: #fdf2f8;
      --card: #ffffff; --text: #1e293b; --muted: #64748b;
      --primary: #6366f1; --primary-dark: #4f46e5;
      --border: #e2e8f0; --soft: #f1f5f9; --success: #10b981;
      --shadow: 0 10px 30px rgba(99, 102, 241, .12);
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg1: #0f172a; --bg2: #1e1b4b;
        --card: #1e293b; --text: #f1f5f9; --muted: #94a3b8;
        --border: #334155; --soft: #0f172a;
        --shadow: 0 10px 30px rgba(0, 0, 0, .4);
      }
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh; color: var(--text);
      font-family: "Noto Sans Thai", system-ui, -apple-system, "Segoe UI", sans-serif;
      background: linear-gradient(135deg, var(--bg1), var(--bg2)) fixed;
    }
    .wrap { max-width: 720px; margin: 0 auto; padding: 48px 16px 64px; }
    header { text-align: center; margin-bottom: 28px; }
    .logo {
      width: 56px; height: 56px; margin: 0 auto 12px; border-radius: 16px;
      display: grid; place-items: center; font-size: 28px; color: #fff;
      background: linear-gradient(135deg, var(--primary), #ec4899);
      box-shadow: var(--shadow);
    }
    h1 { margin: 0; font-size: 1.8rem; }
    header p { margin: 6px 0 0; color: var(--muted); }
    .card {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 20px; padding: 24px; margin-bottom: 20px;
      box-shadow: var(--shadow);
    }
    textarea {
      width: 100%; height: 120px; resize: vertical; padding: 14px 16px;
      font: inherit; color: var(--text); background: var(--soft);
      border: 1.5px solid var(--border); border-radius: 14px; outline: none;
      transition: border-color .2s, box-shadow .2s;
    }
    textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 4px rgba(99, 102, 241, .18); }
    .row { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; }
    .count { color: var(--muted); font-size: .85rem; }
    button {
      font: inherit; font-weight: 600; color: #fff; cursor: pointer;
      padding: 10px 26px; border: 0; border-radius: 12px;
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      transition: transform .15s, box-shadow .15s;
    }
    button:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(99, 102, 241, .4); }
    button:active { transform: translateY(0); }
    .received { border-left: 5px solid var(--success); animation: pop .4s ease; }
    .received .label { color: var(--success); font-weight: 600; font-size: .85rem; margin-bottom: 6px; }
    .received .text { white-space: pre-wrap; word-break: break-word; font-size: 1.05rem; }
    .section-title { display: flex; align-items: center; justify-content: space-between; margin: 0 0 14px; font-size: 1.1rem; }
    .badge { background: var(--soft); color: var(--muted); border-radius: 999px; padding: 2px 12px; font-size: .8rem; font-weight: 500; }
    ul { list-style: none; margin: 0; padding: 0; }
    li { padding: 12px 14px; margin-bottom: 10px; background: var(--soft); border-radius: 12px; animation: pop .3s ease; }
    li .time { color: var(--muted); font-size: .78rem; }
    li .body { margin-top: 2px; word-break: break-word; }
    .empty { text-align: center; color: var(--muted); padding: 24px 0; }
    footer { text-align: center; color: var(--muted); font-size: .8rem; margin-top: 8px; }
    @keyframes pop { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="logo">✉</div>
      <h1>Message Logger</h1>
      <p>ส่งข้อความ แล้วระบบจะบันทึกลง log.txt ให้อัตโนมัติ</p>
    </header>

    <form class="card" method="POST" action="/">
      <textarea id="msg" name="message" maxlength="{{ max_len }}"
                placeholder="พิมพ์ข้อความของคุณที่นี่..." required autofocus></textarea>
      <div class="row">
        <span class="count"><span id="n">0</span> / {{ max_len }}</span>
        <button type="submit">ส่งข้อความ</button>
      </div>
    </form>

    {% if message %}
    <div class="card received">
      <div class="label">✓ ได้รับข้อความแล้ว</div>
      <div class="text">{{ message }}</div>
    </div>
    {% endif %}

    <div class="card">
      <h2 class="section-title">ประวัติข้อความ <span class="badge">{{ entries|length }} รายการ</span></h2>
      {% if entries %}
      <ul>
        {% for e in entries %}
        <li><div class="time">{{ e.time }}</div><div class="body">{{ e.text }}</div></li>
        {% endfor %}
      </ul>
      {% else %}
      <div class="empty">ยังไม่มีข้อความ ลองส่งข้อความแรกดูสิ</div>
      {% endif %}
    </div>

    <footer>บันทึกไว้ที่ {{ log_file }}</footer>
  </div>

  <script>
    const t = document.getElementById("msg"), n = document.getElementById("n");
    t.addEventListener("input", () => n.textContent = t.value.length);
  </script>
</body>
</html>
"""


def read_entries():
    """อ่าน log.txt แล้วคืนรายการล่าสุดขึ้นก่อน"""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        return []
    entries = []
    for line in lines:
        m = LINE_RE.match(line)
        if m:
            entries.append({"time": m.group(1), "text": m.group(2)})
        elif line.strip():
            entries.append({"time": "", "text": line})
    return entries[::-1]


@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    if request.method == "POST":
        message = request.form.get("message", "").strip()[:MAX_LEN]
        if message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            one_line = message.replace("\r", " ").replace("\n", " ")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {one_line}\n")
    return render_template_string(
        PAGE,
        message=message,
        entries=read_entries(),
        max_len=MAX_LEN,
        log_file=LOG_FILE,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
