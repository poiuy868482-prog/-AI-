from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import random
from pathlib import Path

app = FastAPI()

BASE = Path(__file__).resolve().parent

def load_heroes():
    path = BASE / "heroes.json"
    if not path.exists():
        return [
            {"name": "諸葛亮", "camp": "蜀", "troop": "弓"},
            {"name": "姜維", "camp": "蜀", "troop": "槍"},
            {"name": "龐統", "camp": "蜀", "troop": "盾"},
            {"name": "曹操", "camp": "魏", "troop": "騎"},
            {"name": "郭嘉", "camp": "魏", "troop": "盾"},
            {"name": "夏侯惇", "camp": "魏", "troop": "盾"},
        ]
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

@app.get("/", response_class=HTMLResponse)
def home():
    heroes = load_heroes()
    names = [h.get("name", "未知") for h in heroes]
    options = "".join(f"<option>{n}</option>" for n in names)

    html = """
    <html>
    <head>
      <meta charset="utf-8">
      <title>三謀AI勝率模擬器</title>
      <style>
        body { background:#0d1117; color:white; font-family:Arial; padding:24px; }
        .card { background:#161b22; padding:18px; border-radius:12px; margin:14px 0; }
        select, input, button { padding:10px; margin:5px; }
        button { background:#f2c14e; border:0; border-radius:8px; font-weight:bold; }
      </style>
    </head>
    <body>
      <h1>三謀AI勝率模擬器</h1>

      <div class="card">
        <h2>我方 A</h2>
        <select id="a1">OPTIONS</select>
        <select id="a2">OPTIONS</select>
        <select id="a3">OPTIONS</select>
      </div>

      <div class="card">
        <h2>敵方 B</h2>
        <select id="b1">OPTIONS</select>
        <select id="b2">OPTIONS</select>
        <select id="b3">OPTIONS</select>
      </div>

      <div class="card">
        <h2>模擬</h2>
        <input id="times" type="number" value="1000">
        <button onclick="simulate()">開始模擬</button>
        <div id="result" style="font-size:28px;margin-top:20px;"></div>
      </div>

      <script>
      async function simulate() {
        const payload = {
          team_a:[a1.value,a2.value,a3.value],
          team_b:[b1.value,b2.value,b3.value],
          times:Number(times.value)
        };

        const res = await fetch('/api/simulate', {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body:JSON.stringify(payload)
        });

        const data = await res.json();

        result.innerHTML =
          'A勝率：' + data.team_a_win_rate + '%<br>' +
          'B勝率：' + data.team_b_win_rate + '%';
      }
      </script>
    </body>
    </html>
    """

    return html.replace("OPTIONS", options)

@app.post("/api/simulate")
async def simulate(payload: dict):
    times = min(int(payload.get("times", 1000)), 5000)

    a_power = len(payload.get("team_a", [])) * 100
    b_power = len(payload.get("team_b", [])) * 100

    a_win = 0
    b_win = 0

    for _ in range(times):
        if a_power * random.uniform(0.8, 1.2) >= b_power * random.uniform(0.8, 1.2):
            a_win += 1
        else:
            b_win += 1

    return {
        "team_a_win_rate": round(a_win / times * 100, 2),
        "team_b_win_rate": round(b_win / times * 100, 2),
        "times": times
    }

@app.get("/health")
def health():
    return {"status": "ok"}
