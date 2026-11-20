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

MARKETS = {'passing_yards':'Passing yards','passing_tds':'Passing TDs','pass_attempts':'Pass attempts','completions':'Pass completions','interceptions':'Interceptions','rushing_yards':'Rushing yards','carries':'Rushing attempts','rushing_tds':'Rushing TDs','receiving_yards':'Receiving yards','receptions':'Receptions','targets':'Targets','receiving_tds':'Receiving TDs','rush_rec_yards':'Rush + receiving yards','rush_rec_tds':'Rush + receiving TDs','longest_reception':'Longest reception','longest_rush':'Longest rush','sacks':'Sacks','tackles':'Tackles','field_goals':'Field goals','extra_points':'Extra points'}
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
    rows = []
    for item in payload.get("data", []):
        player = item.get("player") or {}
        market = item.get("market") or {}
        event = item.get("event") or {}
        if item.get("is_demo") or item.get("status") not in (None, "active"):
            continue
        sides = {str(x.get("side", "")).lower(): x for x in (item.get("selections") or [])}
        if not any(x.get("available") is True for x in sides.values()):
            continue
        raw_line = item.get("line")
        if raw_line is None or not player.get("name") or not market.get("stat"):
            continue
        rows.append({
            "player": player["name"], "team": player.get("team") or "",
            "market": str(market["stat"]).strip().lower().replace(" ", "_"),
            "period": market.get("period") or "Unknown", "line": raw_line,
            "updated_at": item.get("observed_at") or meta.get("observed_at") or "Unknown",
            "pick_type": "discounted" if item.get("is_discounted") else (item.get("line_type") or "standard"),
            "higher_available": sides.get("higher", {}).get("available") is True,
            "lower_available": sides.get("lower", {}).get("available") is True,
            "higher_multiplier": sides.get("higher", {}).get("payout_multiplier"),
            "lower_multiplier": sides.get("lower", {}).get("payout_multiplier"),
            "opponent": event.get("opponent") or "", "starts_at": event.get("starts_at") or "",
            "provider_id": item.get("id") or "",
        })
    columns = ["player", "team", "market", "period", "line", "updated_at", "pick_type", "higher_available", "lower_available", "higher_multiplier", "lower_multiplier", "opponent", "starts_at", "provider_id"]
    return pd.DataFrame(rows, columns=columns), meta, response.headers.get("X-Credits-Cost", "Unknown")

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
            lines, board_meta, credit_cost = fetch_underdog_board(api_key)
            if not lines.empty:
                st.sidebar.success(f"Retrieved {len(lines)} observed NFL offers (cached for 24 hours).")
            st.sidebar.caption(f"Source observation: {board_meta.get('observed_at', 'Unknown')} | Request credit cost: {credit_cost}")
            if board_meta.get("next_cursor"):
                st.sidebar.warning("Partial board: additional pages exist. Not fetched automatically to protect free credits.")
            if board_meta.get("source_status") not in ("fresh", "live", "ok", None):
                st.sidebar.warning(f"Provider source status: {board_meta.get('source_status')}")
            if lines.empty:
                st.sidebar.warning("The provider returned zero qualifying NFL offers. The app will remain usable, but Best Bets cannot rank lines until valid offers are available. This may reflect the response format, available offers, or filtering rules.")
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
    lines['market'] = lines['market'].astype(str).str.strip().str.lower()
    lines = lines.dropna(subset=['line','player','market'])
    if 'updated_at' not in lines: lines['updated_at'] = 'Not provided'

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
        filter_season = st.selectbox("Season", schedule_seasons, key="game_filter_season")
        available_weeks = sorted(schedule.loc[schedule.season.eq(filter_season), "week"].dropna().astype(int).unique())
        filter_week = st.selectbox("Week", available_weeks, index=len(available_weeks)-1, key="game_filter_week")
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
    board['line'] = pd.to_numeric(board['line'], errors='coerce')
    rows=[]
    for _, pick in board.iterrows():
        player=str(pick['player']); market=str(pick['market']).strip().lower(); line=pick['line']
        if market not in history or not np.isfinite(line): continue
        if str(pick.get('period', 'Full game')).lower() not in ('full game', 'full_game', 'game', 'unknown'): continue
        sample=pd.to_numeric(history.loc[history['player'].astype(str)==player,market],errors='coerce').dropna().tail(17)
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

tabs=st.tabs(['🏆 Best Bets','🏟️ Weekly Games','🔎 Player Research','📈 Momentum','🛡️ Defensive Matchups','🧪 Model Evaluation','📁 Data Guide'])
with tabs[0]:
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
with tabs[1]:
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

with tabs[2]:
    st.header('Advanced Player Research')
    if logs is None:
        st.info('Load automatic NFL statistics or upload a player game-log CSV to start.')
    else:
        players = sorted(logs['player'].astype(str).unique())
        if selected_teams is not None and 'team' in logs:
            matchup_players = sorted(logs.loc[logs['team'].astype(str).isin(selected_teams), 'player'].astype(str).unique())
            if matchup_players:
                players = matchup_players
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
                line = st.number_input('Enter the current Underdog Higher/Lower line', min_value=0.0, value=50.5, step=0.5, key='research_line')
                higher = int((vals > line).sum()); lower = int((vals < line).sum()); pushes = int((vals == line).sum())
                h,l,p = st.columns(3)
                h.metric('Higher in sample', f'{higher}/{len(vals)}')
                l.metric('Lower in sample', f'{lower}/{len(vals)}')
                p.metric('Exactly on line', pushes)
                st.caption('These are descriptive historical counts, not predicted hit probabilities. Verify how Underdog handles ties for this market.')
                plot = view.copy()
                plot['Game'] = (plot['season'].astype('Int64').astype(str) + ' W' + plot['week'].astype('Int64').astype(str)) if {'season','week'}.issubset(plot.columns) else plot['game_date'].dt.strftime('%Y-%m-%d')
                fig = px.line(plot, x='Game', y=market, markers=True, hover_data=['opponent'], title=f'{player} — {MARKETS[market]}')
                fig.add_hline(y=line, line_dash='dash', annotation_text='Underdog line (manual)')
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
with tabs[3]:
    st.header('Momentum Tracker')
    st.write('Momentum is measured as the last-five-game average minus the available historical average. It is descriptive, not proof that a trend will continue.')
    if results.empty: st.info('Load NFL statistics and upload an Underdog board CSV to compare recent form with the baseline.')
    else:
        momentum=results[['player','market_name','season_mean','recent_mean','momentum_delta','sample_games']].sort_values('momentum_delta',ascending=False)
        st.dataframe(momentum,hide_index=True,use_container_width=True)
        st.caption('Different market units are not directly comparable. Do not interpret a 10-yard change as equivalent to a 10-reception change.')
with tabs[4]:
    st.header('Defensive Matchup Research')
    st.write('Coverage shells, man/zone rates, blitz rates, pressure, defensive personnel, injuries, and offensive scheme fit belong here. No verified scheme-level dataset is connected yet.')
    st.warning('The sidebar matchup adjustment is a manual scenario tool, not a measured defensive advantage. It is applied globally to the current projections and should remain at 0% unless you are testing a clearly documented hypothesis.')
    st.markdown('**Planned defensive data fields:** coverage type and frequency; pressure and blitz rate; defensive front and box counts; slot/outside matchup; personnel availability; opponent-adjusted efficiency; and data-source timestamp.')
    st.markdown('**Important:** defensive tendencies vary by opponent, down, distance, and personnel. A team-wide coverage percentage should not automatically determine a player projection.')
with tabs[5]:
    st.header('Model Evaluation')
    st.warning('The current model is a transparent baseline, not a backtested or calibrated prediction model. Do not treat its probabilities as established hit rates.')
    st.markdown('Next milestone: walk-forward validation using only information available **before each game**. We will measure calibration, Brier score, log loss, and performance by market, season, and player sample size. Historical Underdog lines will be required for realistic line-based backtesting.')
    st.markdown('A positive-EV claim additionally requires the applicable Underdog entry payout, joint pick probability, and any relevant product rules. Those are not implemented in Version 1.')
with tabs[6]:
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
