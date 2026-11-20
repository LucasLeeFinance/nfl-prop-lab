import math
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
    opponent_col = first(["opponent_team", "opponent", "recent_team"])
    if player_col is None:
        raise ValueError("NFL data did not include a recognizable player field")
    out = pd.DataFrame({"player": frame[player_col].astype(str)})
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
    return out.dropna(subset=["player", "game_date"]).sort_values("game_date")

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

with st.sidebar:
    st.header('Data inputs')
    st.caption('Upload historical NFL game logs and a current Underdog board. No live feed is connected.')
    source_mode = st.radio('Historical player data', ['Automatic NFL statistics', 'Upload my own CSV'], index=0)
    if source_mode == 'Automatic NFL statistics':
        selected_seasons = st.multiselect('NFL seasons', [2026, 2025, 2024, 2023], default=[2025, 2026])
        st.caption('Source: nflverse via nflreadpy. Weekly statistics may update after games; some markets require other sources.')
        log_upload = None
    else:
        log_upload = st.file_uploader('Player game logs (CSV)', type='csv', key='logs')
    lines_upload = st.file_uploader('Underdog projections (CSV)', type='csv', key='lines')
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
lines = read_csv(lines_upload, REQUIRED_LINES)
if logs is not None:
    logs['game_date'] = pd.to_datetime(logs['game_date'], errors='coerce')
    logs = logs.dropna(subset=['game_date','player']).sort_values('game_date')
    for c in MARKETS:
        if c in logs: logs[c] = pd.to_numeric(logs[c], errors='coerce')
if lines is not None:
    lines['line'] = pd.to_numeric(lines['line'], errors='coerce')
    lines['market'] = lines['market'].astype(str).str.strip().str.lower()
    lines = lines.dropna(subset=['line','player','market'])
    if 'updated_at' not in lines: lines['updated_at'] = 'Not provided'

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
        rows.append({'player':player,'market':market,'market_name':MARKETS.get(market,market.replace('_',' ').title()),'line':line,'projection':round(projected,2),'season_mean':round(base,2),'recent_mean':round(last,2),'momentum_delta':round(last-base,2),'sample_games':len(sample),'volatility':round(sd,2),'higher_prob':higher,'lower_prob':lower,'direction':'Higher' if higher>=lower else 'Lower','estimated_prob':max(higher,lower),'updated_at':pick.get('updated_at','Not provided')})
    return pd.DataFrame(rows)

results=pd.DataFrame()
if logs is not None and lines is not None:
    results=analyze(logs.to_csv(index=False).encode(),lines.to_csv(index=False).encode(),momentum_weight,context_shift)

tabs=st.tabs(['🏆 Best Bets','🔎 Player Research','📈 Momentum','🛡️ Defensive Matchups','🧪 Model Evaluation','📁 Data Guide'])
with tabs[0]:
    st.header('Best Bets — research ranking')
    st.info('This is a statistical research ranking, not a verified list of profitable picks. Probabilities are uncalibrated normal-model estimates; Underdog payout multipliers and pick correlations are not included.')
    if results.empty:
        st.warning('Load NFL statistics and upload a current Underdog projections CSV to generate rankings. No live Underdog feed is connected.')
    else:
        a,b,c=st.columns(3)
        min_games=a.slider('Minimum games',5,17,8)
        min_prob=b.slider('Minimum estimated probability',0.50,0.90,0.55,0.01)
        standard_only=c.checkbox('Exclude nonstandard pick types (if supplied)',value=True)
        view=results[(results.sample_games>=min_games)&(results.estimated_prob>=min_prob)].copy()
        if standard_only and lines is not None and 'pick_type' in lines:
            standard=lines[lines['pick_type'].astype(str).str.lower().eq('standard')][['player','market','line']].drop_duplicates()
            view=view.merge(standard,on=['player','market','line'],how='inner')
        view=view.sort_values('estimated_prob',ascending=False)
        if view.empty: st.warning('No props meet these filters. Try adjusting the filters or adding data.')
        else:
            show=view[['player','market_name','line','direction','estimated_prob','projection','momentum_delta','sample_games','updated_at']].copy()
            show['estimated_prob']=show['estimated_prob'].map(lambda x:f'{x:.1%}')
            st.dataframe(show.rename(columns={'player':'Player','market_name':'Market','line':'Underdog line','direction':'Side','estimated_prob':'Model probability','projection':'Projected stat','momentum_delta':'Recent − baseline','sample_games':'Games','updated_at':'Line updated'}),hide_index=True,use_container_width=True)
            st.download_button('Export research rankings',view.to_csv(index=False),'nfl_prop_rankings.csv','text/csv')
with tabs[1]:
    st.header('Player Research')
    if logs is None: st.info('Load automatic NFL statistics or upload a player game-log CSV to start.')
    else:
        player=st.selectbox('Player',sorted(logs['player'].astype(str).unique()),key='research_player')
        available=[m for m in MARKETS if m in logs and logs.loc[logs.player.astype(str)==player,m].notna().any()]
        if available:
            market=st.selectbox('Stat market',available,format_func=lambda x:MARKETS[x])
            subset=logs[logs.player.astype(str)==player].dropna(subset=[market]).sort_values('game_date')
            if not subset.empty:
                k1,k2,k3=st.columns(3)
                k1.metric('Average',f'{subset[market].mean():.1f}')
                k2.metric('Last 5 average',f'{subset[market].tail(5).mean():.1f}')
                k3.metric('Games',len(subset))
                fig=px.line(subset,x='game_date',y=market,markers=True,hover_data=['opponent'],title=f'{player}: {MARKETS[market]}')
                st.plotly_chart(fig,use_container_width=True)
                st.dataframe(subset[['game_date','opponent',market]].sort_values('game_date',ascending=False),hide_index=True,use_container_width=True)
        else: st.warning('No supported market columns found for this player.')
with tabs[2]:
    st.header('Momentum Tracker')
    st.write('Momentum is measured as the last-five-game average minus the available historical average. It is descriptive, not proof that a trend will continue.')
    if results.empty: st.info('Load NFL statistics and upload an Underdog board CSV to compare recent form with the baseline.')
    else:
        momentum=results[['player','market_name','season_mean','recent_mean','momentum_delta','sample_games']].sort_values('momentum_delta',ascending=False)
        st.dataframe(momentum,hide_index=True,use_container_width=True)
        st.caption('Different market units are not directly comparable. Do not interpret a 10-yard change as equivalent to a 10-reception change.')
with tabs[3]:
    st.header('Defensive Matchup Research')
    st.write('Coverage shells, man/zone rates, blitz rates, pressure, defensive personnel, injuries, and offensive scheme fit belong here. No verified scheme-level dataset is connected yet.')
    st.warning('The sidebar matchup adjustment is a manual scenario tool, not a measured defensive advantage. It is applied globally to the current projections and should remain at 0% unless you are testing a clearly documented hypothesis.')
    st.markdown('**Planned defensive data fields:** coverage type and frequency; pressure and blitz rate; defensive front and box counts; slot/outside matchup; personnel availability; opponent-adjusted efficiency; and data-source timestamp.')
    st.markdown('**Important:** defensive tendencies vary by opponent, down, distance, and personnel. A team-wide coverage percentage should not automatically determine a player projection.')
with tabs[4]:
    st.header('Model Evaluation')
    st.warning('The current model is a transparent baseline, not a backtested or calibrated prediction model. Do not treat its probabilities as established hit rates.')
    st.markdown('Next milestone: walk-forward validation using only information available **before each game**. We will measure calibration, Brier score, log loss, and performance by market, season, and player sample size. Historical Underdog lines will be required for realistic line-based backtesting.')
    st.markdown('A positive-EV claim additionally requires the applicable Underdog entry payout, joint pick probability, and any relevant product rules. Those are not implemented in Version 1.')
with tabs[5]:
    st.header('CSV Data Guide')
    st.markdown('**Game logs:** one row per player per game. Required columns: `player`, `game_date`, `opponent`. Add any supported market columns below using the exact machine-readable names.')
    st.code(', '.join(MARKETS.keys()))
    st.markdown('**Underdog board:** one row per currently offered projection. Required columns: `player`, `market`, `line`. Optional: `updated_at`, `pick_type` (`standard` or other). Player names must match game logs exactly.')
    sample_logs=pd.DataFrame([{'player':'Example Player','game_date':'2026-09-13','opponent':'EXAMPLE','receiving_yards':70,'receptions':5},{'player':'Example Player','game_date':'2026-09-20','opponent':'EXAMPLE','receiving_yards':82,'receptions':6}])
    sample_lines=pd.DataFrame([{'player':'Example Player','market':'receiving_yards','line':74.5,'updated_at':'2026-11-19T12:00:00-06:00','pick_type':'standard'}])
    st.caption('Example rows are fictional and insufficient for a prediction. The model requires at least five game observations.')
    x,y=st.columns(2)
    x.download_button('Download game-log template',sample_logs.to_csv(index=False),'game_logs_template.csv','text/csv')
    y.download_button('Download Underdog board template',sample_lines.to_csv(index=False),'underdog_board_template.csv','text/csv')
    st.markdown('**Data safety:** never put Underdog account credentials or API keys into a CSV or public GitHub repository. Confirm that any automated data collection complies with the source terms.')
