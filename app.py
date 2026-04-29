import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="World Cup Intelligence Dashboard", layout="wide")

st.title("⚽ FIFA World Cup Intelligence Dashboard")

st.markdown("""
### Historical Knockout Match Analytics & Performance Insights

Analyzing FIFA World Cup knockout-stage matches using real StatsBomb event data to explore:
- expected goals (xG)
- attacking efficiency
- shot quality
- momentum trends
- match-winning patterns

Built with Python, Streamlit, Plotly, and real football event data.
""")

matches = {

    "2018 Final — France vs Croatia": {
        "id": 8658,
        "winner": "France",
        "score": "🇫🇷 France 4 - 2 Croatia 🇭🇷"
    },

    "2022 Final — Argentina vs France": {
        "id": 3869685,
        "winner": "Argentina",
        "score": "🇦🇷 Argentina 3 - 3 France 🇫🇷 (4-2 Pens)"
    },
}

all_data = []

for match_name, info in matches.items():
    match_id = info["id"]
    winner = info["winner"]

    url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json"
    response = requests.get(url)

    if response.status_code != 200:
        continue

    events = response.json()
    df = pd.json_normalize(events)

    shots = df[df["type.name"] == "Shot"].copy()
    teams = df["team.name"].dropna().unique()

    for team in teams:
        team_shots = shots[shots["team.name"] == team]

        total_shots = len(team_shots)
        total_xg = team_shots["shot.statsbomb_xg"].fillna(0).sum()
        efficiency = total_xg / total_shots if total_shots > 0 else 0
        result = "Winner" if team == winner else "Loser"

        all_data.append({
            "Match": match_name,
            "Team": team,
            "Result": result,
            "Shots": total_shots,
            "Total_xG": round(total_xg, 2),
            "xG_per_Shot": round(efficiency, 3)
        })

results = pd.DataFrame(all_data)

st.header("🏆 Winners vs Losers Analysis")

comparison = results.groupby("Result")[["Shots", "Total_xG", "xG_per_Shot"]].mean().reset_index()

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(
        comparison,
        x="Result",
        y="Total_xG",
        color="Result",
        title="Average xG: Winners vs Losers"
    )
    fig1.update_layout(template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(
        comparison,
        x="Result",
        y="xG_per_Shot",
        color="Result",
        title="Shot Quality: Winners vs Losers"
    )
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

st.header("🎮 Match Explorer")

selected_match = st.selectbox("Choose a Match", list(matches.keys()))

selected_id = matches[selected_match]["id"]
selected_score = matches[selected_match]["score"]
selected_winner = matches[selected_match]["winner"]

st.subheader(f"🏁 Final Score: {selected_score}")

url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{selected_id}.json"
events = requests.get(url).json()
match_df = pd.json_normalize(events)

shots = match_df[match_df["type.name"] == "Shot"].copy()

shots["xG"] = shots["shot.statsbomb_xg"].fillna(0)
shots["Minute"] = shots["minute"]

team_stats = shots.groupby("team.name").agg(
    Shots=("type.name", "count"),
    Total_xG=("xG", "sum"),
    Avg_xG_per_Shot=("xG", "mean")
).reset_index()

team_stats["Total_xG"] = team_stats["Total_xG"].round(2)
team_stats["Avg_xG_per_Shot"] = team_stats["Avg_xG_per_Shot"].round(3)

st.subheader("📌 Match Summary")

m1, m2, m3 = st.columns(3)
m1.metric("Total Shots", int(team_stats["Shots"].sum()))
m2.metric("Total xG", round(team_stats["Total_xG"].sum(), 2))
m3.metric("Highest Team xG", round(team_stats["Total_xG"].max(), 2))

st.subheader("🧠 Auto Match Insights")

top_xg_team = team_stats.loc[team_stats["Total_xG"].idxmax()]
most_shots_team = team_stats.loc[team_stats["Shots"].idxmax()]
best_eff_team = team_stats.loc[team_stats["Avg_xG_per_Shot"].idxmax()]

c1, c2, c3 = st.columns(3)

with c1:
    st.info(
        f"{top_xg_team['team.name']} created the most dangerous chances with {top_xg_team['Total_xG']} xG."
    )

with c2:
    st.info(
        f"{most_shots_team['team.name']} attempted the most shots with {int(most_shots_team['Shots'])} attempts."
    )

with c3:
    st.info(
        f"{best_eff_team['team.name']} had the highest shot quality averaging {best_eff_team['Avg_xG_per_Shot']} xG per shot."
    )

st.header("📈 xG Progression")

xg_progression = (
    shots.groupby(["Minute", "team.name"])["xG"]
    .sum()
    .groupby(level=1)
    .cumsum()
    .reset_index()
)

fig3 = px.line(
    xg_progression,
    x="Minute",
    y="xG",
    color="team.name",
    title="xG Progression Throughout Match"
)

fig3.update_layout(template="plotly_dark")
st.plotly_chart(fig3, use_container_width=True)

st.header("⏱ Shot Timeline")

fig4 = px.scatter(
    shots,
    x="Minute",
    y="team.name",
    size="xG",
    color="team.name",
    hover_data=["player.name", "shot.outcome.name", "xG"],
    title="Shot Timeline"
)

fig4.update_layout(template="plotly_dark")
st.plotly_chart(fig4, use_container_width=True)

st.header("🎯 Professional Shot Map")

shot_locations = shots.dropna(subset=["location"]).copy()

shot_locations["x"] = shot_locations["location"].apply(lambda loc: loc[0])
shot_locations["y"] = shot_locations["location"].apply(lambda loc: 80 - loc[1])

fig5 = go.Figure()

team_list = list(shot_locations["team.name"].unique())

colors = {}
if len(team_list) >= 1:
    colors[team_list[0]] = "#00BFFF"
if len(team_list) >= 2:
    colors[team_list[1]] = "#FF4B4B"

for team in team_list:
    team_data = shot_locations[shot_locations["team.name"] == team]

    fig5.add_trace(
        go.Scatter(
            x=team_data["x"],
            y=team_data["y"],
            mode="markers",
            name=team,
            text=team_data["player.name"],
            customdata=team_data[["xG", "shot.outcome.name"]],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "xG: %{customdata[0]:.2f}<br>"
                "Outcome: %{customdata[1]}<extra></extra>"
            ),
            marker=dict(
                size=(team_data["xG"] * 40) + 6,
                color=colors.get(team, "#FFFFFF"),
                opacity=0.75,
                line=dict(width=1, color="white")
            )
        )
    )

pitch_shapes = [
    dict(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color="white", width=2)),
    dict(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color="white", width=2)),
    dict(type="circle", x0=50, y0=30, x1=70, y1=50, line=dict(color="white", width=2)),
    dict(type="rect", x0=0, y0=18, x1=18, y1=62, line=dict(color="white", width=2)),
    dict(type="rect", x0=102, y0=18, x1=120, y1=62, line=dict(color="white", width=2)),
    dict(type="rect", x0=0, y0=30, x1=6, y1=50, line=dict(color="white", width=2)),
    dict(type="rect", x0=114, y0=30, x1=120, y1=50, line=dict(color="white", width=2)),
]

fig5.update_layout(
    template="plotly_dark",
    title="Shot Locations on Pitch",
    xaxis=dict(
        range=[0, 120],
        showgrid=False,
        zeroline=False,
        visible=False
    ),
    yaxis=dict(
        range=[0, 80],
        showgrid=False,
        zeroline=False,
        visible=False,
        scaleanchor="x",
        scaleratio=1
    ),
    shapes=pitch_shapes,
    height=650,
    plot_bgcolor="#0B1020",
    paper_bgcolor="#0B1020"
)

st.plotly_chart(fig5, use_container_width=True)

st.header("📊 Match Data")
st.dataframe(results)

st.header("📖 Tournament Findings")

winner_avg_xg = comparison[comparison["Result"] == "Winner"]["Total_xG"].values[0]
loser_avg_xg = comparison[comparison["Result"] == "Loser"]["Total_xG"].values[0]
winner_shot_quality = comparison[comparison["Result"] == "Winner"]["xG_per_Shot"].values[0]
loser_shot_quality = comparison[comparison["Result"] == "Loser"]["xG_per_Shot"].values[0]
winner_shots = comparison[comparison["Result"] == "Winner"]["Shots"].values[0]
loser_shots = comparison[comparison["Result"] == "Loser"]["Shots"].values[0]

st.success(
    f"Winners averaged {winner_avg_xg:.2f} xG compared to losers averaging {loser_avg_xg:.2f} xG."
)

if winner_shot_quality > loser_shot_quality:
    st.info(
        f"Winning teams generated higher quality chances per shot "
        f"({winner_shot_quality:.3f} xG/shot) compared to losing teams "
        f"({loser_shot_quality:.3f} xG/shot)."
    )
else:
    st.warning("Losing teams surprisingly generated better shot quality than winners in the selected sample.")

if winner_shots > loser_shots:
    st.info(
        f"Winners also attempted more shots on average "
        f"({winner_shots:.1f} vs {loser_shots:.1f})."
    )
else:
    st.warning(
        "Winners often succeeded despite taking fewer shots, suggesting efficiency mattered more than volume."
    )

st.markdown("---")

st.subheader("📌 Analyst Conclusion")

st.write(
    """
    This dashboard suggests that knockout-stage success in the FIFA World Cup
    is strongly tied to chance quality and attacking efficiency rather than
    simply total shot volume.

    Teams that generated higher expected-goal value opportunities
    were more likely to advance or win major matches.
    """
)

st.markdown("---")

st.header("🔮 2026 World Cup Outlook")

st.write(
    """
    Based on historical knockout-stage analysis, teams that succeed in the FIFA World Cup
    tend to generate higher quality scoring opportunities rather than relying purely on
    shot volume.

    The data suggests that attacking efficiency, chance quality, and clinical finishing
    may be stronger indicators of tournament success than possession dominance alone.
    """
)

st.info(
    """
    Potential 2026 analytical focus areas:

    • Which national teams generate the highest quality chances?

    • Do possession-heavy systems still succeed in knockout football?

    • Which teams outperform their expected goals?

    • Can attacking efficiency predict deep tournament runs?
    """
)

st.success(
    """
    Future versions of this dashboard could integrate live 2026 World Cup data
    to track match momentum, expected goals, and tournament trends in real time.
    """
)

st.markdown("---")

st.caption(
    "Data Source: StatsBomb Open Data | Dashboard created for sports analytics and educational research purposes."
)