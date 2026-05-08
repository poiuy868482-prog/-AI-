from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import random
from pathlib import Path

app = FastAPI()

BASE = Path(__file__).resolve().parent
SEASON_ORDER = {"S1": 1, "S2": 2, "S3": 3}


def load_heroes():
    path = BASE / "heroes.json"

    if not path.exists():
        return []

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def season_value(season):
    return SEASON_ORDER.get(str(season).upper(), 99)


def filter_heroes_by_season(heroes, season):
    max_season = season_value(season)
    return [
        h for h in heroes
        if season_value(h.get("season", "S1")) <= max_season
    ]


def team_power(names, heroes):
    hero_map = {h.get("name"): h for h in heroes}
    total = 0
    camps = []
    tags = []

    for name in names:
        h = hero_map.get(name)
        if not h:
            total += 100
            continue

        rarity_bonus = 1.08 if h.get("rarity") == "SP" else 1.0
        tag_bonus = len(h.get("tags", [])) * 8

        total += (100 + tag_bonus) * rarity_bonus
        camps.append(h.get("camp", ""))
        tags.extend(h.get("tags", []))

    if len(camps) == 3 and len(set(camps)) == 1:
        total *= 1.10
    elif len(camps) == 3 and len(set(camps)) == 2:
        total *= 1.04

    combo_tags = {
        "蜀智": 35,
        "吳火": 35,
        "魏法": 30,
        "群騎": 30,
        "泰黃魚": 40,
        "控制": 18,
        "治療": 15,
        "燃燒": 15,
        "爆發": 12,
        "減傷": 12,
        "護衛": 12
    }

    for tag, bonus in combo_tags.items():
        if tags.count(tag) >= 2:
            total += bonus

    return round(max(total, 1), 2)


@app.get("/", response_class=HTMLResponse)
def home():
    heroes = load_heroes()

    if not heroes:
        return "<h1>找不到 heroes.json 或格式錯誤</h1>"

    return """
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>三謀AI勝率模擬器 S3</title>
<style>
body {
  margin: 0;
  background: #0d1117;
  color: #e6edf3;
  font-family: Arial, "Noto Sans TC", sans-serif;
}
header {
  padding: 24px;
  border-bottom: 1px solid #30363d;
}
h1 {
  margin: 0;
  color: #f2c14e;
}
main {
  max-width: 1100px;
  margin: auto;
  padding: 20px;
}
.card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 14px;
  padding: 18px;
  margin-bottom: 18px;
}
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}
select, input {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  background: #0d1117;
  color: white;
  border: 1px solid #30363d;
}
button {
  padding: 12px 18px;
  border: 0;
  border-radius: 10px;
  background: #f2c14e;
  color: #111;
  font-weight: bold;
  cursor: pointer;
  margin-top: 12px;
}
.result {
  font-size: 32px;
  font-weight: bold;
  margin-top: 12px;
}
.green { color: #3fb950; }
.red { color: #f85149; }
table {
  width: 100%;
  border-collapse: collapse;
}
td, th {
  border-bottom: 1px solid #30363d;
  padding: 8px;
  text-align: left;
}
.small {
  color: #8b949e;
  font-size: 14px;
}
@media(max-width:800px) {
  .grid, .row {
    grid-template-columns: 1fr;
  }
}
</style>
</head>

<body>
<header>
  <h1>三謀AI勝率模擬器</h1>
  <p>S3 賽季篩選版｜S3 = S1 + S2 + S3 武將池</p>
</header>

<main>

<section class="card">
  <h2>賽季設定</h2>
  <select id="season" onchange="loadHeroes()">
    <option value="S1">S1</option>
    <option value="S2">S2</option>
    <option value="S3" selected>S3</option>
  </select>
  <p class="small">選 S3 時，會包含 S1、S2、S3 武將。</p>
</section>

<div class="grid">
  <section class="card">
    <h2>我方 A</h2>
    <div class="row">
      <select id="a1"></select>
      <select id="a2"></select>
      <select id="a3"></select>
    </div>
  </section>

  <section class="card">
    <h2>敵方 B</h2>
    <div class="row">
      <select id="b1"></select>
      <select id="b2"></select>
      <select id="b3"></select>
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
  <h2>AI 推薦隊伍</h2>
  <button onclick="recommend()">依目前賽季推薦</button>
  <div id="recommendResult"></div>
</section>

<section class="card">
  <h2>目前賽季武將池</h2>
  <div id="heroTable"></div>
</section>

</main>

<script>
let currentHeroes = [];

async function loadHeroes() {
  const s = document.getElementById("season").value;
  const res = await fetch("/api/heroes?season=" + s);
  currentHeroes = await res.json();

  const options = currentHeroes.map(h =>
    `<option value="${h.name}">${h.name}｜${h.camp}｜${h.troop}｜${h.season}</option>`
  ).join("");

  ["a1","a2","a3","b1","b2","b3"].forEach(id => {
    document.getElementById(id).innerHTML = options;
  });

  if (currentHeroes.length >= 6) {
    a1.selectedIndex = 0;
    a2.selectedIndex = 1;
    a3.selectedIndex = 2;
    b1.selectedIndex = 3;
    b2.selectedIndex = 4;
    b3.selectedIndex = 5;
  }

  heroTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>武將</th>
          <th>陣營</th>
          <th>兵種</th>
          <th>賽季</th>
          <th>標籤</th>
        </tr>
      </thead>
      <tbody>
        ${currentHeroes.map(h => `
          <tr>
            <td>${h.name}</td>
            <td>${h.camp}</td>
            <td>${h.troop}</td>
            <td>${h.season}</td>
            <td>${(h.tags || []).join("、")}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

async function simulate() {
  const payload = {
    season: season.value,
    team_a: [a1.value, a2.value, a3.value],
    team_b: [b1.value, b2.value, b3.value],
    times: Number(times.value)
  };

  const res = await fetch("/api/simulate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });

  const data = await res.json();

  result.innerHTML = `
    <div class="grid">
      <div>
        <p>A 勝率</p>
        <div class="result green">${data.team_a_win_rate}%</div>
        <p>戰力：${data.team_a_power}</p>
      </div>
      <div>
        <p>B 勝率</p>
        <div class="result red">${data.team_b_win_rate}%</div>
        <p>戰力：${data.team_b_power}</p>
      </div>
    </div>
    <p class="small">賽季：${data.season}｜模擬次數：${data.times}</p>
  `;
}

async function recommend() {
  const res = await fetch("/api/recommend?season=" + season.value);
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
        ${data.results.map((r, i) => `
          <tr>
            <td>${i + 1}</td>
            <td>${r.team.join(" / ")}</td>
            <td>${r.score}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

loadHeroes();
</script>

</body>
</html>
"""


@app.get("/api/heroes")
def api_heroes(season: str = "S3"):
    heroes = load_heroes()
    return filter_heroes_by_season(heroes, season)


@app.post("/api/simulate")
async def simulate(payload: dict):
    season = payload.get("season", "S3")
    heroes = filter_heroes_by_season(load_heroes(), season)

    team_a = payload.get("team_a", [])
    team_b = payload.get("team_b", [])
    times = min(int(payload.get("times", 1000)), 5000)

    a_power = team_power(team_a, heroes)
    b_power = team_power(team_b, heroes)

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
        "season": season,
        "team_a_win_rate": round(a_win / times * 100, 2),
        "team_b_win_rate": round(b_win / times * 100, 2),
        "team_a_power": a_power,
        "team_b_power": b_power,
        "times": times
    }


@app.get("/api/recommend")
def recommend(season: str = "S3"):
    heroes = filter_heroes_by_season(load_heroes(), season)
    names = [h.get("name") for h in heroes if h.get("name")]

    results = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for k in range(j + 1, len(names)):
                team = [names[i], names[j], names[k]]
                score = team_power(team, heroes)
                results.append({
                    "team": team,
                    "score": score
                })

    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "season": season,
        "results": results[:10]
    }


@app.get("/health")
def health():
    return {"status": "ok"}
