from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

RAW_DATA = ROOT / "data" / "raw"
OUTPUT_DATA = ROOT / "assets" / "data" / "dynasty"

OUTPUT_DATA.mkdir(parents=True, exist_ok=True)

FRANCHISE_MAP = {
    "559134002064789504": "1002342256092762112",
    "626798676303499264": "517080755628453888",
}

FRANCHISE_NAMES = {
    "1002342256092762112": "steeeeeeeeeve",
    "517080755628453888": "RJRJRJ123",
}

regular = pd.read_csv(
    RAW_DATA / "sleeper_matchups.csv",
    dtype={
        "owner_id_1": "string",
        "owner_id_2": "string",
    },
)

postseason = pd.read_csv(
    RAW_DATA / "sleeper_postseason_matchups.csv",
    dtype={
        "owner_id_1": "string",
        "owner_id_2": "string",
    },
)

regular["phase"] = "Regular Season"
postseason["phase"] = "Postseason"

games = pd.concat(
    [regular, postseason],
    ignore_index=True,
)

games["score_1"] = pd.to_numeric(
    games["score_1"],
    errors="coerce",
)

games["score_2"] = pd.to_numeric(
    games["score_2"],
    errors="coerce",
)

# Remove future / unplayed 0-0 matchups
games = games[
    ~(
        (games["score_1"] == 0)
        & (games["score_2"] == 0)
    )
].copy()

# Apply franchise continuity rules
for side in [1, 2]:
    owner_col = f"owner_id_{side}"
    manager_col = f"manager_{side}"

    games[owner_col] = (
        games[owner_col]
        .astype("string")
        .replace(FRANCHISE_MAP)
    )

    for owner_id, manager_name in FRANCHISE_NAMES.items():
        games.loc[
            games[owner_col] == owner_id,
            manager_col,
        ] = manager_name

games = games.sort_values(
    ["season", "week", "phase"]
).reset_index(drop=True)

print()
print("DIAMOND DYNASTY DATA")
print("--------------------")
print(f"Completed games: {len(games)}")

print()
print(games["phase"].value_counts().to_string())

print()
print(
    "Seasons:",
    sorted(games["season"].unique())
)

matchup_file = OUTPUT_DATA / "matchups.json"

games.to_json(
    matchup_file,
    orient="records",
    indent=2,
)

summary = {
    "completed_games": int(len(games)),
    "regular_season_games": int(
        (games["phase"] == "Regular Season").sum()
    ),
    "postseason_games": int(
        (games["phase"] == "Postseason").sum()
    ),
    "seasons": [
        int(x)
        for x in sorted(games["season"].unique())
    ],
}

with open(
    OUTPUT_DATA / "summary.json",
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        summary,
        file,
        indent=2,
    )

print()
print("Website files created:")
print(matchup_file)
print(OUTPUT_DATA / "summary.json")