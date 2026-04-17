import os
import math
import json
import sqlite3
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="ZOLA Elite", page_icon="⚽", layout="wide", initial_sidebar_state="collapsed")

# ----------------------------
# CONFIG
# ----------------------------
API_FOOTBALL_BASE = os.getenv("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
ODDS_API_BASE = os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4")
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
LIMA_TZ = "America/Lima"
DEFAULT_BANKROLL = 1000.0
DB_FILE = "zola_live.db"
SPORT_KEY_SUGGESTIONS = [
    "soccer_conmebol_libertadores","soccer_conmebol_sudamericana","soccer_uefa_champs_league",
    "soccer_spain_la_liga","soccer_epl","soccer_italy_serie_a","soccer_germany_bundesliga",
    "soccer_france_ligue_one","soccer_brazil_campeonato",
]
PREMIUM_KEYWORDS = [
    "libertadores","sudamericana","champions","europa league","premier","la liga","serie a",
    "bundesliga","ligue 1","brasileirao","copa del mundo","world cup","copa america","euro"
]
LIVE_CODES = {"1H", "HT", "2H", "ET", "BT", "P", "INT", "LIVE"}

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

# ----------------------------
# STATE
# ----------------------------
for key in [
    "admin_ok", "api_football_key_override", "odds_api_key_override",
    "sportmonks_token_override", "openai_api_key_override", "selected_fixture_id", "selected_match_label"
]:
    if key not in st.session_state:
        st.session_state[key] = "" if "override" in key or "selected" in key else False

# ----------------------------
# CSS
# ----------------------------
st.markdown(
    """
<style>
:root{
  --bg:#eef3fb;
  --panel:#ffffff;
  --line:#d7e2f4;
  --text:#0f172a;
  --muted:#64748b;
  --brand:#1f4ed8;
  --brand2:#285ee8;
  --green:#13b981;
  --red:#ef4444;
  --amber:#f59e0b;
}
html, body, [class*="css"] { font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.stApp{background:linear-gradient(180deg,#eff4fb 0%,#edf2fa 100%); color:var(--text);}
.block-container{max-width:1400px;padding-top:.65rem;padding-bottom:2rem;}
section[data-testid="stSidebar"]{display:none;}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu, footer {visibility:hidden;}

.z-topbar{background:linear-gradient(90deg,#204fd8 0%,#295fe9 70%,#2e65f0 100%);border-radius:20px;padding:18px 22px;color:#fff;border:1px solid rgba(255,255,255,.18);box-shadow:0 18px 40px rgba(31,78,216,.18);margin-bottom:14px;}
.z-topbar-row{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;}
.z-brand{display:flex;align-items:center;gap:12px;}
.z-brand-badge{width:52px;height:52px;border-radius:14px;background:rgba(255,255,255,.12);display:flex;align-items:center;justify-content:center;border:1px solid rgba(255,255,255,.26);overflow:hidden;}
.z-brand-title{font-size:2rem;font-weight:900;line-height:1;}
.z-brand-sub{font-size:.95rem;opacity:.92;margin-top:4px;}
.z-chip-row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:flex-end;}
.z-chip{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:9px 14px;font-size:.84rem;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.24);}
.z-dot{width:10px;height:10px;border-radius:999px;background:#22c55e;box-shadow:0 0 0 2px rgba(34,197,94,.18);}
.z-subnav{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:14px 0 16px;}
.z-pill-btn{background:#fff;border:1px solid var(--line);padding:10px 16px;border-radius:999px;font-weight:700;}

.z-fixture-card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:14px 16px;box-shadow:0 6px 20px rgba(15,23,42,.04);min-height:116px;}
.z-fixture-head{display:flex;justify-content:space-between;align-items:center;font-size:.84rem;color:var(--muted);margin-bottom:10px;gap:10px;}
.z-fixture-mid{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;}
.z-team-mini{text-align:center;}
.z-team-mini img{width:36px;height:36px;object-fit:contain;display:block;margin:0 auto 6px;}
.z-team-mini .n{font-size:.94rem;font-weight:800;color:var(--text);line-height:1.15;}
.z-score-live{text-align:center;}
.z-score-live .s{font-size:1.55rem;font-weight:900;color:var(--text);line-height:1;}
.z-score-live .t{font-size:.92rem;color:var(--muted);margin-top:5px;}
.z-live-badge,.z-pre-badge,.z-ft-badge{display:inline-flex;align-items:center;border-radius:999px;padding:5px 10px;font-size:.75rem;font-weight:800;}
.z-live-badge{background:rgba(239,68,68,.12);color:#dc2626;}
.z-pre-badge{background:rgba(37,99,235,.1);color:#1d4ed8;}
.z-ft-badge{background:rgba(15,118,110,.11);color:#0f766e;}
.z-card{background:#fff;border:1px solid var(--line);border-radius:22px;padding:16px 18px;box-shadow:0 8px 24px rgba(15,23,42,.04);}
.z-card-title{font-size:1rem;font-weight:900;margin-bottom:10px;color:var(--text);}
.z-match-head{background:#fff;border:1px solid var(--line);border-radius:22px;padding:16px 22px;box-shadow:0 8px 24px rgba(15,23,42,.04);margin-top:8px;margin-bottom:14px;}
.z-league{display:flex;align-items:center;gap:10px;font-size:.95rem;color:var(--muted);font-weight:700;margin-bottom:12px;}
.z-league img{width:22px;height:22px;object-fit:contain;}
.z-match-grid{display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:center;}
.z-team-box{text-align:center;}
.z-team-logo{width:74px;height:74px;object-fit:contain;display:block;margin:0 auto 8px;}
.z-team-name{font-size:2rem;font-weight:900;color:var(--text);}
.z-team-sub{color:var(--muted);font-size:1rem;margin-top:2px;}
.z-center-box{text-align:center;padding:0 12px;}
.z-score-pill{display:inline-flex;align-items:center;justify-content:center;min-width:92px;padding:12px 18px;border-radius:999px;border:1px solid #bfd0f2;background:#f6faff;font-size:2rem;font-weight:900;color:var(--text);}
.z-kick{font-size:1.25rem;font-weight:900;color:var(--text);margin-top:12px;}
.z-meta{font-size:1rem;color:var(--muted);margin-top:6px;}
.z-label-good,.z-label-warn,.z-label-draw{display:inline-flex;border-radius:999px;padding:10px 16px;font-weight:900;font-size:1rem;}
.z-label-good{background:rgba(19,185,129,.11);color:#047857;border:1px solid rgba(19,185,129,.24);}
.z-label-warn{background:rgba(245,158,11,.12);color:#b45309;border:1px solid rgba(245,158,11,.25);}
.z-label-draw{background:rgba(59,130,246,.12);color:#1d4ed8;border:1px solid rgba(59,130,246,.25);}
.z-outcome-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px;}
.z-outcome{border:1px solid var(--line);border-radius:18px;padding:18px 16px;background:#fbfdff;text-align:center;}
.z-outcome span{display:block;font-size:.86rem;color:#5673b3;font-weight:900;}
.z-outcome b{display:block;font-size:2rem;color:var(--text);margin-top:8px;}
.z-mini-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.z-mini-card{border:1px solid var(--line);border-radius:18px;background:#fbfdff;padding:16px 14px;}
.z-mini-card .k{font-size:.83rem;color:#6679a8;font-weight:900;}
.z-mini-card .v{font-size:1.9rem;font-weight:900;margin-top:8px;}
.z-alert{border-radius:18px;padding:14px 16px;border:1px solid var(--line);background:#f9fbff;margin-top:10px;font-size:1rem;}
.z-alert.good{background:rgba(19,185,129,.11);border-color:rgba(19,185,129,.20);color:#065f46;}
.z-alert.warn{background:rgba(245,158,11,.11);border-color:rgba(245,158,11,.22);color:#92400e;}
.z-alert.draw{background:rgba(59,130,246,.10);border-color:rgba(59,130,246,.20);color:#1d4ed8;}
.z-market-best{background:linear-gradient(135deg,#0f224a,#112f6a);color:#fff;border-radius:22px;padding:20px 18px;border:1px solid rgba(255,255,255,.1);}
.z-market-best small{display:block;opacity:.8;font-weight:800;letter-spacing:.03em;}
.z-statline{margin-bottom:12px;}
.z-statline-top{display:flex;justify-content:space-between;gap:12px;font-size:.9rem;margin-bottom:6px;color:var(--muted);}
.z-statbar{background:#e7eef9;border-radius:999px;height:10px;overflow:hidden;}
.z-statbar-fill{background:linear-gradient(90deg,#2a61ea,#3f8cff);height:100%;border-radius:999px;}
.z-muted{color:var(--muted);}
.z-db-note{font-size:.85rem;color:var(--muted);}

@media (max-width: 1000px){
  .z-match-grid{grid-template-columns:1fr;}
  .z-outcome-grid,.z-mini-grid{grid-template-columns:1fr 1fr;}
  .z-team-name{font-size:1.55rem;}
}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------
# DATABASE
# ----------------------------
def db_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS selected_matches (
            fixture_id TEXT PRIMARY KEY,
            match_label TEXT,
            league_name TEXT,
            match_date TEXT,
            status TEXT,
            chosen_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fixture_id TEXT,
            match_label TEXT,
            captured_at TEXT,
            home_goals INTEGER,
            away_goals INTEGER,
            elapsed INTEGER,
            predicted_score TEXT,
            pick_label TEXT,
            confidence TEXT,
            live_status TEXT,
            ai_summary TEXT
        )
        """
    )
    return conn


def save_selected_match(fixture_id, match_label, league_name, match_date, status):
    conn = db_conn()
    conn.execute(
        """
        INSERT INTO selected_matches (fixture_id, match_label, league_name, match_date, status, chosen_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(fixture_id) DO UPDATE SET
            match_label=excluded.match_label,
            league_name=excluded.league_name,
            match_date=excluded.match_date,
            status=excluded.status,
            chosen_at=excluded.chosen_at
        """,
        (str(fixture_id), match_label, league_name, match_date, status, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def save_snapshot(fixture_id, match_label, home_goals, away_goals, elapsed, predicted_score, pick_label, confidence, live_status, ai_summary):
    conn = db_conn()
    conn.execute(
        """
        INSERT INTO analysis_snapshots (fixture_id, match_label, captured_at, home_goals, away_goals, elapsed, predicted_score, pick_label, confidence, live_status, ai_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(fixture_id) if fixture_id is not None else None,
            match_label,
            datetime.utcnow().isoformat(),
            home_goals,
            away_goals,
            elapsed,
            predicted_score,
            pick_label,
            confidence,
            live_status,
            ai_summary,
        ),
    )
    conn.commit()
    conn.close()


def get_saved_matches(limit=12):
    conn = db_conn()
    df = pd.read_sql_query(
        "SELECT fixture_id, match_label, league_name, match_date, status, chosen_at FROM selected_matches ORDER BY chosen_at DESC LIMIT ?",
        conn,
        params=(limit,),
    )
    conn.close()
    return df

# ----------------------------
# HELPERS
# ----------------------------
def current_api_football_key():
    return st.session_state.api_football_key_override or os.getenv("API_FOOTBALL_KEY", "")

def current_odds_api_key():
    return st.session_state.odds_api_key_override or os.getenv("THE_ODDS_API_KEY", "")

def current_sportmonks_token():
    return st.session_state.sportmonks_token_override or os.getenv("SPORTMONKS_API_TOKEN", "")

def current_openai_key():
    return st.session_state.openai_api_key_override or os.getenv("OPENAI_API_KEY", "")


def format_pct(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "N/D"
    return f"{x*100:.1f}%"


def similarity(a, b):
    return SequenceMatcher(None, (a or "").lower().strip(), (b or "").lower().strip()).ratio()


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


def remote_img(url, cls):
    if url:
        return f'<img class="{cls}" src="{url}"/>'
    return ""


def local_logo_tag():
    logo_path = Path("zola_crest.png")
    if logo_path.exists():
        import base64
        data = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        return f'<img src="data:image/png;base64,{data}" style="width:40px;height:40px;object-fit:contain;"/>'
    return '<div style="font-size:1.3rem;font-weight:900;">Z</div>'


def is_premium_competition(league_name):
    lower = (league_name or "").lower()
    return any(k in lower for k in PREMIUM_KEYWORDS)


def implied_prob(decimal_odds):
    if not decimal_odds or decimal_odds <= 1:
        return np.nan
    return 1 / decimal_odds


def expected_value(prob, decimal_odds):
    if not decimal_odds or decimal_odds <= 1:
        return np.nan
    return prob * (decimal_odds - 1) - (1 - prob)


def fair_decimal_odds(prob):
    if not prob or prob <= 0:
        return np.nan
    return 1 / prob


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


def top_scores(matrix, base_a=0, base_b=0, n=10):
    rows = []
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            rows.append((f"{base_a+i}-{base_b+j}", float(matrix[i, j])))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows[:n]


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


def fetch_fixtures(api_key, on_date):
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
    best, best_score = None, 0.0
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
    key = (team_name or "").lower().strip()
    if key in TEAM_PRIORS:
        return TEAM_PRIORS[key].copy()
    seed = abs(hash(key)) % 10000
    rng = np.random.default_rng(seed)
    return {"elo": float(1450 + rng.integers(0, 240)), "form": float(np.round(rng.uniform(1.2, 2.0), 2)), "attack": float(np.round(rng.uniform(1.05, 1.55), 2)), "defense": float(np.round(rng.uniform(1.0, 1.45), 2))}


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
    travel_a = 0 if is_a_home else int(round(haversine_km(a_ctx.get("lat", -12), a_ctx.get("lon", -77), home_ctx.get("lat", -12), home_ctx.get("lon", -77))))
    travel_b = 0 if not is_a_home else int(round(haversine_km(b_ctx.get("lat", -12), b_ctx.get("lon", -77), away_ctx.get("lat", -12), away_ctx.get("lon", -77))))
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


def lineup_strength(lineups, team_name):
    default = {"formation": "N/D", "starters": 11, "bench": 7, "attack_bonus": 0.0, "defense_bonus": 0.0}
    if not lineups:
        return default
    best, bs = None, 0.0
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
        return "Llega completo"
    if info["starters"] >= 10:
        return "Llega competitivo"
    return "Llega con ajustes"


def stats_to_dict(stats_rows, team_name):
    out = {"shots_on_goal": 0.0, "total_shots": 0.0, "corners": 0.0, "possession": 50.0, "yellow": 0.0, "red": 0.0}
    if not stats_rows:
        return out
    best, bs = None, 0.0
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


def build_profile(team_name, lineup_info, stats_info, crowd_factor, travel_km, rest_days, injuries):
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
    }


def pre_match_expected_goals(a, b):
    home_boost = 0.10 + 0.17 * a["crowd_factor"]
    sg = (a["elo"] - b["elo"]) / 100
    la = 1.05 + 0.10 * sg + 0.18 * (a["form"] - b["form"]) + 0.32 * (a["attack"] - b["defense"]) + home_boost + 0.025 * (a["rest_days"] - b["rest_days"]) - 0.018 * a["injuries"] - 0.000025 * max(a["travel_km"] - b["travel_km"], 0)
    lb = 0.90 - 0.09 * sg - 0.14 * (a["form"] - b["form"]) + 0.26 * (b["attack"] - a["defense"]) + 0.025 * (b["rest_days"] - a["rest_days"]) - 0.018 * b["injuries"] - 0.000025 * max(b["travel_km"] - a["travel_km"], 0)
    return max(0.15, min(4.2, la)), max(0.10, min(4.0, lb))


def live_remaining_goals(pre_a, pre_b, score_a, score_b, elapsed, stats_a, stats_b):
    elapsed = max(0, min(int(elapsed or 0), 120))
    remaining_ratio = max(0.07, (95 - min(elapsed, 95)) / 95)
    dom = (stats_a["shots_on_goal"] - stats_b["shots_on_goal"]) * 0.20 + (stats_a["total_shots"] - stats_b["total_shots"]) * 0.08 + ((stats_a["possession"] - stats_b["possession"]) / 10) * 0.06 + (stats_a["corners"] - stats_b["corners"]) * 0.05
    pressure_a = max(-0.45, min(0.45, dom * 0.12))
    pressure_b = max(-0.45, min(0.45, -dom * 0.12))
    need_a = 0.12 if score_a < score_b else 0.0
    need_b = 0.12 if score_b < score_a else 0.0
    protect_a = -0.10 if score_a > score_b and elapsed >= 65 else 0.0
    protect_b = -0.10 if score_b > score_a and elapsed >= 65 else 0.0
    lam_a = max(0.05, pre_a * remaining_ratio * (1 + pressure_a + need_a + protect_a))
    lam_b = max(0.05, pre_b * remaining_ratio * (1 + pressure_b + need_b + protect_b))
    return lam_a, lam_b


def fulltime_distribution(pre_a, pre_b, score_a, score_b, elapsed, stats_a, stats_b, live_mode=False):
    if live_mode:
        lam_a, lam_b = live_remaining_goals(pre_a, pre_b, score_a, score_b, elapsed, stats_a, stats_b)
        mat = score_matrix(lam_a, lam_b, max_goals=6)
        return mat, lam_a, lam_b
    mat = score_matrix(pre_a, pre_b, max_goals=6)
    return mat, pre_a, pre_b


def outcome_probs_from_fulltime(matrix, base_a=0, base_b=0):
    p_a = p_d = p_b = 0.0
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            fa, fb = base_a + i, base_b + j
            if fa > fb:
                p_a += matrix[i, j]
            elif fa == fb:
                p_d += matrix[i, j]
            else:
                p_b += matrix[i, j]
    return float(p_a), float(p_d), float(p_b)


def dominance_index(stats_a, stats_b):
    return (stats_a["shots_on_goal"] - stats_b["shots_on_goal"]) * 0.22 + (stats_a["total_shots"] - stats_b["total_shots"]) * 0.10 + (stats_a["corners"] - stats_b["corners"]) * 0.08 + ((stats_a["possession"] - stats_b["possession"]) / 10) * 0.08 - (stats_a["red"] - stats_b["red"]) * 0.35


def pick_confidence(p_a, p_d, p_b, score_prob, live=False):
    gap = abs(p_a - p_b)
    if max(p_a, p_b) >= 0.76 and score_prob >= 0.11:
        return "Alta"
    if gap >= 0.20:
        return "Media"
    return "Competida" if not live else "Viva"


def prediction_class(p_a, p_d, p_b):
    if p_a > max(p_d, p_b):
        return "local"
    if p_b > max(p_a, p_d):
        return "visita"
    return "empate"


def prediction_badge(pred_class):
    if pred_class == "local":
        return "z-label-good", "Victoria local"
    if pred_class == "visita":
        return "z-label-warn", "Victoria visita"
    return "z-label-draw", "Empate"


def best_bet_summary(odds, p_a, p_d, p_b, p_over, p_under, bankroll):
    opts = [
        ("1 - Local", odds.get("team_a_win"), p_a),
        ("X - Empate", odds.get("draw"), p_d),
        ("2 - Visita", odds.get("team_b_win"), p_b),
        ("Over 2.5", odds.get("over_2_5"), p_over),
        ("Under 2.5", odds.get("under_2_5"), p_under),
    ]
    best, best_ev = None, -999
    for label, odd, prob in opts:
        ev = expected_value(prob, odd)
        if not np.isnan(ev) and ev > best_ev:
            best_ev = ev
            best = (label, odd, prob, ev, kelly_fraction(prob, odd) * bankroll * 0.25, "Mercado")
    if best:
        return best
    # fallback to fair odds from model when market odds missing
    fair_opts = [
        ("1 - Local", fair_decimal_odds(p_a), p_a),
        ("X - Empate", fair_decimal_odds(p_d), p_d),
        ("2 - Visita", fair_decimal_odds(p_b), p_b),
        ("Over 2.5", fair_decimal_odds(p_over), p_over),
        ("Under 2.5", fair_decimal_odds(p_under), p_under),
    ]
    fair_opts.sort(key=lambda x: x[2], reverse=True)
    label, odd, prob = fair_opts[0]
    return (label, odd, prob, np.nan, 0.0, "Modelo")


def fallback_analysis(team_a, team_b, score_now, best_score, pred_class, confidence, minute, status_text, p_a, p_d, p_b, best_bet, dom_index, live_mode):
    if pred_class == "local":
        headline = f"{team_a} cierra mejor el partido y mi salida final es {best_score}."
    elif pred_class == "visita":
        headline = f"{team_b} termina por imponerse y mi salida final es {best_score}."
    else:
        headline = f"El partido se aprieta y mi salida final es {best_score}."
    reasons = []
    if live_mode:
        reasons.append(f"Marcador actual {score_now} al {minute}' . La proyección ya se recalculó desde el estado en vivo.")
    else:
        reasons.append(f"Estado {status_text}. La lectura parte del contexto prepartido y de la data disponible.")
    reasons.append(f"Probabilidades: local {format_pct(p_a)}, empate {format_pct(p_d)}, visita {format_pct(p_b)}.")
    if abs(dom_index) >= 0.8:
        reasons.append(f"La dominancia actual del juego va {'hacia local' if dom_index > 0 else 'hacia visita'}.")
    if best_bet:
        source = "cuota de mercado" if best_bet[5] == "Mercado" else "cuota modelo"
        reasons.append(f"Mejor salida para apostar ahora: {best_bet[0]} @ {best_bet[1]:.2f} ({source}).")
    return headline, reasons[:4]


def ai_match_analysis(openai_key, payload):
    if not openai_key:
        return None
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json",
    }
    prompt = f"""
Eres ZOLA Elite, analista de fútbol y apuestas. Responde en español, directo y sin rodeos.
Con los datos entregados debes dar:
1) pronóstico final exacto en una sola línea
2) mejor apuesta del momento en una sola línea
3) análisis corto en 3 viñetas, sin frases genéricas
No digas 'podría', 'quizá', 'parece', ni des advertencias largas.
No inventes datos fuera del JSON.
JSON:
{json.dumps(payload, ensure_ascii=False)}
""".strip()
    body = {
        "model": OPENAI_MODEL,
        "input": prompt,
    }
    try:
        r = requests.post(f"{OPENAI_BASE}/responses", headers=headers, json=body, timeout=40)
        r.raise_for_status()
        data = r.json()
        if data.get("output_text"):
            return data["output_text"].strip()
        # fallback parse
        out = []
        for item in data.get("output", []):
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    out.append(c.get("text", ""))
        text = "\n".join(out).strip()
        return text or None
    except Exception:
        return None

# ----------------------------
# HEADER
# ----------------------------
st.markdown(
    f"""
<div class="z-topbar">
  <div class="z-topbar-row">
    <div class="z-brand">
      <div class="z-brand-badge">{local_logo_tag()}</div>
      <div>
        <div class="z-brand-title">ZOLA Elite</div>
        <div class="z-brand-sub">Lectura en vivo, predicción recalculada y mejor cuota con IA.</div>
      </div>
    </div>
    <div class="z-chip-row">
      <div class="z-chip"><span class="z-dot"></span>API-Football</div>
      <div class="z-chip"><span class="z-dot"></span>The Odds API</div>
      <div class="z-chip"><span class="z-dot"></span>OpenAI</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------------------
# SETTINGS
# ----------------------------
admin_password = os.getenv("ADMIN_PASSWORD", "")
with st.expander("⚙️ Configuración"):
    if admin_password and not st.session_state.admin_ok:
        typed = st.text_input("Clave admin", type="password")
        if st.button("Entrar", key="admin_login"):
            if typed == admin_password:
                st.session_state.admin_ok = True
                st.success("Acceso habilitado")
            else:
                st.error("Clave incorrecta")
    else:
        st.session_state.admin_ok = True

    if st.session_state.admin_ok:
        st.caption("Estas claves se guardan solo en tu sesión del navegador. Para dejarlas fijas, usa Render > Settings > Environment Variables.")
        af = st.text_input("API Football", value=st.session_state.api_football_key_override, type="password")
        oa = st.text_input("The Odds API", value=st.session_state.odds_api_key_override, type="password")
        op = st.text_input("OpenAI API Key", value=st.session_state.openai_api_key_override, type="password")
        sm = st.text_input("Sportmonks", value=st.session_state.sportmonks_token_override, type="password")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Guardar en esta sesión", key="save_session_keys"):
                st.session_state.api_football_key_override = af.strip()
                st.session_state.odds_api_key_override = oa.strip()
                st.session_state.openai_api_key_override = op.strip()
                st.session_state.sportmonks_token_override = sm.strip()
                st.success("Claves cargadas en esta sesión")
        with c2:
            if st.button("Limpiar claves de sesión", key="clear_session_keys"):
                st.session_state.api_football_key_override = ""
                st.session_state.odds_api_key_override = ""
                st.session_state.openai_api_key_override = ""
                st.session_state.sportmonks_token_override = ""
                st.success("Claves limpiadas")
        st.radio("Tema", ["Sistema", "Claro", "Oscuro"], index=0, horizontal=True, disabled=True)
        st.caption("La app usa las claves del servidor o de esta sesión. El público no las ve.")

# ----------------------------
# FIXTURE CENTER
# ----------------------------
api_football_key = current_api_football_key()
odds_api_key = current_odds_api_key()
openai_key = current_openai_key()

mode = st.radio("Centro de partidos", ["En vivo", "Hoy", "Mañana", "Manual"], horizontal=True, label_visibility="collapsed")
base_date = date.today()
if mode == "Mañana":
    match_date = base_date + timedelta(days=1)
elif mode in ["En vivo", "Hoy"]:
    match_date = base_date
else:
    match_date = st.date_input("Fecha manual", value=base_date)

colA, colB, colC = st.columns([1, 1, .8], gap="medium")
with colA:
    only_premium = st.toggle("Solo torneos top", value=True)
with colB:
    sport_key = st.selectbox("Mercado base", SPORT_KEY_SUGGESTIONS, index=0)
with colC:
    bankroll = st.number_input("Bankroll (S/)", min_value=1.0, value=DEFAULT_BANKROLL, step=50.0)

fixture_message = ""
fixtures = []
if api_football_key and mode != "Manual":
    try:
        fixtures = fetch_fixtures(api_football_key, match_date)
        if mode == "En vivo":
            fixtures = [f for f in fixtures if f.get("fixture", {}).get("status", {}).get("short") in LIVE_CODES]
        if only_premium:
            fixtures = [f for f in fixtures if is_premium_competition(f.get("league", {}).get("name", ""))]
    except Exception as e:
        fixture_message = f"No se pudieron cargar partidos: {e}"
elif mode != "Manual":
    fixture_message = "Falta API Football para cargar partidos del día."

if fixture_message:
    st.caption(fixture_message)

# render fixture cards
selected_fixture = None
if mode != "Manual" and fixtures:
    st.markdown("### Partidos")
    cols = st.columns(3, gap="medium")
    for idx, item in enumerate(fixtures[:18]):
        home = item.get("teams", {}).get("home", {}).get("name", "")
        away = item.get("teams", {}).get("away", {}).get("name", "")
        home_logo = item.get("teams", {}).get("home", {}).get("logo", "")
        away_logo = item.get("teams", {}).get("away", {}).get("logo", "")
        league = item.get("league", {}).get("name", "")
        league_logo = item.get("league", {}).get("logo", "")
        fid = str(item.get("fixture", {}).get("id", ""))
        status = item.get("fixture", {}).get("status", {}).get("short", "NS")
        elapsed = item.get("fixture", {}).get("status", {}).get("elapsed")
        score_h = item.get("goals", {}).get("home")
        score_a = item.get("goals", {}).get("away")
        when = item.get("fixture", {}).get("date", "")
        time_label = f"{elapsed}'" if elapsed else (when[11:16] if when else "PRE")
        status_badge = "z-live-badge" if status in LIVE_CODES else ("z-ft-badge" if status == "FT" else "z-pre-badge")
        with cols[idx % 3]:
            st.markdown(
                f"""
<div class="z-fixture-card">
  <div class="z-fixture-head"><span>{remote_img(league_logo,'')} {league}</span><span class="{status_badge}">{status}</span></div>
  <div class="z-fixture-mid">
    <div class="z-team-mini">{remote_img(home_logo,'')}<div class="n">{home}</div></div>
    <div class="z-score-live"><div class="s">{score_h if score_h is not None else '-'} - {score_a if score_a is not None else '-'}</div><div class="t">{time_label}</div></div>
    <div class="z-team-mini">{remote_img(away_logo,'')}<div class="n">{away}</div></div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
            if st.button(f"Abrir {home} vs {away}", key=f"pick_{fid}", use_container_width=True):
                st.session_state.selected_fixture_id = fid
                st.session_state.selected_match_label = f"{home} vs {away}"
                save_selected_match(fid, f"{home} vs {away}", league, match_date.isoformat(), status)

    if st.session_state.selected_fixture_id:
        selected_fixture = next((f for f in fixtures if str(f.get("fixture", {}).get("id")) == st.session_state.selected_fixture_id), None)

saved = get_saved_matches(8)
if not saved.empty:
    with st.expander("🗂️ Partidos guardados"):
        st.dataframe(saved, use_container_width=True, hide_index=True)
        st.caption("Se guardan en SQLite local de la app. Si Render reinicia la instancia gratuita, esta base puede reiniciarse.")

# manual input
manual_match = st.text_input("Partido manual", value=st.session_state.selected_match_label or "Palmeiras vs Sporting Cristal")
run = st.button("Analizar partido", use_container_width=True)

# ----------------------------
# ANALYSIS
# ----------------------------
if run:
    fixture = selected_fixture or {}
    if not fixture and api_football_key and mode == "Manual":
        # try to locate from today's fixtures for logos/status if text matches
        try:
            look = fetch_fixtures(api_football_key, match_date)
            team_a_in, team_b_in = parse_match_query(manual_match)
            best, best_score = None, 0.0
            for item in look:
                home = item.get("teams", {}).get("home", {}).get("name", "")
                away = item.get("teams", {}).get("away", {}).get("name", "")
                s = max(similarity(team_a_in, home)+similarity(team_b_in, away), similarity(team_a_in, away)+similarity(team_b_in, home))
                if s > best_score:
                    best_score, best = s, item
            if best_score > 1.5:
                fixture = best
        except Exception:
            pass

    team_a_name, team_b_name = parse_match_query(manual_match)
    if fixture:
        team_a_name = fixture.get("teams", {}).get("home", {}).get("name", team_a_name)
        team_b_name = fixture.get("teams", {}).get("away", {}).get("name", team_b_name)
        match_label = f"{team_a_name} vs {team_b_name}"
    else:
        match_label = manual_match

    lineups = stats_rows = events_rows = []
    odds = {}
    auto_error = None
    context = {"crowd_a": 0.8, "crowd_b": 0.2, "travel_a": 0, "travel_b": 1200, "rest_a": 5, "rest_b": 4, "fatigue_a": "Baja", "fatigue_b": "Media"}
    if fixture:
        context = auto_context(team_a_name, team_b_name, fixture)
        if api_football_key:
            try:
                fid = fixture.get("fixture", {}).get("id")
                if fid:
                    lineups = fetch_lineups_api_football(api_football_key, fid)
                    stats_rows = fetch_stats_api_football(api_football_key, fid)
                    events_rows = fetch_events_api_football(api_football_key, fid)
            except Exception as e:
                auto_error = f"No pude leer el detalle live: {e}"
    if odds_api_key:
        try:
            odds = fetch_odds_the_odds_api(odds_api_key, sport_key, team_a_name, team_b_name)
        except Exception:
            odds = {}

    lineup_a = lineup_strength(lineups, team_a_name)
    lineup_b = lineup_strength(lineups, team_b_name)
    stats_a = stats_to_dict(stats_rows, team_a_name)
    stats_b = stats_to_dict(stats_rows, team_b_name)
    a_profile = build_profile(team_a_name, lineup_a, stats_a, context["crowd_a"], context["travel_a"], context["rest_a"], 0)
    b_profile = build_profile(team_b_name, lineup_b, stats_b, context["crowd_b"], context["travel_b"], context["rest_b"], 0)
    pre_a, pre_b = pre_match_expected_goals(a_profile, b_profile)

    status_short = fixture.get("fixture", {}).get("status", {}).get("short", "PRE") if fixture else "PRE"
    elapsed = int(fixture.get("fixture", {}).get("status", {}).get("elapsed") or 0) if fixture else 0
    home_goals = int(fixture.get("goals", {}).get("home") or 0) if fixture else 0
    away_goals = int(fixture.get("goals", {}).get("away") or 0) if fixture else 0
    live_mode = status_short in LIVE_CODES

    mat, rem_a, rem_b = fulltime_distribution(pre_a, pre_b, home_goals, away_goals, elapsed, stats_a, stats_b, live_mode=live_mode)
    p_a, p_d, p_b = outcome_probs_from_fulltime(mat, home_goals if live_mode else 0, away_goals if live_mode else 0)
    p_over, p_under = over_under_prob(mat, 2.5 - (home_goals + away_goals) if live_mode else 2.5)
    p_btts = both_teams_to_score(mat) if not live_mode else np.nan
    score_rows = top_scores(mat, home_goals if live_mode else 0, away_goals if live_mode else 0, n=10)
    best_score, best_prob = score_rows[0]
    dom_index = dominance_index(stats_a, stats_b)
    confidence = pick_confidence(p_a, p_d, p_b, best_prob, live=live_mode)
    pred_class = prediction_class(p_a, p_d, p_b)
    badge_class, badge_text = prediction_badge(pred_class)
    best_bet = best_bet_summary(odds, p_a, p_d, p_b, p_over, p_under, bankroll)

    score_now = f"{home_goals}-{away_goals}"
    ai_payload = {
        "match": match_label,
        "league": fixture.get("league", {}).get("name", "Partido manual") if fixture else "Partido manual",
        "status": status_short,
        "elapsed": elapsed,
        "score_now": score_now,
        "predicted_fulltime": best_score,
        "probabilities": {"local": round(p_a, 4), "draw": round(p_d, 4), "visit": round(p_b, 4)},
        "dominance_index": round(dom_index, 3),
        "shots": {team_a_name: stats_a["total_shots"], team_b_name: stats_b["total_shots"]},
        "shots_on_goal": {team_a_name: stats_a["shots_on_goal"], team_b_name: stats_b["shots_on_goal"]},
        "possession": {team_a_name: stats_a["possession"], team_b_name: stats_b["possession"]},
        "corners": {team_a_name: stats_a["corners"], team_b_name: stats_b["corners"]},
        "best_bet": {"label": best_bet[0], "odds": round(best_bet[1], 2) if best_bet and best_bet[1] else None, "source": best_bet[5] if best_bet else None},
    }
    ai_text = ai_match_analysis(openai_key, ai_payload)
    if ai_text:
        ai_headline = ai_text.splitlines()[0].strip()
        ai_bullets = [ln.strip("-• ") for ln in ai_text.splitlines()[1:] if ln.strip()][:4]
    else:
        ai_headline, ai_bullets = fallback_analysis(team_a_name, team_b_name, score_now, best_score, pred_class, confidence, elapsed, status_short, p_a, p_d, p_b, best_bet, dom_index, live_mode)
    style = "good" if pred_class == "local" else ("warn" if pred_class == "visita" else "draw")

    if fixture.get("fixture", {}).get("id"):
        save_snapshot(fixture.get("fixture", {}).get("id"), match_label, home_goals, away_goals, elapsed, best_score, best_bet[0], confidence, status_short, ai_headline)

    team_a_logo = fixture.get("teams", {}).get("home", {}).get("logo", "") if fixture else ""
    team_b_logo = fixture.get("teams", {}).get("away", {}).get("logo", "") if fixture else ""
    league_logo = fixture.get("league", {}).get("logo", "") if fixture else ""
    league_name = fixture.get("league", {}).get("name", "Partido manual") if fixture else "Partido manual"
    venue = fixture.get("fixture", {}).get("venue", {}).get("name", "Sin estadio") if fixture else "Sin estadio"
    center_time = f"{elapsed}'" if live_mode and elapsed else (fixture.get("fixture", {}).get("date", "")[11:16] if fixture else "PRE")

    st.markdown(
        f"""
<div class="z-match-head">
  <div class="z-league">{remote_img(league_logo, '')}<span>{league_name}</span></div>
  <div class="z-match-grid">
    <div class="z-team-box">{remote_img(team_a_logo, 'z-team-logo')}<div class="z-team-name">{team_a_name}</div><div class="z-team-sub">Prob. ganar {format_pct(p_a)}</div></div>
    <div class="z-center-box">
      <div class="z-score-pill">{best_score}</div>
      <div class="z-kick">{center_time}</div>
      <div class="z-meta">{score_now if live_mode else venue}</div>
      <div style="margin-top:10px;"><span class="{badge_class}">{badge_text}</span></div>
    </div>
    <div class="z-team-box">{remote_img(team_b_logo, 'z-team-logo')}<div class="z-team-name">{team_b_name}</div><div class="z-team-sub">Prob. ganar {format_pct(p_b)}</div></div>
  </div>
  <div class="z-outcome-grid">
    <div class="z-outcome"><span>1 · GANA LOCAL</span><b>{format_pct(p_a)}</b></div>
    <div class="z-outcome"><span>X · EMPATE</span><b>{format_pct(p_d)}</b></div>
    <div class="z-outcome"><span>2 · GANA VISITA</span><b>{format_pct(p_b)}</b></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    if auto_error:
        st.warning(auto_error)

    left1, right1 = st.columns([1.55, .95], gap="medium")
    with left1:
        st.markdown('<div class="z-card">', unsafe_allow_html=True)
        st.markdown('<div class="z-card-title">Análisis IA</div>', unsafe_allow_html=True)
        st.markdown(f"<div class='z-alert {style}'><b>{ai_headline}</b></div>", unsafe_allow_html=True)
        for bullet in ai_bullets:
            st.markdown(f"<div class='z-alert'>{bullet}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='z-db-note'>Base: {('recalculo en vivo con minuto, marcador y stats' if live_mode else 'proyección prepartido con contexto y stats disponibles')}.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right1:
        bookmaker_name = odds.get("bookmaker", "") if odds else ""
        source_label = "Mercado real" if best_bet[5] == "Mercado" else "Cuota modelo"
        extra = f"EV {best_bet[3]:.3f} · Stake S/ {best_bet[4]:.2f}" if pd.notna(best_bet[3]) else "Mercado sin cuota live; se muestra cuota justa del modelo."
        st.markdown(
            f"""
<div class="z-market-best">
  <small>MEJOR CUOTA DEL MOMENTO</small>
  <div style="font-size:1.4rem;font-weight:900;margin-top:8px;">{best_bet[0]}</div>
  <div style="font-size:2rem;font-weight:900;margin-top:6px;">@ {best_bet[1]:.2f}</div>
  <div style="margin-top:8px;">{extra}</div>
  <div style="margin-top:10px;color:#cbd5e1;">Fuente: {source_label}{' · ' + bookmaker_name if bookmaker_name else ''}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
<div class="z-card">
  <div class="z-card-title">Resumen rápido</div>
  <div class="z-mini-grid">
    <div class="z-mini-card"><div class="k">OVER 2.5</div><div class="v">{format_pct(p_over)}</div></div>
    <div class="z-mini-card"><div class="k">BTTS</div><div class="v">{format_pct(p_btts) if pd.notna(p_btts) else 'LIVE'}</div></div>
    <div class="z-mini-card"><div class="k">DOMINANCIA</div><div class="v">{dom_index:.2f}</div></div>
    <div class="z-mini-card"><div class="k">RESULTADO</div><div class="v">{best_score}</div></div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    c1, c2 = st.columns([1.45, .95], gap="medium")
    with c1:
        df_market = pd.DataFrame([
            [f"1 - {team_a_name}", p_a, odds.get("team_a_win") if odds else np.nan, fair_decimal_odds(p_a)],
            ["X - Empate", p_d, odds.get("draw") if odds else np.nan, fair_decimal_odds(p_d)],
            [f"2 - {team_b_name}", p_b, odds.get("team_b_win") if odds else np.nan, fair_decimal_odds(p_b)],
            ["Over 2.5", p_over, odds.get("over_2_5") if odds else np.nan, fair_decimal_odds(p_over)],
            ["Under 2.5", p_under, odds.get("under_2_5") if odds else np.nan, fair_decimal_odds(p_under)],
        ], columns=["Mercado", "Probabilidad", "Cuota mercado", "Cuota modelo"])
        df_market["EV"] = df_market.apply(lambda r: expected_value(r["Probabilidad"], r["Cuota mercado"]), axis=1)
        with st.container(border=True):
            st.markdown("### Mercados principales")
            st.dataframe(df_market.style.format({"Probabilidad": "{:.1%}", "Cuota mercado": "{:.2f}", "Cuota modelo": "{:.2f}", "EV": "{:.3f}"}), use_container_width=True, hide_index=True)
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
        st.write("Abre un partido del centro en vivo/hoy/mañana o escribe uno manualmente. La predicción se recalcula en vivo con marcador, minuto y estadísticas cuando el partido ya empezó.")
        st.write("Para activar IA generativa, carga tu `OPENAI_API_KEY` en Render o en **⚙️ Configuración**.")
