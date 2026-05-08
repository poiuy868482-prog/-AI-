from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import random
from pathlib import Path
import csv
import urllib.request
from io import StringIO

app = FastAPI()

BASE = Path(__file__).resolve().parent

SHEET_ID = "16U-O0PMGxtQjbZ7W4I5j4PbkiLguqBNRa-HR4Dw5PCQ"
SHEET_GID = "1739733298"

SEASON_ORDER = {
    "S1": 1,
    "S2": 2,
    "S3": 3
}


def load_google_sheet_rows():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            csv_text = response.read().decode("utf-8-sig")
    except Exception:
        return []

    reader = csv.DictReader(StringIO(csv_text))
    return list(reader)


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
    hero_map = {
        h.get("name"): h
        for h in heroes
    }

    total = 0
    camps = []
    tags = []

    for name in names:
        hero = hero_map.get(name)

        if not hero:
            total += 100
            continue

        rarity_bonus = 1.08 if hero.get("rarity") == "SP" else 1.0

        tag_bonus = len(hero.get("tags", [])) * 8

        total += (100 + tag_bonus) * rarity_bonus

        camps.append(hero.get("camp", ""))
        tags.extend(hero.get("tags", []))

    if len(camps) == 3 and len(set(camps)) == 1:
        total *= 1.10

    elif len(camps) == 3 and len(set(camps)) == 2:
        total *= 1.04

    combo_tags = {
        "蜀智": 35,
        "魏法": 35,
        "吳火": 35,
        "群騎": 30,
        "泰黃魚": 40,
        "控制": 18,
        "爆發": 12,
        "燃燒": 15,
        "護衛": 12,
        "減傷": 12
    }

    for tag, bonus in combo_tags.items():
        if tags.count(tag) >= 2:
            total += bonus

    return round(max(total, 1), 2)


@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!doctype html>
<html lang="zh-Hant">

<head>

<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>三謀AI勝率模擬器</title>

<style>

body{
    margin:0;
    background:#0d1117;
    color:#e6edf3;
    font-family:Arial,sans-serif;
}

header{
    padding:24px;
    border-bottom:1px solid #30363d;
}

h1{
    margin:0;
    color:#f2c14e;
}

main{
    max-width:1200px;
    margin:auto;
    padding:20px;
}

.card{
    background:#161b22;
    border:1px solid #30363d;
    border-radius:14px;
    padding:18px;
    margin-bottom:18px;
}

.grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:18px;
}

.row{
    display:grid;
    grid-template-columns:1fr 1fr 1fr;
    gap:8px;
}

select,input{
    width:100%;
    padding:10px;
    border-radius:8px;
    background:#0d1117;
    color:white;
    border:1px solid #30363d;
}

button{
    padding:12px 18px;
    border:0;
    border-radius:10px;
    background:#f2c14e;
    color:#111;
    font-weight:bold;
    cursor:pointer;
    margin-top:12px;
}

.result{
    font-size:32px;
    font-weight:bold;
    margin-top:12px;
}

.green{color:#3fb950;}
.red{color:#f85149;}

table{
    width:100%;
    border-collapse:collapse;
}

td,th{
    border-bottom:1px solid #30363d;
    padding:8px;
    text-align:left;
}

.small{
    color:#8b949e;
    font-size:14px;
}

@media(max-width:800px){

.grid,.row{
    grid-template-columns:1fr;
}

}

</style>

</head>

<body>

<header>

<h1>三謀AI勝率模擬器</h1>

<p>S3 AI版｜Google Sheet 已接入</p>

</header>

<main>

<section class="card">

<h2>賽季</h2>

<select id="season" onchange="loadHeroes()">

<option value="S1">S1</option>
<option value="S2">S2</option>
<option value="S3" selected>S3</option>

</select>

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

<input id="times" type="number" value="1000">

<button onclick="simulate()">
開始模擬
</button>

<div id="result"></div>

</section>

<section class="card">

<h2>AI推薦</h2>

<button onclick="recommend()">
產生推薦隊伍
</button>

<div id="recommendResult"></div>

</section>

<section class="card">

<h2>Google Sheet 資料測試</h2>

<button onclick="sheetTest()">
讀取 Google Sheet
</button>

<div id="sheetResult"></div>

</section>

</main>

<script>

let currentHeroes=[];

async function loadHeroes(){

    const s=season.value;

    const res=await fetch('/api/heroes?season='+s);

    currentHeroes=await res.json();

    const options=currentHeroes.map(h=>
        `<option value="${h.name}">
            ${h.name}｜${h.camp}｜${h.troop}
        </option>`
    ).join("");

    ["a1","a2","a3","b1","b2","b3"].forEach(id=>{
        document.getElementById(id).innerHTML=options;
    });

}

async function simulate(){

    const payload={

        season:season.value,

        team_a:[
            a1.value,
            a2.value,
            a3.value
        ],

        team_b:[
            b1.value,
            b2.value,
            b3.value
        ],

        times:Number(times.value)

    };

    const res=await fetch('/api/simulate',{

        method:'POST',

        headers:{
            'Content-Type':'application/json'
        },

        body:JSON.stringify(payload)

    });

    const data=await res.json();

    result.innerHTML=`

    <div class="grid">

    <div>
        <p>A勝率</p>
        <div class="result green">
            ${data.team_a_win_rate}%
        </div>
        <p>戰力：${data.team_a_power}</p>
    </div>

    <div>
        <p>B勝率</p>
        <div class="result red">
            ${data.team_b_win_rate}%
        </div>
        <p>戰力：${data.team_b_power}</p>
    </div>

    </div>

    `;

}

async function recommend(){

    const res=await fetch('/api/recommend?season='+season.value);

    const data=await res.json();

    recommendResult.innerHTML=`

    <table>

    <thead>

    <tr>
        <th>#</th>
        <th>隊伍</th>
        <th>評分</th>
    </tr>

    </thead>

    <tbody>

    ${data.results.map((r,i)=>`

    <tr>
        <td>${i+1}</td>
        <td>${r.team.join(" / ")}</td>
        <td>${r.score}</td>
    </tr>

    `).join("")}

    </tbody>

    </table>

    `;

}

async function sheetTest(){

    const res=await fetch('/api/google-sheet');

    const data=await res.json();

    sheetResult.innerHTML=`

    <p>
        成功讀取：
        ${data.count}
        筆資料
    </p>

    <pre>
${JSON.stringify(data.sample,null,2)}
    </pre>

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

    return filter_heroes_by_season(
        heroes,
        season
    )


@app.post("/api/simulate")
async def simulate(payload: dict):

    season = payload.get("season", "S3")

    heroes = filter_heroes_by_season(
        load_heroes(),
        season
    )

    team_a = payload.get("team_a", [])
    team_b = payload.get("team_b", [])

    times = min(
        int(payload.get("times", 1000)),
        5000
    )

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

    heroes = filter_heroes_by_season(
        load_heroes(),
        season
    )

    names = [
        h.get("name")
        for h in heroes
        if h.get("name")
    ]

    results = []

    for i in range(len(names)):

        for j in range(i + 1, len(names)):

            for k in range(j + 1, len(names)):

                team = [
                    names[i],
                    names[j],
                    names[k]
                ]

                score = team_power(
                    team,
                    heroes
                )

                results.append({
                    "team": team,
                    "score": score
                })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return {
        "season": season,
        "results": results[:10]
    }


@app.get("/api/google-sheet")
def google_sheet():

    rows = load_google_sheet_rows()

    return {
        "count": len(rows),
        "sample": rows[:5]
    }


@app.get("/health")
def health():

    return {
        "status": "ok"
    }
