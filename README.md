# NFL Prop Lab — Underdog Higher / Lower Research

An early-stage Streamlit NFL player-prop research dashboard with player game logs, recent-form analysis, manual matchup scenarios, and imported Underdog projections.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

1. Create a new GitHub repository (e.g. `nfl-prop-lab`).
2. Upload `app.py`, `requirements.txt`, and `README.md` to the repository root.
3. In Streamlit Community Cloud, select **Create app**, choose the repository, branch `main`, and entry point `app.py`.
4. Deploy, then upload CSVs through the app sidebar.

## Data inputs

- Game logs CSV: `player`, `game_date`, `opponent`, plus supported market columns such as `receiving_yards`, `receptions`, `rushing_yards`, `passing_yards`, etc.
- Underdog board CSV: `player`, `market`, `line`, optional `updated_at`, `pick_type`.
- Player names must match exactly. At least 5 observations are required per player-market.
- Uploaded CSVs are session inputs and are not stored persistently by this application.

## Limitations

This is a research prototype, not a wagering recommendation system. It has no automatic Underdog connection, no verified live lines, no defensive tracking-data integration, no validated momentum effect, no backtested/calibrated probabilities, no Underdog payout model, and no entry-correlation analysis. Estimated probabilities use a simple normal approximation and can be particularly unreliable for discrete, rare-event markets such as touchdowns. Do not interpret rankings as established edges or guaranteed outcomes.

## Next steps

1. Add a trustworthy historical NFL statistics ingestion pipeline.
2. Build a market-by-market model with walk-forward backtesting and calibration.
3. Integrate verified matchup, injury, and scheme information with source timestamps.
4. Investigate permitted, reliable current Underdog projection ingestion.
5. Add Underdog-specific entry rules, payouts, and pick correlation analysis.
