
import os
import math
from datetime import date
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="ZOLA Elite Blue Backup Blue",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root{
  --bg:#090e1c;
  --bg2:#0c1222;
  --panel:#11192d;
  --panel2:#0f1629;
  --line:#263351;
  --text:#eef3ff;
  --muted:#94a3c7;
  --blue:#5f7cff;
  --blue2:#97adff;
  --red:#a80f2e;
  --red2:#d11643;
}
.stApp{
  background:
    radial-gradient(circle at 10% 0%, rgba(73,103,255,.10), transparent 20%),
    radial-gradient(circle at 95% 5%, rgba(255,255,255,.05), transparent 16%),
    linear-gradient(180deg, #0d1322 0%, #111b34 100%);
  color:var(--text);
}
.block-container{max-width:1580px;padding-top:.7rem;padding-bottom:1.5rem;}
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0b1121,#09101d);
  border-right:1px solid #1f2a44;
}
h1,h2,h3,h4,h5,h6,p,span,label,div{color:var(--text);}
.hero{
  position:relative; overflow:hidden;
  border-radius:24px;
  border:1px solid #2b3960;
  background:
    radial-gradient(circle at 15% 30%, rgba(122,146,245,.14), transparent 22%),
    radial-gradient(circle at 92% 25%, rgba(255,255,255,.06), transparent 18%),
    linear-gradient(135deg,#141c33 0%,#10172c 45%,#0d1426 100%);
  padding:1.25rem 1.35rem;
  box-shadow:0 20px 48px rgba(0,0,0,.30);
  margin-bottom:1rem;
}
.hero:after{
  content:"";
  position:absolute; right:-6%; top:-8%; width:38%; height:170%;
  background:repeating-linear-gradient(120deg, rgba(255,255,255,.03), rgba(255,255,255,.03) 3px, transparent 3px, transparent 11px);
  transform:rotate(8deg);
}
.hero h1{margin:0;font-size:2.2rem;color:#aebdff;font-weight:800;}
.hero p{margin:.45rem 0 0 0;color:#dbe4ff;max-width:840px;}
.topnav{
  display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:.8rem; font-weight:700;
}
.topnav .item{
  color:#c7d2f3; padding:.2rem .15rem; border-bottom:2px solid transparent;
}
.topnav .active{color:#ffffff;border-color:#8ea5ff;}
.logo{
  font-size:1.7rem;font-weight:900;color:#93a8f6; display:flex; align-items:center; gap:.55rem;
}
.panel, .glass, .kpi, .feed-card{
  background:linear-gradient(180deg, rgba(18,28,52,.97), rgba(14,22,40,.97));
  border:1px solid var(--line);
  border-radius:18px;
  box-shadow:0 10px 28px rgba(0,0,0,.22);
}
.panel{padding:1rem;}
.glass{padding:.85rem;}
.kpi{padding:.9rem 1rem; min-height:106px;}
.feed-card{padding:.65rem .8rem; margin-bottom:.5rem;}
.muted{color:var(--muted); font-size:.9rem;}
.section-title{font-size:1.85rem;font-weight:850;margin-bottom:.25rem;}
.card-title{font-size:.95rem;color:#b8c5eb;margin-bottom:.4rem;}
.compact-title{font-size:.85rem;color:#9fb1df;margin-bottom:.35rem;text-transform:uppercase;letter-spacing:.04em;}
div[data-testid="stMetric"]{
  background:linear-gradient(180deg, rgba(18,28,52,.97), rgba(14,22,40,.97));
  border:1px solid var(--line);
  border-radius:18px;
  box-shadow:0 10px 28px rgba(0,0,0,.22);
  padding:.9rem 1rem;
}
div.stButton > button{
  border-radius:14px !important;
  border:1px solid #33415f !important;
  background:linear-gradient(180deg,#edf2ff,#dfe8ff)!important;
  color:#0b1733!important;
}
div.stButton > button[kind="primary"]{
  background:linear-gradient(180deg,#c81642,#9c0e2c)!important;
  border:1px solid #ee4a70!important;
}
.stSelectbox div[data-baseweb="select"] > div,
.stTextInput input,
.stNumberInput input,
.stDateInput input{
  background:#edf2ff!important;
  color:#0b1733!important;
  border:1px solid #9eb2ea!important;
  border-radius:14px!important;
}
.stProgress > div > div > div > div{
  background:linear-gradient(90deg,#4766ff,#7f98ff);
}
.signal-good,.signal-warn,.signal-info{border-radius:15px;padding:.85rem 1rem;margin-bottom:.55rem;}
.signal-good{background:rgba(22,163,74,.12);border:1px solid rgba(22,163,74,.30);color:#baf7cf;}
.signal-warn{background:rgba(234,88,12,.12);border:1px solid rgba(234,88,12,.30);color:#ffd5ae;}
.signal-info{background:rgba(73,103,255,.14);border:1px solid rgba(73,103,255,.34);color:#dce5ff;}
.green-pill,.yellow-pill,.red-pill,.blue-pill{
  display:inline-block;padding:.22rem .56rem;border-radius:999px;font-weight:800;font-size:.78rem;
}
.green-pill{background:rgba(22,163,74,.16);color:#b8f5ca;}
.yellow-pill{background:rgba(245,158,11,.16);color:#ffd98b;}
.red-pill{background:rgba(220,38,38,.16);color:#ffb2b2;}
.blue-pill{background:rgba(73,103,255,.18);color:#d8e1ff;}
.small-chip{
  display:inline-block;padding:.18rem .5rem;border-radius:999px;background:rgba(73,103,255,.13);border:1px solid rgba(73,103,255,.28);color:#d7e1ff;font-size:.76rem;
}
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

left, right = st.columns([1.1, 4.2], gap="large")

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### Claves API")
    api_football_key = st.text_input("API-Football key ⭐", value=os.getenv("API_FOOTBALL_KEY", ""), type="password")
    odds_api_key = st.text_input("The Odds API ⭐", value=os.getenv("THE_ODDS_API_KEY", ""), type="password")
    sportmonks_token = st.text_input("Sportmonks token (backup live) ⭐", value=os.getenv("SPORTMONKS_API_TOKEN", ""), type="password")
    odds_live_source = st.selectbox("Proveedor odds live", ["The Odds API", "API-Football live odds", "Sportmonks inplay odds"], index=0)
    st.markdown('<div class="muted">Prematch: The Odds API. Live: API-Football o Sportmonks como respaldo si el partido está en curso.</div>', unsafe_allow_html=True)
    st.markdown("---")
    sport_key = st.selectbox("Sport key odds", SPORT_KEY_SUGGESTIONS, index=0)
    st.markdown('<div class="muted">Selector claro: texto oscuro sobre fondo claro para mejor visibilidad.</div>', unsafe_allow_html=True)
    bankroll = st.number_input("Bankroll (S/)", min_value=1.0, value=DEFAULT_BANKROLL, step=50.0)
    match_date = st.date_input("Fecha", value=date.today())
    auto_refresh = st.selectbox("Auto-refresh", ["Off", "30s", "60s"], index=0)
    only_premium = st.toggle("Solo torneos top", value=True)
    st.markdown('<div class="muted">Backup live sugerido: Sportmonks solo para partidos en vivo.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown("""
    <div class="topnav">
      <div class="item active">🎯 Dashboard</div>
      <div class="item">📡 Live Center</div>
      <div class="item">💸 Trader Signals</div>
      <div class="item">🧠 Informe IA</div>
      <div class="item">📒 Historial y aprendizaje</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero">
      <div class="logo">⚽ ZOLA Elite</div>
      <h1>Algoritmo ZOLA Elite</h1>
      <p>Panel profesional que completa contexto automáticamente, detecta valor, guarda historial y te ayuda a estudiar patrones para mejorar el siguiente partido.</p>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["🎯 Dashboard", "📡 Live Center", "💸 Trader Signals", "🧠 Informe IA", "📒 Historial y aprendizaje"])

fixture = {}
lineups = []
stats_rows = []
events_rows = []
odds = {}
context = {"crowd_a":0.8,"crowd_b":0.2,"travel_a":0,"travel_b":1200,"rest_a":5,"rest_b":4,"fatigue_a":"Carga baja","fatigue_b":"Carga media"}
api_message = None

with tabs[0]:
    c_main, c_feed = st.columns([3.35, 1.1], gap="medium")
    with c_main:
        st.markdown('<div class="section-title">Partido a analizar</div>', unsafe_allow_html=True)
        fixture_lookup = {}
        selected_fixture = None
        try:
            if api_football_key:
                all_fixtures = fetch_today_fixtures(api_football_key, match_date)
                if only_premium:
                    all_fixtures = [f for f in all_fixtures if is_premium_competition(f.get("league",{}).get("name",""))]
                labels = []
                for item in all_fixtures:
                    home = item.get("teams",{}).get("home",{}).get("name","")
                    away = item.get("teams",{}).get("away",{}).get("name","")
                    league = item.get("league",{}).get("name","")
                    status = item.get("fixture",{}).get("status",{}).get("short","")
                    lab = f"{home} vs {away} | {league} | {status}"
                    labels.append(lab)
                    fixture_lookup[lab] = item
                selected_label = st.selectbox("Partidos disponibles", labels, index=0 if labels else None)
                if selected_label:
                    selected_fixture = fixture_lookup[selected_label]
                    auto_home = selected_fixture.get("teams",{}).get("home",{}).get("name","")
                    auto_away = selected_fixture.get("teams",{}).get("away",{}).get("name","")
                    match_query = st.text_input("Partido seleccionado", value=f"{auto_home} vs {auto_away}")
                else:
                    match_query = st.text_input("Partido seleccionado", value="Palmeiras vs Sporting Cristal")
            else:
                match_query = st.text_input("Partido seleccionado", value="Palmeiras vs Sporting Cristal")
        except Exception as e:
            api_message = f"No pude cargar los partidos: {e}"
            match_query = st.text_input("Partido seleccionado", value="Palmeiras vs Sporting Cristal")

        team_a_name, team_b_name = parse_match_query(match_query)
        if selected_fixture:
            context = auto_context(team_a_name, team_b_name, selected_fixture)

        a1, a2, a3 = st.columns([1.05, .72, .7])
        with a1:
            st.markdown('<div class="glass">', unsafe_allow_html=True)
            st.markdown('<div class="compact-title">Apoyo</div>', unsafe_allow_html=True)
            render_bar("Apoyo", round(context["crowd_a"]*100), round(context["crowd_b"]*100), "%")
            st.markdown(f"<div class='muted'>A</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with a2:
            st.markdown(f'<div class="kpi"><div class="compact-title">Travel Fatigue (KM)</div><div style="font-size:2rem;font-weight:850;text-align:center;margin-top:.7rem">{max(context["travel_a"], context["travel_b"])}</div></div>', unsafe_allow_html=True)
        with a3:
            st.markdown(f'<div class="kpi"><div class="compact-title">Descanso</div><div style="display:flex;justify-content:space-between;margin-top:.35rem"><b>A</b><b>{context["rest_a"]}</b></div><div style="display:flex;justify-content:space-between"><b>B</b><b>{context["rest_b"]}</b></div><div style="display:flex;justify-content:space-between"><b>S</b><b>{context["rest_a"]}</b></div><div style="display:flex;justify-content:space-between"><b>S</b><b>{context["rest_b"]}</b></div></div>', unsafe_allow_html=True)

        b1, b2 = st.columns([1.1, 1])
        with b1:
            run = st.button("Ejecutar Zola Elite", type="primary", use_container_width=True)
        with b2:
            if st.button("Añadir a watchlist", use_container_width=True):
                wl = f"{team_a_name} vs {team_b_name}"
                if wl not in st.session_state.watchlist:
                    st.session_state.watchlist.append(wl)

    with c_feed:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("### Live Feed")
        if selected_fixture:
            home = selected_fixture.get("teams",{}).get("home",{}).get("name","")
            away = selected_fixture.get("teams",{}).get("away",{}).get("name","")
            st.markdown(f'<div class="feed-card">🟡 {home}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="feed-card">🔵 {away}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="feed-card"><span class="small-chip">{selected_fixture.get("fixture",{}).get("status",{}).get("short","NS")}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="feed-card">Sin partido cargado</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if auto_refresh != "Off":
    st.caption(f"Auto-refresh sugerido: {auto_refresh}")

if 'team_a_name' not in locals():
    team_a_name, team_b_name = "Palmeiras", "Sporting Cristal"
    run = False

if run:
    auto_error = None
    if selected_fixture and api_football_key:
        try:
            fixture = selected_fixture
            fixture_id = fixture.get("fixture",{}).get("id")
            if fixture_id:
                lineups = fetch_lineups_api_football(api_football_key, fixture_id)
                stats_rows = fetch_stats_api_football(api_football_key, fixture_id)
                events_rows = fetch_events_api_football(api_football_key, fixture_id)
        except Exception as e:
            auto_error = f"No pude leer API-Football: {e}"
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
    p_a,p_d,p_b = outcome_probabilities(matrix)
    p_over,p_under = over_under_prob(matrix,2.5)
    p_btts = both_teams_to_score(matrix)
    score_rows = top_scores(matrix,10)
    best_score,best_prob = score_rows[0]
    dom_index = dominance_index(stats_a, stats_b)
    signals = build_trader_signals(team_a_name, team_b_name, p_a,p_d,p_b,p_over,p_under,p_btts, odds, stats_a, stats_b, score_rows)
    best_bet = best_bet_summary(odds,p_a,p_d,p_b,p_over,p_under,bankroll)
    ai_text = ai_summary_text(team_a_name, team_b_name, p_a,p_d,p_b,best_score,signals)

    save_history_row({
        "match": f"{team_a_name} vs {team_b_name}",
        "prediction": best_score,
        "team_a_win": round(p_a,4),
        "draw": round(p_d,4),
        "team_b_win": round(p_b,4),
        "best_market": best_bet[0] if best_bet else "",
        "best_market_ev": round(best_bet[3],4) if best_bet else np.nan,
        "league": fixture.get("league",{}).get("name","") if fixture else "",
    })
    history_file_df = load_history_file()

    with tabs[0]:
        if api_message:
            st.warning(api_message)
        if auto_error:
            st.warning(auto_error)
        t1,t2,t3,t4 = st.columns(4)
        t1.metric("Competición", fixture.get("league",{}).get("name","N/D") if fixture else "N/D")
        t2.metric("Estadio", fixture.get("fixture",{}).get("venue",{}).get("name","N/D") if fixture else "N/D")
        t3.metric("Estado", fixture.get("fixture",{}).get("status",{}).get("long","N/D") if fixture else "N/D")
        t4.metric("Kickoff", fixture.get("fixture",{}).get("date","N/D") if fixture else "N/D")

        st.markdown("### Panel central")
        p1, p2, p3 = st.columns([1.2, 1.1, 1.1])
        p1.markdown('<div class="kpi-box"><b>Provider prematch</b><br>The Odds API</div>', unsafe_allow_html=True)
        p2.markdown('<div class="kpi-box"><b>Provider live principal</b><br>API-Football</div>', unsafe_allow_html=True)
        p3.markdown(f'<div class="kpi-box"><b>Backup live</b><br>{"Sportmonks listo" if sportmonks_token else "Pendiente token Sportmonks"}</div>', unsafe_allow_html=True)
        k1,k2,k3,k4 = st.columns(4)
        best_market_label = best_bet[0] if best_bet else "Sin señal"
        best_market_conf = f"{best_bet[3]:.3f} EV" if best_bet else "Sin edge"
        value_color = "green-pill" if best_bet and best_bet[3] > 0 else "yellow-pill"
        confidence = "Alta" if abs(p_a-p_b)>0.38 and best_prob>0.14 else "Media" if abs(p_a-p_b)>0.22 else "Moderada"
        semaphore = "green-pill" if signals and any(s[0]=="good" for s in signals) else "yellow-pill" if signals else "red-pill"
        sem_text = "Value" if signals and any(s[0]=="good" for s in signals) else "Vigilar" if signals else "Evitar"
        k1.markdown(f'<div class="kpi"><b>Predicción final</b><br><span style="font-size:1.85rem;font-weight:850">{best_score}</span></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi"><b>Mejor mercado</b><br><span style="font-size:1.12rem;font-weight:800">{best_market_label}</span><br><span class="{value_color}">{best_market_conf}</span></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi"><b>Confianza</b><br><span style="font-size:1.25rem;font-weight:800">{confidence}</span></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi"><b>Semáforo</b><br><span class="{semaphore}">{sem_text}</span></div>', unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("Live Center")
        r1,r2,r3,r4 = st.columns(4)
        score_live = fixture.get("goals",{}) if fixture else {}
        r1.metric("Marcador", f"{score_live.get('home',0)} - {score_live.get('away',0)}")
        r2.metric("Minuto", fixture.get("fixture",{}).get("status",{}).get("elapsed","-") if fixture else "-")
        r3.metric("Estado", fixture.get("fixture",{}).get("status",{}).get("short","PRE") if fixture else "PRE")
        r4.metric("Dominancia", f"{dom_index:.2f}")
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(f'<div class="kpi"><b>Travel A / B</b><br>{context["travel_a"]} km / {context["travel_b"]} km</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="kpi"><b>Fatiga A / B</b><br>{context["fatigue_a"]} / {context["fatigue_b"]}</div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="kpi"><b>Llegada alineación A</b><br>{lineup_readiness(lineup_a)}</div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="kpi"><b>Llegada alineación B</b><br>{lineup_readiness(lineup_b)}</div>', unsafe_allow_html=True)
        d1,d2 = st.columns(2)
        with d1:
            render_bar("Posesión", stats_a["possession"], stats_b["possession"], "%")
            render_bar("Tiros", stats_a["total_shots"], stats_b["total_shots"])
            render_bar("Tiros al arco", stats_a["shots_on_goal"], stats_b["shots_on_goal"])
        with d2:
            render_bar("Corners", stats_a["corners"], stats_b["corners"])
            render_bar("Amarillas", stats_a["yellow"], stats_b["yellow"])
            render_bar("Rojas", stats_a["red"], stats_b["red"])

    with tabs[2]:
        st.subheader("Trader Signals")
        if signals:
            for level,text in signals:
                cls = "signal-good" if level=="good" else "signal-warn" if level=="warn" else "signal-info"
                st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)
        else:
            st.info("Todavía no hay señales claras.")
        if odds:
            df_market = pd.DataFrame([
                [f"{team_a_name} gana", odds.get("team_a_win"), p_a],
                ["Empate", odds.get("draw"), p_d],
                [f"{team_b_name} gana", odds.get("team_b_win"), p_b],
                ["Over 2.5", odds.get("over_2_5"), p_over],
                ["Under 2.5", odds.get("under_2_5"), p_under],
            ], columns=["Mercado","Cuota","Probabilidad modelo"])
            df_market["Prob. implícita"] = df_market["Cuota"].apply(implied_prob)
            df_market["Edge"] = df_market["Probabilidad modelo"] - df_market["Prob. implícita"]
            df_market["EV"] = df_market.apply(lambda r: expected_value(r["Probabilidad modelo"], r["Cuota"]), axis=1)
            df_market["Stake sugerido S/"] = df_market.apply(lambda r: kelly_fraction(r["Probabilidad modelo"], r["Cuota"]) * bankroll * 0.25, axis=1)
            st.dataframe(df_market.style.format({"Cuota":"{:.2f}","Probabilidad modelo":"{:.1%}","Prob. implícita":"{:.1%}","Edge":"{:.1%}","EV":"{:.3f}","Stake sugerido S/":"{:.2f}"}), use_container_width=True, hide_index=True)

    with tabs[3]:
        st.subheader("Informe IA")
        ga,gb = best_score.split("-")
        final_text = f"{team_a_name} {ga}-{gb} {team_b_name}" if ga != gb else f"Empate {ga}-{gb}"
        conf = "Alta" if abs(p_a-p_b)>0.38 and best_prob>0.14 else "Media" if abs(p_a-p_b)>0.22 else "Moderada"
        trader_text = signals[0][1] if signals else "No aparece una señal premium dominante todavía."
        pattern_text = pattern_summary(history_file_df, team_a_name, team_b_name)
        st.markdown(f"""
<div class="panel">
<b>Predicción final de ZOLA:</b> {final_text}<br><br>
<b>Confianza:</b> {conf}<br><br>
<b>Resumen IA:</b> {ai_text}<br><br>
<b>Trader note:</b> {trader_text}<br><br>
<b>Patrón detectado:</b> {pattern_text}
</div>
""", unsafe_allow_html=True)

    with tabs[4]:
        st.subheader("Historial y aprendizaje")
        ch,cw = st.columns(2)
        with ch:
            st.markdown("### Historial guardado")
            if not history_file_df.empty:
                st.dataframe(history_file_df, use_container_width=True, hide_index=True)
            else:
                st.info("Todavía no hay historial guardado.")
        with cw:
            st.markdown("### Watchlist")
            if st.session_state.watchlist:
                st.dataframe(pd.DataFrame({"Partidos": st.session_state.watchlist}), use_container_width=True, hide_index=True)
            else:
                st.info("Todavía no hay partidos en watchlist.")
            st.markdown("### Aprendizaje postpartido")
            real_match = st.text_input("Partido finalizado", value=f"{team_a_name} vs {team_b_name}")
            xa, xb = st.columns(2)
            with xa:
                real_a = st.number_input("Goles reales A", 0, 20, 0)
            with xb:
                real_b = st.number_input("Goles reales B", 0, 20, 0)
            if st.button("Guardar resultado real para aprendizaje"):
                save_history_row({
                    "match": real_match,
                    "prediction": best_score,
                    "real_result": f"{real_a}-{real_b}",
                    "prediction_hit_exact": int(best_score == f"{real_a}-{real_b}"),
                    "team_a_win": round(p_a,4),
                    "draw": round(p_d,4),
                    "team_b_win": round(p_b,4),
                    "best_market": best_bet[0] if best_bet else "",
                    "best_market_ev": round(best_bet[3],4) if best_bet else np.nan,
                    "league": fixture.get("league",{}).get("name","") if fixture else "",
                })
                st.success("Resultado real guardado.")
else:
    with tabs[0]:
        st.markdown("""
        <div class="panel">
        <b>Interfaz premium ampliada.</b><br><br>
        • cards más compactas<br>
        • topnav más parecido al mock<br>
        • live feed lateral derecho<br>
        • look dark más cercano a dashboard premium
        </div>
        """, unsafe_allow_html=True)
