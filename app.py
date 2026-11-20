import math
import re
from statistics import NormalDist
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='NFL Prop Lab | Underdog Research', page_icon='🏈', layout='wide')
st.markdown("""<style>
/* NFL Prop Lab — dark research workstation */
:root {color-scheme:dark}
.stApp {background:radial-gradient(ellipse 70% 35% at 60% -12%,rgba(45,105,103,.17),transparent),#090e17;color:#eaf0f7}
.block-container {max-width:1530px;padding-top:1.05rem;padding-bottom:4rem}
section[data-testid="stSidebar"] {background:#101827;border-right:1px solid #26344b}
section[data-testid="stSidebar"] .block-container {padding-top:1rem}
h1,h2,h3 {letter-spacing:-.045em!important;color:#f4f8fc}
h1 {font-size:2rem!important}h2 {font-size:1.45rem!important}h3 {font-size:1.14rem!important}
p, .stCaption {color:#b5c2d5}
[data-testid="stMetric"] {background:linear-gradient(145deg,#152238,#101a2b);border:1px solid #2a3a53;border-radius:16px;padding:18px 20px;box-shadow:0 9px 28px rgba(0,0,0,.13)}
[data-testid="stMetricLabel"] {color:#9fb0c8}
[data-testid="stMetricValue"] {color:#f7fafc;font-weight:750;letter-spacing:-.05em}
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:5px;border-bottom:1px solid #2a394f;overflow-x:auto}
[data-testid="stTabs"] button {background:#121c2b;border:1px solid #26364d;border-radius:10px 10px 0 0;color:#b6c5d9;font-weight:650;padding:11px 14px}
[data-testid="stTabs"] button[aria-selected="true"] {background:#193b3d;color:#9ef5db;border-color:#317d73}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background:#58d7b8}
[data-testid="stDataFrame"] {border:1px solid #26374d;border-radius:12px;overflow:hidden}
[data-testid="stImage"] img {border-radius:16px;background:#1a2637}
[data-testid="stExpander"] {background:#111c2b;border:1px solid #2a3b50;border-radius:12px}
.stButton button, .stDownloadButton button {border-radius:10px;font-weight:650;border:1px solid #3d796f}
[data-baseweb="select"]>div,[data-baseweb="input"]>div {border-radius:10px;background:#152235}
hr {border-color:#26364b!important}
.nfl-brand {display:flex;align-items:center;gap:13px;margin-bottom:4px}
.nfl-mark {width:46px;height:46px;border-radius:13px;background:linear-gradient(145deg,#1d8e7a,#123d5b);display:flex;align-items:center;justify-content:center;font-size:26px;box-shadow:0 7px 24px #061414}
.nfl-name {font-weight:850;font-size:27px;letter-spacing:-1.3px;color:#f3f8ff;line-height:1.1}
.nfl-sub {font-size:12px;letter-spacing:1.1px;text-transform:uppercase;color:#72d8bd;font-weight:700}
.nfl-pill {display:inline-block;background:#14392f;border:1px solid #276f58;color:#8be8c4;padding:5px 10px;border-radius:999px;font-size:12px;font-weight:650;margin:0 6px 10px 0}
.nfl-muted-pill {background:#18253a;border-color:#31445d;color:#afc3df}
.profile-shell {padding:18px 22px;border-radius:18px;background:linear-gradient(120deg,#15283b,#101a2a);border:1px solid #2c4960;margin:8px 0 17px}
.profile-eyebrow {text-transform:uppercase;color:#6dd7c0;font-weight:750;letter-spacing:1.2px;font-size:11px}

/* V18 workspace redesign: dense, navigable, less vertical chrome */
.block-container {max-width:1640px!important;padding-top:.7rem!important}
section[data-testid="stSidebar"] {min-width:265px;max-width:300px}
section[data-testid="stSidebar"] [data-testid="stRadio"] label {font-size:.89rem}
section[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {gap:4px}
section[data-testid="stSidebar"] [data-testid="stRadio"] [role="radio"] {accent-color:#58d7b8}
[data-testid="stVerticalBlock"] {gap:.62rem}
[data-testid="stMetric"] {padding:11px 14px;border-radius:11px;min-height:85px}
[data-testid="stMetricValue"] {font-size:1.65rem}
[data-testid="stPlotlyChart"] {border:1px solid #253950;border-radius:13px;overflow:hidden}
[data-testid="stSelectbox"] label,[data-testid="stMultiSelect"] label {font-size:.82rem;font-weight:650}
[data-testid="stDataFrame"] {background:#111b2b}
.workspace-kicker {font-size:10px;letter-spacing:1.8px;color:#57cdb2;font-weight:800;margin:6px 0}
.hero-title {font-size:26px;font-weight:850;letter-spacing:-.9px;color:#f5f8fd}
.hero-sub {font-size:13px;color:#99abc4;margin-top:3px;margin-bottom:14px}
.quick-tag {display:inline-block;background:#1b2b40;color:#c9d8eb;border:1px solid #30445e;border-radius:9px;padding:6px 10px;margin-right:6px;font-size:12px}

/* V19 compact dark prop dashboard inspired by the supplied reference layout */
.stApp {background:#080a0d!important;color:#f3f4f6!important}
.block-container {max-width:1720px!important;padding:0.65rem 1.2rem 2rem!important}
section[data-testid="stSidebar"] {background:#0d1014!important;border-right:1px solid #24272b!important;min-width:235px!important;max-width:255px!important}
[data-testid="stVerticalBlock"] {gap:.4rem!important}
h1,h2,h3 {letter-spacing:-.035em!important} h1{font-size:1.55rem!important} h2{font-size:1.18rem!important} h3{font-size:1.03rem!important}
[data-testid="stMetric"] {background:#111417!important;border:1px solid #22282c!important;border-radius:10px!important;padding:9px 12px!important;min-height:70px!important;box-shadow:none!important}
[data-testid="stMetricValue"] {font-size:1.38rem!important;color:#f8fafc!important}
[data-testid="stMetricLabel"] {font-size:.72rem!important}
[data-testid="stPlotlyChart"] {background:#0d0f12!important;border:1px solid #22262b!important;border-radius:13px!important}
[data-testid="stExpander"] {background:#111417!important;border:1px solid #24282d!important}
[data-testid="stDataFrame"] {border:1px solid #252a2e!important}
.stButton button {border-radius:9px!important;background:#161a1e!important;border:1px solid #31373c!important}
.stButton button[kind="primary"] {background:#14cda1!important;color:#08110f!important}
[data-baseweb="select"]>div,[data-baseweb="input"]>div {background:#161a1e!important;border:1px solid #292e33!important}
.nfl-brand {margin-bottom:2px!important}.nfl-mark {background:#132c2a!important;width:35px!important;height:35px!important;font-size:19px!important;box-shadow:none!important}
.nfl-name {font-size:19px!important}.nfl-sub {font-size:9px!important;color:#45d2ae!important}
.nfl-pill {font-size:10px!important;padding:3px 8px!important;margin-bottom:5px!important;background:#103027!important;border-color:#1f5547!important}
.nfl-muted-pill {background:#161b20!important;border-color:#2b3238!important;color:#9aa7b4!important}
.workspace-kicker {color:#49cfae!important}.hero-title {font-size:23px!important}.hero-sub{margin-bottom:7px!important}
[data-testid="stRadio"] [role="radiogroup"] {gap:2px!important}
[data-testid="stRadio"] label {padding:4px 0!important}
.profile-eyebrow {color:#48d5ad!important}
/* V20: compact app shell and always-accessible navigation */
section[data-testid="stSidebar"] {height:100vh!important;overflow-y:auto!important}
section[data-testid="stSidebar"] > div {height:100vh!important;overflow-y:auto!important}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.35rem!important}
[data-testid="stSidebarNav"] {position:sticky;top:0}
.block-container {padding-top:.35rem!important}
.nfl-brand {display:none!important}
.nfl-pill {display:none!important}
[data-testid="stSelectbox"] {margin-bottom:0!important}
[data-testid="stMultiSelect"] {margin-bottom:0!important}
[data-testid="stMetric"] {min-height:60px!important;padding:7px 10px!important}
[data-testid="stMetricValue"] {font-size:1.23rem!important}
[data-testid="stExpander"] details summary {padding:7px 11px!important}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="nfl-brand"><div class="nfl-mark">🏈</div><div><div class="nfl-name">NFL PROP LAB</div><div class="nfl-sub">Player prop research workstation</div></div></div>', unsafe_allow_html=True)
st.markdown("""<style>
/* V22 — high-density interactive prop terminal */
.block-container{padding-top:2.95rem!important;max-width:1850px!important;padding-left:1rem!important;padding-right:1rem!important}
header[data-testid="stHeader"]{height:2.45rem!important;background:#090b10!important}
.stApp{background:#080a10!important}
[data-testid="stVerticalBlock"]{gap:.32rem!important}
[data-testid="stHorizontalBlock"]{gap:.55rem!important}
[data-testid="stSelectbox"]>div,[data-testid="stNumberInput"]>div{min-height:32px!important}
[data-testid="stSelectbox"] [data-baseweb="select"]>div{min-height:33px!important;border-radius:8px!important}
[data-testid="stWidgetLabel"]{margin-bottom:1px!important}
[data-testid="stWidgetLabel"] p{font-size:9px!important;letter-spacing:.08em!important}
[data-testid="stPills"] button,[data-testid="stSegmentedControl"] button{background:#171b26!important;border:1px solid #303747!important;color:#bdc7d8!important;border-radius:8px!important;padding:5px 11px!important;font-weight:750!important}
[data-testid="stPills"] button[aria-pressed="true"],[data-testid="stSegmentedControl"] button[aria-checked="true"]{background:#173c35!important;color:#64e6bc!important;border-color:#279f80!important}
[data-testid="stPlotlyChart"]{border:1px solid #242b39!important;border-radius:13px!important}
[data-testid="stDataFrame"]{border-radius:10px!important}
.profile-title{font-size:33px!important;letter-spacing:-1.15px!important;line-height:1.03!important}
.profile-title span{font-size:13px!important;color:#8ee7d2!important}
.profile-sub{font-size:11px!important}
.mini-score{min-height:58px!important;padding:8px 11px!important;background:#111723!important;border:1px solid #263044!important;border-radius:10px!important}
.mini-score strong{font-size:23px!important;letter-spacing:-.6px!important}
.compact-section{margin:7px 0 4px!important;font-size:11px!important;letter-spacing:.07em!important}
.defense-stat{padding:9px 10px!important;border-radius:8px!important;background:#111722!important;border:1px solid #263044!important;margin:3px 0!important;display:flex;align-items:center;justify-content:space-between;gap:8px}
.defense-stat span{font-size:12px!important;flex:1}
.defense-stat strong{font-size:22px!important;color:#f2f5fa!important}
.defense-stat b{font-size:15px!important}
.profile-rail-title{font-size:12px;font-weight:850;color:#e7f0fa;letter-spacing:.07em;margin:8px 0 5px}
.profile-note{font-size:10px;color:#7f8da2}
[data-testid="stPopover"] button{border-radius:8px!important}
section[data-testid="stSidebar"]{position:sticky!important;top:0!important;height:100vh!important;overflow-y:auto!important}
@media(max-width:850px){.profile-title{font-size:25px!important}.block-container{padding-left:.6rem!important;padding-right:.6rem!important}}
</style>""",unsafe_allow_html=True)
st.markdown('<span class="nfl-pill">UNDERDOG HIGHER / LOWER</span><span class="nfl-pill nfl-muted-pill">OFFENSE + KICKERS</span><span class="nfl-pill nfl-muted-pill">HISTORICAL MATCHUP RESEARCH</span>', unsafe_allow_html=True)

st.markdown("""<style>
/* V21 compact, fixed-height workstation */
.block-container{padding-top:2.7rem!important;padding-bottom:1.2rem!important;max-width:1800px!important}
header[data-testid="stHeader"]{background:#0b0d10!important;height:2.4rem!important}
[data-testid="stAppViewContainer"]{background:#080b10!important}
section[data-testid="stSidebar"]{min-width:225px!important;max-width:250px!important}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.35rem!important}
[data-testid="stVerticalBlock"]{gap:.45rem!important}
[data-testid="stHorizontalBlock"]{gap:.6rem!important}
[data-testid="stWidgetLabel"] p{font-size:10px!important;letter-spacing:.07em;color:#91a2b5!important;text-transform:uppercase}
[data-testid="stSelectbox"]{margin-bottom:0!important}
[data-testid="stMetric"]{padding:8px!important}
[data-testid="stExpander"]{border-color:#232a35!important}
[data-testid="stPlotlyChart"]{margin:0!important}
.profile-title{font-size:23px;line-height:1.15;font-weight:850;color:#f4f7fa;letter-spacing:-.5px}
.profile-title span{font-size:12px;font-weight:600;color:#68d4bd;letter-spacing:0;margin-left:10px}
.profile-sub{font-size:11px;color:#8c9eaf;margin-top:4px}
.mini-score{border:1px solid #242d38;background:#111820;border-radius:9px;padding:8px 10px;min-height:58px}
.mini-score small{display:block;color:#92a3b4;font-size:10px;margin-bottom:3px}
.mini-score strong{display:block;color:#f5f8fc;font-size:21px;line-height:1.1}
.compact-section{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #26303b;margin:9px 0 5px;padding-bottom:5px;font-weight:800;font-size:12px;color:#f1f6f9;letter-spacing:.05em}
.compact-section span{font-size:10px;letter-spacing:0;font-weight:500;color:#92a5b4}
.defense-stat{display:grid;grid-template-columns:1fr 55px 63px;align-items:center;gap:6px;border-bottom:1px solid #242b33;padding:7px 4px;font-size:11px;color:#b8c4d0}
.defense-stat strong{font-size:14px;text-align:right;color:#f4f8fc}
.defense-stat b{text-align:right;font-size:11px}
[data-testid="stCaptionContainer"] p{font-size:10px!important;line-height:1.3!important}
</style>""", unsafe_allow_html=True)

MARKETS = {'passing_yards':'Passing yards','passing_tds':'Passing TDs','pass_attempts':'Pass attempts','completions':'Pass completions','interceptions':'Interceptions','rushing_yards':'Rushing yards','carries':'Rushing attempts','rushing_tds':'Rushing TDs','receiving_yards':'Receiving yards','receptions':'Receptions','targets':'Targets','receiving_tds':'Receiving TDs','rush_rec_yards':'Rush + receiving yards','rush_rec_tds':'Rush + receiving TDs','longest_reception':'Longest reception','longest_rush':'Longest rush','field_goals':'Field goals','extra_points':'Extra points'}
# Normalize provider labels without assuming every offered market has nflverse data.
MARKET_ALIASES = {
    "pass_yds":"passing_yards", "pass_yards":"passing_yards", "passing_yds":"passing_yards",
    "passing_yard":"passing_yards", "pass_td":"passing_tds", "pass_tds":"passing_tds",
    "passing_touchdowns":"passing_tds", "pass_touchdowns":"passing_tds",
    "passing_attempts":"pass_attempts", "pass_att":"pass_attempts", "pass_completions":"completions",
    "passing_completions":"completions", "completions":"completions", "pass_int":"interceptions",
    "passing_interceptions":"interceptions", "interceptions_thrown":"interceptions",
    "rush_yds":"rushing_yards", "rush_yards":"rushing_yards", "rushing_yds":"rushing_yards",
    "rush_attempts":"carries", "rushing_attempts":"carries", "rush_att":"carries",
    "rush_tds":"rushing_tds", "rushing_touchdowns":"rushing_tds",
    "rec_yds":"receiving_yards", "receiving_yds":"receiving_yards", "rec_yards":"receiving_yards",
    "rec":"receptions", "catches":"receptions", "receptions":"receptions",
    "rec_tds":"receiving_tds", "receiving_touchdowns":"receiving_tds",
    "rush_rec_yds":"rush_rec_yards", "rushing_receiving_yards":"rush_rec_yards",
    "rushing_and_receiving_yards":"rush_rec_yards", "rush_plus_rec_yards":"rush_rec_yards",
    "rush_rec_touchdowns":"rush_rec_tds", "rushing_receiving_tds":"rush_rec_tds",
}
def normalized_market(value):
    key = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
    return MARKET_ALIASES.get(key, key)

def normalized_player(value):
    # Names can differ by punctuation, suffix, or spacing between providers.
    name = re.sub(r"[^a-z0-9 ]", " ", str(value).lower())
    name = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", name)
    return re.sub(r"\s+", " ", name).strip()

@st.cache_data(ttl=21600, show_spinner="Loading NFL weekly statistics...")
def fetch_nfl_stats(seasons):
    import nflreadpy as nfl
    frames = nfl.load_player_stats(seasons=list(seasons), summary_level="week")
    frame = frames.to_pandas() if hasattr(frames, "to_pandas") else pd.DataFrame(frames)
    if frame.empty:
        raise ValueError("NFL source returned no weekly player statistics")
    def first(names):
        return next((n for n in names if n in frame.columns), None)
    player_col = first(["player_display_name", "player_name", "player", "player_id"])
    week_col = first(["week"])
    date_col = first(["game_date", "gameday", "date"])
    opponent_col = first(["opponent_team", "opponent"])
    if player_col is None:
        raise ValueError("NFL data did not include a recognizable player field")
    out = pd.DataFrame({"player": frame[player_col].astype(str)})
    out["season"] = pd.to_numeric(frame["season"], errors="coerce") if "season" in frame else pd.NA
    out["week"] = pd.to_numeric(frame["week"], errors="coerce") if "week" in frame else pd.NA
    team_col = first(["recent_team", "team", "posteam"])
    out["team"] = frame[team_col].astype(str) if team_col else "Unknown"
    if date_col:
        out["game_date"] = pd.to_datetime(frame[date_col], errors="coerce")
    elif "season" in frame and week_col:
        # Date is used for chronological ordering; season/week preserves that order.
        out["game_date"] = pd.to_datetime(frame["season"].astype(str) + "-01-01", errors="coerce") + pd.to_timedelta(pd.to_numeric(frame[week_col], errors="coerce").fillna(0) * 7, unit="D")
    else:
        raise ValueError("NFL data did not include season/week or game date")
    out["opponent"] = frame[opponent_col].astype(str) if opponent_col else "Unknown"
    mapping = {
        "passing_yards":["passing_yards"], "passing_tds":["passing_tds"],
        "pass_attempts":["attempts", "passing_attempts"],
        "completions":["completions", "passing_completions"],
        "interceptions":["interceptions", "passing_interceptions"],
        "rushing_yards":["rushing_yards"], "carries":["carries", "rushing_attempts"],
        "rushing_tds":["rushing_tds"], "receiving_yards":["receiving_yards"],
        "receptions":["receptions"], "targets":["targets"],
        "receiving_tds":["receiving_tds"]
    }
    for dest, candidates in mapping.items():
        source = first(candidates)
        if source:
            out[dest] = pd.to_numeric(frame[source], errors="coerce")
    if {"rushing_yards", "receiving_yards"}.issubset(out.columns):
        out["rush_rec_yards"] = out["rushing_yards"].fillna(0) + out["receiving_yards"].fillna(0)
    if {"rushing_tds", "receiving_tds"}.issubset(out.columns):
        out["rush_rec_tds"] = out["rushing_tds"].fillna(0) + out["receiving_tds"].fillna(0)
    return out.dropna(subset=["player", "game_date"]).sort_values(["season", "week", "game_date"], na_position="last")

@st.cache_data(ttl=21600, show_spinner="Loading NFL schedule...")
def fetch_schedule(seasons):
    import nflreadpy as nfl
    frames = nfl.load_schedules(seasons=list(seasons))
    schedule = frames.to_pandas() if hasattr(frames, "to_pandas") else pd.DataFrame(frames)
    needed = {"season", "week", "home_team", "away_team"}
    if not needed.issubset(schedule.columns):
        raise ValueError("Schedule source is missing game identifiers")
    schedule = schedule.copy()
    schedule["season"] = pd.to_numeric(schedule["season"], errors="coerce")
    schedule["week"] = pd.to_numeric(schedule["week"], errors="coerce")
    if "game_type" in schedule:
        schedule = schedule[schedule["game_type"].astype(str).eq("REG")]
    if "gameday" in schedule:
        schedule["kickoff"] = pd.to_datetime(schedule["gameday"], errors="coerce")
    else:
        schedule["kickoff"] = pd.NaT
    schedule["matchup"] = schedule["away_team"].astype(str) + " @ " + schedule["home_team"].astype(str)
    return schedule.sort_values(["season", "week", "kickoff"])

OFFENSIVE_POSITIONS = {"QB", "RB", "WR", "TE", "K", "PK", "FB"}
DEFENSIVE_MARKET_TERMS = ("tackle", "sack", "defensive", "interception_return", "passes_defended", "forced_fumble", "fumble_recovery", "defense", "dst")

def offensive_market(market):
    key = normalized_market(market)
    return not any(term in key for term in DEFENSIVE_MARKET_TERMS)

@st.cache_data(ttl=21600, show_spinner="Loading current NFL rosters...")
def fetch_current_rosters(season):
    import nflreadpy as nfl
    raw = nfl.load_rosters(seasons=[int(season)])
    roster = raw.to_pandas() if hasattr(raw, "to_pandas") else pd.DataFrame(raw)
    if roster.empty:
        raise ValueError("Roster source returned no players")
    pos_col = next((c for c in ("position", "position_group", "pos") if c in roster), None)
    name_col = next((c for c in ("full_name", "player_name", "player_display_name", "player", "name") if c in roster), None)
    team_col = next((c for c in ("team", "team_abbr", "recent_team") if c in roster), None)
    if not pos_col or not name_col:
        raise ValueError("Roster fields for player names or positions were unavailable")
    roster = roster[roster[pos_col].astype(str).str.upper().isin(OFFENSIVE_POSITIONS)].copy()
    roster["_player_key"] = roster[name_col].map(normalized_player)
    roster["roster_player"] = roster[name_col].astype(str)
    roster["roster_position"] = roster[pos_col].astype(str).str.upper()
    roster["roster_team"] = roster[team_col].astype(str) if team_col else ""
    # nflverse roster feeds may expose a player portrait under different column names.
    photo_col = next((c for c in ("headshot_url", "headshot", "headshot_href", "player_headshot", "espn_headshot") if c in roster.columns), None)
    roster["roster_headshot"] = roster[photo_col].astype("string") if photo_col else pd.Series(pd.NA, index=roster.index, dtype="string")
    # A roster entry is not proof of being healthy or scheduled to play.
    return roster[["_player_key", "roster_player", "roster_position", "roster_team", "roster_headshot"]].drop_duplicates("_player_key")

@st.cache_data(ttl=21600, show_spinner="Loading NFL injury reports...")
def fetch_injury_reports(season):
    import nflreadpy as nfl
    raw = nfl.load_injuries(seasons=[int(season)])
    df = raw.to_pandas() if hasattr(raw, "to_pandas") else pd.DataFrame(raw)
    if df.empty:
        return df
    # Preserve original source fields; schemas vary by nflverse release.
    return df


@st.cache_data(ttl=86400, show_spinner="Loading free FTN play charting...")
def fetch_ftn_charting(season):
    import nflreadpy as nfl
    loader = getattr(nfl, "load_ftn_charting", None)
    if loader is None:
        raise RuntimeError("Installed nflreadpy does not expose load_ftn_charting")
    raw = loader(seasons=[int(season)])
    data = raw.to_pandas() if hasattr(raw, "to_pandas") else pd.DataFrame(raw)
    return data



@st.cache_data(ttl=86400, show_spinner="Matching FTN plays to nflverse play-by-play...")
def fetch_pbp_defense_keys(season):
    import nflreadpy as nfl
    raw = nfl.load_pbp(seasons=[int(season)])
    pbp = raw.to_pandas() if hasattr(raw, "to_pandas") else pd.DataFrame(raw)
    cols = [c for c in ("game_id", "play_id", "defteam", "posteam") if c in pbp.columns]
    if not {"game_id", "play_id", "defteam"}.issubset(cols):
        raise ValueError("Play-by-play source does not expose game_id, play_id and defteam")
    return pbp[cols].dropna(subset=["game_id", "play_id"]).drop_duplicates(["game_id", "play_id"])

def ftn_defense_summary(data, team, schedule_data=None, pbp_keys=None):
    """Only compute explicitly identified charting fields; no guessed coverage labels."""
    if data is None or data.empty or not team:
        return pd.DataFrame(), "No FTN charting rows available."
    df = data.copy()
    team_field = next((x for x in ("defteam", "defense_team", "defensive_team", "def_team") if x in df), None)
    # FTN charting commonly identifies game/play, not the defensive team.
    # Join only on exact play keys; never assign a defense based on a guess.
    if team_field is None and pbp_keys is not None and not pbp_keys.empty:
        game_key = next((c for c in ("game_id", "nflverse_game_id") if c in df), None)
        play_key = next((c for c in ("play_id", "nflverse_play_id") if c in df), None)
        if game_key and play_key:
            lookup = pbp_keys[["game_id", "play_id", "defteam"]].copy()
            left = df.copy()
            left["_join_game"] = left[game_key].astype(str).str.strip()
            left["_join_play"] = pd.to_numeric(left[play_key], errors="coerce").astype("Int64")
            lookup["_join_game"] = lookup["game_id"].astype(str).str.strip()
            lookup["_join_play"] = pd.to_numeric(lookup["play_id"], errors="coerce").astype("Int64")
            lookup = lookup.dropna(subset=["_join_play"]).drop_duplicates(["_join_game", "_join_play"])
            df = left.merge(lookup[["_join_game", "_join_play", "defteam"]], on=["_join_game", "_join_play"], how="left", validate="many_to_one")
            team_field = "defteam"

    if team_field is None and schedule_data is not None and not schedule_data.empty:
        game_field = next((x for x in ("nflverse_game_id", "game_id") if x in df), None)
        schedule_game = next((x for x in ("game_id", "nflverse_game_id") if x in schedule_data), None)
        offense_field = next((x for x in ("posteam", "offense_team", "offensive_team") if x in df), None)
        if game_field and schedule_game and offense_field and {"home_team", "away_team"}.issubset(schedule_data.columns):
            teams = schedule_data[[schedule_game, "home_team", "away_team"]].drop_duplicates(schedule_game)
            df = df.merge(teams, left_on=game_field, right_on=schedule_game, how="left", suffixes=("", "_schedule"))
            df["_resolved_defense"] = np.where(df[offense_field].eq(df["home_team"]), df["away_team"],
                np.where(df[offense_field].eq(df["away_team"]), df["home_team"], None))
            team_field = "_resolved_defense"
    if team_field is None:
        return pd.DataFrame(), "Charting data has no identifiable defense-team field; cannot safely attribute plays."
    df = df[df[team_field].astype(str).str.upper().eq(str(team).upper())].copy()
    if df.empty:
        return pd.DataFrame(), "No charted plays matched this defense."
    # Only explicit boolean flags. Generic 'pressure' text, front numbers and coverage codes
    # are not interpreted without a documented schema.
    known_flags = {
        "Blitz": ("is_blitz", "blitz"),
        "Pressure": ("is_pressure", "pressure"),
        "Man coverage": ("is_man_coverage",),
        "Zone coverage": ("is_zone_coverage",),
    }
    metrics=[]
    for label, candidates in known_flags.items():
        field = next((c for c in candidates if c in df), None)
        if field is None:
            continue
        raw = df[field]
        normalized = raw.astype(str).str.strip().str.lower().map({"true":1,"false":0,"1":1,"0":0,"yes":1,"no":0})
        valid = normalized.dropna()
        if len(valid) < 10:
            continue
        metrics.append({"Charted tendency":label, "Rate":f"{valid.mean():.1%}", "Charted plays":len(valid), "Source field":field})
    if not metrics:
        return pd.DataFrame(), f"{len(df):,} charted plays found, but no validated binary scheme flags were recognized."
    return pd.DataFrame(metrics), f"{len(df):,} matching charting records. Percentages use nonmissing flags only."


def injury_team_view(injuries, team, season, week=None):
    if injuries is None or injuries.empty or not team:
        return pd.DataFrame(), "No injury reports returned for this season."
    data = injuries.copy()
    team_col = next((c for c in ("team", "team_abbr", "club_code") if c in data.columns), None)
    if team_col is None:
        return pd.DataFrame(), "Injury report does not expose a recognized team field."
    data = data[data[team_col].astype(str).str.upper().eq(str(team).upper())].copy()
    if data.empty:
        return data, "No reported entries for this defense."
    week_col = next((c for c in ("week", "game_week") if c in data.columns), None)
    if week_col:
        data[week_col] = pd.to_numeric(data[week_col], errors="coerce")
        weeks = data[week_col].dropna()
        if not weeks.empty:
            # Never substitute a future week or imply the report is current.
            eligible = weeks[weeks <= int(week)] if week is not None else weeks
            if eligible.empty:
                return pd.DataFrame(), "No published injury reports at or before the selected week."
            latest = int(eligible.max())
            data = data[data[week_col].eq(latest)].copy()
    else:
        latest = None
    name_col = next((c for c in ("full_name", "player_name", "player", "name") if c in data), None)
    pos_col = next((c for c in ("position", "pos") if c in data), None)
    status_col = next((c for c in ("report_status", "game_status", "status", "injury_status") if c in data), None)
    practice_col = next((c for c in ("practice_status", "practice_participation", "practice_status_description") if c in data), None)
    detail_col = next((c for c in ("report_primary_injury", "injury", "primary_injury") if c in data), None)
    keep = [(name_col,"Player"),(pos_col,"Position"),(status_col,"Game status"),(practice_col,"Practice"),(detail_col,"Injury")]
    cols = {col: label for col,label in keep if col is not None}
    if not cols:
        return pd.DataFrame(), "Injury report fields were not recognized."
    result = data[list(cols)].rename(columns=cols)
    if "Practice" in result.columns:
        def practice_abbrev(value):
            if pd.isna(value) or str(value).strip().lower() in ('', 'nan', 'none', 'not reported'):
                return '—'
            v = str(value).strip().lower()
            if v in ('dnp','did not practice','did not participate','did not participate in practice','non participant','not participating') or 'did not practice' in v or 'did not participate' in v:
                return 'DNP'
            if v in ('lp','limited','limited participation','limited participant','limited practice') or 'limited' in v:
                return 'LP'
            if v in ('fp','full','full participation','full participant','full practice') or 'full participation' in v:
                return 'FP'
            return str(value)
        result['Practice'] = result['Practice'].map(practice_abbrev)
    if "Position" in result:
        # Only defensive personnel; include DB position variants and front seven.
        defensive = {"CB","DB","S","FS","SS","LB","ILB","OLB","MLB","DE","DT","DL","NT","EDGE"}
        result = result[result["Position"].astype(str).str.upper().isin(defensive)]
    result = result.drop_duplicates()
    note = f"Latest available report week: {latest}." if latest is not None else "Report week unavailable."
    return result, note

REQUIRED_LOG = ['player','game_date','opponent']
REQUIRED_LINES = ['player','market','line']

def read_csv(upload, required):
    if upload is None: return None
    try:
        frame = pd.read_csv(upload)
        missing = sorted(set(required) - set(frame.columns))
        if missing: st.error('Missing CSV columns: ' + ', '.join(missing)); return None
        return frame
    except Exception as exc:
        st.error(f'Unable to read CSV: {exc}'); return None

@st.cache_data(ttl=86400, show_spinner="Fetching a limited NFL Underdog board page...")
def fetch_underdog_board(api_key):
    # One compact page per 24-hour cache window. Do not automatically paginate.
    import requests
    response = requests.get(
        "https://underdogapi.com/api/v1/projections",
        params={"league": "NFL", "view": "compact", "limit": 100},
        headers={"Authorization": f"Bearer {api_key}",
                 "X-User-Request": "NFL Prop Lab current NFL research board"},
        timeout=25,
    )
    if response.status_code == 429:
        raise RuntimeError("API rate limit or monthly credit allowance reached (HTTP 429). Do not retry until credits are available.")
    response.raise_for_status()
    payload = response.json()
    meta = payload.get("meta") or {}
    if meta.get("is_demo") or str(meta.get("mode", "")).lower() == "demo":
        raise RuntimeError("Provider returned demonstration data, not real Underdog lines.")
    raw_data = payload.get("data", [])
    diagnostics = {
        "payload_keys": sorted(payload.keys()),
        "data_type": type(raw_data).__name__,
        "raw_count": len(raw_data) if isinstance(raw_data, (list, dict)) else 0,
        "first_item_keys": [],
        "nested_keys": {},
        "rejected": {"demo_or_status": 0, "no_available_selection": 0, "missing_player_market_or_line": 0},
    }
    if isinstance(raw_data, dict):
        diagnostics["data_keys"] = sorted(raw_data.keys())
        raw_data = next((raw_data[k] for k in ("items", "results", "projections", "offers") if isinstance(raw_data.get(k), list)), [])
    if not isinstance(raw_data, list):
        raw_data = []
    if raw_data and isinstance(raw_data[0], dict):
        first_item = raw_data[0]
        diagnostics["first_item_keys"] = sorted(first_item.keys())
        diagnostics["nested_keys"] = {k: sorted(v.keys()) for k, v in first_item.items() if isinstance(v, dict)}
        diagnostics["selection_example_keys"] = sorted(first_item["selections"][0].keys()) if isinstance(first_item.get("selections"), list) and first_item["selections"] and isinstance(first_item["selections"][0], dict) else []
    diagnostics["parsed_count"] = len(raw_data)
    rows = []
    for item in raw_data:
        if not isinstance(item, dict):
            continue
        # The compact endpoint exposes player/stat and side availability at the
        # top level. Older code incorrectly expected nested selections objects.
        if item.get("is_demo") is True or str(item.get("status", "")).lower() in {"inactive", "closed", "suspended", "cancelled", "canceled", "settled"}:
            diagnostics["rejected"]["demo_or_status"] += 1
            continue
        if str(item.get("league", "NFL")).upper() != "NFL" and str(item.get("sport", "")).lower() not in {"football", "american_football", "nfl"}:
            diagnostics["rejected"]["demo_or_status"] += 1
            continue
        raw_sides = item.get("sides")
        sides = {}
        if isinstance(raw_sides, dict):
            sides = {str(k).lower(): v for k, v in raw_sides.items()}
        elif isinstance(raw_sides, list):
            sides = {str(v.get("side", v.get("name", ""))).lower(): v for v in raw_sides if isinstance(v, dict)}
        def available(direction):
            top = item.get(direction + "_available")
            if top is not None:
                return top is True or str(top).lower() in ("true", "1", "yes")
            val = sides.get(direction)
            if isinstance(val, dict):
                return val.get("available") is True
            return val is True
        higher_ok = available("higher")
        lower_ok = available("lower")
        if not higher_ok and not lower_ok:
            diagnostics["rejected"]["no_available_selection"] += 1
            continue
        player_raw = item.get("player")
        player_name = player_raw.get("name", player_raw.get("display_name")) if isinstance(player_raw, dict) else player_raw
        market_raw = item.get("stat") or item.get("market")
        stat_name = market_raw.get("stat", market_raw.get("name")) if isinstance(market_raw, dict) else market_raw
        raw_line = item.get("line")
        if raw_line is None or not player_name or not stat_name:
            diagnostics["rejected"]["missing_player_market_or_line"] += 1
            continue
        def multiplier(direction):
            direct = item.get(direction + "_mult")
            if direct is not None:
                return direct
            side = sides.get(direction)
            return side.get("payout_multiplier", side.get("multiplier")) if isinstance(side, dict) else None
        rows.append({
            "player": str(player_name), "team": item.get("team") or (player_raw.get("team") if isinstance(player_raw, dict) else "") or "",
            "market": normalized_market(stat_name), "source_market": str(stat_name),
            "period": item.get("period") or "Unknown", "line": raw_line,
            "updated_at": item.get("observed_at") or meta.get("observed_at") or "Unknown",
            "pick_type": item.get("line_type") or ("special" if item.get("higher_only") or item.get("multiplier_scale") not in (None, 1, 1.0) else "standard"),
            "higher_available": higher_ok, "lower_available": lower_ok,
            "higher_multiplier": multiplier("higher"),
            "lower_multiplier": multiplier("lower"),
            "opponent": item.get("opponent") or "", "starts_at": item.get("starts_at") or "",
            "provider_id": item.get("id") or "",
        })
    columns = ["player", "team", "market", "source_market", "period", "line", "updated_at", "pick_type", "higher_available", "lower_available", "higher_multiplier", "lower_multiplier", "opponent", "starts_at", "provider_id"]
    diagnostics["accepted_count"] = len(rows)
    return pd.DataFrame(rows, columns=columns), meta, response.headers.get("X-Credits-Cost", "Unknown"), diagnostics

NAV_ITEMS = ['🏠 Dashboard', '👤 Player Research', '🏟️ Games', '🏆 Best Bets', '📈 Trends', '⚙️ Data & Model']
with st.sidebar:
    st.markdown('### NFL PROP LAB')
    nav_page = st.radio('Workspace', NAV_ITEMS, index=1, label_visibility='collapsed', key='primary_navigation')
    st.divider()
    with st.expander('Data sources & model settings', expanded=False):
        st.caption('NFL history via nflreadpy; Underdog lines via your private API key. Free API credits are limited.')
        source_mode = st.radio('Historical player data', ['Automatic NFL statistics', 'Upload my own CSV'], index=0)
        if source_mode == 'Automatic NFL statistics':
            selected_seasons = st.multiselect('NFL seasons', [2026, 2025, 2024, 2023], default=[2026])
            st.caption('Source: nflverse via nflreadpy. Weekly statistics may update after games; some markets require other sources.')
            log_upload = None
        else:
            log_upload = st.file_uploader('Player game logs (CSV)', type='csv', key='logs')
        board_mode = st.radio('Underdog lines', ['Automatic API', 'Upload CSV'], index=0)
        lines_upload = st.file_uploader('Underdog projections (CSV)', type='csv', key='lines') if board_mode == 'Upload CSV' else None
        st.markdown('**Optional qualitative matchup inputs**')
        st.caption('Adjustments are research scenarios, not validated prediction improvements.')
        momentum_weight = st.slider('Recent-form weight', 0.0, 0.5, 0.25, 0.05)
        context_shift = st.slider('Manual matchup adjustment (%)', -20, 20, 0, 1)
        st.caption('Positive adjustment raises the estimated stat mean; negative lowers it.')

logs = None
if source_mode == 'Automatic NFL statistics':
    if selected_seasons:
        try:
            logs = fetch_nfl_stats(tuple(sorted(selected_seasons)))
            st.sidebar.success(f'Loaded {len(logs):,} weekly player records')
        except Exception as exc:
            st.sidebar.error(f'Automatic data unavailable: {exc}')
            st.sidebar.info('You can switch to CSV upload while we resolve the data source.')
else:
    logs = read_csv(log_upload, REQUIRED_LOG)
lines = None
board_meta = {}
if board_mode == 'Automatic API':
    api_key = st.secrets.get("UNDERDOG_API_KEY", "")
    if not api_key:
        st.sidebar.error("UNDERDOG_API_KEY is missing from Streamlit Secrets.")
    else:
        try:
            lines, board_meta, credit_cost, board_diagnostics = fetch_underdog_board(api_key)
            if not lines.empty:
                st.sidebar.success(f"Retrieved {len(lines)} observed NFL offers (cached for 24 hours).")
            st.sidebar.caption(f"Source observation: {board_meta.get('observed_at', 'Unknown')} | Request credit cost: {credit_cost}")
            if board_meta.get("next_cursor"):
                st.sidebar.warning("Partial board: additional pages exist. Not fetched automatically to protect free credits.")
            if board_meta.get("source_status") not in ("fresh", "live", "ok", None):
                st.sidebar.warning(f"Provider source status: {board_meta.get('source_status')}")
            if lines.empty:
                st.sidebar.warning("No qualifying NFL offers were recognized. Expand API diagnostics below to identify the mismatch.")
                with st.sidebar.expander("API diagnostics — safe to share", expanded=True):
                    st.json(board_diagnostics)
                    st.caption("Only response field names and counts are shown. No API key, player data, or complete response is displayed.")
        except Exception as exc:
            st.sidebar.error(f"Underdog API unavailable: {exc}")
else:
    lines = read_csv(lines_upload, REQUIRED_LINES)
if logs is not None:
    logs['game_date'] = pd.to_datetime(logs['game_date'], errors='coerce')
    logs = logs.dropna(subset=['game_date','player']).sort_values('game_date')
    for c in MARKETS:
        if c in logs: logs[c] = pd.to_numeric(logs[c], errors='coerce')
if lines is not None and not set(REQUIRED_LINES).issubset(lines.columns):
    st.sidebar.warning('The line source did not return the required player, market, and line fields. No lines will be analyzed.')
    lines = None
if lines is not None:
    lines['line'] = pd.to_numeric(lines['line'], errors='coerce')
    lines['market'] = lines['market'].map(normalized_market)
    lines = lines.dropna(subset=['line','player','market'])
    if 'updated_at' not in lines: lines['updated_at'] = 'Not provided'

# Prefer current roster membership to historical participation. A roster is not an injury report.
current_roster = None
roster_error = None
current_season = max(selected_seasons) if source_mode == 'Automatic NFL statistics' and selected_seasons else None
if current_season is not None:
    try:
        current_roster = fetch_current_rosters(current_season)
    except Exception as exc:
        roster_error = str(exc)
if logs is not None:
    logs["_player_key"] = logs["player"].map(normalized_player)
    if current_roster is not None:
        logs = logs.merge(current_roster, on="_player_key", how="left")
        logs["_current_roster"] = logs["roster_position"].notna()
    else:
        logs["_current_roster"] = logs["season"].eq(current_season) if "season" in logs and current_season is not None else True
if lines is not None:
    lines = lines[lines["market"].map(offensive_market)].copy()
    lines["_player_key"] = lines["player"].map(normalized_player)
    if current_roster is not None:
        lines = lines.merge(current_roster, on="_player_key", how="left")
        # Only explicitly identified defensive roster positions are excluded;
        # unknown names remain visible rather than silently hiding real offers.
    if "team" in lines:
        lines["team"] = lines["team"].fillna("").astype(str).str.upper().str.strip()

# Free nflverse injury data; never call a paid provider for defensive context.
injury_reports = None
injury_error = None
if current_season is not None:
    try:
        injury_reports = fetch_injury_reports(current_season)
    except Exception as exc:
        injury_error = str(exc)

# Shared matchup selector. Selecting a game filters the research and available board.
schedule = None
if source_mode == 'Automatic NFL statistics' and selected_seasons:
    try:
        schedule = fetch_schedule(tuple(sorted(selected_seasons)))
    except Exception as exc:
        st.sidebar.warning(f"Schedule unavailable: {exc}")

with st.sidebar:
    with st.expander("Weekly game filter", expanded=False):
        if schedule is not None and not schedule.empty:
            schedule_seasons = sorted(schedule["season"].dropna().astype(int).unique(), reverse=True)
            filter_season = st.selectbox("Season", schedule_seasons, index=schedule_seasons.index(current_season) if current_season in schedule_seasons else 0, key="game_filter_season")
            available_weeks = sorted(schedule.loc[schedule.season.eq(filter_season), "week"].dropna().astype(int).unique())
            # Default to the current/upcoming regular-season week, not Week 18.
            now_utc = pd.Timestamp.now(tz="UTC")
            season_games = schedule.loc[schedule.season.eq(filter_season)].copy()
            dates = pd.to_datetime(season_games.get("gameday"), errors="coerce", utc=True)
            future_games = season_games.loc[dates.ge(now_utc.normalize())]
            if not future_games.empty:
                suggested_week = int(future_games.assign(_date=dates.loc[future_games.index]).sort_values("_date").iloc[0]["week"])
            else:
                past_games = season_games.loc[dates.notna() & dates.lt(now_utc.normalize())]
                suggested_week = int(past_games.sort_values("week").iloc[-1]["week"]) if not past_games.empty else available_weeks[0]
            filter_week = st.selectbox("Week", available_weeks, index=available_weeks.index(suggested_week), key="game_filter_week")
            week_schedule = schedule[schedule.season.eq(filter_season) & schedule.week.eq(filter_week)].copy()
            game_choices = ["All games"] + week_schedule["matchup"].drop_duplicates().tolist()
            selected_matchup = st.selectbox("Game", game_choices, key="game_filter_matchup")
        else:
            filter_season = None
            filter_week = None
            week_schedule = pd.DataFrame()
            selected_matchup = "All games"
            st.caption("Weekly games appear after a schedule is loaded.")

# Preserve the complete historical dataset for player research; use the selector for slate views.
slate_logs = logs.copy() if logs is not None else None
slate_lines = lines.copy() if lines is not None else None
selected_teams = None
if selected_matchup != "All games" and not week_schedule.empty:
    game_row = week_schedule[week_schedule.matchup.eq(selected_matchup)].iloc[0]
    selected_teams = {str(game_row["home_team"]), str(game_row["away_team"])}
if slate_logs is not None and filter_season is not None and "season" in slate_logs:
    # Do not filter historical samples to the current week; that would cause look-ahead bias
    # and erase the observations needed for player research.
    pass
if slate_lines is not None and selected_teams is not None and "team" in slate_lines:
    slate_lines = slate_lines[slate_lines["team"].astype(str).isin(selected_teams)]

@st.cache_data(show_spinner=False)
def analyze(log_bytes, line_bytes, weight, adjustment):
    history = pd.read_csv(pd.io.common.BytesIO(log_bytes))
    board = pd.read_csv(pd.io.common.BytesIO(line_bytes))
    history['game_date'] = pd.to_datetime(history['game_date'], errors='coerce')
    history = history.dropna(subset=['game_date']).sort_values('game_date')
    history['_player_key'] = history['player'].map(normalized_player)
    board['line'] = pd.to_numeric(board['line'], errors='coerce')
    rows=[]
    for _, pick in board.iterrows():
        player=str(pick['player']); market=normalized_market(pick['market']); line=pick['line']
        if not offensive_market(market) or market not in history or not np.isfinite(line): continue
        if str(pick.get('period', 'Full game')).lower() not in ('full game', 'full_game', 'game', 'unknown'): continue
        player_rows = history.loc[history['_player_key'].eq(normalized_player(player))]
        # Only use observations before the offer's scheduled start.
        start = pd.to_datetime(pick.get('starts_at'), errors='coerce', utc=True)
        if pd.notna(start):
            game_dates = pd.to_datetime(player_rows['game_date'], errors='coerce', utc=True)
            player_rows = player_rows.loc[game_dates.lt(start)]
        sample=pd.to_numeric(player_rows[market],errors='coerce').dropna().tail(17)
        if len(sample)<5: continue
        recent=sample.tail(min(5,len(sample)))
        base=float(sample.mean()); last=float(recent.mean())
        projected=((1-weight)*base+weight*last)*(1+adjustment/100)
        sd=float(sample.std(ddof=1))
        if not np.isfinite(sd) or sd<=0: continue
        # Continuity correction for integer-valued statistics; normal approximation only.
        threshold=float(line)+0.5 if float(line).is_integer() else float(line)
        higher=1-NormalDist(mu=projected,sigma=sd).cdf(threshold)
        lower=1-higher
        if 'higher_available' in pick and str(pick['higher_available']).lower() == 'false': higher = float('nan')
        if 'lower_available' in pick and str(pick['lower_available']).lower() == 'false': lower = float('nan')
        if not np.isfinite(higher) and not np.isfinite(lower): continue
        rows.append({'player':player,'market':market,'market_name':MARKETS.get(market,market.replace('_',' ').title()),'line':line,'projection':round(projected,2),'season_mean':round(base,2),'recent_mean':round(last,2),'momentum_delta':round(last-base,2),'sample_games':len(sample),'volatility':round(sd,2),'higher_prob':higher,'lower_prob':lower,'direction':'Higher' if (np.isfinite(higher) and (not np.isfinite(lower) or higher>=lower)) else 'Lower','estimated_prob':max(x for x in (higher,lower) if np.isfinite(x)),'updated_at':pick.get('updated_at','Not provided'),'starts_at':pick.get('starts_at','')})
    return pd.DataFrame(rows)

results=pd.DataFrame()
if logs is not None and slate_lines is not None and not slate_lines.empty:
    results=analyze(logs.to_csv(index=False).encode(),slate_lines.to_csv(index=False).encode(),momentum_weight,context_shift)

# Explain why a real API board may not yield model-supported picks.
if logs is not None and slate_lines is not None and not slate_lines.empty:
    hist_names = set(logs['player'].map(normalized_player))
    supported = slate_lines['market'].isin(logs.columns)
    matched = slate_lines['player'].map(normalized_player).isin(hist_names)
    full_period = slate_lines['period'].astype(str).str.lower().isin(['full game', 'full_game', 'game', 'unknown']) if 'period' in slate_lines else pd.Series(True, index=slate_lines.index)
    with st.expander('Data coverage & model diagnostics', expanded=False):
        st.write(f"Observed offers on selected board: **{len(slate_lines)}**")
        st.write(f"Markets supported by historical stats: **{int(supported.sum())}**")
        st.write(f"Player names matched to history: **{int(matched.sum())}**")
        st.write(f"Supported market + matched player + full-game period: **{int((supported & matched & full_period).sum())}**")
        st.write(f"Offers with usable statistical estimates: **{len(results)}**")
        unknown = slate_lines.loc[~supported, 'source_market' if 'source_market' in slate_lines else 'market'].value_counts().head(12)
        if not unknown.empty:
            st.caption('Top provider market labels not yet supported by nflverse weekly data:')
            st.dataframe(unknown.rename_axis('Provider market').reset_index(name='Offers'), hide_index=True)
        st.caption('This diagnostic does not make additional API requests or consume extra credits.')

# Compact application navigation: only the selected workspace is rendered.

# Workspace heading is incorporated into the page-specific navigation.

if nav_page == '🏠 Dashboard':
    st.markdown('<div class="hero-title">Current Prop Board</div><div class="hero-sub">Search the observed Underdog board, filter the slate, and open player research from the sidebar.</div>', unsafe_allow_html=True)
    x1,x2,x3 = st.columns(3)
    x1.metric('Observed offers', len(slate_lines) if slate_lines is not None else 0)
    x2.metric('Players on board', int(slate_lines['player'].nunique()) if slate_lines is not None and not slate_lines.empty else 0)
    x3.metric('Model-supported offers', len(results))
    st.caption("Actual provider observations, not model-generated lines. Free-tier coverage is partial; a listed offer may have changed since observation.")
    if lines is None or lines.empty:
        st.warning("No offensive Underdog projections were retrieved. Check the API status in the sidebar.")
    else:
        board = slate_lines.copy() if slate_lines is not None else lines.copy()
        q = st.text_input("Search player or market", key="board_search").strip()
        a,b = st.columns(2)
        market_options = ["All markets"] + sorted(board["market"].dropna().astype(str).unique().tolist())
        selected_market = a.selectbox("Market", market_options, key="board_market")
        team_options = ["All teams"] + sorted(x for x in board.get("team", pd.Series(dtype=str)).dropna().astype(str).unique() if x)
        selected_team = b.selectbox("Team", team_options, key="board_team")
        if selected_market != "All markets":
            board = board[board["market"].eq(selected_market)]
        if selected_team != "All teams" and "team" in board:
            board = board[board["team"].eq(selected_team)]
        if q:
            board = board[board["player"].astype(str).str.contains(re.escape(q), case=False, na=False) | board["market"].astype(str).str.contains(re.escape(q), case=False, na=False)]
        if "roster_position" in board:
            board = board[board["roster_position"].isna() | board["roster_position"].isin(OFFENSIVE_POSITIONS)]
        st.metric("Displayed offers", len(board))
        if board.empty:
            st.info("No offers match the selected filters. The first API page may not include this matchup or player.")
        else:
            cols = [c for c in ("player", "team", "roster_position", "opponent", "source_market", "line", "higher_available", "lower_available", "higher_multiplier", "lower_multiplier", "pick_type", "starts_at", "updated_at") if c in board]
            st.dataframe(board[cols].rename(columns={"player":"Player", "team":"Team", "roster_position":"Position", "opponent":"Opponent", "source_market":"Market", "line":"Underdog line", "higher_available":"Higher offered", "lower_available":"Lower offered", "higher_multiplier":"Higher multiplier", "lower_multiplier":"Lower multiplier", "pick_type":"Line type", "starts_at":"Starts at", "updated_at":"Observed at"}), hide_index=True, use_container_width=True)
            # One-click board-to-profile navigation without changing the data source.
            selected_board_player = st.selectbox('Open player research', sorted(board['player'].dropna().astype(str).unique()), key='board_open_player')
            if st.button('Research selected player', type='primary', key='open_board_player'):
                st.session_state['requested_player'] = selected_board_player
                st.session_state['primary_navigation'] = '👤 Player Research'
                st.rerun()
            st.download_button("Export displayed lines", board.to_csv(index=False), "observed_underdog_lines.csv", "text/csv")
    if roster_error:
        st.caption("Roster data unavailable; defensive markets are excluded by market type, but player-position verification is incomplete.")
    elif current_roster is not None:
        st.caption("Position information comes from the current-season roster dataset; this does not verify injury status or game-day availability.")

if nav_page == '🏆 Best Bets':
    st.header('Best Bets — research ranking')
    st.info('This is a statistical research ranking, not a verified list of profitable picks. Probabilities are uncalibrated normal-model estimates; Underdog payout multipliers and pick correlations are not included.')
    if results.empty:
        st.warning('No eligible model rankings. Check API status, supported markets, player name matching, and game history.')
    else:
        a,b,c=st.columns(3)
        min_games=a.slider('Minimum games',5,17,8)
        min_prob=b.slider('Minimum estimated probability',0.50,0.90,0.55,0.01)
        standard_only=c.checkbox('Exclude nonstandard pick types (if supplied)',value=True)
        view=results[(results.sample_games>=min_games)&(results.estimated_prob>=min_prob)].copy()
        if standard_only and slate_lines is not None and 'pick_type' in slate_lines:
            standard=slate_lines[slate_lines['pick_type'].astype(str).str.lower().isin(['standard','balanced'])][['player','market','line']].drop_duplicates()
            view=view.merge(standard,on=['player','market','line'],how='inner')
        # Only rank observations with a plausible future start when the provider supplies one.
        if 'starts_at' in view.columns:
            upcoming = pd.to_datetime(view['starts_at'], errors='coerce', utc=True)
            view = view.loc[upcoming.isna() | upcoming.ge(pd.Timestamp.now(tz='UTC'))]
        view=view.sort_values('estimated_prob',ascending=False)
        if view.empty: st.warning('No props meet these filters. The partial API board may not contain supported standard offensive props; inspect the diagnostics above before changing thresholds.')
        else:
            show=view[['player','market_name','line','direction','estimated_prob','projection','momentum_delta','sample_games','updated_at']].copy()
            show['estimated_prob']=show['estimated_prob'].map(lambda x:f'{x:.1%}')
            st.dataframe(show.rename(columns={'player':'Player','market_name':'Market','line':'Underdog line','direction':'Side','estimated_prob':'Model probability','projection':'Projected stat','momentum_delta':'Recent − baseline','sample_games':'Games','updated_at':'Line updated'}),hide_index=True,use_container_width=True)
            st.download_button('Export research rankings',view.to_csv(index=False),'nfl_prop_rankings.csv','text/csv')
if nav_page == '🏟️ Games':
    st.header("Weekly Games")
    if week_schedule.empty:
        st.info("Load automatic NFL statistics to retrieve the schedule. Game selection requires the schedule source.")
    else:
        st.caption(f"{filter_season} • Week {filter_week} • {selected_matchup}")
        games_to_show = week_schedule if selected_matchup == "All games" else week_schedule[week_schedule.matchup.eq(selected_matchup)]
        fields = [c for c in ["matchup", "gameday", "gametime", "weekday", "stadium"] if c in games_to_show]
        st.dataframe(games_to_show[fields].rename(columns={"matchup":"Matchup", "gameday":"Date", "gametime":"Time", "weekday":"Day", "stadium":"Stadium"}), hide_index=True, use_container_width=True)
        if selected_teams is not None and logs is not None and "team" in logs:
            relevant = logs[logs["team"].astype(str).isin(selected_teams)]
            st.metric("Players with historical records for these teams", relevant["player"].nunique())
        st.caption("The selected matchup filters available Underdog offers by team when the API provides team identifiers.")

        if slate_lines is not None and not slate_lines.empty:
            st.subheader("Observed Underdog NFL projections")
            st.caption("Only the first cached API page is shown. This may not be the complete board; check observation timestamps and availability.")
            cols = [c for c in ["player", "team", "opponent", "market", "period", "line", "higher_available", "lower_available", "higher_multiplier", "lower_multiplier", "updated_at"] if c in slate_lines]
            st.dataframe(slate_lines[cols], hide_index=True, use_container_width=True)

if nav_page == '👤 Player Research':
    if logs is None or logs.empty:
        st.info('Load NFL statistics from Data & Model to begin player research.')
    else:
        # The profile is a compact workspace: controls, scorecard, chart, defense rail.
        position_markets = {
            'QB': ['passing_yards','passing_tds','pass_attempts','completions','interceptions','rushing_yards','carries','rushing_tds'],
            'RB': ['rushing_yards','carries','rushing_tds','receiving_yards','receptions','targets','receiving_tds','rush_rec_yards','rush_rec_tds'],
            'FB': ['rushing_yards','carries','receiving_yards','receptions','targets','rush_rec_yards'],
            'WR': ['receiving_yards','receptions','targets','receiving_tds','rushing_yards','carries','rush_rec_yards'],
            'TE': ['receiving_yards','receptions','targets','receiving_tds'],
            'K': ['field_goals','extra_points'], 'PK': ['field_goals','extra_points'],
        }
        with st.sidebar.expander('Player pool', expanded=False):
            show_historical = st.checkbox('Include non-current players', value=False, key='include_historical_players')
        player_pool = logs if show_historical else logs.loc[logs['_current_roster'].fillna(False)].copy()
        players = sorted(player_pool['player'].dropna().astype(str).unique().tolist())
        if selected_teams and 'team' in player_pool:
            matched = sorted(player_pool.loc[player_pool['team'].astype(str).isin(selected_teams),'player'].dropna().astype(str).unique())
            if matched: players = matched
        if not players:
            st.warning('No matching players. Change the game filter or enable historical players in the sidebar.')
        else:
            requested = st.session_state.pop('requested_player', None)
            if requested in players: st.session_state['research_player'] = requested
            if st.session_state.get('research_player') not in players: st.session_state.pop('research_player', None)
            top_player, top_market, top_season, top_window = st.columns([2.5,2.25,.9,.9], gap='small')
            player = top_player.selectbox('PLAYER', players, key='research_player')
            profile = player_pool[player_pool['player'].astype(str).eq(player)].sort_values('game_date')
            latest = profile.iloc[-1]
            pos = str(latest.get('roster_position','')).upper().strip()
            if pos in ('NAN','NONE'): pos = ''
            roster_team = str(latest.get('roster_team','')).upper().strip()
            team = roster_team if roster_team not in ('','NAN','NONE') else str(latest.get('team','')).upper().strip()
            portrait = latest.get('roster_headshot')
            permitted = position_markets.get(pos, list(MARKETS))
            available = [m for m in permitted if m in logs and pd.to_numeric(profile[m],errors='coerce').notna().any() and (pd.to_numeric(profile[m],errors='coerce').fillna(0).abs().sum()>0)]
            if not available:
                st.info('No supported statistics for this player.')
            else:
                market_key = f'profile_market_{normalized_player(player)}'
                market = top_market.selectbox('PROP', available, format_func=lambda m:MARKETS.get(m,m), key=market_key)
                full = logs.loc[logs['player'].astype(str).eq(player)].copy()
                full[market] = pd.to_numeric(full[market],errors='coerce')
                full = full.dropna(subset=[market]).sort_values(['season','week','game_date'])
                years = sorted(full['season'].dropna().astype(int).unique().tolist(),reverse=True) if 'season' in full else []
                if years:
                    season_default = 2026 if 2026 in years else years[0]
                    chosen_year = top_season.selectbox('SEASON',years,index=years.index(season_default),key='profile_single_season')
                    full = full.loc[full['season'].eq(chosen_year)].copy()
                else: chosen_year = None
                window = top_window.selectbox('SAMPLE',['L5','L10','L20','All'],index=0,key='profile_window')
                with st.popover('More filters', use_container_width=False):
                    opponents = ['All opponents']+sorted(full['opponent'].dropna().astype(str).unique().tolist())
                    opponent_filter = st.selectbox('Historical opponent',opponents,key='profile_history_opponent')
                    if opponent_filter != 'All opponents':
                        st.caption('Filtering changes the sample and chart, not the upcoming opponent.')
                sample = full if opponent_filter=='All opponents' else full.loc[full['opponent'].astype(str).eq(opponent_filter)]
                view = sample.tail({'L5':5,'L10':10,'L20':20,'All':len(sample)}[window]).copy()
                if view.empty:
                    st.info('No game logs match these filters.')
                else:
                    vals = pd.to_numeric(view[market],errors='coerce').dropna()
                    recent = pd.to_numeric(full[market],errors='coerce').dropna().tail(5)
                    prior = pd.to_numeric(full[market],errors='coerce').dropna().iloc[-10:-5]
                    def fmt(x):
                        if x is None or not np.isfinite(float(x)): return '—'
                        return f'{float(x):.1f}'.rstrip('0').rstrip('.')
                    # Resolve opponent from selected game, then next scheduled game.
                    opponent = None
                    if selected_teams and team in selected_teams: opponent = next(iter(selected_teams-{team}),None)
                    if opponent is None and schedule is not None and not schedule.empty and team:
                        games = schedule.copy()
                        game_dates = pd.to_datetime(games.get('gameday'),errors='coerce',utc=True)
                        future = games.loc[game_dates.ge(pd.Timestamp.now(tz='UTC').normalize()) & (games['home_team'].astype(str).eq(team)|games['away_team'].astype(str).eq(team))]
                        if not future.empty:
                            game = future.assign(_dt=game_dates.loc[future.index]).sort_values('_dt').iloc[0]
                            opponent = str(game['away_team'] if game['home_team']==team else game['home_team'])
                    name_col, info_col = st.columns([.10,.90],vertical_alignment='center',gap='small')
                    with name_col:
                        if isinstance(portrait,str) and portrait.startswith('https://'): st.image(portrait,width=82)
                        else: st.markdown('🏈')
                    with info_col:
                        st.markdown(f'<div class="profile-title">{player} <span>{pos} · {team}</span></div>',unsafe_allow_html=True)
                        st.markdown(f'<div class="profile-sub">{MARKETS.get(market,market)} &nbsp;·&nbsp; {("vs "+opponent) if opponent else "Opponent unconfirmed"} &nbsp;·&nbsp; {chosen_year or "All seasons"}</div>',unsafe_allow_html=True)
                    matching = lines.loc[lines['_player_key'].eq(normalized_player(player)) & lines['market'].eq(market)] if lines is not None and '_player_key' in lines else pd.DataFrame()
                    observed = not matching.empty
                    line = None
                    if observed:
                        line_values = sorted(pd.to_numeric(matching['line'],errors='coerce').dropna().unique().tolist())
                        if line_values: line = st.selectbox('Observed Underdog line',line_values,key=f'profile_observed_{normalized_player(player)}_{market}',format_func=fmt)
                    if not observed:
                        with st.popover('No observed line · optional comparison'):
                            st.caption('The free API board is partial. This does not mean Underdog has no offer.')
                            manual_on = st.checkbox('Use hypothetical line',key='profile_manual_on')
                            manual_val = st.number_input('Hypothetical line',min_value=0.0,value=float(round(vals.mean()*2)/2),step=0.5,key=f'profile_manual_{normalized_player(player)}_{market}') if manual_on else None
                        if manual_on: line = manual_val
                    score_cols = st.columns(5,gap='small')
                    score_items = [('Sample avg',fmt(vals.mean())),('Last 5',fmt(recent.mean())),('Previous 5',fmt(prior.mean()) if len(prior)>=3 else '—'),('Games',str(len(vals))),('Line',fmt(line) if line is not None else '—')]
                    for col,(label,value) in zip(score_cols,score_items):
                        with col: st.markdown(f'<div class="mini-score"><small>{label}</small><strong>{value}</strong></div>',unsafe_allow_html=True)
                    main,rail = st.columns([2.05,1],gap='small')
                    with main:
                        if line is not None:
                            above=int((vals>line).sum()); below=int((vals<line).sum()); pushes=int((vals==line).sum())
                            st.markdown(f'<div class="compact-section">GAME LOG <span>{above}/{len(vals)} above · {below}/{len(vals)} below · {pushes} pushes · {"Observed" if observed else "Hypothetical"} line</span></div>',unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="compact-section">GAME LOG <span>Historical results · No comparison line</span></div>',unsafe_allow_html=True)
                        plot=view.copy()
                        plot['Game'] = (plot['season'].astype('Int64').astype(str)+' W'+plot['week'].astype('Int64').astype(str)) if {'season','week'}.issubset(plot.columns) else plot['game_date'].dt.strftime('%m/%d')
                        plot['Result'] = 'No line' if line is None else np.select([plot[market]>line,plot[market]<line],['Higher','Lower'],default='Push')
                        fig=px.bar(plot,x='Game',y=market,color='Result',color_discrete_map={'Higher':'#12d69d','Lower':'#e33e1a','Push':'#f0c36b','No line':'#368cbd'},hover_data=['opponent'])
                        if line is not None: fig.add_hline(y=line,line_dash='dash',line_color='#d4b86a')
                        fig.update_layout(template='plotly_dark',height=260,margin=dict(l=2,r=2,t=5,b=5),paper_bgcolor='#0b0d10',plot_bgcolor='#0b0d10',showlegend=False,font=dict(size=10,color='#b9c4d0'),xaxis=dict(showgrid=False,title=None),yaxis=dict(gridcolor='#24272c',title=None),bargap=.22)
                        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
                        if line is not None and len(vals):
                            higher_pct = 100*above/len(vals)
                            st.markdown(f'<div style="display:flex;gap:10px;align-items:center;margin:-1px 0 5px;font-size:11px"><b style="color:#4fe4b0">HIGHER {higher_pct:.0f}%</b><div style="flex:1;background:#a83d2e;border-radius:7px;height:8px;overflow:hidden"><div style="width:{higher_pct:.1f}%;background:#2bd8a0;height:100%"></div></div><b style="color:#f17b6c">LOWER {100*below/len(vals):.0f}%</b></div>',unsafe_allow_html=True)

                        with st.popover('Game log / export'):
                            cols=[c for c in ['season','week','opponent',market,'targets','carries','pass_attempts'] if c in view]
                            shown=view[cols].iloc[::-1].copy()
                            for c in shown.select_dtypes(include='number').columns:
                                if c not in ('season','week'): shown[c]=shown[c].round(1)
                            st.dataframe(shown,hide_index=True,use_container_width=True)
                            st.download_button('Download CSV',view.to_csv(index=False),f'{normalized_player(player).replace(" ","_")}_games.csv','text/csv')
                        st.markdown('<div class="compact-section">OPPORTUNITY <span>Last five vs previous five games</span></div>',unsafe_allow_html=True)
                        usage=[]
                        usage_metrics={'QB':['pass_attempts','completions','carries'],'RB':['carries','targets','receptions'],'WR':['targets','receptions','carries'],'TE':['targets','receptions']}.get(pos,['targets','carries'])
                        for m in usage_metrics:
                            if m not in full: continue
                            series=pd.to_numeric(full[m],errors='coerce').dropna()
                            if len(series)<3: continue
                            r=series.tail(5); p=series.iloc[-10:-5]
                            usage.append({'Stat':MARKETS.get(m,m),'L5':fmt(r.mean()),'Previous 5':fmt(p.mean()) if len(p)>=3 else '—','Change':fmt(r.mean()-p.mean()) if len(p)>=3 else '—'})
                        if usage:
                            for u in usage:
                                st.markdown(f'<div class="defense-stat"><span>{u["Stat"]}</span><strong>{u["L5"]}</strong><b style="color:#7bdfc5">{u["Change"]}</b></div>',unsafe_allow_html=True)
                        else: st.caption('Opportunity data unavailable for this player.')
                    with rail:
                        st.markdown(f'<div class="compact-section">DEFENSE <span>{("vs "+opponent) if opponent else "No matchup"}</span></div>',unsafe_allow_html=True)
                        if opponent and pos in ('QB','RB','WR','TE') and {'season','week','opponent','roster_position'}.issubset(logs):
                            defensive = logs.loc[logs['roster_position'].fillna('').astype(str).str.upper().eq(pos)].copy()
                            if chosen_year is not None: defensive=defensive.loc[defensive['season'].eq(chosen_year)]
                            metrics={'QB':['passing_yards','passing_tds','rushing_yards','interceptions'],'RB':['rushing_yards','carries','receiving_yards','receptions'],'WR':['receiving_yards','receptions','targets','receiving_tds'],'TE':['receiving_yards','receptions','targets','receiving_tds']}[pos]
                            defense_rows=[]
                            for m in metrics:
                                if m not in defensive: continue
                                grouped=defensive.groupby(['opponent','season','week'],as_index=False)[m].sum().groupby('opponent')[m].mean().sort_values()
                                if opponent not in grouped.index: continue
                                rank=int(grouped.index.get_loc(opponent))+1
                                n=len(grouped)
                                defense_rows.append({'Stat':MARKETS.get(m,m),'Allowed':fmt(grouped.loc[opponent]),'Rank':f'#{rank}/{n}','_rank':rank,'_count':n})
                            if defense_rows:
                                for row in defense_rows:
                                    color='#f87171' if row['_rank']<=max(1,row['_count']//3) else '#4ade80' if row['_rank']>=max(1,2*row['_count']//3) else '#e4c56e'
                                    st.markdown(f'<div class="defense-stat"><span>{row["Stat"]}</span><strong>{row["Allowed"]}</strong><b style="color:{color}">{row["Rank"]}</b></div>',unsafe_allow_html=True)

                            else: st.caption('No matching defense totals.')
                        else: st.caption('Select an opponent to view defensive allowances.')
                        st.markdown('<div class="profile-rail-title">DEFENSIVE SCHEME</div>',unsafe_allow_html=True)
                        with st.popover('Inspect coverage / blitz charting', use_container_width=True):
                            st.caption('Source: free FTN charting; team-level data only. Unrecognized fields are not interpreted.')
                            if opponent and chosen_year is not None:
                                if st.button('Load scheme statistics',key='load_ftn_on_demand'):
                                    try:
                                        chart=fetch_ftn_charting(int(chosen_year))
                                        try: pbp=fetch_pbp_defense_keys(int(chosen_year))
                                        except Exception: pbp=None
                                        ftn,ftn_note=ftn_defense_summary(chart,opponent,schedule,pbp)
                                        if ftn.empty: st.info('No verified scheme rates could be extracted for this matchup.')
                                        else: st.dataframe(ftn,hide_index=True,use_container_width=True)
                                    except Exception as exc: st.info('Scheme feed unavailable. Try again later.')
                            st.link_button('Published team coverage rates', 'https://www.sharpfootballanalysis.com/stats-nfl/nfl-coverage-schemes/', use_container_width=True)
                        st.markdown('<div class="profile-note">Coverage splits require verified charting; no fabricated player-versus-scheme advantage.</div>',unsafe_allow_html=True)
                        st.markdown('<div class="compact-section">INJURY REPORT <span>Defensive personnel</span></div>',unsafe_allow_html=True)
                        if opponent:
                            report,note=injury_team_view(injury_reports,opponent,current_season,filter_week)
                            if not report.empty:
                                report=report.copy()
                                for col in ['Practice','Game status']:
                                    if col in report:
                                        text_col=report[col].fillna('').astype(str).str.strip()
                                        if col=='Practice':
                                            report[col]=text_col.map(lambda x:'DNP' if re.search(r'(?i)did not practice|not participating|non.participant|^dnp$',x) else 'LP' if re.search(r'(?i)limited|^lp$',x) else 'FP' if re.search(r'(?i)full participation|full practice|^fp$',x) else x)
                                keep=[c for c in ['Player','Position','Practice','Game status'] if c in report]
                                st.dataframe(report[keep].head(8),hide_index=True,use_container_width=True,height=min(315,38+35*min(len(report),8)))

                            else: st.caption(note)
                        else: st.caption('No confirmed opponent.')
if nav_page == '📈 Trends':
    st.header('Momentum Tracker')
    st.write('Momentum is measured as the last-five-game average minus the available historical average. It is descriptive, not proof that a trend will continue.')
    if results.empty: st.info('Load NFL statistics and an Underdog board to compare recent form with the baseline.')
    else:
        momentum=results[['player','market_name','season_mean','recent_mean','momentum_delta','sample_games']].sort_values('momentum_delta',ascending=False)
        st.dataframe(momentum,hide_index=True,use_container_width=True)
        st.caption('Different market units are not directly comparable. Do not interpret a 10-yard change as equivalent to a 10-reception change.')
if nav_page == '⚙️ Data & Model':
    st.header('Model Evaluation')
    st.warning('The current model is a transparent baseline, not a backtested or calibrated prediction model. Do not treat its probabilities as established hit rates.')
    st.markdown('Next milestone: walk-forward validation using only information available **before each game**. We will measure calibration, Brier score, log loss, and performance by market, season, and player sample size. Historical Underdog lines will be required for realistic line-based backtesting.')
    st.markdown('A positive-EV claim additionally requires the applicable Underdog entry payout, joint pick probability, and any relevant product rules. Those are not implemented in current version.')
if nav_page == '⚙️ Data & Model':
  with st.expander('CSV Data Guide and templates', expanded=False):
      st.header('CSV Data Guide')
      st.markdown('**Game logs:** one row per player per game. Required columns: `player`, `game_date`, `opponent`. Add any supported market columns below using the exact machine-readable names.')
      st.code(', '.join(MARKETS.keys()))
      st.markdown('**Underdog board:** one row per currently offered projection. Required columns: `player`, `market`, `line`. Optional: `updated_at`, `pick_type` (`standard` or other), `team` (NFL team abbreviation for game filtering). Player names must match game logs exactly.')
      sample_logs=pd.DataFrame([{'player':'Example Player','game_date':'2026-09-13','opponent':'EXAMPLE','receiving_yards':70,'receptions':5},{'player':'Example Player','game_date':'2026-09-20','opponent':'EXAMPLE','receiving_yards':82,'receptions':6}])
      sample_lines=pd.DataFrame([{'player':'Example Player','market':'receiving_yards','line':74.5,'updated_at':'2026-11-19T12:00:00-06:00','pick_type':'standard'}])
      st.caption('Example rows are fictional and insufficient for a prediction. The model requires at least five game observations.')
      x,y=st.columns(2)
      x.download_button('Download game-log template',sample_logs.to_csv(index=False),'game_logs_template.csv','text/csv')
      y.download_button('Download Underdog board template',sample_lines.to_csv(index=False),'underdog_board_template.csv','text/csv')
      st.markdown('**Data safety:** never put Underdog account credentials or API keys into a CSV or public GitHub repository. Confirm that any automated data collection complies with the source terms.')
