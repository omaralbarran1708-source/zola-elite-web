import os
import math
from datetime import date
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="ZOLA Elite",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY", "")
SPORTMONKS_API_TOKEN = os.getenv("SPORTMONKS_API_TOKEN", "")
APP_LOGO_URL = os.getenv("APP_LOGO_URL", "")

st.markdown("""
<style>
:root{
  --bg:#eef3ff;
  --surface:#ffffff;
  --surface-2:#f7f9ff;
  --line:#dbe5ff;
  --text:#0e1a36;
  --muted:#67789b;
  --brand:#1f4ddb;
  --brand-2:#0f3bbf;
  --success:#0f9f62;
  --warn:#d89a00;
}
.stApp{background:linear-gradient(180deg,#eef3ff 0%,#f8fbff 100%);color:var(--text);}
.block-container{max-width:1380px;padding-top:.9rem;padding-bottom:2rem;}
header[data-testid="stHeader"]{background:transparent;}
section[data-testid="stSidebar"]{display:none;}
div[data-testid="stToolbar"]{right:1rem;}
.hero{background:linear-gradient(90deg,var(--brand),#2a60ff);border-radius:22px;padding:1rem 1.2rem;color:white;box-shadow:0 18px 40px rgba(31,77,219,.22);}
.hero-grid{display:grid;grid-template-columns:1.4fr .8fr;gap:1rem;align-items:center;}
.hero h1{margin:0;font-size:2.05rem;color:white;font-weight:800;}
.hero p{margin:.35rem 0 0 0;color:#e9efff;}
.top-badges{display:flex;gap:.55rem;flex-wrap:wrap;margin-top:.75rem;}
.badge{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.22);padding:.3rem .6rem;border-radius:999px;font-size:.82rem;color:white;}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:1rem;box-shadow:0 10px 28px rgba(23,42,99,.07);}
.section-title{font-size:1.15rem;font-weight:800;color:var(--text);margin-bottom:.65rem;}
.meta{color:var(--muted);font-size:.92rem;}
.fixture-row{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:1rem;box-shadow:0 10px 28px rgba(23,42,99,.07);}
.fixture-head{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin-bottom:1rem;}
.teams-grid{display:grid;grid-template-columns:1fr 120px 1fr;gap:1rem;align-items:center;}
.team-box{text-align:center;padding:.7rem;border-radius:18px;background:var(--surface-2);border:1px solid var(--line);}
.team-box img{height:58px;max-width:58px;display:block;margin:0 auto .45rem auto;}
.team-name{font-size:1.2rem;font-weight:800;color:var(--text);}
.team-sub{font-size:.88rem;color:var(--muted);}
.center-box{text-align:center;}
.prob-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem;margin-top:1rem;}
.odds-card{background:var(--surface-2);border:1px solid var(--line);border-radius:18px;padding:.85rem;text-align:center;}
.odds-card .label{font-size:.82rem;color:var(--muted);text-transform:uppercase;font-weight:700;}
.odds-card .value{font-size:1.5rem;font-weight:800;color:var(--text);margin-top:.2rem;}
.odds-card .sub{font-size:.82rem;color:var(--muted);margin-top:.15rem;}
.mini-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;}
.stat-card{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:.9rem;}
.stat-card .k{font-size:.82rem;color:var(--muted);text-transform:uppercase;font-weight:700;}
.stat-card .v{font-size:1.4rem;font-weight:800;color:var(--text);margin-top:.2rem;}
.market-table table{width:100%;border-collapse:collapse;}
.market-table th,.market-table td{padding:.75rem;border-bottom:1px solid var(--line);text-align:left;}
.market-table th{font-size:.82rem;color:var(--muted);text-transform:uppercase;}
.market-table td:last-child,.market-table th:last-child{text-align:right;}
.signal{padding:.8rem 1rem;border-radius:16px;margin-bottom:.5rem;border:1px solid var(--line);}
.signal.good{background:#effcf6;border-color:#caeddc;color:#0c7e50;}
.signal.warn{background:#fff9eb;border-color:#f6e2a3;color:#946a00;}
.signal.info{background:#eef4ff;border-color:#d5e2ff;color:#2550d9;}
.note{padding:.85rem 1rem;border-radius:16px;background:#eef4ff;border:1px solid #d5e2ff;color:#254eb3;}
.footer-note{font-size:.9rem;color:var(--muted);}
</style>
""", unsafe_allow_html=True)
DEFAULT_BANKROLL = 1000.0
API_FOOTBALL_BASE = os.getenv("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
ODDS_API_BASE = os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4")
LIMA_TZ = "America/Lima"
HISTORY_FILE = "zola_match_history.csv"

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
    "soccer_conmebol_libertadores","soccer_conmebol_sudamericana","soccer_uefa_champs_league",
    "soccer_spain_la_liga","soccer_epl","soccer_italy_serie_a","soccer_germany_bundesliga",
    "soccer_france_ligue_one","soccer_brazil_campeonato",
]
PREMIUM_KEYWORDS = [
    "libertadores","sudamericana","champions","europa league","premier","la liga","serie a",
    "bundesliga","ligue 1","brasileirao","campeonato brasileiro","argentina","mls","liga mx",
    "afc champions","caf champions","world cup","copa america","euro","nations league"
]

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

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

def render_bar(title, value_a, value_b, suffix=""):
    total = max(value_a + value_b, 1e-9)
    st.markdown(f"**{title}**")
    st.progress(value_a / total, text=f"A: {value_a}{suffix} | B: {value_b}{suffix}")

def is_premium_competition(league_name):
    lower = league_name.lower()
    return any(k in lower for k in PREMIUM_KEYWORDS)

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p = math.pi/180
    dlat = (lat2-lat1)*p
    dlon = (lon2-lon1)*p
    a = math.sin(dlat/2)**2 + math.cos(lat1*p)*math.cos(lat2*p)*math.sin(dlon/2)**2
    return 2*r*math.asin(math.sqrt(a))

def fatigue_label(km, rest_days):
    score = km/1500 - rest_days*0.35
    if score >= 1.8: return "Alta carga"
    if score >= 0.7: return "Carga media"
    return "Carga baja"

def auto_context(team_a_name, team_b_name, fixture):
    a_key = team_a_name.lower().strip()
    b_key = team_b_name.lower().strip()
    a_ctx = TEAM_CONTEXT.get(a_key, {})
    b_ctx = TEAM_CONTEXT.get(b_key, {})
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
    payload = api_get(f"{ODDS_API_BASE}/sports/{sport_key}/odds", params={"apiKey": api_key, "regions": "eu", "markets": "h2h,totals", "oddsFormat": "decimal", "dateFormat": "iso"})
    best = None
    best_score = 0.0
    for event in payload:
        home = event.get("home_team","")
        away = event.get("away_team","")
        score = max(similarity(team_a, home)+similarity(team_b, away), similarity(team_a, away)+similarity(team_b, home))
        if score > best_score:
            best_score = score
            best = event
    out = {"team_a_win": np.nan, "draw": np.nan, "team_b_win": np.nan, "over_2_5": np.nan, "under_2_5": np.nan, "bookmaker": ""}
    if not best or not best.get("bookmakers"):
        return out
    bm = best["bookmakers"][0]
    out["bookmaker"] = bm.get("title","")
    for market in bm.get("markets", []):
        key = market.get("key")
        for o in market.get("outcomes", []):
            nm = o.get("name","")
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

def lineup_readiness(info):
    if info["formation"] == "N/D": return "Alineación aún no liberada"
    if info["starters"] >= 11 and info["bench"] >= 7: return "Llega completo"
    if info["starters"] >= 10: return "Llega competitivo"
    return "Llega con ajustes"

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

def build_auto_profile(team_name, lineup_info, stats_info, crowd_factor, travel_km, rest_days, injuries):
    base = infer_team_base(team_name)
    attack = base["attack"] + lineup_info["attack_bonus"] + min(0.18, stats_info["shots_on_goal"]*0.025) + min(0.10, stats_info["corners"]*0.012)
    defense = base["defense"] - lineup_info["defense_bonus"] - min(0.12, stats_info["possession"]/100*0.08) + min(0.20, stats_info["red"]*0.08)
    form = base["form"] + min(0.20, stats_info["total_shots"]*0.01) - min(0.15, stats_info["red"]*0.08)
    return {"elo": base["elo"], "form": max(0.4,form), "attack": max(0.4,attack), "defense": max(0.4,defense), "injuries": injuries, "rest_days": rest_days, "travel_km": travel_km, "crowd_factor": crowd_factor, "formation": lineup_info["formation"], "starters": lineup_info["starters"], "bench": lineup_info["bench"]}

def expected_goals(a, b):
    home_boost = 0.10 + 0.17*a["crowd_factor"]
    sg = (a["elo"] - b["elo"])/100
    la = 1.05 + 0.10*sg + 0.18*(a["form"]-b["form"]) + 0.32*(a["attack"]-b["defense"]) + home_boost + 0.025*(a["rest_days"]-b["rest_days"]) - 0.018*a["injuries"] - 0.000025*max(a["travel_km"]-b["travel_km"],0)
    lb = 0.90 - 0.09*sg - 0.14*(a["form"]-b["form"]) + 0.26*(b["attack"]-a["defense"]) + 0.025*(b["rest_days"]-a["rest_days"]) - 0.018*b["injuries"] - 0.000025*max(b["travel_km"]-a["travel_km"],0)
    return max(0.15,min(4.2,la)), max(0.10,min(4.0,lb))

def dominance_index(stats_a, stats_b):
    return (stats_a["shots_on_goal"]-stats_b["shots_on_goal"])*0.22 + (stats_a["total_shots"]-stats_b["total_shots"])*0.10 + (stats_a["corners"]-stats_b["corners"])*0.08 + ((stats_a["possession"]-stats_b["possession"])/10)*0.08 - (stats_a["red"]-stats_b["red"])*0.35

def build_trader_signals(team_a, team_b, p_a,p_d,p_b,p_over,p_under,p_btts, odds, stats_a, stats_b, score_rows):
    sig=[]
    dom=dominance_index(stats_a,stats_b)
    best_score=score_rows[0][0] if score_rows else "N/D"
    if odds:
        for market, prob, odd in [(f"{team_a} gana",p_a,odds.get("team_a_win")),("Empate",p_d,odds.get("draw")),(f"{team_b} gana",p_b,odds.get("team_b_win")),("Over 2.5",p_over,odds.get("over_2_5")),("Under 2.5",p_under,odds.get("under_2_5"))]:
            imp=implied_prob(odd)
            if odd and not np.isnan(imp):
                edge=prob-imp
                if edge>=0.07: sig.append(("good",f"Value detectado en {market}. Prob. modelo {prob:.1%} vs prob. implícita {imp:.1%}."))
                elif edge<=-0.08: sig.append(("warn",f"Mercado más fuerte que el modelo en {market}."))
    if dom>=1.2: sig.append(("info",f"Señal live: {team_a} domina claramente el partido por volumen y control."))
    elif dom<=-1.2: sig.append(("info",f"Señal live: {team_b} está imponiendo condiciones del partido."))
    if p_a>0.70 and best_score.startswith(("2-","3-","1-0")): sig.append(("good",f"Escenario principal consistente con favorito fuerte: {best_score} para {team_a}."))
    if p_btts<0.42: sig.append(("info","El modelo ve sesgo a portería a cero de uno de los dos."))
    return sig

def best_bet_summary(odds,p_a,p_d,p_b,p_over,p_under,bankroll):
    opts=[("Victoria equipo A",odds.get("team_a_win"),p_a),("Empate",odds.get("draw"),p_d),("Victoria equipo B",odds.get("team_b_win"),p_b),("Over 2.5",odds.get("over_2_5"),p_over),("Under 2.5",odds.get("under_2_5"),p_under)]
    best=None; best_ev=-999
    for label,odd,prob in opts:
        ev=expected_value(prob,odd)
        if not np.isnan(ev) and ev>best_ev:
            best_ev=ev; best=(label,odd,prob,ev,kelly_fraction(prob,odd)*bankroll*0.25)
    return best

def ai_summary_text(team_a, team_b, p_a,p_d,p_b,best_score,signals):
    lead = "ZOLA detecta un favoritismo claro." if max(p_a,p_b)>0.68 else "ZOLA detecta un partido más competido de lo que parece."
    sig = signals[0][1] if signals else "No aparece una señal premium dominante todavía."
    return f"{lead} Escenario base: {best_score}. {sig}"

def pattern_summary(history_df, team_a, team_b):
    if history_df.empty:
        return "Todavía no hay historial suficiente para detectar patrones aprendidos."
    subset = history_df[history_df["match"].str.contains(team_a, case=False, na=False) | history_df["match"].str.contains(team_b, case=False, na=False)]
    if subset.empty:
        return "Todavía no hay historial suficiente para detectar patrones aprendidos."
    n=len(subset)
    if "prediction_hit_exact" in subset.columns and subset["prediction_hit_exact"].notna().any():
        hit = subset["prediction_hit_exact"].fillna(0).mean()
        return f"ZOLA ya tiene {n} partidos relacionados. Exactitud exacta registrada: {hit:.1%}."
    return f"ZOLA ya tiene {n} partidos relacionados guardados. Registra más resultados reales para afinar patrones."


history_file_df = load_history_file()

def render_signal(level, text):
    st.markdown(f'<div class="signal {level}">{text}</div>', unsafe_allow_html=True)

def env_status(label, ok):
    return f"{label}: {'Conectado' if ok else 'Pendiente'}"

logo_html = f'<img src="{APP_LOGO_URL}" style="height:56px;border-radius:12px;background:white;padding:6px;" />' if APP_LOGO_URL else '<div style="height:56px;width:56px;border-radius:14px;background:white;color:#1f4ddb;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:900;">Z</div>'

st.markdown(f"""
<div class="hero">
  <div class="hero-grid">
    <div>
      <div style="display:flex;align-items:center;gap:.85rem;">
        {logo_html}
        <div>
          <h1>ZOLA Elite</h1>
          <p>Lectura de partidos, probabilidades y señales de valor en una interfaz pública más limpia.</p>
        </div>
      </div>
      <div class="top-badges">
        <span class="badge">{env_status('API-Football', bool(API_FOOTBALL_KEY))}</span>
        <span class="badge">{env_status('The Odds API', bool(THE_ODDS_API_KEY))}</span>
        <span class="badge">{env_status('Sportmonks', bool(SPORTMONKS_API_TOKEN))}</span>
      </div>
    </div>
    <div class="panel" style="background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.18);color:white;">
      <div style="font-size:.82rem;opacity:.9;text-transform:uppercase;font-weight:700;">Privacidad</div>
      <div style="font-size:1rem;font-weight:800;margin-top:.2rem;">Las claves no se muestran al público</div>
      <div style="font-size:.9rem;opacity:.92;margin-top:.25rem;">Esta versión solo lee las variables del servidor y no tiene campos visibles para API keys.</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

filters_left, filters_right = st.columns([1.1, 2.2], gap="medium")
with filters_left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    match_date = st.date_input("Fecha", value=date.today())
    only_premium = st.toggle("Solo torneos top", value=True)
    sport_key = st.selectbox("Mercado base", SPORT_KEY_SUGGESTIONS, index=0)
    bankroll = st.number_input("Bankroll (S/)", min_value=1.0, value=DEFAULT_BANKROLL, step=50.0)
    st.markdown('</div>', unsafe_allow_html=True)

fixture = {}
lineups = []
stats_rows = []
events_rows = []
odds = {}
api_message = None
context = {"crowd_a":0.8,"crowd_b":0.2,"travel_a":0,"travel_b":1200,"rest_a":5,"rest_b":4,"fatigue_a":"Carga baja","fatigue_b":"Carga media"}
selected_fixture = None
team_a_name, team_b_name = "Palmeiras", "Sporting Cristal"

with filters_right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    fixture_lookup = {}
    labels = []
    if API_FOOTBALL_KEY:
        try:
            all_fixtures = fetch_today_fixtures(API_FOOTBALL_KEY, match_date)
            if only_premium:
                all_fixtures = [f for f in all_fixtures if is_premium_competition(f.get("league",{}).get("name",""))]
            for item in all_fixtures:
                home = item.get("teams",{}).get("home",{}).get("name","")
                away = item.get("teams",{}).get("away",{}).get("name","")
                league = item.get("league",{}).get("name","")
                status = item.get("fixture",{}).get("status",{}).get("short","")
                lab = f"{home} vs {away} | {league} | {status}"
                labels.append(lab)
                fixture_lookup[lab] = item
        except Exception as e:
            api_message = f"No pude cargar los partidos: {e}"
    if labels:
        selected_label = st.selectbox("Selecciona partido", labels, index=0)
        selected_fixture = fixture_lookup[selected_label]
        team_a_name = selected_fixture.get("teams",{}).get("home",{}).get("name","Equipo A")
        team_b_name = selected_fixture.get("teams",{}).get("away",{}).get("name","Equipo B")
        context = auto_context(team_a_name, team_b_name, selected_fixture)
    else:
        team_a_name, team_b_name = parse_match_query(st.text_input("Partido manual", value="Palmeiras vs Sporting Cristal"))
    run = st.button("Analizar partido", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if api_message:
    st.warning(api_message)

if run:
    if selected_fixture and API_FOOTBALL_KEY:
        try:
            fixture = selected_fixture
            fixture_id = fixture.get("fixture",{}).get("id")
            if fixture_id:
                lineups = fetch_lineups_api_football(API_FOOTBALL_KEY, fixture_id)
                stats_rows = fetch_stats_api_football(API_FOOTBALL_KEY, fixture_id)
                events_rows = fetch_events_api_football(API_FOOTBALL_KEY, fixture_id)
        except Exception as e:
            st.warning(f"No pude leer API-Football: {e}")
    if THE_ODDS_API_KEY:
        try:
            odds = fetch_odds_the_odds_api(THE_ODDS_API_KEY, sport_key, team_a_name, team_b_name)
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
    p_a,p_d,p_b = outcome_probabilities(matrix)
    p_over,p_under = over_under_prob(matrix,2.5)
    p_btts = both_teams_to_score(matrix)
    score_rows = top_scores(matrix,10)
    best_score,best_prob = score_rows[0]
    dom_index = dominance_index(stats_a, stats_b)
    signals = build_trader_signals(team_a_name, team_b_name, p_a,p_d,p_b,p_over,p_under,p_btts, odds, stats_a, stats_b, score_rows)
    best_bet = best_bet_summary(odds,p_a,p_d,p_b,p_over,p_under,bankroll)

    home_logo = fixture.get("teams",{}).get("home",{}).get("logo","") if fixture else ""
    away_logo = fixture.get("teams",{}).get("away",{}).get("logo","") if fixture else ""
    league_name = fixture.get("league",{}).get("name","Análisis de partido") if fixture else "Análisis de partido"
    country_name = fixture.get("league",{}).get("country","") if fixture else ""
    venue_name = fixture.get("fixture",{}).get("venue",{}).get("name","Sin estadio") if fixture else "Sin estadio"
    kickoff = fixture.get("fixture",{}).get("date","") if fixture else ""

    st.markdown(f"""
    <div class="fixture-row">
      <div class="fixture-head">
        <div>
          <div class="section-title">{league_name}</div>
          <div class="meta">{country_name} · {venue_name}</div>
        </div>
        <div class="meta">{kickoff}</div>
      </div>
      <div class="teams-grid">
        <div class="team-box">
          {f'<img src="{home_logo}" />' if home_logo else ''}
          <div class="team-name">{team_a_name}</div>
          <div class="team-sub">Prob. ganar {p_a:.1%}</div>
        </div>
        <div class="center-box">
          <div class="meta">Marcador proyectado</div>
          <div style="font-size:2.2rem;font-weight:900;color:var(--text);">{best_score}</div>
          <div class="meta">Empate {p_d:.1%}</div>
        </div>
        <div class="team-box">
          {f'<img src="{away_logo}" />' if away_logo else ''}
          <div class="team-name">{team_b_name}</div>
          <div class="team-sub">Prob. ganar {p_b:.1%}</div>
        </div>
      </div>
      <div class="prob-grid">
        <div class="odds-card"><div class="label">1 · Gana local</div><div class="value">{p_a:.1%}</div><div class="sub">{odds.get('team_a_win','-')}</div></div>
        <div class="odds-card"><div class="label">X · Empate</div><div class="value">{p_d:.1%}</div><div class="sub">{odds.get('draw','-')}</div></div>
        <div class="odds-card"><div class="label">2 · Gana visita</div><div class="value">{p_b:.1%}</div><div class="sub">{odds.get('team_b_win','-')}</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    top1, top2 = st.columns([1.45, 1], gap="medium")
    with top1:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Mercados principales</div>', unsafe_allow_html=True)
        market_rows = [
            ("Gana local", p_a, odds.get("team_a_win")),
            ("Empate", p_d, odds.get("draw")),
            ("Gana visita", p_b, odds.get("team_b_win")),
            ("Over 2.5", p_over, odds.get("over_2_5")),
            ("Under 2.5", p_under, odds.get("under_2_5")),
            ("BTTS Sí", p_btts, None),
        ]
        html = ['<div class="market-table"><table><thead><tr><th>Mercado</th><th>Modelo</th><th>Cuota</th><th>EV</th></tr></thead><tbody>']
        for name, prob, odd in market_rows:
            ev = expected_value(prob, odd) if odd else np.nan
            ev_txt = '-' if np.isnan(ev) else f'{ev:.3f}'
            odd_txt = '-' if not odd or (isinstance(odd,float) and np.isnan(odd)) else f'{odd:.2f}'
            html.append(f'<tr><td>{name}</td><td>{prob:.1%}</td><td>{odd_txt}</td><td>{ev_txt}</td></tr>')
        html.append('</tbody></table></div>')
        st.markdown(''.join(html), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel" style="margin-top:1rem;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top marcadores</div>', unsafe_allow_html=True)
        score_df = pd.DataFrame(score_rows, columns=["Marcador", "Probabilidad"])
        st.dataframe(score_df.style.format({"Probabilidad":"{:.1%}"}), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with top2:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Resumen rápido</div>', unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card"><div class="k">Over 2.5</div><div class="v">{p_over:.1%}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card"><div class="k">BTTS</div><div class="v">{p_btts:.1%}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card"><div class="k">Dominancia</div><div class="v">{dom_index:.2f}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card"><div class="k">Mejor mercado</div><div class="v" style="font-size:1rem;">{best_bet[0] if best_bet else 'N/D'}</div></div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)
        if signals:
            for level, text in signals[:4]:
                render_signal(level, text)
        else:
            st.markdown('<div class="note">Todavía no hay señales claras para este partido.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel" style="margin-top:1rem;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Tabla de contexto</div>', unsafe_allow_html=True)
        context_df = pd.DataFrame([
            [team_a_name, lineup_readiness(lineup_a), context["travel_a"], context["rest_a"], context["fatigue_a"]],
            [team_b_name, lineup_readiness(lineup_b), context["travel_b"], context["rest_b"], context["fatigue_b"]],
        ], columns=["Equipo", "Estado", "Viaje km", "Descanso", "Fatiga"])
        st.dataframe(context_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    stats_left, stats_right = st.columns(2, gap="medium")
    with stats_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Comparativa de equipos</div>', unsafe_allow_html=True)
        compare_df = pd.DataFrame([
            ["Tiros", stats_a["total_shots"], stats_b["total_shots"]],
            ["Tiros al arco", stats_a["shots_on_goal"], stats_b["shots_on_goal"]],
            ["Posesión", stats_a["possession"], stats_b["possession"]],
            ["Corners", stats_a["corners"], stats_b["corners"]],
            ["Amarillas", stats_a["yellow"], stats_b["yellow"]],
            ["Rojas", stats_a["red"], stats_b["red"]],
        ], columns=["Indicador", team_a_name, team_b_name])
        st.dataframe(compare_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with stats_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Historial de aprendizaje</div>', unsafe_allow_html=True)
        if not history_file_df.empty:
            st.dataframe(history_file_df.tail(10), use_container_width=True, hide_index=True)
        else:
            st.markdown('<div class="note">Todavía no hay historial guardado.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    save_history_row({
        "match": f"{team_a_name} vs {team_b_name}",
        "prediction": best_score,
        "team_a_win": round(p_a,4),
        "draw": round(p_d,4),
        "team_b_win": round(p_b,4),
        "best_market": best_bet[0] if best_bet else "",
        "best_market_ev": round(best_bet[3],4) if best_bet else np.nan,
        "league": league_name,
    })

else:
    st.markdown('<div class="panel"><div class="section-title">Listo para análisis</div><div class="footer-note">Selecciona un partido y pulsa <b>Analizar partido</b>. Ya no se muestran claves ni paneles internos al público.</div></div>', unsafe_allow_html=True)
