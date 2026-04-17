
import os, math, sqlite3
from datetime import date, timedelta, datetime
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="ZOLA Elite", page_icon="⚽", layout="wide")

DB_PATH = Path("zola_app.db")
LIMA_TZ = "America/Lima"
API_FOOTBALL_BASE = os.getenv("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
ODDS_API_BASE = os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4")
SPORTMONKS_BASE = os.getenv("SPORTMONKS_BASE_URL", "https://api.sportmonks.com/v3/football")

COMP_KEYS = {
    "Top": [39, 140, 78, 135, 61, 2, 3, 848, 1, 4, 34, 9, 94, 95],
    "Europa": [39, 140, 78, 135, 61, 2, 3, 848],
    "Sudamérica": [1, 2, 11, 13, 71, 128, 129],
    "Internacional": [4, 34, 9, 94, 95],
}
SPORT_KEY_SUGGESTIONS = [
    "soccer_conmebol_libertadores","soccer_conmebol_sudamericana","soccer_uefa_champs_league",
    "soccer_spain_la_liga","soccer_epl","soccer_italy_serie_a","soccer_germany_bundesliga",
    "soccer_france_ligue_one","soccer_brazil_campeonato"
]
TEAM_PRIORS = {
    "palmeiras": {"elo": 1875, "form": 2.35, "attack": 2.05, "defense": 0.78},
    "sporting cristal": {"elo": 1545, "form": 1.55, "attack": 1.18, "defense": 1.58},
    "real madrid": {"elo": 1915, "form": 2.30, "attack": 2.15, "defense": 0.86},
    "manchester city": {"elo": 1920, "form": 2.28, "attack": 2.12, "defense": 0.88},
    "barcelona": {"elo": 1860, "form": 2.05, "attack": 1.95, "defense": 0.98},
    "arsenal": {"elo": 1870, "form": 2.12, "attack": 1.92, "defense": 0.94},
    "bayern munich": {"elo": 1880, "form": 2.10, "attack": 2.00, "defense": 0.95},
    "psg": {"elo": 1865, "form": 2.08, "attack": 2.02, "defense": 1.02},
    "alianza lima": {"elo": 1495, "form": 1.52, "attack": 1.20, "defense": 1.34},
    "universitario": {"elo": 1530, "form": 1.78, "attack": 1.30, "defense": 1.16},
}
TEAM_CONTEXT = {
    "palmeiras": {"lat": -23.5505, "lon": -46.6333, "crowd": 0.88},
    "sporting cristal": {"lat": -12.0464, "lon": -77.0428, "crowd": 0.20},
    "real madrid": {"lat": 40.4168, "lon": -3.7038, "crowd": 0.85},
    "manchester city": {"lat": 53.4808, "lon": -2.2426, "crowd": 0.82},
    "barcelona": {"lat": 41.3874, "lon": 2.1686, "crowd": 0.84},
    "arsenal": {"lat": 51.5072, "lon": -0.1276, "crowd": 0.82},
    "bayern munich": {"lat": 48.1351, "lon": 11.5820, "crowd": 0.84},
    "psg": {"lat": 48.8566, "lon": 2.3522, "crowd": 0.83},
    "alianza lima": {"lat": -12.0464, "lon": -77.0428, "crowd": 0.80},
    "universitario": {"lat": -12.0464, "lon": -77.0428, "crowd": 0.82},
}

for k, v in {"page":"live", "theme":"light", "query":"", "selected_fixture_id":None}.items():
    st.session_state.setdefault(k, v)

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS selections(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fixture_id INTEGER,
        home_team TEXT,
        away_team TEXT,
        league_name TEXT,
        fixture_date TEXT,
        saved_at TEXT
    )
    """)
    con.commit()
    con.close()

def save_selection(fixture):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO selections(fixture_id, home_team, away_team, league_name, fixture_date, saved_at) VALUES(?,?,?,?,?,?)",
        (
            fixture.get("fixture",{}).get("id"),
            fixture.get("teams",{}).get("home",{}).get("name",""),
            fixture.get("teams",{}).get("away",{}).get("name",""),
            fixture.get("league",{}).get("name",""),
            fixture.get("fixture",{}).get("date",""),
            datetime.utcnow().isoformat(),
        )
    )
    con.commit()
    con.close()

init_db()

def get_secret(name, default=""):
    if st.session_state.get(name):
        return st.session_state[name]
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)

API_FOOTBALL_KEY = get_secret("API_FOOTBALL_KEY")
THE_ODDS_API_KEY = get_secret("THE_ODDS_API_KEY")
SPORTMONKS_API_TOKEN = get_secret("SPORTMONKS_API_TOKEN")
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD")

def inject_css(theme="light"):
    dark = theme == "dark"
    bg = "#081124" if dark else "#edf2fb"
    text = "#eef4ff" if dark else "#0d2147"
    soft = "#13213d" if dark else "#ffffff"
    soft2 = "#0d1a33" if dark else "#f8fbff"
    border = "#233a66" if dark else "#d6e2fb"
    mut = "#a8b8d8" if dark else "#6e7ea6"
    header = "#2343d3"
    st.markdown(f"""
    <style>
    :root{{--bg:{bg};--text:{text};--soft:{soft};--soft2:{soft2};--border:{border};--mut:{mut};--blue:{header};--accent:#ff5656;--green:#26cc6b;}}
    .stApp{{background:var(--bg);color:var(--text);}}
    .block-container{{padding-top:0rem;max-width:1520px;}}
    h1,h2,h3,h4,h5,h6,p,span,div,label{{color:var(--text)}}
    .topbar{{background:linear-gradient(90deg,#273fd8,#264ce6);border-radius:0 0 18px 18px;padding:14px 18px 12px;border:1px solid rgba(255,255,255,.08);box-shadow:0 14px 30px rgba(18,30,65,.18);margin-bottom:18px;}}
    .topbar-row{{display:flex;align-items:center;gap:14px;justify-content:space-between;}}
    .brand{{display:flex;align-items:center;gap:12px;min-width:240px;}}
    .brand img{{width:38px;height:38px;border-radius:10px;border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.08);padding:4px;object-fit:contain;}}
    .brand .title{{font-weight:900;font-size:1.15rem;color:#fff;line-height:1;}}
    .search-wrap{{flex:1;max-width:540px;}}
    .search-shell{{display:flex;align-items:center;background:#fff;border-radius:13px;padding:8px 12px;gap:10px;}}
    .search-shell input{{border:none !important;box-shadow:none !important;background:transparent !important;color:#24314e !important;}}
    .top-actions{{display:flex;align-items:center;gap:10px;}}
    .pill{{display:inline-flex;align-items:center;gap:7px;padding:8px 13px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);color:#fff;font-size:.88rem;font-weight:700;}}
    .dot{{width:11px;height:11px;border-radius:50%;background:var(--green);display:inline-block;box-shadow:0 0 0 3px rgba(37,202,106,.14);}}
    .sports{{display:flex;gap:12px;align-items:center;overflow:auto;padding-top:12px;}}
    .sports .item{{color:#e9efff;font-weight:800;font-size:.88rem;white-space:nowrap;opacity:.95}}
    .sports .item.active{{border-bottom:3px solid #fff;padding-bottom:7px;}}
    .card{{background:var(--soft);border:1px solid var(--border);border-radius:18px;padding:16px;box-shadow:0 10px 24px rgba(10,20,45,.08);}}
    .subcard{{background:var(--soft2);border:1px solid var(--border);border-radius:16px;padding:14px;}}
    .fixture-row{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 10px;border-radius:14px;border:1px solid var(--border);background:var(--soft2);margin-bottom:10px;cursor:pointer;}}
    .fixture-row.active{{box-shadow:inset 0 0 0 2px #3d5eff;background:rgba(61,94,255,.08);}}
    .league{{font-size:.82rem;color:var(--mut);font-weight:700;margin-bottom:6px;}}
    .teams{{display:flex;flex-direction:column;gap:7px;}}
    .teamline{{display:flex;align-items:center;gap:8px;font-weight:800;}}
    .teamline img{{width:18px;height:18px;object-fit:contain;}}
    .scoretime{{text-align:right;min-width:72px;}}
    .score{{font-weight:900;font-size:1rem;}}
    .status-live{{color:#ff4d4d;font-weight:900;}}
    .status-pre{{color:var(--mut);font-weight:800;}}
    .match-hero{{display:grid;grid-template-columns:1fr 210px 1fr;gap:20px;align-items:center;}}
    .team-hero{{text-align:center;}}
    .team-hero img{{width:72px;height:72px;object-fit:contain;display:block;margin:0 auto 8px;}}
    .team-name{{font-size:1.95rem;font-weight:900;line-height:1.05;}}
    .center-hero{{text-align:center;}}
    .competition{{display:inline-flex;align-items:center;gap:8px;background:var(--soft2);padding:6px 10px;border:1px solid var(--border);border-radius:999px;font-weight:800;font-size:.85rem;margin-bottom:12px;}}
    .competition img{{width:18px;height:18px;object-fit:contain;}}
    .bigscore{{font-weight:900;font-size:3.2rem;line-height:1;}}
    .bigstatus{{font-weight:900;margin-top:6px;}}
    .section-title{{font-size:1.02rem;font-weight:900;margin-bottom:10px;}}
    .market-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}}
    .market-box{{border:1px solid var(--border);border-radius:16px;background:var(--soft2);padding:14px;text-align:center;}}
    .market-box .label{{font-size:.9rem;color:#5778b7;font-weight:900;letter-spacing:.02em;}}
    .market-box .value{{font-size:2rem;font-weight:900;margin-top:10px;}}
    .quick-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}}
    .quick-box{{border:1px solid var(--border);border-radius:16px;background:var(--soft2);padding:14px;min-height:92px;}}
    .quick-box .k{{font-size:.8rem;color:#6f84b7;font-weight:900;}}
    .quick-box .v{{font-size:1.8rem;font-weight:900;margin-top:6px;}}
    .good{{background:rgba(31,190,93,.10);border:1px solid rgba(31,190,93,.24);padding:14px;border-radius:14px;}}
    .warn{{background:rgba(36,71,255,.08);border:1px solid rgba(36,71,255,.18);padding:14px;border-radius:14px;}}
    .tiny{{font-size:.8rem;color:var(--mut);}}
    .selector [data-baseweb="select"] > div, .selector input{{background:var(--soft2)!important;border:1px solid var(--border)!important;color:var(--text)!important;border-radius:12px!important;}}
    .stButton button{{border-radius:12px;border:1px solid var(--border);}}
    .primary-cta button{{background:#ff5257!important;color:white!important;border:none!important;font-weight:800!important;}}
    @media (max-width: 980px){{
      .match-hero{{grid-template-columns:1fr;}}
      .market-grid,.quick-grid{{grid-template-columns:1fr 1fr;}}
      .topbar-row{{flex-direction:column;align-items:stretch;}}
      .brand{{justify-content:center;}}
    }}
    </style>
    """, unsafe_allow_html=True)

inject_css(st.session_state.theme)

def similarity(a,b):
    return SequenceMatcher(None, str(a).lower().strip(), str(b).lower().strip()).ratio()

def api_get(url, headers=None, params=None):
    r = requests.get(url, headers=headers, params=params, timeout=25)
    r.raise_for_status()
    return r.json()

def implied_prob(decimal_odds):
    if not decimal_odds or decimal_odds <= 1:
        return np.nan
    return 1 / decimal_odds

def expected_value(prob, decimal_odds):
    if not decimal_odds or decimal_odds <= 1:
        return np.nan
    return prob * (decimal_odds - 1) - (1 - prob)

def kelly_fraction(prob, decimal_odds):
    if not decimal_odds or decimal_odds <= 1:
        return 0.0
    b = decimal_odds - 1
    q = 1 - prob
    return max(0.0, (b * prob - q) / b)

def poisson_pmf(k, lam):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def score_matrix(lambda_a, lambda_b, max_goals=6):
    pa = [poisson_pmf(i, lambda_a) for i in range(max_goals + 1)]
    pb = [poisson_pmf(i, lambda_b) for i in range(max_goals + 1)]
    return np.outer(pa, pb)

def outcome_probabilities(matrix):
    return float(np.sum(np.tril(matrix, -1))), float(np.sum(np.diag(matrix))), float(np.sum(np.triu(matrix, 1)))

def over_under_prob(matrix, line=2.5):
    total = 0.0
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if i + j > line:
                total += matrix[i, j]
    return float(total), float(1 - total)

def both_teams_to_score(matrix):
    total = 0.0
    for i in range(1, matrix.shape[0]):
        for j in range(1, matrix.shape[1]):
            total += matrix[i, j]
    return float(total)

def top_scores(matrix, current_home=0, current_away=0, n=10):
    rows = []
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            rows.append((f"{i+current_home}-{j+current_away}", float(matrix[i, j])))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows[:n]

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p = math.pi/180
    dlat = (lat2-lat1)*p
    dlon = (lon2-lon1)*p
    a = math.sin(dlat/2)**2 + math.cos(lat1*p)*math.cos(lat2*p)*math.sin(dlon/2)**2
    return 2*r*math.asin(math.sqrt(a))

def fatigue_label(km, rest_days):
    score = km/1500 - rest_days*0.35
    if score >= 1.8: return "Alta"
    if score >= 0.7: return "Media"
    return "Baja"

def infer_team_base(team_name):
    key = team_name.lower().strip()
    if key in TEAM_PRIORS:
        return TEAM_PRIORS[key].copy()
    seed = abs(hash(key)) % 10000
    rng = np.random.default_rng(seed)
    return {"elo": float(1450+rng.integers(0,240)), "form": float(np.round(rng.uniform(1.2,2.0),2)), "attack": float(np.round(rng.uniform(1.05,1.55),2)), "defense": float(np.round(rng.uniform(1.0,1.45),2))}

def lineup_strength(lineups, team_name):
    default = {"formation":"N/D","starters":11,"bench":7,"attack_bonus":0.0,"defense_bonus":0.0}
    if not lineups:
        return default
    best=None; bs=0.0
    for item in lineups:
        s = similarity(team_name, item.get("team",{}).get("name",""))
        if s > bs:
            bs=s; best=item
    if not best:
        return default
    formation = best.get("formation","N/D")
    start_xi = best.get("startXI",[]) or []
    subs = best.get("substitutes",[]) or []
    defenders = midfielders = attackers = 0
    for p in start_xi:
        pos = str(p.get("player",{}).get("pos","")).upper()
        if pos=="D": defenders += 1
        elif pos=="M": midfielders += 1
        elif pos=="F": attackers += 1
    return {
        "formation": formation,
        "starters": len(start_xi),
        "bench": len(subs),
        "attack_bonus": min(0.25, attackers*0.03 + max(midfielders-3,0)*0.01),
        "defense_bonus": min(0.18, defenders*0.02),
    }

def stats_to_dict(stats_rows, team_name):
    out = {"shots_on_goal":0.0,"total_shots":0.0,"corners":0.0,"possession":50.0,"yellow":0.0,"red":0.0}
    if not stats_rows:
        return out
    best=None; bs=0.0
    for item in stats_rows:
        s=similarity(team_name, item.get("team",{}).get("name",""))
        if s>bs:
            bs=s; best=item
    if not best:
        return out
    mapping={row.get("type",""):row.get("value") for row in best.get("statistics",[])}
    def clean(v):
        if isinstance(v,str) and "%" in v:
            return float(v.replace("%","").strip())
        try: return float(v)
        except: return 0.0
    out["shots_on_goal"]=clean(mapping.get("Shots on Goal",0))
    out["total_shots"]=clean(mapping.get("Total Shots",0))
    out["corners"]=clean(mapping.get("Corner Kicks",0))
    out["possession"]=clean(mapping.get("Ball Possession",50))
    out["yellow"]=clean(mapping.get("Yellow Cards",0))
    out["red"]=clean(mapping.get("Red Cards",0))
    return out

def auto_context(team_a_name, team_b_name, fixture):
    a_key = team_a_name.lower().strip(); b_key = team_b_name.lower().strip()
    a_ctx = TEAM_CONTEXT.get(a_key, {}); b_ctx = TEAM_CONTEXT.get(b_key, {})
    home_name = fixture.get("teams",{}).get("home",{}).get("name","")
    away_name = fixture.get("teams",{}).get("away",{}).get("name","")
    is_a_home = similarity(team_a_name, home_name) > similarity(team_a_name, away_name)
    crowd_a = a_ctx.get("crowd", 0.80 if is_a_home else 0.20)
    crowd_b = b_ctx.get("crowd", 0.80 if not is_a_home else 0.20)
    home_ctx = TEAM_CONTEXT.get(home_name.lower().strip(), a_ctx if is_a_home else b_ctx)
    away_ctx = TEAM_CONTEXT.get(away_name.lower().strip(), b_ctx if not is_a_home else a_ctx)
    if a_ctx and home_ctx:
        travel_a = 0 if is_a_home else int(round(haversine_km(a_ctx["lat"], a_ctx["lon"], home_ctx["lat"], home_ctx["lon"])))
    else:
        travel_a = 0 if is_a_home else 1200
    if b_ctx and away_ctx:
        travel_b = 0 if not is_a_home else int(round(haversine_km(b_ctx["lat"], b_ctx["lon"], away_ctx["lat"], away_ctx["lon"])))
    else:
        travel_b = 1200 if not is_a_home else 0
    return {
        "crowd_a": min(max(crowd_a,0.0),1.0),
        "crowd_b": min(max(crowd_b,0.0),1.0),
        "travel_a": max(travel_a,0),
        "travel_b": max(travel_b,0),
        "rest_a": 5,
        "rest_b": 4,
        "fatigue_a": fatigue_label(max(travel_a,0), 5),
        "fatigue_b": fatigue_label(max(travel_b,0), 4),
    }

def build_auto_profile(team_name, lineup_info, stats_info, crowd_factor, travel_km, rest_days, injuries):
    base = infer_team_base(team_name)
    attack = base["attack"] + lineup_info["attack_bonus"] + min(0.18, stats_info["shots_on_goal"]*0.025) + min(0.10, stats_info["corners"]*0.012)
    defense = base["defense"] - lineup_info["defense_bonus"] - min(0.12, stats_info["possession"]/100*0.08) + min(0.20, stats_info["red"]*0.08)
    form = base["form"] + min(0.20, stats_info["total_shots"]*0.01) - min(0.15, stats_info["red"]*0.08)
    return {"elo": base["elo"], "form": max(0.4,form), "attack": max(0.4,attack), "defense": max(0.4,defense), "injuries": injuries, "rest_days": rest_days, "travel_km": travel_km, "crowd_factor": crowd_factor, "formation": lineup_info["formation"], "starters": lineup_info["starters"], "bench": lineup_info["bench"]}

def expected_goals(a, b, fixture=None, stats_a=None, stats_b=None):
    stats_a = stats_a or {}
    stats_b = stats_b or {}
    current_home = (fixture or {}).get("goals",{}).get("home")
    current_away = (fixture or {}).get("goals",{}).get("away")
    minute = (fixture or {}).get("fixture",{}).get("status",{}).get("elapsed") or 0
    home_boost = 0.10 + 0.17*a["crowd_factor"]
    sg = (a["elo"] - b["elo"])/100
    la = 1.05 + 0.10*sg + 0.18*(a["form"]-b["form"]) + 0.32*(a["attack"]-b["defense"]) + home_boost + 0.025*(a["rest_days"]-b["rest_days"]) - 0.018*a["injuries"] - 0.000025*max(a["travel_km"]-b["travel_km"],0)
    lb = 0.90 - 0.09*sg - 0.14*(a["form"]-b["form"]) + 0.26*(b["attack"]-a["defense"]) + 0.025*(b["rest_days"]-a["rest_days"]) - 0.018*b["injuries"] - 0.000025*max(b["travel_km"]-a["travel_km"],0)
    if fixture and minute and minute > 0:
        rem = max(5, 95 - minute) / 90.0
        lead_home = (current_home or 0) - (current_away or 0)
        live_momentum = ((stats_a.get("shots_on_goal",0)-stats_b.get("shots_on_goal",0))*0.08 +
                         (stats_a.get("total_shots",0)-stats_b.get("total_shots",0))*0.02 +
                         ((stats_a.get("possession",50)-stats_b.get("possession",50))/100)*0.25)
        la = max(0.05, (la + live_momentum - max(0, lead_home)*0.12) * rem)
        lb = max(0.05, (lb - live_momentum + max(0, -lead_home)*0.12) * rem)
    return max(0.05,min(4.2,la)), max(0.05,min(4.0,lb))

def dominance_index(stats_a, stats_b):
    return (stats_a["shots_on_goal"]-stats_b["shots_on_goal"])*0.22 + (stats_a["total_shots"]-stats_b["total_shots"])*0.10 + (stats_a["corners"]-stats_b["corners"])*0.08 + ((stats_a["possession"]-stats_b["possession"])/10)*0.08 - (stats_a["red"]-stats_b["red"])*0.35

def ai_fallback(match_name, fixture, probs, best_score, best_bet, dom_idx):
    p1, px, p2 = probs
    minute = (fixture or {}).get("fixture",{}).get("status",{}).get("elapsed")
    score_now = fixture.get("goals",{}) if fixture else {}
    if p1 >= p2 and p1 > 0.44:
        verdict = f"{match_name.split(' vs ')[0]} gana"
    elif p2 > p1 and p2 > 0.44:
        verdict = f"{match_name.split(' vs ')[1]} gana"
    else:
        verdict = "Empate con cierre ajustado"
    live_note = f" Va {score_now.get('home',0)}-{score_now.get('away',0)} al {minute}' y ZOLA recalcula con datos en vivo." if minute else ""
    bet = best_bet[0] if best_bet else "Sin mercado premium"
    return f"Predicción ZOLA: {verdict}. Marcador proyectado: {best_score}. Dominancia estimada: {dom_idx:.2f}.{live_note} Mejor oportunidad detectada: {bet}."

def ai_analysis(match_name, fixture, stats_a, stats_b, probs, best_score, best_bet, top_scores_rows):
    if not OPENAI_API_KEY:
        return ai_fallback(match_name, fixture, probs, best_score, best_bet, dominance_index(stats_a, stats_b))
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = f"""
Eres ZOLA Elite, analista directo de fútbol con tono firme y profesional.
Partido: {match_name}
Estado: {fixture.get('fixture',{}).get('status',{}).get('long','PRE')}
Minuto: {fixture.get('fixture',{}).get('status',{}).get('elapsed','0')}
Marcador actual: {fixture.get('goals',{}).get('home',0)}-{fixture.get('goals',{}).get('away',0)}
Probabilidades modelo local/empate/visita: {probs}
Marcador principal modelo: {best_score}
Top marcadores: {top_scores_rows[:5]}
Stats local: {stats_a}
Stats visita: {stats_b}
Mejor mercado detectado: {best_bet}
Devuelve SOLO:
1) una predicción final firme en una frase
2) una explicación corta en 2 frases
3) una mejor apuesta del momento en 1 frase
Sin advertencias, sin listas, sin decir que eres IA.
"""
        resp = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
        )
        return (getattr(resp, "output_text", None) or ai_fallback(match_name, fixture, probs, best_score, best_bet, dominance_index(stats_a, stats_b))).strip()
    except Exception:
        return ai_fallback(match_name, fixture, probs, best_score, best_bet, dominance_index(stats_a, stats_b))

@st.cache_data(ttl=120)
def fetch_fixtures(api_key, on_date):
    if not api_key:
        return []
    headers = {"x-apisports-key": api_key}
    data = api_get(f"{API_FOOTBALL_BASE}/fixtures", headers=headers, params={"date": on_date.isoformat(), "timezone": LIMA_TZ})
    return data.get("response", [])

@st.cache_data(ttl=120)
def fetch_lineups(api_key, fixture_id):
    if not api_key or not fixture_id:
        return []
    headers = {"x-apisports-key": api_key}
    return api_get(f"{API_FOOTBALL_BASE}/fixtures/lineups", headers=headers, params={"fixture": fixture_id}).get("response", [])

@st.cache_data(ttl=60)
def fetch_stats(api_key, fixture_id):
    if not api_key or not fixture_id:
        return []
    headers = {"x-apisports-key": api_key}
    return api_get(f"{API_FOOTBALL_BASE}/fixtures/statistics", headers=headers, params={"fixture": fixture_id}).get("response", [])

def fetch_odds(the_odds_key, sport_key, team_a, team_b):
    out = {"team_a_win": np.nan, "draw": np.nan, "team_b_win": np.nan, "over_2_5": np.nan, "under_2_5": np.nan, "bookmaker": ""}
    if not the_odds_key:
        return out
    try:
        payload = api_get(f"{ODDS_API_BASE}/sports/{sport_key}/odds", params={"apiKey": the_odds_key, "regions": "eu", "markets": "h2h,totals", "oddsFormat": "decimal", "dateFormat": "iso"})
        best = None; best_score = 0.0
        for event in payload:
            home = event.get("home_team","")
            away = event.get("away_team","")
            score = max(similarity(team_a, home)+similarity(team_b, away), similarity(team_a, away)+similarity(team_b, home))
            if score > best_score:
                best_score = score; best = event
        if not best or not best.get("bookmakers"):
            return out
        bm = best["bookmakers"][0]
        out["bookmaker"] = bm.get("title","")
        for market in bm.get("markets", []):
            key = market.get("key")
            for o in market.get("outcomes", []):
                nm = o.get("name",""); pr = o.get("price")
                if key == "h2h":
                    if similarity(nm, team_a) > 0.8: out["team_a_win"] = pr
                    elif similarity(nm, team_b) > 0.8: out["team_b_win"] = pr
                    elif nm.lower() == "draw": out["draw"] = pr
                elif key == "totals" and o.get("point") == 2.5:
                    if str(nm).lower() == "over": out["over_2_5"] = pr
                    elif str(nm).lower() == "under": out["under_2_5"] = pr
        return out
    except Exception:
        return out

def model_odds(prob):
    return round(1/max(prob, 0.03), 2)

def best_bet_summary(odds, p_a, p_d, p_b, p_over, p_under, bankroll):
    opts = [("Victoria local", odds.get("team_a_win"), p_a), ("Empate", odds.get("draw"), p_d), ("Victoria visita", odds.get("team_b_win"), p_b), ("Over 2.5", odds.get("over_2_5"), p_over), ("Under 2.5", odds.get("under_2_5"), p_under)]
    best=None; best_ev=-999
    for label, odd, prob in opts:
        if not odd or np.isnan(odd):
            odd = model_odds(prob)
        ev = expected_value(prob, odd)
        if not np.isnan(ev) and ev > best_ev:
            best_ev = ev
            best = (label, odd, prob, ev, kelly_fraction(prob, odd)*bankroll*0.25)
    return best

# Header
logo_path = "zola_crest.png" if Path("zola_crest.png").exists() else ""
st.markdown('<div class="topbar">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([2.2, 3.8, 2.2])
with c1:
    if logo_path:
        st.markdown(f'<div class="brand"><img src="data:image/png;base64,{Path(logo_path).read_bytes().hex()}"></div>', unsafe_allow_html=False)
# above won't work with hex directly; use streamlit image below
    cols = st.columns([0.18,0.82])
    with cols[0]:
        if logo_path:
            st.image(logo_path, width=40)
    with cols[1]:
        st.markdown('<div class="brand"><div><div class="title">ZOLA Elite</div><div style="color:#dbe5ff;font-size:.84rem;font-weight:700">Live-score, cuotas e IA en una sola lectura.</div></div></div>', unsafe_allow_html=True)
with c2:
    q = st.text_input("Buscar partido", value=st.session_state.query, placeholder="Busca partidos, competiciones, equipos...", label_visibility="collapsed")
    st.session_state.query = q
with c3:
    st.markdown(f"""
    <div style="display:flex;justify-content:flex-end;gap:10px;flex-wrap:wrap">
      <div class="pill"><span class="dot"></span>API-Football</div>
      <div class="pill"><span class="dot"></span>The Odds API</div>
      <div class="pill"><span class="dot"></span>IA</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("""
<div class="sports">
  <div class="item active">Fútbol</div>
  <div class="item">En vivo</div>
  <div class="item">Hoy</div>
  <div class="item">Mañana</div>
  <div class="item">Top ligas</div>
  <div class="item">Movimiento de cuotas</div>
  <div class="item">IA ZOLA</div>
</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

with st.popover("⚙️ Configuración", use_container_width=False):
    if ADMIN_PASSWORD:
        pwd = st.text_input("Clave admin", type="password")
        if pwd != ADMIN_PASSWORD:
            st.info("Ingresa la clave para ver o cambiar la configuración.")
            st.stop()
    th = st.radio("Tema", ["Claro","Oscuro"], index=0 if st.session_state.theme=="light" else 1, horizontal=True)
    if th == "Claro":
        st.session_state.theme = "light"
    else:
        st.session_state.theme = "dark"
    st.caption("Puedes dejar las claves en Render o guardarlas solo en esta sesión del navegador.")
    st.session_state["API_FOOTBALL_KEY"] = st.text_input("API Football", value=API_FOOTBALL_KEY, type="password")
    st.session_state["THE_ODDS_API_KEY"] = st.text_input("The Odds API", value=THE_ODDS_API_KEY, type="password")
    st.session_state["SPORTMONKS_API_TOKEN"] = st.text_input("Sportmonks", value=SPORTMONKS_API_TOKEN, type="password")
    st.session_state["OPENAI_API_KEY"] = st.text_input("OpenAI", value=OPENAI_API_KEY, type="password")
    st.success("Configuración lista. Si cambiaste algo, recarga la página o analiza de nuevo.")
    st.caption("Para dejarlo fijo en producción, usa Render > Environment.")

# refresh after config potentially
API_FOOTBALL_KEY = st.session_state.get("API_FOOTBALL_KEY", API_FOOTBALL_KEY)
THE_ODDS_API_KEY = st.session_state.get("THE_ODDS_API_KEY", THE_ODDS_API_KEY)
SPORTMONKS_API_TOKEN = st.session_state.get("SPORTMONKS_API_TOKEN", SPORTMONKS_API_TOKEN)
OPENAI_API_KEY = st.session_state.get("OPENAI_API_KEY", OPENAI_API_KEY)
inject_css(st.session_state.theme)

nav_col, right = st.columns([1.2, 2.2], gap="large")

with nav_col:
    page = st.radio("Vista", ["En vivo","Hoy","Mañana"], index=["live","today","tomorrow"].index(st.session_state.page) if st.session_state.page in ["live","today","tomorrow"] else 0, horizontal=True, label_visibility="collapsed")
    st.session_state.page = {"En vivo":"live","Hoy":"today","Mañana":"tomorrow"}[page]
    target_date = date.today()
    if st.session_state.page == "tomorrow":
        target_date = date.today() + timedelta(days=1)
    fixtures = fetch_fixtures(API_FOOTBALL_KEY, target_date)
    if st.session_state.page == "live":
        fixtures = [f for f in fixtures if f.get("fixture",{}).get("status",{}).get("short") not in ("NS","TBD","PST","CANC","ABD")]
    if st.session_state.query:
        q = st.session_state.query.lower()
        fixtures = [f for f in fixtures if q in f.get("teams",{}).get("home",{}).get("name","").lower() or q in f.get("teams",{}).get("away",{}).get("name","").lower() or q in f.get("league",{}).get("name","").lower()]
    comp = st.segmented_control("Competición", list(COMP_KEYS.keys()), selection_mode="single", default="Top")
    league_filter = set(COMP_KEYS.get(comp or "Top", []))
    filtered = [f for f in fixtures if not league_filter or f.get("league",{}).get("id") in league_filter]
    if not filtered:
        st.info("No hay partidos para esta vista.")
    for fx in filtered[:60]:
        fxid = fx.get("fixture",{}).get("id")
        home = fx.get("teams",{}).get("home",{}).get("name","")
        away = fx.get("teams",{}).get("away",{}).get("name","")
        lg = fx.get("league",{}).get("name","")
        lg_logo = fx.get("league",{}).get("logo","")
        hlogo = fx.get("teams",{}).get("home",{}).get("logo","")
        alogo = fx.get("teams",{}).get("away",{}).get("logo","")
        short = fx.get("fixture",{}).get("status",{}).get("short","")
        elapsed = fx.get("fixture",{}).get("status",{}).get("elapsed")
        active_cls = "active" if st.session_state.selected_fixture_id == fxid else ""
        score_home = fx.get("goals",{}).get("home")
        score_away = fx.get("goals",{}).get("away")
        status_txt = f"{elapsed}'" if elapsed else short
        with st.container():
            cols = st.columns([8,1], gap="small")
            with cols[0]:
                st.markdown(f'<div class="league">{lg}</div>', unsafe_allow_html=True)
                if st.button(f"{home} vs {away} | {status_txt}", key=f"fx{fxid}", use_container_width=True):
                    st.session_state.selected_fixture_id = fxid
                    save_selection(fx)
                    st.rerun()
            with cols[1]:
                st.write(f"{score_home if score_home is not None else '-'}-{score_away if score_away is not None else '-'}")
    if filtered and not st.session_state.selected_fixture_id:
        st.session_state.selected_fixture_id = filtered[0].get("fixture",{}).get("id")

selected = None
for f in fixtures:
    if f.get("fixture",{}).get("id") == st.session_state.selected_fixture_id:
        selected = f
        break
if not selected and fixtures:
    selected = fixtures[0]

with right:
    if not selected:
        st.info("Selecciona un partido.")
    else:
        fixture = selected
        fixture_id = fixture.get("fixture",{}).get("id")
        home = fixture.get("teams",{}).get("home",{}).get("name","")
        away = fixture.get("teams",{}).get("away",{}).get("name","")
        match_name = f"{home} vs {away}"
        home_logo = fixture.get("teams",{}).get("home",{}).get("logo","")
        away_logo = fixture.get("teams",{}).get("away",{}).get("logo","")
        league_name = fixture.get("league",{}).get("name","")
        league_logo = fixture.get("league",{}).get("logo","")
        goals = fixture.get("goals",{})
        elapsed = fixture.get("fixture",{}).get("status",{}).get("elapsed")
        status_long = fixture.get("fixture",{}).get("status",{}).get("long","PRE")
        lineups = fetch_lineups(API_FOOTBALL_KEY, fixture_id)
        stats_rows = fetch_stats(API_FOOTBALL_KEY, fixture_id)
        context = auto_context(home, away, fixture)
        lineup_a = lineup_strength(lineups, home)
        lineup_b = lineup_strength(lineups, away)
        stats_a = stats_to_dict(stats_rows, home)
        stats_b = stats_to_dict(stats_rows, away)
        a_profile = build_auto_profile(home, lineup_a, stats_a, context["crowd_a"], context["travel_a"], context["rest_a"], 0)
        b_profile = build_auto_profile(away, lineup_b, stats_b, context["crowd_b"], context["travel_b"], context["rest_b"], 0)
        lam_home, lam_away = expected_goals(a_profile, b_profile, fixture, stats_a, stats_b)
        current_home = int(goals.get("home") or 0)
        current_away = int(goals.get("away") or 0)
        matrix = score_matrix(lam_home, lam_away, max_goals=6)
        p1, px, p2 = outcome_probabilities(matrix)
        p_over, p_under = over_under_prob(matrix,2.5)
        p_btts = both_teams_to_score(matrix)
        score_rows = top_scores(matrix, current_home, current_away, 10)
        best_score, best_prob = score_rows[0]
        odds = fetch_odds(THE_ODDS_API_KEY, SPORT_KEY_SUGGESTIONS[0], home, away)
        best_bet = best_bet_summary(odds, p1, px, p2, p_over, p_under, 1000)
        ai_text = ai_analysis(match_name, fixture, stats_a, stats_b, (p1,px,p2), best_score, best_bet, score_rows)
        dom_idx = dominance_index(stats_a, stats_b)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        left_h, center_h, right_h = st.columns([1.25,1,1.25])
        with left_h:
            if home_logo:
                st.image(home_logo, width=72)
            st.markdown(f'<div class="team-name">{home}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tiny">Prob. ganar {p1:.1%}</div>', unsafe_allow_html=True)
        with center_h:
            if league_logo:
                st.image(league_logo, width=22)
            st.markdown(f'<div class="competition">{league_name}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="bigscore">{current_home}-{current_away}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="bigstatus">{"EN VIVO " + str(elapsed) + "\'" if elapsed else status_long}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tiny">Predicción ZOLA: {best_score}</div>', unsafe_allow_html=True)
        with right_h:
            if away_logo:
                st.image(away_logo, width=72)
            st.markdown(f'<div class="team-name">{away}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tiny">Prob. ganar {p2:.1%}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        cta = st.columns(4)
        qvals = [("1 · Gana local", p1), ("X · Empate", px), ("2 · Gana visita", p2), ("Mejor cuota", best_bet[1] if best_bet else np.nan)]
        for i,(label,val) in enumerate(qvals):
            with cta[i]:
                if i < 3:
                    st.markdown(f'<div class="market-box"><div class="label">{label}</div><div class="value">{val:.1%}</div></div>', unsafe_allow_html=True)
                else:
                    shown = f"{val:.2f}" if val and not np.isnan(val) else "N/D"
                    st.markdown(f'<div class="market-box"><div class="label">{label}</div><div class="value">{shown}</div></div>', unsafe_allow_html=True)

        lcol, rcol = st.columns([1.35, 1], gap="medium")
        with lcol:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">IA ZOLA</div>', unsafe_allow_html=True)
            st.write(ai_text)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Mercados principales</div>', unsafe_allow_html=True)
            rows = [
                [f"1 Local", p1, odds.get("team_a_win") if odds.get("team_a_win") and not np.isnan(odds.get("team_a_win")) else model_odds(p1)],
                [f"X Empate", px, odds.get("draw") if odds.get("draw") and not np.isnan(odds.get("draw")) else model_odds(px)],
                [f"2 Visita", p2, odds.get("team_b_win") if odds.get("team_b_win") and not np.isnan(odds.get("team_b_win")) else model_odds(p2)],
                ["Over 2.5", p_over, odds.get("over_2_5") if odds.get("over_2_5") and not np.isnan(odds.get("over_2_5")) else model_odds(p_over)],
                ["Under 2.5", p_under, odds.get("under_2_5") if odds.get("under_2_5") and not np.isnan(odds.get("under_2_5")) else model_odds(p_under)],
                ["BTTS Sí", p_btts, model_odds(p_btts)],
            ]
            dfm = pd.DataFrame(rows, columns=["Mercado","Modelo","Cuota"])
            dfm["EV"] = dfm.apply(lambda r: expected_value(r["Modelo"], r["Cuota"]), axis=1)
            st.dataframe(dfm.style.format({"Modelo":"{:.1%}","Cuota":"{:.2f}","EV":"{:.3f}"}), use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Top marcadores</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(score_rows, columns=["Marcador","Probabilidad"]).style.format({"Probabilidad":"{:.1%}"}), use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with rcol:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Resumen rápido</div>', unsafe_allow_html=True)
            quick = st.columns(4)
            vals = [("Over 2.5", p_over),("BTTS", p_btts),("Dominancia", dom_idx),("Stake", best_bet[4] if best_bet else 0)]
            for i,(k,v) in enumerate(vals):
                with quick[i]:
                    txt = f"{v:.1%}" if i < 2 else f"{v:.2f}" if i==2 else f"S/ {v:.2f}"
                    st.markdown(f'<div class="quick-box"><div class="k">{k}</div><div class="v">{txt}</div></div>', unsafe_allow_html=True)
            winner_text = "Victoria local" if p1 >= max(px,p2) else "Empate" if px >= max(p1,p2) else "Victoria visita"
            st.markdown(f'<div class="good">Escenario principal: {winner_text}. Marcador proyectado: {best_score}.</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="warn">Operador: {odds.get("bookmaker","Modelo propio")} · Mejor jugada: {best_bet[0] if best_bet else "N/D"}.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Comparativa</div>', unsafe_allow_html=True)
            comp_df = pd.DataFrame({
                "Indicador":["Tiros","Tiros al arco","Posesión","Corners","Amarillas","Rojas"],
                home:[stats_a["total_shots"], stats_a["shots_on_goal"], stats_a["possession"], stats_a["corners"], stats_a["yellow"], stats_a["red"]],
                away:[stats_b["total_shots"], stats_b["shots_on_goal"], stats_b["possession"], stats_b["corners"], stats_b["yellow"], stats_b["red"]],
            })
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Contexto</div>', unsafe_allow_html=True)
            ctx_df = pd.DataFrame([
                [home, lineup_a["formation"], context["travel_a"], context["rest_a"], context["fatigue_a"]],
                [away, lineup_b["formation"], context["travel_b"], context["rest_b"], context["fatigue_b"]],
            ], columns=["Equipo","Formación","Viaje km","Descanso","Fatiga"])
            st.dataframe(ctx_df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
