import math
import re
from statistics import NormalDist
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='NFL Prop Lab | Underdog Research', page_icon='🏈', layout='wide')
st.markdown('''<style>.block-container{padding-top:2rem;max-width:1350px}h1,h2,h3{letter-spacing:-.025em}div[data-testid="stMetric"]{border:1px solid #374151;border-radius:12px;padding:15px}</style>''', unsafe_allow_html=True)
st.title('🏈 NFL Prop Lab')
st.caption('Underdog Higher / Lower research • historical performance • momentum • matchup context')

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
    # A roster entry is not proof of being healthy or scheduled to play.
    return roster[["_player_key", "roster_player", "roster_position", "roster_team"]].drop_duplicates("_player_key")

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

with st.sidebar:
    st.header('Data inputs')
    st.caption('NFL history via nflreadpy; Underdog lines via your private API key. Free API credits are limited.')
    source_mode = st.radio('Historical player data', ['Automatic NFL statistics', 'Upload my own CSV'], index=0)
    if source_mode == 'Automatic NFL statistics':
        selected_seasons = st.multiselect('NFL seasons', [2026, 2025, 2024, 2023], default=[2025, 2026])
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

# Shared matchup selector. Selecting a game filters the research and available board.
schedule = None
if source_mode == 'Automatic NFL statistics' and selected_seasons:
    try:
        schedule = fetch_schedule(tuple(sorted(selected_seasons)))
    except Exception as exc:
        st.sidebar.warning(f"Schedule unavailable: {exc}")

with st.sidebar:
    st.divider()
    st.subheader("Weekly game filter")
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
            suggested_week = int(future_games.sort_values("week").iloc[0]["week"])
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
        rows.append({'player':player,'market':market,'market_name':MARKETS.get(market,market.replace('_',' ').title()),'line':line,'projection':round(projected,2),'season_mean':round(base,2),'recent_mean':round(last,2),'momentum_delta':round(last-base,2),'sample_games':len(sample),'volatility':round(sd,2),'higher_prob':higher,'lower_prob':lower,'direction':'Higher' if (np.isfinite(higher) and (not np.isfinite(lower) or higher>=lower)) else 'Lower','estimated_prob':max(x for x in (higher,lower) if np.isfinite(x)),'updated_at':pick.get('updated_at','Not provided')})
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
    with st.expander('Why some Underdog lines are not ranked', expanded=results.empty):
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

tabs=st.tabs(['🎯 Underdog Lines','🏆 Best Bets','🏟️ Weekly Games','🔎 Player Research','📈 Momentum','🛡️ Defensive Matchups','🧪 Model Evaluation','📁 Data Guide'])
with tabs[0]:
    st.header("Underdog Lines — observed board")
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
            st.download_button("Export displayed lines", board.to_csv(index=False), "observed_underdog_lines.csv", "text/csv")
    if roster_error:
        st.caption("Roster data unavailable; defensive markets are excluded by market type, but player-position verification is incomplete.")
    elif current_roster is not None:
        st.caption("Position information comes from the current-season roster dataset; this does not verify injury status or game-day availability.")

with tabs[1]:
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
        view=view.sort_values('estimated_prob',ascending=False)
        if view.empty: st.warning('No props meet these filters. Try adjusting the filters or adding data.')
        else:
            show=view[['player','market_name','line','direction','estimated_prob','projection','momentum_delta','sample_games','updated_at']].copy()
            show['estimated_prob']=show['estimated_prob'].map(lambda x:f'{x:.1%}')
            st.dataframe(show.rename(columns={'player':'Player','market_name':'Market','line':'Underdog line','direction':'Side','estimated_prob':'Model probability','projection':'Projected stat','momentum_delta':'Recent − baseline','sample_games':'Games','updated_at':'Line updated'}),hide_index=True,use_container_width=True)
            st.download_button('Export research rankings',view.to_csv(index=False),'nfl_prop_rankings.csv','text/csv')
with tabs[2]:
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

with tabs[3]:
    st.header('Advanced Player Research')
    if logs is None:
        st.info('Load automatic NFL statistics or upload a player game-log CSV to start.')
    else:
        show_historical = st.checkbox("Include historical / non-current players", value=False, key="include_historical_players")
        player_pool = logs if show_historical else logs[logs["_current_roster"]].copy()
        if not show_historical and current_roster is None:
            st.caption("Current roster unavailable: using players who appeared in the latest selected season as a fallback, not verified active status.")
        players = sorted(player_pool['player'].astype(str).unique())
        if selected_teams is not None and 'team' in logs:
            matchup_players = sorted(player_pool.loc[player_pool['team'].astype(str).isin(selected_teams), 'player'].astype(str).unique())
            if matchup_players:
                players = matchup_players
        if not players:
            st.warning('No players match the current roster and game filters. Enable historical players or select All games.')
            st.stop()
        player = st.selectbox('Player', players, key='research_player')
        available = [m for m in MARKETS if m in logs and logs.loc[logs.player.astype(str).eq(player), m].notna().any()]
        if not available:
            st.warning('No supported market columns found for this player.')
        else:
            market = st.selectbox('Stat market', available, format_func=lambda x: MARKETS[x])
            full = logs[logs.player.astype(str).eq(player)].dropna(subset=[market]).copy()
            full = full.sort_values(['season','week','game_date'] if {'season','week'}.issubset(full.columns) else ['game_date'])
            if 'season' in full and full['season'].notna().any():
                seasons = sorted(full['season'].dropna().astype(int).unique(), reverse=True)
                chosen_seasons = st.multiselect('Seasons to display', seasons, default=seasons, key='research_seasons')
                full = full[full['season'].isin(chosen_seasons)]
            window = st.selectbox('Games to display', ['All games','Last 3','Last 5','Last 10','Last 17'], index=0)
            opponent_choices = ['All opponents'] + sorted(full['opponent'].dropna().astype(str).unique().tolist())
            opponent_choice = st.selectbox('Historical opponent filter', opponent_choices)
            if opponent_choice != 'All opponents':
                full = full[full['opponent'].astype(str).eq(opponent_choice)]
            window_n = {'All games':None,'Last 3':3,'Last 5':5,'Last 10':10,'Last 17':17}[window]
            view = full.tail(window_n) if window_n else full
            if view.empty:
                st.warning('No games match these filters.')
            else:
                vals = pd.to_numeric(view[market], errors='coerce').dropna()
                a,b,c,d = st.columns(4)
                a.metric('Displayed average', f'{vals.mean():.1f}')
                b.metric('Last 5 average', f'{vals.tail(5).mean():.1f}')
                c.metric('Games displayed', len(vals))
                d.metric('Std. deviation', f'{vals.std():.1f}' if len(vals)>1 else 'N/A')
                st.subheader('Underdog line comparison')
                matching_lines = lines[(lines["_player_key"].eq(normalized_player(player))) & (lines["market"].eq(market))] if lines is not None and "_player_key" in lines else pd.DataFrame()
                if not matching_lines.empty:
                    chosen_line = st.selectbox("Observed Underdog line", sorted(matching_lines["line"].dropna().astype(float).unique().tolist()), key=f"observed_{normalized_player(player)}_{market}")
                    st.caption("Line selected from the retrieved API board. Check its observation time before use.")
                    line = float(chosen_line)
                else:
                    line = st.number_input('Manual comparison line (no observed line for this player/market)', min_value=0.0, value=50.5, step=0.5, key='research_line')
                higher = int((vals > line).sum()); lower = int((vals < line).sum()); pushes = int((vals == line).sum())
                h,l,p = st.columns(3)
                h.metric('Higher in sample', f'{higher}/{len(vals)}')
                l.metric('Lower in sample', f'{lower}/{len(vals)}')
                p.metric('Exactly on line', pushes)
                st.caption('These are descriptive historical counts, not predicted hit probabilities. Verify how Underdog handles ties for this market.')
                plot = view.copy()
                plot['Game'] = (plot['season'].astype('Int64').astype(str) + ' W' + plot['week'].astype('Int64').astype(str)) if {'season','week'}.issubset(plot.columns) else plot['game_date'].dt.strftime('%Y-%m-%d')
                fig = px.line(plot, x='Game', y=market, markers=True, hover_data=['opponent'], title=f'{player} — {MARKETS[market]}')
                fig.add_hline(y=line, line_dash='dash', annotation_text='Comparison line')
                st.plotly_chart(fig, use_container_width=True)
                cols = [c for c in ['season','week','game_date','team','opponent',market,'targets','carries','pass_attempts'] if c in view.columns]
                cols = list(dict.fromkeys(cols))
                st.dataframe(view[cols].iloc[::-1], hide_index=True, use_container_width=True)
                st.download_button('Download filtered game logs', view.to_csv(index=False), f'{re.sub(r"[^a-zA-Z0-9]+", "_", player)}_game_logs.csv', 'text/csv')
                if len(full)>=5:
                    st.subheader('Momentum snapshot')
                    recent = pd.to_numeric(full[market],errors='coerce').dropna().tail(5)
                    baseline = pd.to_numeric(full[market],errors='coerce').dropna()
                    st.write(f'Last 5 average: **{recent.mean():.1f}** | Selected-history average: **{baseline.mean():.1f}** | Difference: **{recent.mean()-baseline.mean():+.1f}**')
                    st.caption('Recent performance can reflect opportunity, matchups, or random variation. This is not an independently validated prediction adjustment.')
with tabs[4]:
    st.header('Momentum Tracker')
    st.write('Momentum is measured as the last-five-game average minus the available historical average. It is descriptive, not proof that a trend will continue.')
    if results.empty: st.info('Load NFL statistics and an Underdog board to compare recent form with the baseline.')
    else:
        momentum=results[['player','market_name','season_mean','recent_mean','momentum_delta','sample_games']].sort_values('momentum_delta',ascending=False)
        st.dataframe(momentum,hide_index=True,use_container_width=True)
        st.caption('Different market units are not directly comparable. Do not interpret a 10-yard change as equivalent to a 10-reception change.')
with tabs[5]:
    st.header('Defensive Matchup Research')
    st.write('Coverage shells, man/zone rates, blitz rates, pressure, defensive personnel, injuries, and offensive scheme fit belong here. No verified scheme-level dataset is connected yet.')
    st.warning('The sidebar matchup adjustment is a manual scenario tool, not a measured defensive advantage. It is applied globally to the current projections and should remain at 0% unless you are testing a clearly documented hypothesis.')
    st.markdown('**Planned defensive data fields:** coverage type and frequency; pressure and blitz rate; defensive front and box counts; slot/outside matchup; personnel availability; opponent-adjusted efficiency; and data-source timestamp.')
    st.markdown('**Important:** defensive tendencies vary by opponent, down, distance, and personnel. A team-wide coverage percentage should not automatically determine a player projection.')
with tabs[6]:
    st.header('Model Evaluation')
    st.warning('The current model is a transparent baseline, not a backtested or calibrated prediction model. Do not treat its probabilities as established hit rates.')
    st.markdown('Next milestone: walk-forward validation using only information available **before each game**. We will measure calibration, Brier score, log loss, and performance by market, season, and player sample size. Historical Underdog lines will be required for realistic line-based backtesting.')
    st.markdown('A positive-EV claim additionally requires the applicable Underdog entry payout, joint pick probability, and any relevant product rules. Those are not implemented in Version 1.')
with tabs[7]:
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
