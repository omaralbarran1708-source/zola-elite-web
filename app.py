import os
import math
from datetime import date
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="ZOLA Elite", page_icon="⚽", layout="wide", initial_sidebar_state="collapsed")

# ----------------------------
# THEME / CSS
# ----------------------------
st.markdown(
    """
<style>
:root{
  --bg:#eef3fb;
  --panel:#ffffff;
  --line:#d9e3f2;
  --text:#0f172a;
  --muted:#64748b;
  --brand:#1d4ed8;
  --brand2:#2563eb;
  --green:#10b981;
  --red:#ef4444;
  --orange:#f59e0b;
  --soft:#f8fbff;
}
html, body, [class*="css"]  { font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.stApp{background:linear-gradient(180deg,#eff4fb 0%,#edf2fa 100%); color:var(--text);}
.block-container{max-width:1380px;padding-top:0.7rem;padding-bottom:2rem;}
section[data-testid="stSidebar"]{display:none;}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu, footer {visibility:hidden;}

.z-topbar{
  background:linear-gradient(90deg,#1f4ed8 0%,#285ee8 70%,#2b63ef 100%);
  color:white; border-radius:20px; padding:18px 22px; box-shadow:0 16px 36px rgba(29,78,216,.16);
  margin-bottom:18px; border:1px solid rgba(255,255,255,.18);
}
.z-topbar-row{display:flex; justify-content:space-between; align-items:center; gap:16px;}
.z-brand{display:flex; align-items:center; gap:12px;}
.z-brand-badge{
  width:48px;height:48px;border-radius:14px;background:rgba(255,255,255,.16);display:flex;align-items:center;justify-content:center;
  border:1px solid rgba(255,255,255,.28); backdrop-filter: blur(4px);
}
.z-brand-title{font-size:2rem;font-weight:900;line-height:1;letter-spacing:.01em;}
.z-brand-sub{font-size:.95rem;opacity:.92;margin-top:4px;}
.z-topbar-right{display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:flex-end;}
.z-chip{
  display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:8px 12px; font-size:.82rem;
  background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.22); color:white;
}
.z-card{
  background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:16px 16px 14px 16px;
  box-shadow:0 8px 22px rgba(15,23,42,.04);
}
.z-card-title{font-weight:800; font-size:1.05rem; margin-bottom:10px; color:#0b1326;}
.z-muted{color:var(--muted);}
.z-match-head{
  background:var(--panel); border:1px solid var(--line); border-radius:20px; padding:18px; margin-bottom:16px; box-shadow:0 8px 22px rgba(15,23,42,.04);
}
.z-match-grid{display:grid; grid-template-columns: 1.2fr .9fr 1.2fr; gap:16px; align-items:center;}
.z-team-box{text-align:center;}
.z-team-name{font-weight:900; font-size:1.55rem; color:#0f172a; line-height:1.15;}
.z-team-sub{color:var(--muted); font-size:.92rem; margin-top:6px;}
.z-center-box{text-align:center;}
.z-kick{font-size:2rem; font-weight:900; color:#0f172a;}
.z-meta{color:var(--muted); font-size:.95rem; margin-top:4px;}
.z-league{display:flex; justify-content:center; align-items:center; gap:8px; color:#0f172a; font-weight:700; margin-bottom:10px;}
.z-outcome-grid{display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:14px;}
.z-outcome{
  background:#f8fbff; border:1px solid #d8e6ff; border-radius:18px; padding:14px 10px; text-align:center;
}
.z-outcome b{display:block; font-size:1.9rem; color:#0f172a; margin-top:6px;}
.z-outcome span{font-size:.88rem; color:#5974a3; font-weight:800; letter-spacing:.03em;}
.z-score-pill{
  display:inline-flex; align-items:center; justify-content:center; background:#f0f7ff; border:1px solid #cfe2ff; color:#0f172a;
  border-radius:999px; padding:10px 18px; font-weight:900; font-size:1.2rem;
}
.z-pill-win{background:#ecfdf5;border-color:#b7f0d3;color:#065f46;}
.z-pill-draw{background:#fff7ed;border-color:#fed7aa;color:#9a3412;}
.z-pill-loss{background:#fef2f2;border-color:#fecaca;color:#991b1b;}
.z-statline{margin-bottom:14px;}
.z-statline-top{display:flex;justify-content:space-between;font-size:.92rem;margin-bottom:6px;}
.z-statbar{height:10px;background:#edf2f9;border-radius:999px;overflow:hidden;border:1px solid #d8e0ec;}
.z-statbar-fill{height:100%;background:linear-gradient(90deg,#2563eb,#3b82f6);border-radius:999px;}
.z-alert{
  border-radius:16px; padding:14px 16px; margin-top:10px; font-size:1rem; line-height:1.45; border:1px solid #dbeafe; background:#eff6ff; color:#1d4ed8;
}
.z-alert.good{background:#ecfdf5;border-color:#b7f0d3;color:#166534;}
.z-alert.warn{background:#fff7ed;border-color:#fed7aa;color:#b45309;}
.z-market-best{
  background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%); color:white; border-radius:18px; padding:16px; border:1px solid #1e3a8a;
}
.z-market-best small{color:#cbd5e1;}
.z-mini-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.z-mini-card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:14px;}
.z-mini-card .k{font-size:.82rem;color:#64748b;font-weight:800;letter-spacing:.03em;}
.z-mini-card .v{font-size:1.95rem;font-weight:900;color:#0f172a;margin-top:8px;}
.z-table-wrap table{width:100%;border-collapse:collapse;overflow:hidden;border-radius:14px;}
.z-table-wrap th,.z-table-wrap td{padding:12px 12px;border-bottom:1px solid #e6edf7;text-align:left;font-size:.95rem;}
.z-table-wrap thead th{background:#f8fbff;color:#58719a;font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;}
.z-table-wrap tr:last-child td{border-bottom:none;}
img.z-logo-mini{max-height:40px; width:auto; display:block; margin:auto;}
img.z-team-logo{max-height:72px; width:auto; display:block; margin:0 auto 10px auto;}
img.z-league-logo{max-height:24px; width:auto;}
div[data-testid="stHorizontalBlock"] > div:has(> div > .z-card){height:100%;}
.stButton>button{
  background:linear-gradient(90deg,#ef4444,#ff5a5f)!important; color:white!important; border:none!important; border-radius:14px!important;
  font-weight:800!important; min-height:46px;
}
.stTextInput input, .stNumberInput input, .stDateInput input,
.stSelectbox [data-baseweb="select"] > div, .stTextArea textarea{
  background:#fff!important;border:1px solid #d9e3f2!important;border-radius:14px!important;color:#0f172a!important;
}
.stToggle label{font-weight:700;}
[data-testid="column"] .stImage img{border-radius:16px;}
</style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# CONFIG / CONSTANTS
# ----------------------------
API_FOOTBALL_BASE = os.getenv("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
ODDS_API_BASE = os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4")
LIMA_TZ = "America/Lima"
HISTORY_FILE = "zola_match_history.csv"
DEFAULT_BANKROLL = 1000.0
LOGO_CREST_PATH = "zola_crest.png"

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
SPORT_KEY_SUGGESTIONS = [
    "soccer_conmebol_libertadores", "soccer_conmebol_sudamericana", "soccer_uefa_champs_league",
    "soccer_spain_la_liga", "soccer_epl", "soccer_italy_serie_a", "soccer_germany_bundesliga",
    "soccer_france_ligue_one", "soccer_brazil_campeonato",
]
PREMIUM_KEYWORDS = [
    "libertadores", "sudamericana", "champions", "europa league", "premier", "la liga", "serie a",
    "bundesliga", "ligue 1", "brasileirao", "campeonato brasileiro", "argentina", "mls", "liga mx",
    "afc champions", "caf champions", "world cup", "copa america", "euro", "nations league"
]

# ----------------------------
# SESSION STATE
# ----------------------------
for key, default in {
    "watchlist": [],
    "api_football_key_override": "",
    "odds_api_key_override": "",
    "sportmonks_token_override": "",
    "admin_ok": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ----------------------------
# HELPERS
# ----------------------------
def current_api_football_key():
    return st.session_state.api_football_key_override or os.getenv("API_FOOTBALL_KEY", "")

def current_odds_api_key():
    return st.session_state.odds_api_key_override or os.getenv("THE_ODDS_API_KEY", "")

def current_sportmonks_token():
    return st.session_state.sportmonks_token_override or os.getenv("SPORTMONKS_API_TOKEN", "")

def admin_password():
    return os.getenv("ADMIN_PASSWORD", "")

def load_history_file():
    if os.path.exists(HISTORY_FILE):
        try:
            return pd.read_csv(HISTORY_FILE)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def save_history_row(row):
    df = load_history_file()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(HISTORY_FILE, index=False)

def similarity(a, b):
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def parse_match_query(text):
    for sep in [" vs ", " VS ", " Vs ", " v ", " - ", " contra "]:
        if sep in text:
            p = text.split(sep, 1)
            return p[0].strip(), p[1].strip()
    return text.strip(), ""

def api_get(url, headers=None, params=None):
    r = requests.get(url, headers=headers, params=params, timeout=30)
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

def top_scores(matrix, n=10):
    rows = []
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            rows.append((f"{i}-{j}", float(matrix[i, j])))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows[:n]

def is_premium_competition(league_name):
    lower = league_name.lower()
    return any(k in lower for k in PREMIUM_KEYWORDS)

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p = math.pi / 180
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def fatigue_label(km, rest_days):
    score = km / 1500 - rest_days * 0.35
    if score >= 1.8:
        return "Alta"
    if score >= 0.7:
        return "Media"
    return "Baja"

def auto_context(team_a_name, team_b_name, fixture):
    a_key = team_a_name.lower().strip()
    b_key = team_b_name.lower().strip()
    a_ctx = TEAM_CONTEXT.get(a_key, {})
    b_ctx = TEAM_CONTEXT.get(b_key, {})
    home_name = fixture.get("teams", {}).get("home", {}).get("name", "")
    away_name = fixture.get("teams", {}).get("away", {}).get("name", "")
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
        "crowd_a": min(max(crowd_a, 0.0), 1.0),
        "crowd_b": min(max(crowd_b, 0.0), 1.0),
        "travel_a": max(travel_a, 0),
        "travel_b": max(travel_b, 0),
        "rest_a": 5,
        "rest_b": 4,
        "fatigue_a": fatigue_label(max(travel_a, 0), 5),
        "fatigue_b": fatigue_label(max(travel_b, 0), 4),
    }

def fetch_today_fixtures(api_key, on_date):
    headers = {"x-apisports-key": api_key}
    return api_get(f"{API_FOOTBALL_BASE}/fixtures", headers=headers, params={"date": on_date.isoformat(), "timezone": LIMA_TZ}).get("response", [])

def fetch_lineups_api_football(api_key, fixture_id):
    headers = {"x-apisports-key": api_key}
    return api_get(f"{API_FOOTBALL_BASE}/fixtures/lineups", headers=headers, params={"fixture": fixture_id}).get("response", [])

def fetch_stats_api_football(api_key, fixture_id):
    headers = {"x-apisports-key": api_key}
    return api_get(f"{API_FOOTBALL_BASE}/fixtures/statistics", headers=headers, params={"fixture": fixture_id}).get("response", [])

def fetch_events_api_football(api_key, fixture_id):
    headers = {"x-apisports-key": api_key}
    return api_get(f"{API_FOOTBALL_BASE}/fixtures/events", headers=headers, params={"fixture": fixture_id}).get("response", [])

def fetch_odds_the_odds_api(api_key, sport_key, team_a, team_b):
    payload = api_get(
        f"{ODDS_API_BASE}/sports/{sport_key}/odds",
        params={"apiKey": api_key, "regions": "eu", "markets": "h2h,totals", "oddsFormat": "decimal", "dateFormat": "iso"},
    )
    best = None
    best_score = 0.0
    for event in payload:
        home = event.get("home_team", "")
        away = event.get("away_team", "")
        score = max(similarity(team_a, home) + similarity(team_b, away), similarity(team_a, away) + similarity(team_b, home))
        if score > best_score:
            best_score = score
            best = event
    out = {"team_a_win": np.nan, "draw": np.nan, "team_b_win": np.nan, "over_2_5": np.nan, "under_2_5": np.nan, "bookmaker": ""}
    if not best or not best.get("bookmakers"):
        return out
    bm = best["bookmakers"][0]
    out["bookmaker"] = bm.get("title", "")
    for market in bm.get("markets", []):
        key = market.get("key")
        for o in market.get("outcomes", []):
            nm = o.get("name", "")
            pr = o.get("price")
            if key == "h2h":
                if similarity(nm, team_a) > 0.8:
                    out["team_a_win"] = pr
                elif similarity(nm, team_b) > 0.8:
                    out["team_b_win"] = pr
                elif nm.lower() == "draw":
                    out["draw"] = pr
            elif key == "totals" and o.get("point") == 2.5:
                if str(nm).lower() == "over":
                    out["over_2_5"] = pr
                elif str(nm).lower() == "under":
                    out["under_2_5"] = pr
    return out

def infer_team_base(team_name):
    key = team_name.lower().strip()
    if key in TEAM_PRIORS:
        return TEAM_PRIORS[key].copy()
    seed = abs(hash(key)) % 10000
    rng = np.random.default_rng(seed)
    return {"elo": float(1450 + rng.integers(0, 240)), "form": float(np.round(rng.uniform(1.2, 2.0), 2)), "attack": float(np.round(rng.uniform(1.05, 1.55), 2)), "defense": float(np.round(rng.uniform(1.0, 1.45), 2))}

def lineup_strength(lineups, team_name):
    default = {"formation": "N/D", "starters": 11, "bench": 7, "attack_bonus": 0.0, "defense_bonus": 0.0}
    if not lineups:
        return default
    best = None
    bs = 0.0
    for item in lineups:
        s = similarity(team_name, item.get("team", {}).get("name", ""))
        if s > bs:
            bs = s
            best = item
    if not best:
        return default
    formation = best.get("formation", "N/D")
    start_xi = best.get("startXI", []) or []
    subs = best.get("substitutes", []) or []
    defenders = midfielders = attackers = 0
    for p in start_xi:
        pos = str(p.get("player", {}).get("pos", "")).upper()
        if pos == "D":
            defenders += 1
        elif pos == "M":
            midfielders += 1
        elif pos == "F":
            attackers += 1
    return {
        "formation": formation,
        "starters": len(start_xi),
        "bench": len(subs),
        "attack_bonus": min(0.25, attackers * 0.03 + max(midfielders - 3, 0) * 0.01),
        "defense_bonus": min(0.18, defenders * 0.02),
    }

def lineup_readiness(info):
    if info["formation"] == "N/D":
        return "Alineación aún no liberada"
    if info["starters"] >= 11 and info["bench"] >= 7:
        return "Plantel completo"
    if info["starters"] >= 10:
        return "Plantel competitivo"
    return "Equipo con ajustes"

def stats_to_dict(stats_rows, team_name):
    out = {"shots_on_goal": 0.0, "total_shots": 0.0, "corners": 0.0, "possession": 50.0, "yellow": 0.0, "red": 0.0}
    if not stats_rows:
        return out
    best = None
    bs = 0.0
    for item in stats_rows:
        s = similarity(team_name, item.get("team", {}).get("name", ""))
        if s > bs:
            bs = s
            best = item
    if not best:
        return out
    mapping = {row.get("type", ""): row.get("value") for row in best.get("statistics", [])}

    def clean(v):
        if isinstance(v, str) and "%" in v:
            return float(v.replace("%", "").strip())
        try:
            return float(v)
        except Exception:
            return 0.0

    out["shots_on_goal"] = clean(mapping.get("Shots on Goal", 0))
    out["total_shots"] = clean(mapping.get("Total Shots", 0))
    out["corners"] = clean(mapping.get("Corner Kicks", 0))
    out["possession"] = clean(mapping.get("Ball Possession", 50))
    out["yellow"] = clean(mapping.get("Yellow Cards", 0))
    out["red"] = clean(mapping.get("Red Cards", 0))
    return out

def build_auto_profile(team_name, lineup_info, stats_info, crowd_factor, travel_km, rest_days, injuries):
    base = infer_team_base(team_name)
    attack = base["attack"] + lineup_info["attack_bonus"] + min(0.18, stats_info["shots_on_goal"] * 0.025) + min(0.10, stats_info["corners"] * 0.012)
    defense = base["defense"] - lineup_info["defense_bonus"] - min(0.12, stats_info["possession"] / 100 * 0.08) + min(0.20, stats_info["red"] * 0.08)
    form = base["form"] + min(0.20, stats_info["total_shots"] * 0.01) - min(0.15, stats_info["red"] * 0.08)
    return {
        "elo": base["elo"],
        "form": max(0.4, form),
        "attack": max(0.4, attack),
        "defense": max(0.4, defense),
        "injuries": injuries,
        "rest_days": rest_days,
        "travel_km": travel_km,
        "crowd_factor": crowd_factor,
        "formation": lineup_info["formation"],
        "starters": lineup_info["starters"],
        "bench": lineup_info["bench"],
    }

def expected_goals(a, b):
    home_boost = 0.10 + 0.17 * a["crowd_factor"]
    sg = (a["elo"] - b["elo"]) / 100
    la = 1.05 + 0.10 * sg + 0.18 * (a["form"] - b["form"]) + 0.32 * (a["attack"] - b["defense"]) + home_boost + 0.025 * (a["rest_days"] - b["rest_days"]) - 0.018 * a["injuries"] - 0.000025 * max(a["travel_km"] - b["travel_km"], 0)
    lb = 0.90 - 0.09 * sg - 0.14 * (a["form"] - b["form"]) + 0.26 * (b["attack"] - a["defense"]) + 0.025 * (b["rest_days"] - a["rest_days"]) - 0.018 * b["injuries"] - 0.000025 * max(b["travel_km"] - a["travel_km"], 0)
    return max(0.15, min(4.2, la)), max(0.10, min(4.0, lb))

def dominance_index(stats_a, stats_b):
    return (
        (stats_a["shots_on_goal"] - stats_b["shots_on_goal"]) * 0.22
        + (stats_a["total_shots"] - stats_b["total_shots"]) * 0.10
        + (stats_a["corners"] - stats_b["corners"]) * 0.08
        + ((stats_a["possession"] - stats_b["possession"]) / 10) * 0.08
        - (stats_a["red"] - stats_b["red"]) * 0.35
    )

def build_trader_signals(team_a, team_b, p_a, p_d, p_b, p_over, p_under, p_btts, odds, stats_a, stats_b, score_rows):
    sig = []
    dom = dominance_index(stats_a, stats_b)
    best_score = score_rows[0][0] if score_rows else "N/D"
    if odds:
        for market, prob, odd in [
            (f"{team_a} gana", p_a, odds.get("team_a_win")),
            ("Empate", p_d, odds.get("draw")),
            (f"{team_b} gana", p_b, odds.get("team_b_win")),
            ("Over 2.5", p_over, odds.get("over_2_5")),
            ("Under 2.5", p_under, odds.get("under_2_5")),
        ]:
            imp = implied_prob(odd)
            if odd and not np.isnan(imp):
                edge = prob - imp
                if edge >= 0.07:
                    sig.append(("good", f"Valor activo en {market}. Modelo {prob:.1%} vs mercado {imp:.1%}."))
                elif edge <= -0.08:
                    sig.append(("warn", f"Mercado más fuerte que el modelo en {market}."))
    if dom >= 1.2:
        sig.append(("good", f"{team_a} está dominando el partido por volumen y control."))
    elif dom <= -1.2:
        sig.append(("good", f"{team_b} está imponiendo ritmo y ventaja territorial."))
    if p_a > 0.70 and best_score.startswith(("2-", "3-", "1-0")):
        sig.append(("good", f"Escenario principal consistente con favorito fuerte: {best_score} para {team_a}."))
    if p_btts < 0.42:
        sig.append(("warn", "Sesgo fuerte a portería a cero de uno de los dos."))
    return sig

def best_bet_summary(odds, p_a, p_d, p_b, p_over, p_under, bankroll):
    opts = [
        ("1 - Local", odds.get("team_a_win"), p_a),
        ("X - Empate", odds.get("draw"), p_d),
        ("2 - Visita", odds.get("team_b_win"), p_b),
        ("Over 2.5", odds.get("over_2_5"), p_over),
        ("Under 2.5", odds.get("under_2_5"), p_under),
    ]
    best = None
    best_ev = -999
    for label, odd, prob in opts:
        ev = expected_value(prob, odd)
        if not np.isnan(ev) and ev > best_ev:
            best_ev = ev
            best = (label, odd, prob, ev, kelly_fraction(prob, odd) * bankroll * 0.25)
    return best

def pick_confidence(p_a, p_d, p_b, score_prob):
    gap = abs(p_a - p_b)
    if max(p_a, p_b) >= 0.72 and score_prob >= 0.14:
        return "Alta"
    if gap >= 0.22:
        return "Media"
    return "Competida"

def prediction_class(p_a, p_d, p_b):
    if p_a > max(p_d, p_b):
        return "local"
    if p_b > max(p_a, p_d):
        return "visita"
    return "empate"

def prediction_badge(pred_class):
    if pred_class == "local":
        return "z-pill-win", "Victoria local"
    if pred_class == "visita":
        return "z-pill-loss", "Victoria visita"
    return "z-pill-draw", "Empate"

def dynamic_ai_prediction(team_a, team_b, p_a, p_d, p_b, best_score, confidence, stats_a, stats_b, odds, best_bet, fixture_status):
    winner_class = prediction_class(p_a, p_d, p_b)
    ga, gb = best_score.split("-")
    if winner_class == "local":
        headline = f"{team_a} gana {ga}-{gb}"
        style = "good"
        reasons = [
            f"{team_a} llega con el mejor paquete ofensivo y control territorial.",
            f"La proyección central del modelo marca {best_score} como escenario dominante.",
        ]
    elif winner_class == "visita":
        headline = f"{team_b} gana {ga}-{gb}"
        style = "good"
        reasons = [
            f"{team_b} llega con ventaja de eficiencia ofensiva y respuesta defensiva.",
            f"El partido se abre hacia {best_score} como desenlace principal.",
        ]
    else:
        headline = f"Empate {ga}-{gb}"
        style = "warn"
        reasons = [
            "Los dos equipos llegan con fuerzas muy cercanas en el modelo central.",
            f"El cruce se cierra en {best_score} como marcador principal.",
        ]
    if stats_a["shots_on_goal"] + stats_b["shots_on_goal"] > 0:
        if stats_a["shots_on_goal"] > stats_b["shots_on_goal"]:
            reasons.append(f"{team_a} está produciendo más remates claros al arco.")
        elif stats_b["shots_on_goal"] > stats_a["shots_on_goal"]:
            reasons.append(f"{team_b} está generando las ocasiones más limpias del juego.")
    if best_bet:
        reasons.append(f"La mejor cuota activa del modelo es {best_bet[0]} @ {best_bet[1]:.2f}.")
    if fixture_status in {"1H", "2H", "HT", "ET", "BT", "P", "LIVE"}:
        reasons.append("Lectura en vivo integrada con el estado actual del encuentro.")
    return headline, confidence, style, reasons[:4]

def pattern_summary(history_df, team_a, team_b):
    if history_df.empty:
        return "Sin historial previo guardado en esta instancia."
    subset = history_df[
        history_df["match"].str.contains(team_a, case=False, na=False)
        | history_df["match"].str.contains(team_b, case=False, na=False)
    ]
    if subset.empty:
        return "Sin enfrentamientos guardados para estos equipos en la instancia actual."
    n = len(subset)
    if "prediction_hit_exact" in subset.columns and subset["prediction_hit_exact"].notna().any():
        hit = subset["prediction_hit_exact"].fillna(0).mean()
        return f"Historial ZOLA: {n} partidos relacionados y {hit:.1%} de exactitud exacta registrada."
    return f"Historial ZOLA: {n} partidos guardados."

def local_img(path, cls="z-logo-mini"):
    if os.path.exists(path):
        import base64
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f'<img class="{cls}" src="data:image/png;base64,{encoded}"/>'
    return ""

def remote_img(url, cls):
    if not url:
        return ""
    return f'<img class="{cls}" src="{url}"/>'

def format_pct(x):
    return f"{x:.1%}"

# ----------------------------
# TOP BAR
# ----------------------------
logo_html = local_img(LOGO_CREST_PATH)
api_ok = bool(current_api_football_key())
odds_ok = bool(current_odds_api_key())
sport_ok = bool(current_sportmonks_token())
status_chip = lambda label, ok: f'<span class="z-chip">{"🟢" if ok else "⚪"} {label}</span>'

st.markdown(
    f"""
<div class="z-topbar">
  <div class="z-topbar-row">
    <div class="z-brand">
      <div class="z-brand-badge">{logo_html if logo_html else '⚽'}</div>
      <div>
        <div class="z-brand-title">ZOLA Elite</div>
        <div class="z-brand-sub">Lectura en vivo, predicción directa y cuota de valor en una interfaz limpia.</div>
      </div>
    </div>
    <div class="z-topbar-right">
      {status_chip('API-Football', api_ok)}
      {status_chip('The Odds API', odds_ok)}
      {status_chip('Sportmonks', sport_ok)}
    </div>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# SETTINGS / ADMIN
# ----------------------------
with st.popover("⚙️ Configuración", use_container_width=False):
    st.markdown("### Acceso de configuración")
    if admin_password():
        pw = st.text_input("Clave admin", type="password", key="admin_password_input")
        if st.button("Ingresar", key="admin_login_btn"):
            st.session_state.admin_ok = pw == admin_password()
            if st.session_state.admin_ok:
                st.success("Acceso habilitado")
            else:
                st.error("Clave incorrecta")
    else:
        st.session_state.admin_ok = True
        st.info("No hay ADMIN_PASSWORD en Render. La configuración funciona libre en esta sesión.")

    if st.session_state.admin_ok:
        st.markdown("### Claves de sesión")
        st.caption("Estas claves viven solo en tu sesión del navegador. Para dejarlo fijo, usa Render > Settings > Environment Variables.")
        af = st.text_input("API Football", value=st.session_state.api_football_key_override, type="password")
        oa = st.text_input("The Odds API", value=st.session_state.odds_api_key_override, type="password")
        sm = st.text_input("Sportmonks", value=st.session_state.sportmonks_token_override, type="password")
        if st.button("Guardar en esta sesión", key="save_session_keys"):
            st.session_state.api_football_key_override = af.strip()
            st.session_state.odds_api_key_override = oa.strip()
            st.session_state.sportmonks_token_override = sm.strip()
            st.success("Claves cargadas en esta sesión")
        if st.button("Limpiar claves de sesión", key="clear_session_keys"):
            st.session_state.api_football_key_override = ""
            st.session_state.odds_api_key_override = ""
            st.session_state.sportmonks_token_override = ""
            st.success("Claves de sesión limpiadas")
        st.markdown("### Tema")
        st.radio("Modo visual", ["Sistema", "Claro"], index=1, horizontal=True, disabled=True)
        st.caption("Esta versión está optimizada en claro tipo live-score.")

# ----------------------------
# INPUTS
# ----------------------------
left, right = st.columns([1, 2.1], gap="medium")
with left:
    with st.container(border=False):
        match_date = st.date_input("Fecha", value=date.today())
        only_premium = st.toggle("Solo torneos top", value=True)
        sport_key = st.selectbox("Mercado base", SPORT_KEY_SUGGESTIONS, index=0)
        bankroll = st.number_input("Bankroll (S/)", min_value=1.0, value=DEFAULT_BANKROLL, step=50.0)

with right:
    api_football_key = current_api_football_key()
    fixture_lookup = {}
    selected_fixture = None
    labels = []
    fixture_message = ""
    if api_football_key:
        try:
            all_fixtures = fetch_today_fixtures(api_football_key, match_date)
            if only_premium:
                all_fixtures = [f for f in all_fixtures if is_premium_competition(f.get("league", {}).get("name", ""))]
            for item in all_fixtures:
                home = item.get("teams", {}).get("home", {}).get("name", "")
                away = item.get("teams", {}).get("away", {}).get("name", "")
                league = item.get("league", {}).get("name", "")
                status = item.get("fixture", {}).get("status", {}).get("short", "")
                lab = f"{home} vs {away} | {league} | {status}"
                labels.append(lab)
                fixture_lookup[lab] = item
        except Exception as e:
            fixture_message = f"No se pudieron cargar partidos del día: {e}"
    else:
        fixture_message = "Ingresa la API en Configuración o usa las variables de Render para cargar partidos automáticos."

    if labels:
        selected_label = st.selectbox("Partido del día", labels)
        selected_fixture = fixture_lookup[selected_label]
        default_match = f"{selected_fixture.get('teams', {}).get('home', {}).get('name', '')} vs {selected_fixture.get('teams', {}).get('away', {}).get('name', '')}"
    else:
        default_match = "Palmeiras vs Sporting Cristal"
    manual_match = st.text_input("Partido manual", value=default_match)
    run = st.button("Analizar partido", use_container_width=True)
    if fixture_message:
        st.caption(fixture_message)

# ----------------------------
# MAIN LOGIC
# ----------------------------
history_file_df = load_history_file()
team_a_name, team_b_name = parse_match_query(manual_match)
fixture = {}
lineups = []
stats_rows = []
events_rows = []
odds = {}
context = {"crowd_a": 0.8, "crowd_b": 0.2, "travel_a": 0, "travel_b": 1200, "rest_a": 5, "rest_b": 4, "fatigue_a": "Baja", "fatigue_b": "Media"}

if selected_fixture:
    context = auto_context(team_a_name, team_b_name, selected_fixture)

if run:
    auto_error = None
    if selected_fixture and api_football_key:
        try:
            fixture = selected_fixture
            fixture_id = fixture.get("fixture", {}).get("id")
            if fixture_id:
                lineups = fetch_lineups_api_football(api_football_key, fixture_id)
                stats_rows = fetch_stats_api_football(api_football_key, fixture_id)
                events_rows = fetch_events_api_football(api_football_key, fixture_id)
        except Exception as e:
            auto_error = f"No se pudo leer API-Football: {e}"

    odds_api_key = current_odds_api_key()
    if odds_api_key:
        try:
            odds = fetch_odds_the_odds_api(odds_api_key, sport_key, team_a_name, team_b_name)
        except Exception:
            odds = {}

    lineup_a = lineup_strength(lineups, team_a_name)
    lineup_b = lineup_strength(lineups, team_b_name)
    stats_a = stats_to_dict(stats_rows, team_a_name)
    stats_b = stats_to_dict(stats_rows, team_b_name)
    a_profile = build_auto_profile(team_a_name, lineup_a, stats_a, context["crowd_a"], context["travel_a"], context["rest_a"], 0)
    b_profile = build_auto_profile(team_b_name, lineup_b, stats_b, context["crowd_b"], context["travel_b"], context["rest_b"], 0)

    lambda_a, lambda_b = expected_goals(a_profile, b_profile)
    matrix = score_matrix(lambda_a, lambda_b, max_goals=6)
    p_a, p_d, p_b = outcome_probabilities(matrix)
    p_over, p_under = over_under_prob(matrix, 2.5)
    p_btts = both_teams_to_score(matrix)
    score_rows = top_scores(matrix, 10)
    best_score, best_prob = score_rows[0]
    dom_index = dominance_index(stats_a, stats_b)
    signals = build_trader_signals(team_a_name, team_b_name, p_a, p_d, p_b, p_over, p_under, p_btts, odds, stats_a, stats_b, score_rows)
    best_bet = best_bet_summary(odds, p_a, p_d, p_b, p_over, p_under, bankroll)
    confidence = pick_confidence(p_a, p_d, p_b, best_prob)
    fixture_status = fixture.get("fixture", {}).get("status", {}).get("short", "PRE") if fixture else "PRE"
    pred_headline, pred_conf, pred_style, pred_reasons = dynamic_ai_prediction(
        team_a_name, team_b_name, p_a, p_d, p_b, best_score, confidence, stats_a, stats_b, odds, best_bet, fixture_status
    )
    pattern_text = pattern_summary(history_file_df, team_a_name, team_b_name)

    save_history_row({
        "match": f"{team_a_name} vs {team_b_name}",
        "prediction": best_score,
        "team_a_win": round(p_a, 4),
        "draw": round(p_d, 4),
        "team_b_win": round(p_b, 4),
        "best_market": best_bet[0] if best_bet else "",
        "best_market_ev": round(best_bet[3], 4) if best_bet else np.nan,
        "league": fixture.get("league", {}).get("name", "") if fixture else "",
    })

    team_a_logo = fixture.get("teams", {}).get("home", {}).get("logo", "") if fixture else ""
    team_b_logo = fixture.get("teams", {}).get("away", {}).get("logo", "") if fixture else ""
    league_logo = fixture.get("league", {}).get("logo", "") if fixture else ""
    league_name = fixture.get("league", {}).get("name", "Partido manual") if fixture else "Partido manual"
    kick = fixture.get("fixture", {}).get("date", "") if fixture else ""
    venue = fixture.get("fixture", {}).get("venue", {}).get("name", "Sin estadio") if fixture else "Sin estadio"

    pred_class = prediction_class(p_a, p_d, p_b)
    badge_class, badge_text = prediction_badge(pred_class)
    score_ga, score_gb = best_score.split("-")
    bookmaker_name = odds.get("bookmaker", "Mercado sin operador") if odds else "Mercado sin operador"

    match_head = f"""
    <div class="z-match-head">
      <div class="z-league">{remote_img(league_logo, 'z-league-logo')}<span>{league_name}</span></div>
      <div class="z-match-grid">
        <div class="z-team-box">{remote_img(team_a_logo, 'z-team-logo')}<div class="z-team-name">{team_a_name}</div><div class="z-team-sub">Prob. ganar {format_pct(p_a)}</div></div>
        <div class="z-center-box">
          <div class="z-score-pill">{score_ga} - {score_gb}</div>
          <div class="z-kick">{fixture.get('fixture', {}).get('status', {}).get('elapsed', kick) if fixture else 'PRE'}</div>
          <div class="z-meta">{venue}</div>
          <div style="margin-top:10px;"><span class="z-score-pill {badge_class}">{badge_text}</span></div>
        </div>
        <div class="z-team-box">{remote_img(team_b_logo, 'z-team-logo')}<div class="z-team-name">{team_b_name}</div><div class="z-team-sub">Prob. ganar {format_pct(p_b)}</div></div>
      </div>
      <div class="z-outcome-grid">
        <div class="z-outcome"><span>1 · GANA LOCAL</span><b>{format_pct(p_a)}</b></div>
        <div class="z-outcome"><span>X · EMPATE</span><b>{format_pct(p_d)}</b></div>
        <div class="z-outcome"><span>2 · GANA VISITA</span><b>{format_pct(p_b)}</b></div>
      </div>
    </div>
    """
    st.markdown(match_head, unsafe_allow_html=True)
    if auto_error:
        st.warning(auto_error)

    a, b = st.columns([1.55, .95], gap="medium")
    with a:
        st.markdown('<div class="z-card">', unsafe_allow_html=True)
        st.markdown('<div class="z-card-title">Predicción IA</div>', unsafe_allow_html=True)
        st.markdown(f"<div class='z-alert {pred_style}'><b>{pred_headline}</b><br>Confianza {pred_conf}.</div>", unsafe_allow_html=True)
        for reason in pred_reasons:
            st.markdown(f"<div class='z-alert'>{reason}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='z-alert'>Patrón histórico: {pattern_text}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with b:
        st.markdown(f"""
        <div class="z-market-best">
          <small>MEJOR CUOTA DEL MOMENTO</small>
          <div style="font-size:1.45rem;font-weight:900;margin-top:8px;">{best_bet[0] if best_bet else 'Sin cuota cargada'}</div>
          <div style="font-size:2rem;font-weight:900;margin-top:6px;">{f'@ {best_bet[1]:.2f}' if best_bet else 'N/D'}</div>
          <div style="margin-top:8px;">{f'EV {best_bet[3]:.3f} · Stake S/ {best_bet[4]:.2f}' if best_bet else 'Carga The Odds API para activar valor y stake.'}</div>
          <div style="margin-top:10px;color:#cbd5e1;">Operador: {bookmaker_name}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="z-card">
          <div class="z-card-title">Resumen rápido</div>
          <div class="z-mini-grid">
            <div class="z-mini-card"><div class="k">OVER 2.5</div><div class="v">{format_pct(p_over)}</div></div>
            <div class="z-mini-card"><div class="k">BTTS</div><div class="v">{format_pct(p_btts)}</div></div>
            <div class="z-mini-card"><div class="k">DOMINANCIA</div><div class="v">{dom_index:.2f}</div></div>
            <div class="z-mini-card"><div class="k">PREDICCIÓN</div><div class="v">{best_score}</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    c1, c2 = st.columns([1.45, .95], gap="medium")
    with c1:
        df_market = pd.DataFrame([
            [f"1 - {team_a_name}", p_a, odds.get("team_a_win") if odds else np.nan],
            ["X - Empate", p_d, odds.get("draw") if odds else np.nan],
            [f"2 - {team_b_name}", p_b, odds.get("team_b_win") if odds else np.nan],
            ["Over 2.5", p_over, odds.get("over_2_5") if odds else np.nan],
            ["Under 2.5", p_under, odds.get("under_2_5") if odds else np.nan],
            ["BTTS Sí", p_btts, np.nan],
        ], columns=["Mercado", "Modelo", "Cuota"])
        df_market["EV"] = df_market.apply(lambda r: expected_value(r["Modelo"], r["Cuota"]), axis=1)
        df_market["Valor"] = df_market["EV"].apply(lambda x: "🔥" if pd.notna(x) and x > 0 else "—")
        with st.container(border=True):
            st.markdown("### Mercados principales")
            st.dataframe(df_market.style.format({"Modelo": "{:.1%}", "Cuota": "{:.2f}", "EV": "{:.3f}"}), use_container_width=True, hide_index=True)

        score_df = pd.DataFrame(score_rows, columns=["Marcador", "Probabilidad"])
        with st.container(border=True):
            st.markdown("### Top marcadores")
            st.dataframe(score_df.style.format({"Probabilidad": "{:.1%}"}), use_container_width=True, hide_index=True)

    with c2:
        with st.container(border=True):
            st.markdown("### Tabla de contexto")
            ctx_df = pd.DataFrame([
                [team_a_name, lineup_readiness(lineup_a), context["travel_a"], context["rest_a"], context["fatigue_a"]],
                [team_b_name, lineup_readiness(lineup_b), context["travel_b"], context["rest_b"], context["fatigue_b"]],
            ], columns=["Equipo", "Estado", "Viaje km", "Descanso", "Fatiga"])
            st.dataframe(ctx_df, use_container_width=True, hide_index=True)

        with st.container(border=True):
            st.markdown("### Comparativa de equipos")
            compare_df = pd.DataFrame([
                ["Tiros", stats_a["total_shots"], stats_b["total_shots"]],
                ["Tiros al arco", stats_a["shots_on_goal"], stats_b["shots_on_goal"]],
                ["Posesión", stats_a["possession"], stats_b["possession"]],
                ["Corners", stats_a["corners"], stats_b["corners"]],
                ["Amarillas", stats_a["yellow"], stats_b["yellow"]],
                ["Rojas", stats_a["red"], stats_b["red"]],
            ], columns=["Indicador", team_a_name, team_b_name])
            st.dataframe(compare_df, use_container_width=True, hide_index=True)

        with st.container(border=True):
            st.markdown("### Balance visual")
            comparisons = [
                ("Posesión", stats_a["possession"], stats_b["possession"], "%"),
                ("Tiros", stats_a["total_shots"], stats_b["total_shots"], ""),
                ("Tiros al arco", stats_a["shots_on_goal"], stats_b["shots_on_goal"], ""),
                ("Corners", stats_a["corners"], stats_b["corners"], ""),
            ]
            for title, va, vb, suf in comparisons:
                total = max(va + vb, 1e-9)
                share = va / total if total else 0.5
                st.markdown(f"<div class='z-statline'><div class='z-statline-top'><span>{team_a_name} {va:.0f}{suf}</span><span><b>{title}</b></span><span>{team_b_name} {vb:.0f}{suf}</span></div><div class='z-statbar'><div class='z-statbar-fill' style='width:{share*100:.1f}%'></div></div></div>", unsafe_allow_html=True)
else:
    with st.container(border=True):
        st.markdown("### Centro de análisis")
        st.write("Carga un partido del día o escribe uno manualmente. Luego pulsa **Analizar partido** para abrir la predicción, mercados y comparativas.")
        st.write("La configuración de APIs está en **⚙️ Configuración**. Ahí puedes cargar claves solo para tu sesión o usar las variables de Render.")
