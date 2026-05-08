from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import random
from pathlib import Path

app = FastAPI(title="三謀AI勝率模擬器")

BASE = Path(__file__).resolve().parent


def load_json(filename):
    path = BASE / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def get_stat(stats, key):
    value = stats.get(key, {})
    if isinstance(value, dict):
        base = float(value.get("base", 50))
        growth = float(value.get("growth", 1))
        return base + growth * 49
    return 50


def hero_power(hero):
    stats = hero.get("stats", {})

    force = get_stat(stats, "force")
    command = get_stat(stats, "command")
    intelligence = get_stat(stats, "intelligence")
    initiative = get_stat(stats, "initiative")

    camp_bonus = {
        "蜀": 1.03,
        "魏": 1.03,
        "吴": 1.03,
        "群": 1.02,
    }.get(hero.get("camp", ""), 1.0)

    return (
        force * 1.1
        + command * 1.0
        + intelligence * 1.1
        + initiative * 0.65
    ) * camp_bonus


def team_power(names):
    heroes = load_json("heroes.json")
    hero_map = {h.get("name"): h for h in heroes}

    total = 0
    camps = []

    for name in names:
        hero = hero_map.get(name)
        if hero:
            total += hero_power(hero)
            camps.append(hero.get("camp", ""))
        else:
            total += 100

    if len(camps) == 3 and len(set(camps)) == 1:
        total *= 1.08
    elif len(camps) == 3 and len(set(camps)) == 2:
        total *= 1.03

    return max(total, 1)


@app.get("/", response_class=HTMLResponse)
def home():
    heroes = load_json("heroes.json")

    if not heroes:
        return """
        <h1>找不到 heroes.json</h1>
        <p>請確認 GitHub 最外層有 heroes.json。</p>
        """

    names = [h.get("name", "未知") for h in heroes]
    options = "".join([f"<option value='{n}'>{n}</option>" for n in names])

    return f"""
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>三謀AI勝率模擬器</title>
<style>
body {{
    margin: 0;
    background: #0d1117;
    color: #e6edf3;
    font-family: Arial, "Noto Sans TC", sans-serif;
}}
header {{
    padding: 24px;
    border-bottom: 1px solid #30363d;
}}
h1 {{
    margin: 0;
    color: #f2c14e;
}}
main {{
    max-width: 1000px;
    margin: auto;
    padding: 20px;
}}
.card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 18px;
}}
.grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
}}
.row {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
}}
select, input {{
    width: 100%;
    padding: 10px;
    border-radius: 8px;
    background: #0d1117;
    color: white;
    border: 1px solid #30363d;
}}
button {{
    padding: 12px 18px;
    border: 0;
    border-radius: 10px;
    background: #f2c14e;
    color: #111;
    font-weight: bold;
    cursor: pointer;
    margin-top: 12px;
}}
.result {{
    font-size: 32px;
    font-weight: bold;
    margin-top: 16px;
}}
.green {{ color: #3fb950; }}
.red {{ color: #f85149; }}
table {{
    width: 100%;
    border-collapse: collapse;
}}
td, th {{
    border-bottom: 1px solid #30363d;
    padding: 8px;
    text-align: left;
}}
@media(max-width: 800px) {{
    .grid, .row {{
        grid-template-columns: 1fr;
    }}
}}
</style>
</head>
<body>
<header>
    <h1>三謀AI勝率模擬器</h1>
    <p>隊伍碰撞勝率模擬｜個人測試版</p>
</header>

<main>
    <div class="grid">
        <section class="card">
            <h2>我方 A</h2>
            <div class="row">
                <select id="a1">{options}</select>
                <select id="a2">{options}</select>
                <select id="a3">{options}</select>
            </div>
        </section>

        <section class="card">
            <h2>敵方 B</h2>
            <div class="row">
                <select id="b1">{options}</select>
                <select id="b2">{options}</select>
                <select id="b3">{options}</select>
            </div>
        </section>
    </div>

    <section class="card">
        <h2>模擬設定</h2>
        <label>模擬次數</label>
        <input id="times" type="number" value="1000" min="100" max="5000">
        <button onclick="simulate()">開始模擬</button>
        <div id="result"></div>
    </section>

    <section class="card">
        <h2>AI 快速推薦</h2>
        <button onclick="recommend()">從目前武將池推薦隊伍</button>
        <div id="recommendResult"></div>
    </section>

    <section class="card">
        <h2>目前武將資料</h2>
        <table>
            <thead>
                <tr>
                    <th>武將</th>
                    <th>陣營</th>
                    <th>兵種</th>
                    <th>自帶戰法</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td>{h.get('name')}</td><td>{h.get('camp')}</td><td>{h.get('troop')}</td><td>{h.get('own_skill')}</td></tr>" for h in heroes])}
            </tbody>
        </table>
    </section>
</main>

<script>
async function simulate() {{
    const payload = {{
        team_a: [a1.value, a2.value, a3.value],
        team_b: [b1.value, b2.value, b3.value],
        times: Number(times.value)
    }};

    const res = await fetch('/api/simulate', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify(payload)
    }});

    const data = await res.json();

    result.innerHTML = `
        <div class="grid">
            <div>
                <p>我方 A 勝率</p>
                <div class="result green">${{data.team_a_win_rate}}%</div>
                <p>戰力：${{data.team_a_power}}</p>
            </div>
            <div>
                <p>敵方 B 勝率</p>
                <div class="result red">${{data.team_b_win_rate}}%</div>
                <p>戰力：${{data.team_b_power}}</p>
            </div>
        </div>
        <p>模擬次數：${{data.times}}</p>
    `;
}}

async function recommend() {{
    const res = await fetch('/api/recommend');
    const data = await res.json();

    recommendResult.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>隊伍</th>
                    <th>評分</th>
                </tr>
            </thead>
            <tbody>
                ${{data.results.map((r, i) => `
                    <tr>
                        <td>${{i + 1}}</td>
                        <td>${{r.team.join(' / ')}}</td>
                        <td>${{r.score}}</td>
                    </tr>
                `).join('')}}
            </tbody>
        </table>
    `;
}}
</script>
</body>
</html>
"""


@app.post("/api/simulate")
async def simulate(payload: dict):
    team_a = payload.get("team_a", [])
    team_b = payload.get("team_b", [])
    times = min(int(payload.get("times", 1000)), 5000)

    a_power = team_power(team_a)
    b_power = team_power(team_b)

    a_win = 0
    b_win = 0

    for _ in range(times):
        a_score = a_power * random.uniform(0.82, 1.18)
        b_score = b_power * random.uniform(0.82, 1.18)

        if a_score >= b_score:
            a_win += 1
        else:
            b_win += 1

    return {
        "team_a_win_rate": round(a_win / times * 100, 2),
        "team_b_win_rate": round(b_win / times * 100, 2),
        "team_a_power": round(a_power, 2),
        "team_b_power": round(b_power, 2),
        "times": times
    }


@app.get("/api/recommend")
def recommend():
    heroes = load_json("heroes.json")
    names = [h.get("name") for h in heroes if h.get("name")]

    results = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for k in range(j + 1, len(names)):
                team = [names[i], names[j], names[k]]
                score = team_power(team)
                results.append({
                    "team": team,
                    "score": round(score, 2)
                })

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "results": results[:10]
    }


@app.get("/health")
def health():
    return {"status": "ok"}
