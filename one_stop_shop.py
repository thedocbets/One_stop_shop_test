"""Streamlit MLB Betting Model Skeleton
=====================================
Brandon – clone this file, run `streamlit run app.py`.
Fills in:
1. Team & probable‐pitcher dropdown sourced from MLB StatsAPI.
2. DraftKings odds pull stub (replace TODO with real endpoint parsing).
3. Basic model placeholder returning random edge% (to be replaced by true calc).
4. Stake‐manager cap (1 % per bet, 5 % slate).
"""

import os
import datetime as dt
import json
from typing import Tuple

import pandas as pd
import requests
import streamlit as st

# ----------------------------- CONFIG ----------------------------------
DK_EVENT_GROUP_ID = 84240  # MLB regular season; may change yearly
MAX_UNIT_PCT = 0.01  # 1 %
MAX_SLATE_PCT = 0.05  # 5 %

# ---------------------- DATA INGESTION LAYER ---------------------------

def fetch_mlb_schedule(date: dt.date) -> pd.DataFrame:
    """Return DataFrame with games and probable pitchers for the date."""
    url = (
        "https://statsapi.mlb.com/api/v1/schedule?date=" + date.strftime("%Y-%m-%d")
        + "&sportId=1&hydrate=probablePitcher(note),lineups"
    )
    resp = requests.get(url, timeout=10).json()
    games = []
    for date_block in resp.get("dates", []):
        for game in date_block.get("games", []):
            games.append(
                {
                    "gamePk": game["gamePk"],
                    "away": game["teams"]["away"]["team"]["name"],
                    "home": game["teams"]["home"]["team"]["name"],
                    "away_pitcher": (
                        game["teams"]["away"].get("probablePitcher", {})
                    ).get("fullName", "TBA"),
                    "home_pitcher": (
                        game["teams"]["home"].get("probablePitcher", {})
                    ).get("fullName", "TBA"),
                }
            )
    return pd.DataFrame(games)


def pull_dk_props(game_pk: int) -> pd.DataFrame:
    """Stub – query DraftKings API for player prop markets for game_pk."""
    # TODO: reverse‐engineer DK event path; for now return empty.
    return pd.DataFrame(
        [], columns=["player", "market", "line", "odds"]
    )


# ----------------------- MODEL PLACEHOLDER -----------------------------

def dummy_edge_calc(row) -> Tuple[float, float]:
    """Return (true_prob, edge_pct) placeholders."""
    import random

    true_p = random.uniform(0.45, 0.65)
    # Convert American odds to break‐even prob
    odds = row["odds"]
    be = 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)
    edge = true_p - be
    return round(true_p * 100, 1), round(edge * 100, 1)


# ------------------------------ UI -------------------------------------

def main():
    st.title("⚾ One‑Stop MLB Model – Prototype")

    # Select date
    slate_date = st.sidebar.date_input(
        "Choose slate date", value=dt.date.today()
    )
    schedule_df = fetch_mlb_schedule(slate_date)
    if schedule_df.empty:
        st.error("No MLB games found for this date.")
        return

    # Game selector
    game_options = (
        schedule_df["away"] + " @ " + schedule_df["home"] + " – "
        + schedule_df["away_pitcher"] + " vs " + schedule_df["home_pitcher"]
    )
    choice = st.sidebar.selectbox("Select game", game_options)
    game_row = schedule_df.loc[game_options == choice].iloc[0]

    st.subheader(f"Selected: {choice}")

    # Pull DK props (stub)
    dk_df = pull_dk_props(game_row["gamePk"])
    if dk_df.empty:
        st.info("DraftKings prop pull not implemented yet – paste odds below.")
        player = st.text_input("Player name")
        market = st.selectbox(
            "Market", ["K", "Outs", "Total Bases", "HR", "Hits"]
        )
        line = st.text_input("Line (e.g. 5.5)")
        odds = st.number_input("Odds (American, e.g. -120)", step=1)
        if st.button("Add prop"):
            dk_df = dk_df.append(
                {"player": player, "market": market, "line": line, "odds": odds},
                ignore_index=True,
            )

    if not dk_df.empty:
        st.write("### Enter stake (units) for each prop, then run model:")
        dk_df["stake"] = 0.0
        edited_df = st.data_editor(dk_df, num_rows="dynamic")

        if st.button("Run Model"):
            results = []
            total_risk = 0.0
            for _, r in edited_df.iterrows():
                true_p, edge = dummy_edge_calc(r)
                results.append({**r, "true_prob%": true_p, "edge%": edge})
                total_risk += r["stake"] * MAX_UNIT_PCT
            res_df = pd.DataFrame(results)
            st.write("## Results")
            st.dataframe(res_df)
            if total_risk > MAX_SLATE_PCT:
                st.warning(
                    f"Slate risk {total_risk*100:.1f}% exceeds 5% bankroll cap!"
                )


if __name__ == "__main__":
    main()
