from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
from pathlib import Path
import random

app = FastAPI()

BASE = Path(__file__).resolve().parent

def load_json(name):
    path = BASE / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

@app.get("/", response_class=HTMLResponse)
def home():
    heroes = load_json("heroes.json")
    names = [h.get("name", "未知") for h in heroes]

    options = "".join([f"<option>{n}</option>" for n in names])

    return f"""
    <!doctype html>
    <html lang="zh-Hant">
    <head>
      <meta charset="utf-8">
      <title>三謀AI勝率模擬器</title>
      <style>
        body {{ background:#0d1117; color:white; font-family:Arial; padding:30px; }}
        .card {{ background:#161b22; padding:20px; border-radius:12px; margin-bottom:20px; }}
        h1 {{ color:#f2c14e; }}
        select, input, button {{ padding:10px; margin:5px; }}
        button {{ background:#f2c14e; border:0; border-radius:8px; font-weight:bold; }}
      </style>
    </head>
    <body>
      <h1>三謀AI勝率模擬器</h1>

      <div class="card">
        <h2>我方 A</h2>
        <select id="a1">{options}</select>
        <select id="a2">{options}</select>
        <select id="a3">{options}</select>
      </div>

      <div class="card">
        <h2>敵方 B</h2>
        <select id="b1">{options}</select>
        <select id="b2">{options}</select>
        <select id="b3">{options}</select>
      </div>

      <div class="card">
        <h2>模擬設定</h2>
        <input id="times" type="number" value="1000">
        <button onclick="simulate()">開始模擬</button>
        <div id="result" style="font-size:28px;margin-top:20px;"></div>
      </div>

      <script>
        async function simulate() {{
          const payload = {{
            team_a: [a1.value, a2.value, a3.value],
            team_b: [b1.value, b2.value, b3.value],
            times: Number(times.value)
          }};

          const res = await fetch('/api/simulate', {{
            method:'POST',
            headers:{{'Content-Type':'application/json'}},
            body:JSON.stringify(payload)
          }});

          const data = await res.json();

          result.innerHTML =
            'A 勝率：' + data.team_a_win_rate + '%<br>' +
            'B 勝率：' + data.team_b_win_rate + '%';
        }}
      </script>
    </body>
    </html>
    """

@app.post("/api/simulate")
async def simulate(payload: dict):
    times = min(int(payload.get("times", 1000)), 5000)

    a_power = team_power(payload.get("team_a", []))
    b_power = team_power(payload.get("team_b", []))

    a_win = 0
    b_win = 0

    for _ in range(times):
        a_score = a_power * random.uniform(0.85, 1.15)
        b_score = b_power * random.uniform(0.85, 1.15)

        if a_score >= b_score:
            a_win += 1
        else:
            b_win += 1

    return {
        "team_a_win_rate": round(a_win / times * 100, 2),
        "team_b_win_rate": round(b_win / times * 100, 2),
        "times": times
    }

def team_power(names):
    heroes = load_json("heroes.json")
    hero_map = {h.get("name"): h for h in heroes}

    total = 0

    for name in names:
        h = hero_map.get(name)
        if not h:
            total += 100
            continue

        stats = h.get("stats", {})
        force = get_stat(stats, "force")
        command = get_stat(stats, "command")
        intelligence = get_stat(stats, "intelligence")
        initiative = get_stat(stats, "initiative")

        total += force * 1.1 + command * 1.0 + intelligence * 1.1 + initiative * 0.6

    return max(total, 1)

def get_stat(stats, key):
    value = stats.get(key, {})
    if isinstance(value, dict):
        return float(value.get("base", 50)) + float(value.get("growth", 1)) * 49
    return 50

@app.get("/health")
def health():
    return {"status": "ok"}
