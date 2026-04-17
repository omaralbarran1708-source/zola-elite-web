import os, math, json, sqlite3
from datetime import date, timedelta, datetime
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title='ZOLA Elite', page_icon='⚽', layout='wide', initial_sidebar_state='collapsed')

API_FOOTBALL_BASE = os.getenv('API_FOOTBALL_BASE_URL', 'https://v3.football.api-sports.io')
ODDS_API_BASE = os.getenv('ODDS_API_BASE_URL', 'https://api.the-odds-api.com/v4')
OPENAI_BASE = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-5-mini')
DB_FILE = 'zola_elite_app.db'
LIMA_TZ = 'America/Lima'
DEFAULT_BANKROLL = 1000.0
LIVE_CODES = {'1H','HT','2H','ET','P','LIVE','INT','BT'}
SPORT_KEY_SUGGESTIONS = [
    'soccer_conmebol_libertadores','soccer_conmebol_sudamericana','soccer_uefa_champs_league',
    'soccer_spain_la_liga','soccer_epl','soccer_italy_serie_a','soccer_germany_bundesliga',
    'soccer_france_ligue_one','soccer_brazil_campeonato'
]

TEAM_PRIORS = {
    'palmeiras': {'elo': 1875, 'form': 2.35, 'attack': 2.05, 'defense': 0.78},
    'sporting cristal': {'elo': 1545, 'form': 1.55, 'attack': 1.18, 'defense': 1.58},
    'real madrid': {'elo': 1915, 'form': 2.30, 'attack': 2.15, 'defense': 0.86},
    'manchester city': {'elo': 1920, 'form': 2.28, 'attack': 2.12, 'defense': 0.88},
    'barcelona': {'elo': 1860, 'form': 2.05, 'attack': 1.95, 'defense': 0.98},
    'arsenal': {'elo': 1870, 'form': 2.12, 'attack': 1.92, 'defense': 0.94},
    'bayern munich': {'elo': 1880, 'form': 2.10, 'attack': 2.00, 'defense': 0.95},
    'psg': {'elo': 1865, 'form': 2.08, 'attack': 2.02, 'defense': 1.02},
    'alianza lima': {'elo': 1495, 'form': 1.52, 'attack': 1.20, 'defense': 1.34},
    'universitario': {'elo': 1530, 'form': 1.78, 'attack': 1.30, 'defense': 1.16},
}

for k, default in {
    'api_football_key_override':'', 'odds_api_key_override':'', 'sportmonks_token_override':'',
    'openai_api_key_override':'', 'selected_fixture_id':'', 'admin_ok':False,
}.items():
    st.session_state.setdefault(k, default)

st.markdown('''
<style>
:root{--brand:#2347d8; --brand2:#2f59ff; --bg:#f2f4f8; --panel:#ffffff; --line:#e2e8f0; --text:#0f172a; --muted:#64748b; --green:#16a34a; --red:#ef4444; --amber:#f59e0b;}
html, body, [class*="css"] { font-family: Inter, system-ui, sans-serif; }
.stApp{background:var(--bg); color:var(--text);} header[data-testid="stHeader"]{background:transparent;} #MainMenu,footer{visibility:hidden;} .block-container{max-width:1450px;padding-top:0.3rem;}
[data-testid="stSidebar"]{display:none;}
.z-header{background:linear-gradient(180deg,var(--brand),var(--brand2)); color:white; border-radius:0 0 18px 18px; padding:14px 18px 10px; margin:-10px -15px 18px; box-shadow:0 10px 30px rgba(35,71,216,.2)}
.z-top-row{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;}
.z-brand{display:flex;align-items:center;gap:12px;min-width:280px;}
.z-logo{width:38px;height:38px;border-radius:10px;background:rgba(255,255,255,.12);display:flex;align-items:center;justify-content:center;border:1px solid rgba(255,255,255,.18);overflow:hidden}
.z-logo img{width:100%;height:100%;object-fit:cover}
.z-brand h1{font-size:28px;line-height:1;margin:0;font-weight:800}
.z-searchbar{flex:1;min-width:340px;max-width:580px;background:#fff;border-radius:14px;padding:10px 14px;color:#334155;display:flex;align-items:center;gap:10px}
.z-searchbar span{opacity:.7}
.z-status-pills{display:flex;gap:8px;flex-wrap:wrap}
.z-pill{color:#fff;border:1px solid rgba(255,255,255,.22);padding:7px 12px;border-radius:999px;font-weight:700;font-size:13px;background:rgba(255,255,255,.08)}
.z-nav{display:flex;gap:18px;flex-wrap:wrap;align-items:center;padding-top:10px;font-weight:700;font-size:14px}
.z-nav .active{background:rgba(255,255,255,.16);padding:9px 12px;border-radius:12px}
.z-card{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 4px 16px rgba(15,23,42,.04)}
.z-section-title{font-size:24px;font-weight:800;margin:0 0 10px}
.z-sub{color:var(--muted)}
.z-list-item{display:flex;align-items:center;justify-content:space-between;padding:11px 8px;border-radius:12px;cursor:pointer}
.z-list-item:hover{background:#f8fafc}
.z-team{display:flex;align-items:center;gap:8px;font-weight:700;color:var(--text)}
.z-team img,.z-league-icon{width:22px;height:22px;object-fit:contain}
.z-mini{font-size:12px;color:var(--muted)}
.z-match-hero{display:grid;grid-template-columns:1fr 220px 1fr;gap:14px;align-items:center;padding:18px 10px}
.z-center{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px}
.z-score{font-size:44px;font-weight:900;line-height:1}
.z-live{background:#fff1f2;color:#be123c;border:1px solid #fecdd3;padding:5px 10px;border-radius:999px;font-weight:800;font-size:13px}
.z-pre{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;padding:5px 10px;border-radius:999px;font-weight:800;font-size:13px}
.z-team-panel{text-align:center}
.z-team-panel img{width:70px;height:70px;object-fit:contain;margin-bottom:8px}
.z-team-name{font-size:30px;font-weight:900;line-height:1.1}
.z-prob{font-size:15px;color:var(--muted);margin-top:5px}
.z-odds-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px}
.z-odd{border:1px solid var(--line);border-radius:16px;padding:14px;background:#fcfdff;text-align:center}
.z-odd .lab{font-size:14px;color:#4967b2;font-weight:800;text-transform:uppercase;letter-spacing:.02em}
.z-odd .num{font-size:24px;font-weight:900;margin-top:8px}
.z-odd .quo{font-size:13px;color:var(--muted);margin-top:4px}
.z-badge-green{background:#ecfdf5;border:1px solid #a7f3d0;color:#065f46;padding:10px 14px;border-radius:14px;font-weight:700}
.z-badge-blue{background:#eff6ff;border:1px solid #bfdbfe;color:#1d4ed8;padding:10px 14px;border-radius:14px;font-weight:700}
.z-ai{background:linear-gradient(180deg,#0f1d4d,#152961);color:#fff;border-radius:18px;padding:18px;border:1px solid rgba(255,255,255,.06)}
.z-ai h3{margin:0 0 10px;font-size:20px}
.z-ai p{margin:0;line-height:1.6;color:#e5edff}
.z-grid-4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.z-kpi{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px}
.z-kpi .t{font-size:13px;color:#64748b;text-transform:uppercase;font-weight:800}
.z-kpi .v{font-size:20px;font-weight:900;margin-top:8px}
.z-table table{width:100%;border-collapse:collapse}.z-table th,.z-table td{padding:10px;border-bottom:1px solid #edf2f7;text-align:left}.z-table th{font-size:13px;color:#64748b}
.z-competition-chip{display:inline-flex;align-items:center;gap:8px;padding:9px 12px;border-radius:999px;background:#fff;border:1px solid var(--line);font-weight:700;margin:0 8px 8px 0;cursor:pointer}
div[data-testid="stVerticalBlockBorderWrapper"]{border:none}
.stButton>button{border-radius:14px !important;font-weight:800 !important}
div[data-baseweb="select"]>div,.stTextInput input,.stDateInput input,.stNumberInput input{border-radius:14px !important}
@media(max-width:900px){.z-match-hero{grid-template-columns:1fr}.z-odds-row,.z-grid-4{grid-template-columns:1fr}.z-searchbar{min-width:unset;width:100%}}
</style>
''', unsafe_allow_html=True)


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS saved_matches (
        fixture_id TEXT PRIMARY KEY,
        home TEXT, away TEXT, league TEXT, match_date TEXT, status TEXT, picked_at TEXT
    )''')
    conn.commit(); conn.close()


def save_match(fixture):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''INSERT OR REPLACE INTO saved_matches VALUES (?,?,?,?,?,?,?)''', (
        str(fixture.get('fixture',{}).get('id','')),
        fixture.get('teams',{}).get('home',{}).get('name',''),
        fixture.get('teams',{}).get('away',{}).get('name',''),
        fixture.get('league',{}).get('name',''),
        fixture.get('fixture',{}).get('date',''),
        fixture.get('fixture',{}).get('status',{}).get('short',''),
        datetime.utcnow().isoformat()
    ))
    conn.commit(); conn.close()


def get_saved_matches(limit=15):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f'SELECT * FROM saved_matches ORDER BY picked_at DESC LIMIT {limit}', conn)
    conn.close(); return df

init_db()


def get_secret(name, override_key):
    return st.session_state.get(override_key) or os.getenv(name, '')


def similarity(a,b):
    return SequenceMatcher(None, (a or '').lower(), (b or '').lower()).ratio()


def api_get(url, headers=None, params=None):
    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status(); return r.json()


def football_headers(api_key):
    return {'x-apisports-key': api_key} if api_key else {}

@st.cache_data(ttl=120, show_spinner=False)
def fetch_fixtures(api_key, on_date):
    if not api_key:
        return []
    try:
        js = api_get(f'{API_FOOTBALL_BASE}/fixtures', headers=football_headers(api_key), params={'date': on_date.isoformat(), 'timezone': LIMA_TZ})
        return js.get('response', [])
    except Exception:
        return []

@st.cache_data(ttl=90, show_spinner=False)
def fetch_statistics(api_key, fixture_id):
    if not api_key or not fixture_id:
        return []
    try:
        return api_get(f'{API_FOOTBALL_BASE}/fixtures/statistics', headers=football_headers(api_key), params={'fixture': fixture_id}).get('response', [])
    except Exception:
        return []

@st.cache_data(ttl=180, show_spinner=False)
def fetch_lineups(api_key, fixture_id):
    if not api_key or not fixture_id:
        return []
    try:
        return api_get(f'{API_FOOTBALL_BASE}/fixtures/lineups', headers=football_headers(api_key), params={'fixture': fixture_id}).get('response', [])
    except Exception:
        return []

@st.cache_data(ttl=90, show_spinner=False)
def fetch_events(api_key, fixture_id):
    if not api_key or not fixture_id:
        return []
    try:
        return api_get(f'{API_FOOTBALL_BASE}/fixtures/events', headers=football_headers(api_key), params={'fixture': fixture_id}).get('response', [])
    except Exception:
        return []


def fetch_odds_event(api_key, sport_key, home, away):
    if not api_key:
        return {}
    try:
        payload = api_get(f'{ODDS_API_BASE}/sports/{sport_key}/odds', params={'apiKey': api_key, 'regions':'eu', 'markets':'h2h,totals', 'oddsFormat':'decimal', 'dateFormat':'iso'})
    except Exception:
        return {}
    best = None; best_score = 0
    for ev in payload:
        score = max(similarity(home, ev.get('home_team',''))+similarity(away, ev.get('away_team','')), similarity(home, ev.get('away_team',''))+similarity(away, ev.get('home_team','')))
        if score > best_score:
            best_score = score; best = ev
    out = {'bookmaker':'', 'team_a_win':np.nan, 'draw':np.nan, 'team_b_win':np.nan, 'over_2_5':np.nan, 'under_2_5':np.nan}
    if not best or not best.get('bookmakers'):
        return out
    bm = best['bookmakers'][0]; out['bookmaker'] = bm.get('title','')
    for m in bm.get('markets',[]):
        for o in m.get('outcomes',[]):
            if m.get('key') == 'h2h':
                if similarity(o.get('name',''), home) > .8: out['team_a_win'] = o.get('price')
                elif similarity(o.get('name',''), away) > .8: out['team_b_win'] = o.get('price')
                elif str(o.get('name','')).lower() == 'draw': out['draw'] = o.get('price')
            elif m.get('key') == 'totals' and o.get('point') == 2.5:
                if str(o.get('name','')).lower() == 'over': out['over_2_5'] = o.get('price')
                if str(o.get('name','')).lower() == 'under': out['under_2_5'] = o.get('price')
    return out


def parse_stats(stats_rows, team_name):
    out = {'shots_on_goal':0.0,'total_shots':0.0,'corners':0.0,'possession':50.0,'yellow':0.0,'red':0.0}
    best = None; bs = 0
    for row in stats_rows or []:
        s = similarity(team_name, row.get('team',{}).get('name',''))
        if s > bs: bs = s; best = row
    if not best: return out
    mp = {r.get('type',''): r.get('value') for r in best.get('statistics',[])}
    def clean(v, default=0.0):
        if isinstance(v, str) and '%' in v:
            try: return float(v.replace('%','').strip())
            except: return default
        try: return float(v)
        except: return default
    out['shots_on_goal'] = clean(mp.get('Shots on Goal',0))
    out['total_shots'] = clean(mp.get('Total Shots',0))
    out['corners'] = clean(mp.get('Corner Kicks',0))
    out['possession'] = clean(mp.get('Ball Possession',50), 50)
    out['yellow'] = clean(mp.get('Yellow Cards',0))
    out['red'] = clean(mp.get('Red Cards',0))
    return out


def infer_team_base(name):
    key = (name or '').lower().strip()
    if key in TEAM_PRIORS: return TEAM_PRIORS[key].copy()
    seed = abs(hash(key)) % 10000; rng = np.random.default_rng(seed)
    return {'elo': float(1450+rng.integers(0,240)), 'form': float(np.round(rng.uniform(1.2,2.0),2)), 'attack': float(np.round(rng.uniform(1.05,1.55),2)), 'defense': float(np.round(rng.uniform(1.0,1.45),2))}


def lineup_info(lineups, team_name):
    best=None; bs=0
    for item in lineups or []:
        s = similarity(team_name, item.get('team',{}).get('name',''))
        if s>bs: bs=s; best=item
    if not best: return {'formation':'N/D','starters':0,'bench':0,'attack_bonus':0,'defense_bonus':0}
    start = best.get('startXI',[]) or []
    subs = best.get('substitutes',[]) or []
    d=m=f=0
    for p in start:
        pos = str(p.get('player',{}).get('pos','')).upper()
        if pos == 'D': d +=1
        elif pos == 'M': m +=1
        elif pos == 'F': f +=1
    return {'formation':best.get('formation','N/D'),'starters':len(start),'bench':len(subs),'attack_bonus':min(.25,f*.03+max(m-3,0)*.01),'defense_bonus':min(.18,d*.02)}


def build_profile(team_name, stats, lineup):
    base = infer_team_base(team_name)
    attack = base['attack'] + lineup['attack_bonus'] + min(0.18, stats['shots_on_goal']*0.025) + min(0.08, stats['corners']*0.01)
    defense = base['defense'] - lineup['defense_bonus'] - min(0.10, stats['possession']/100*0.06) + min(0.16, stats['red']*0.08)
    form = base['form'] + min(0.20, stats['total_shots']*0.01) - min(0.18, stats['red']*0.08)
    return {'elo':base['elo'],'form':max(.5,form),'attack':max(.5,attack),'defense':max(.4,defense)}


def poisson_pmf(k, lam):
    return math.exp(-lam)*(lam**k)/math.factorial(k)


def score_matrix(a,b,max_goals=6):
    pa=[poisson_pmf(i,a) for i in range(max_goals+1)]
    pb=[poisson_pmf(i,b) for i in range(max_goals+1)]
    return np.outer(pa,pb)


def outcome_probs(matrix):
    return float(np.sum(np.tril(matrix,-1))), float(np.sum(np.diag(matrix))), float(np.sum(np.triu(matrix,1)))


def top_scores(matrix, n=8):
    rows=[]
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            rows.append((f'{i}-{j}', float(matrix[i,j])))
    rows.sort(key=lambda x:x[1], reverse=True)
    return rows[:n]


def implied_prob(odd):
    try:
        odd=float(odd)
        return np.nan if odd<=1 else 1/odd
    except: return np.nan


def expected_value(prob, odd):
    try:
        odd=float(odd)
        return np.nan if odd<=1 else prob*(odd-1) - (1-prob)
    except: return np.nan


def kelly_fraction(prob, odd):
    try:
        odd=float(odd)
        if odd<=1: return 0.0
        b=odd-1; q=1-prob; return max(0.0, (b*prob-q)/b)
    except: return 0.0


def compute_live_model(fixture, stats_rows, lineups):
    home = fixture.get('teams',{}).get('home',{}).get('name','Home')
    away = fixture.get('teams',{}).get('away',{}).get('name','Away')
    hs = fixture.get('goals',{}).get('home') or 0
    aw = fixture.get('goals',{}).get('away') or 0
    minute = fixture.get('fixture',{}).get('status',{}).get('elapsed') or 0
    status = fixture.get('fixture',{}).get('status',{}).get('short','NS')

    s_home = parse_stats(stats_rows, home)
    s_away = parse_stats(stats_rows, away)
    l_home = lineup_info(lineups, home)
    l_away = lineup_info(lineups, away)
    p_home = build_profile(home, s_home, l_home)
    p_away = build_profile(away, s_away, l_away)

    # pre-match base
    elo_gap=(p_home['elo']-p_away['elo'])/100
    lam_h=1.10 + 0.09*elo_gap + 0.18*(p_home['form']-p_away['form']) + 0.30*(p_home['attack']-p_away['defense']) + 0.11
    lam_a=0.95 - 0.08*elo_gap - 0.14*(p_home['form']-p_away['form']) + 0.26*(p_away['attack']-p_home['defense'])
    lam_h=max(.15,min(4.0,lam_h)); lam_a=max(.10,min(3.7,lam_a))

    if status in LIVE_CODES and minute:
        remaining=max(1, 90-int(minute))
        ratio=remaining/90.0
        stat_push = (s_home['shots_on_goal']-s_away['shots_on_goal'])*0.09 + (s_home['corners']-s_away['corners'])*0.03 + ((s_home['possession']-s_away['possession'])/100)*0.25
        game_state = hs-aw
        lam_h = max(.03, lam_h*ratio + max(-0.45, min(0.55, stat_push - 0.18*max(game_state,0) + 0.10*max(-game_state,0))))
        lam_a = max(.03, lam_a*ratio + max(-0.45, min(0.55, -stat_push - 0.18*max(-game_state,0) + 0.10*max(game_state,0))))
        # future-goals matrix, then add current score
        m = score_matrix(lam_h, lam_a, max_goals=5)
        rows=[]
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                rows.append((f'{hs+i}-{aw+j}', float(m[i,j])))
        rows.sort(key=lambda x:x[1], reverse=True)
        p_home_win = float(sum(prob for score,prob in rows if int(score.split('-')[0]) > int(score.split('-')[1])))
        p_draw = float(sum(prob for score,prob in rows if int(score.split('-')[0]) == int(score.split('-')[1])))
        p_away_win = float(sum(prob for score,prob in rows if int(score.split('-')[0]) < int(score.split('-')[1])))
        top = rows[:8]
    else:
        m = score_matrix(lam_h, lam_a, max_goals=6)
        p_home_win,p_draw,p_away_win = outcome_probs(m)
        top = top_scores(m,8)

    best_score, best_prob = top[0]
    p_over25 = float(sum(prob for score,prob in top_scores(score_matrix(max(lam_h,.15), max(lam_a,.10), 7), 49) if sum(map(int,score.split('-'))) > 2))
    p_btts = float(sum(v for s,v in top_scores(score_matrix(max(lam_h,.15), max(lam_a,.10), 7), 49) if min(map(int,s.split('-'))) >= 1))
    dominance=(s_home['shots_on_goal']-s_away['shots_on_goal'])*0.25 + (s_home['total_shots']-s_away['total_shots'])*0.08 + (s_home['corners']-s_away['corners'])*0.06 + ((s_home['possession']-s_away['possession'])/10)*0.08
    return {
        'home':home,'away':away,'status':status,'minute':minute,'score_now':f'{hs}-{aw}', 'best_score':best_score,
        'best_prob':best_prob,'home_win':p_home_win,'draw':p_draw,'away_win':p_away_win,
        'over25':p_over25,'btts':p_btts,'dominance':dominance,'top_scores':top,
        'stats_home':s_home,'stats_away':s_away,'league':fixture.get('league',{}).get('name',''),
        'league_logo':fixture.get('league',{}).get('logo',''),'home_logo':fixture.get('teams',{}).get('home',{}).get('logo',''),'away_logo':fixture.get('teams',{}).get('away',{}).get('logo',''),
        'venue':fixture.get('fixture',{}).get('venue',{}).get('name','Sin estadio'),'date':fixture.get('fixture',{}).get('date','')
    }


def best_bet(model, odds, bankroll):
    opts=[('1 Local', odds.get('team_a_win'), model['home_win']), ('X Empate', odds.get('draw'), model['draw']), ('2 Visita', odds.get('team_b_win'), model['away_win']), ('Over 2.5', odds.get('over_2_5'), model['over25'])]
    best=None; best_ev=-999
    for label,odd,prob in opts:
        ev=expected_value(prob, odd)
        if not np.isnan(ev) and ev>best_ev:
            best_ev=ev; best={'label':label,'odd':odd,'prob':prob,'ev':ev,'stake':kelly_fraction(prob, odd)*bankroll*0.25,'bookmaker':odds.get('bookmaker','')}
    if best: return best
    # fallback model quote
    prob=max(model['home_win'], model['draw'], model['away_win'])
    label='1 Local' if prob==model['home_win'] else 'X Empate' if prob==model['draw'] else '2 Visita'
    return {'label':label,'odd': round(1/max(prob,0.05),2), 'prob':prob, 'ev': None, 'stake':0.0, 'bookmaker':'Cuota modelo'}


def generate_ai_summary(model, best_bet, openai_key):
    home, away = model['home'], model['away']
    system = 'Eres analista senior de fútbol. Responde en español claro, directo y breve. No uses disculpas ni ambigüedad. Da una predicción, score probable, lectura táctica y mejor apuesta.'
    prompt = f'''Partido: {home} vs {away}\nEstado: {model['status']} minuto {model['minute']} marcador actual {model['score_now']}\nProbabilidades modelo: local {model['home_win']:.1%}, empate {model['draw']:.1%}, visita {model['away_win']:.1%}\nMarcador principal del modelo: {model['best_score']}\nDominancia: {model['dominance']:.2f}\nStats local: {json.dumps(model['stats_home'])}\nStats visita: {json.dumps(model['stats_away'])}\nMejor apuesta: {best_bet['label']} cuota {best_bet['odd']}\nEscribe 3 párrafos cortos y firmes: 1) predicción final, 2) por qué, 3) mejor apuesta del momento.''' 
    if not openai_key:
        winner = home if model['home_win'] >= max(model['draw'], model['away_win']) else away if model['away_win'] > model['draw'] else 'Empate'
        tempo = 'dominio local' if model['dominance'] > 0.8 else 'partido equilibrado' if abs(model['dominance']) < 0.45 else 'dominio visitante'
        return f"Predicción ZOLA: {winner}. Marcador principal: {model['best_score']}. La lectura del juego apunta a {tempo}. Mejor cuota del momento: {best_bet['label']} @ {best_bet['odd']}."
    try:
        headers={'Authorization':f'Bearer {openai_key}','Content-Type':'application/json'}
        payload={'model':OPENAI_MODEL,'input':[{'role':'system','content':system},{'role':'user','content':prompt}], 'max_output_tokens':220}
        r=requests.post(f'{OPENAI_BASE}/responses', headers=headers, json=payload, timeout=45)
        r.raise_for_status(); data=r.json()
        text = data.get('output_text','').strip()
        if text: return text
        for item in data.get('output',[]):
            for c in item.get('content',[]):
                if c.get('type') == 'output_text': return c.get('text','').strip()
    except Exception:
        pass
    return f"Predicción ZOLA: {home if model['home_win']>model['away_win'] else away}. Marcador principal: {model['best_score']}. Mejor apuesta: {best_bet['label']} @ {best_bet['odd']}."


def fixture_label(f):
    home=f.get('teams',{}).get('home',{}).get('name','')
    away=f.get('teams',{}).get('away',{}).get('name','')
    lg=f.get('league',{}).get('name','')
    status=f.get('fixture',{}).get('status',{}).get('short','')
    elapsed=f.get('fixture',{}).get('status',{}).get('elapsed')
    suffix = f"{status}" if not elapsed else f"{elapsed}'"
    return f'{home} vs {away} | {lg} | {suffix}'


def render_header():
    crest = 'zola_crest.png' if Path('zola_crest.png').exists() else ''
    logo_html = f'<img src="data:image/png;base64,{img_to_b64(crest)}">' if crest else '⚽'
    st.markdown(f'''
    <div class="z-header">
      <div class="z-top-row">
        <div class="z-brand"><div class="z-logo">{logo_html}</div><h1>ZOLA Elite</h1></div>
        <div class="z-searchbar"><span>🔎</span><div>Buscar partido, competencia o equipo</div></div>
        <div class="z-status-pills"><div class="z-pill">API-Football</div><div class="z-pill">The Odds API</div><div class="z-pill">IA</div></div>
      </div>
      <div class="z-nav"><div class="active">Fútbol</div><div>En vivo</div><div>Hoy</div><div>Mañana</div><div>Competiciones</div><div>Movimiento de cuotas</div></div>
    </div>
    ''', unsafe_allow_html=True)


def img_to_b64(path):
    import base64
    with open(path,'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def render_match_list(fixtures):
    if not fixtures:
        st.info('No hay partidos para esa fecha o falta API-Football.')
        return []
    search = st.text_input('Buscar partido', placeholder='Ej. Palmeiras, Libertadores, Real Madrid', label_visibility='collapsed')
    groups = {}
    for f in fixtures:
        league = f.get('league',{}).get('name','Otros')
        groups.setdefault(league, []).append(f)
    selected = None
    query = search.lower().strip()
    for league, items in groups.items():
        filt = [f for f in items if not query or query in fixture_label(f).lower()]
        if not filt: continue
        logo = filt[0].get('league',{}).get('logo','')
        with st.expander(f'🏆 {league} ({len(filt)})', expanded=(selected is None and len(filt) < 6)):
            for f in filt:
                c1,c2,c3 = st.columns([6,2,1])
                with c1:
                    home=f.get('teams',{}).get('home',{}).get('name','')
                    away=f.get('teams',{}).get('away',{}).get('name','')
                    st.markdown(f'''<div class="z-list-item"><div><div class="z-team"><img src="{f.get('teams',{}).get('home',{}).get('logo','')}">{home}</div><div class="z-team" style="margin-top:4px"><img src="{f.get('teams',{}).get('away',{}).get('logo','')}">{away}</div></div></div>''', unsafe_allow_html=True)
                with c2:
                    elapsed = f.get('fixture',{}).get('status',{}).get('elapsed')
                    short = f.get('fixture',{}).get('status',{}).get('short','')
                    score = f"{f.get('goals',{}).get('home') or 0} - {f.get('goals',{}).get('away') or 0}"
                    label = f"{elapsed}'" if elapsed else short
                    st.markdown(f"<div style='text-align:center;padding-top:10px;font-weight:800'>{score}<br><span class='z-mini'>{label}</span></div>", unsafe_allow_html=True)
                with c3:
                    if st.button('Ver', key=f"view_{f.get('fixture',{}).get('id')}"):
                        st.session_state.selected_fixture_id = str(f.get('fixture',{}).get('id'))
                        save_match(f)
                        st.rerun()
    return []


def find_selected_fixture(fixtures):
    fid = str(st.session_state.get('selected_fixture_id',''))
    for f in fixtures:
        if str(f.get('fixture',{}).get('id','')) == fid:
            return f
    return fixtures[0] if fixtures else None


def settings_popover():
    with st.popover('⚙️ Configuración', use_container_width=False):
        st.caption('Las claves viven mejor en Render. Aquí puedes probarlas en tu sesión.')
        st.session_state.api_football_key_override = st.text_input('API Football', value=st.session_state.api_football_key_override, type='password')
        st.session_state.odds_api_key_override = st.text_input('The Odds API', value=st.session_state.odds_api_key_override, type='password')
        st.session_state.openai_api_key_override = st.text_input('OpenAI / ChatGPT', value=st.session_state.openai_api_key_override, type='password')
        st.session_state.sportmonks_token_override = st.text_input('Sportmonks', value=st.session_state.sportmonks_token_override, type='password')
        st.caption('Si quieres dejarlo fijo: Render > Settings > Environment Variables')


def render_analysis(model, odds, ai_text, bet):
    status_badge = 'z-live' if model['status'] in LIVE_CODES else 'z-pre'
    status_text = (f"EN VIVO {int(model['minute'])}'" if model['status'] in LIVE_CODES and model['minute'] else 'PREVIA')
    st.markdown('<div class="z-card">', unsafe_allow_html=True)
    st.markdown(f'''
    <div class="z-mini" style="display:flex;align-items:center;gap:8px;font-size:14px;margin-bottom:8px"><img class="z-league-icon" src="{model['league_logo']}">{model['league']}</div>
    <div class="z-match-hero">
      <div class="z-team-panel"><img src="{model['home_logo']}"><div class="z-team-name">{model['home']}</div><div class="z-prob">Prob. ganar {model['home_win']:.1%}</div></div>
      <div class="z-center"><div class="{status_badge}">{status_text}</div><div class="z-score">{model['score_now'] if model['status'] in LIVE_CODES else model['best_score']}</div><div class="z-sub">{model['venue']}</div></div>
      <div class="z-team-panel"><img src="{model['away_logo']}"><div class="z-team-name">{model['away']}</div><div class="z-prob">Prob. ganar {model['away_win']:.1%}</div></div>
    </div>
    <div class="z-odds-row">
      <div class="z-odd"><div class="lab">1 · Gana local</div><div class="num">{model['home_win']:.1%}</div><div class="quo">Cuota {odds.get('team_a_win') if not pd.isna(odds.get('team_a_win')) else round(1/max(model['home_win'],0.05),2)}</div></div>
      <div class="z-odd"><div class="lab">X · Empate</div><div class="num">{model['draw']:.1%}</div><div class="quo">Cuota {odds.get('draw') if not pd.isna(odds.get('draw')) else round(1/max(model['draw'],0.05),2)}</div></div>
      <div class="z-odd"><div class="lab">2 · Gana visita</div><div class="num">{model['away_win']:.1%}</div><div class="quo">Cuota {odds.get('team_b_win') if not pd.isna(odds.get('team_b_win')) else round(1/max(model['away_win'],0.05),2)}</div></div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    c1,c2 = st.columns([1.25, .85], gap='medium')
    with c1:
        st.markdown(f'<div class="z-ai"><h3>IA ZOLA</h3><p>{ai_text}</p></div>', unsafe_allow_html=True)
    with c2:
        ev_text = 'Modelo activo' if bet['ev'] is None else f"EV {bet['ev']:.3f}"
        st.markdown(f'''<div class="z-ai"><h3>Mejor cuota del momento</h3><p><b>{bet['label']}</b></p><p style="font-size:30px;font-weight:900;color:#fff">{bet['odd']}</p><p>{ev_text}</p><p>Operador: {bet['bookmaker'] or 'Mercado sin operador'}</p></div>''', unsafe_allow_html=True)

    row1,row2 = st.columns([1.35, .85], gap='medium')
    with row1:
        st.markdown('<div class="z-card"><h3 class="z-section-title" style="font-size:22px">Mercados principales</h3>', unsafe_allow_html=True)
        data = [
            ['Gana local', model['home_win'], odds.get('team_a_win') if not pd.isna(odds.get('team_a_win')) else round(1/max(model['home_win'],0.05),2)],
            ['Empate', model['draw'], odds.get('draw') if not pd.isna(odds.get('draw')) else round(1/max(model['draw'],0.05),2)],
            ['Gana visita', model['away_win'], odds.get('team_b_win') if not pd.isna(odds.get('team_b_win')) else round(1/max(model['away_win'],0.05),2)],
            ['Over 2.5', model['over25'], odds.get('over_2_5') if not pd.isna(odds.get('over_2_5')) else round(1/max(model['over25'],0.05),2)],
            ['BTTS Sí', model['btts'], round(1/max(model['btts'],0.05),2)],
        ]
        df=pd.DataFrame(data, columns=['Mercado','Modelo','Cuota'])
        df['EV']=df.apply(lambda r: expected_value(r['Modelo'], r['Cuota']), axis=1)
        st.dataframe(df.style.format({'Modelo':'{:.1%}','Cuota':'{:.2f}','EV':'{:.3f}'}), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with row2:
        st.markdown('<div class="z-card"><h3 class="z-section-title" style="font-size:22px">Resumen rápido</h3>', unsafe_allow_html=True)
        st.markdown(f'''<div class="z-grid-4">
          <div class="z-kpi"><div class="t">Over 2.5</div><div class="v">{model['over25']:.1%}</div></div>
          <div class="z-kpi"><div class="t">BTTS</div><div class="v">{model['btts']:.1%}</div></div>
          <div class="z-kpi"><div class="t">Dominancia</div><div class="v">{model['dominance']:.2f}</div></div>
          <div class="z-kpi"><div class="t">Marcador IA</div><div class="v">{model['best_score']}</div></div>
        </div>''', unsafe_allow_html=True)
        winner = model['home'] if model['home_win'] > max(model['draw'], model['away_win']) else model['away'] if model['away_win']>model['draw'] else 'Empate'
        st.markdown(f"<div style='margin-top:14px' class='z-badge-green'>Lectura principal: {winner} con score base {model['best_score']}.</div>", unsafe_allow_html=True)
        if model['status'] in LIVE_CODES:
            st.markdown(f"<div style='margin-top:12px' class='z-badge-blue'>Recalculo live activo al minuto {int(model['minute'] or 0)} con marcador {model['score_now']}.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    row3,row4 = st.columns([1.1,.9], gap='medium')
    with row3:
        st.markdown('<div class="z-card"><h3 class="z-section-title" style="font-size:22px">Top marcadores</h3>', unsafe_allow_html=True)
        df = pd.DataFrame(model['top_scores'], columns=['Marcador','Probabilidad'])
        st.dataframe(df.style.format({'Probabilidad':'{:.1%}'}), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with row4:
        st.markdown('<div class="z-card"><h3 class="z-section-title" style="font-size:22px">Comparativa de equipos</h3>', unsafe_allow_html=True)
        df = pd.DataFrame([
            ['Tiros', model['stats_home']['total_shots'], model['stats_away']['total_shots']],
            ['Tiros al arco', model['stats_home']['shots_on_goal'], model['stats_away']['shots_on_goal']],
            ['Posesión', model['stats_home']['possession'], model['stats_away']['possession']],
            ['Corners', model['stats_home']['corners'], model['stats_away']['corners']],
            ['Amarillas', model['stats_home']['yellow'], model['stats_away']['yellow']],
            ['Rojas', model['stats_home']['red'], model['stats_away']['red']],
        ], columns=['Indicador', model['home'], model['away']])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

render_header()
settings_popover()

api_football_key = get_secret('API_FOOTBALL_KEY','api_football_key_override')
odds_api_key = get_secret('THE_ODDS_API_KEY','odds_api_key_override')
openai_key = get_secret('OPENAI_API_KEY','openai_api_key_override')

# Controls
status_tab = st.radio('Estado', ['En vivo','Hoy','Mañana'], horizontal=True, label_visibility='collapsed')
base_day = date.today() if status_tab != 'Mañana' else date.today()+timedelta(days=1)
fixtures = fetch_fixtures(api_football_key, base_day)
if status_tab == 'En vivo':
    fixtures = [f for f in fixtures if f.get('fixture',{}).get('status',{}).get('short','') in LIVE_CODES]
# today includes all except maybe live if empty still okay
if not fixtures and status_tab == 'En vivo':
    st.warning('No encontré partidos en vivo para esa fecha.')

left,right = st.columns([.88,1.42], gap='medium')
with left:
    st.markdown('<div class="z-card">', unsafe_allow_html=True)
    st.markdown('<h3 class="z-section-title" style="font-size:22px">Competiciones y partidos</h3>', unsafe_allow_html=True)
    saved = get_saved_matches(8)
    if not saved.empty:
        chips = ' '.join([f"<span class='z-competition-chip'>{row['league']}</span>" for _,row in saved.drop_duplicates('league').iterrows()][:6])
        st.markdown(chips, unsafe_allow_html=True)
    render_match_list(fixtures)
    st.markdown('</div>', unsafe_allow_html=True)
with right:
    selected = find_selected_fixture(fixtures)
    if not selected:
        st.markdown('<div class="z-card"><h3 class="z-section-title">Centro de análisis</h3><p class="z-sub">Selecciona un partido del panel izquierdo. Si no aparece nada, revisa tu API-Football en Configuración.</p></div>', unsafe_allow_html=True)
    else:
        fid = selected.get('fixture',{}).get('id')
        stats_rows = fetch_statistics(api_football_key, fid)
        lineups = fetch_lineups(api_football_key, fid)
        model = compute_live_model(selected, stats_rows, lineups)
        odds = fetch_odds_event(odds_api_key, st.selectbox('Mercado base', SPORT_KEY_SUGGESTIONS, index=0), model['home'], model['away'])
        bet = best_bet(model, odds, DEFAULT_BANKROLL)
        ai_text = generate_ai_summary(model, bet, openai_key)
        render_analysis(model, odds, ai_text, bet)
