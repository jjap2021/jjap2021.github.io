from pathlib import Path
import pandas as pd
import json

# ==================================================
# Configuration
# ==================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "assets" / "data" / "dynasty"
MATCHUPS_FILE = DATA_DIR / "matchups.json"


# ==================================================
# Load data
# ==================================================

def load_games():
    """Load cleaned Diamond Dynasty matchup data."""

    games = pd.read_json(MATCHUPS_FILE)

    games = games.sort_values(
        ["season", "week", "phase"]
    ).reset_index(drop=True)

    return games


# ==================================================
# Franchise helpers
# ==================================================

def get_managers(games):
    """Return a sorted list of all current franchise names."""

    managers = sorted(
        set(games["manager_1"])
        .union(games["manager_2"])
    )

    return managers


# ==================================================
# Standardize matchup results
# ==================================================

def build_game_results(games):
    """
    Convert each matchup into a standardized result row.

    Adds:
    - winner
    - loser
    - margin
    - total_points
    """

    game_results = []

    for _, game in games.iterrows():

        manager_1 = game["manager_1"]
        manager_2 = game["manager_2"]

        score_1 = float(game["score_1"])
        score_2 = float(game["score_2"])

        if score_1 > score_2:
            winner = manager_1
            loser = manager_2

        elif score_2 > score_1:
            winner = manager_2
            loser = manager_1

        else:
            winner = None
            loser = None

        game_results.append(
            {
                "season": int(game["season"]),
                "week": int(game["week"]),
                "phase": game["phase"],
                "manager_1": manager_1,
                "manager_2": manager_2,
                "score_1": score_1,
                "score_2": score_2,
                "winner": winner,
                "loser": loser,
                "margin": round(
                    abs(score_1 - score_2),
                    2,
                ),
                "total_points": round(
                    score_1 + score_2,
                    2,
                ),
            }
        )

    return pd.DataFrame(game_results)


# ==================================================
# Shared manager-stat calculator
# ==================================================

def calculate_manager_stats(games, manager):
    """
    Calculate record and scoring statistics for one
    manager from any subset of games.
    """

    manager_games = games[
        (games["manager_1"] == manager)
        | (games["manager_2"] == manager)
    ]

    if manager_games.empty:
        return None

    wins = int(
        (manager_games["winner"] == manager).sum()
    )

    losses = int(
        (manager_games["loser"] == manager).sum()
    )

    games_played = wins + losses

    points_for = (
        manager_games.loc[
            manager_games["manager_1"] == manager,
            "score_1",
        ].sum()
        +
        manager_games.loc[
            manager_games["manager_2"] == manager,
            "score_2",
        ].sum()
    )

    points_against = (
        manager_games.loc[
            manager_games["manager_1"] == manager,
            "score_2",
        ].sum()
        +
        manager_games.loc[
            manager_games["manager_2"] == manager,
            "score_1",
        ].sum()
    )

    point_diff = points_for - points_against

    win_pct = (
        wins / games_played
        if games_played
        else 0
    )

    avg_points = (
        points_for / games_played
        if games_played
        else 0
    )

    avg_points_against = (
        points_against / games_played
        if games_played
        else 0
    )

    return {
        "wins": wins,
        "losses": losses,
        "games": games_played,
        "win_pct": round(win_pct, 4),
        "points_for": round(points_for, 2),
        "points_against": round(
            points_against,
            2,
        ),
        "point_diff": round(
            point_diff,
            2,
        ),
        "avg_points": round(
            avg_points,
            2,
        ),
        "avg_points_against": round(
            avg_points_against,
            2,
        ),
    }


# ==================================================
# All-time standings
# ==================================================

def build_all_time_standings(results, managers):

    standings = []

    for manager in managers:

        stats = calculate_manager_stats(
            results,
            manager,
        )

        standings.append(
            {
                "manager": manager,
                **stats,
            }
        )

    standings_df = pd.DataFrame(
        standings
    )

    standings_df = standings_df.sort_values(
        [
            "wins",
            "win_pct",
            "point_diff",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    ).reset_index(drop=True)

    return standings_df


# ==================================================
# Head-to-head records
# ==================================================

def build_h2h(results, managers):

    h2h_records = []

    for manager in managers:

        for opponent in managers:

            if manager == opponent:
                continue

            matchup_games = results[
                (
                    (
                        results["manager_1"]
                        == manager
                    )
                    &
                    (
                        results["manager_2"]
                        == opponent
                    )
                )
                |
                (
                    (
                        results["manager_1"]
                        == opponent
                    )
                    &
                    (
                        results["manager_2"]
                        == manager
                    )
                )
            ]

            stats = calculate_manager_stats(
                matchup_games,
                manager,
            )

            if stats is None:
                continue

            h2h_records.append(
                {
                    "manager": manager,
                    "opponent": opponent,
                    **stats,
                }
            )

    return pd.DataFrame(h2h_records)


# ==================================================
# H2H display matrix
# ==================================================

def build_h2h_matrix(
    h2h_df,
    managers,
):

    matrix = pd.DataFrame(
        index=managers,
        columns=managers,
    )

    for manager in managers:

        for opponent in managers:

            if manager == opponent:
                matrix.loc[
                    manager,
                    opponent,
                ] = "—"

                continue

            record = h2h_df[
                (
                    h2h_df["manager"]
                    == manager
                )
                &
                (
                    h2h_df["opponent"]
                    == opponent
                )
            ]

            if record.empty:
                matrix.loc[
                    manager,
                    opponent,
                ] = "0-0"

                continue

            row = record.iloc[0]

            matrix.loc[
                manager,
                opponent,
            ] = (
                f"{row['wins']}-"
                f"{row['losses']}"
            )

    return matrix


# ==================================================
# Season-by-season records
# ==================================================

def build_season_records(
    results,
    managers,
):

    season_records = []

    seasons = sorted(
        results["season"].unique()
    )

    for season in seasons:

        season_games = results[
            results["season"] == season
        ]

        for manager in managers:

            stats = calculate_manager_stats(
                season_games,
                manager,
            )

            if stats is None:
                continue

            season_records.append(
                {
                    "season": int(season),
                    "manager": manager,

                    # These currently include all
                    # postseason-week games.
                    "scope": "Full Season",

                    **stats,
                }
            )

    season_records_df = pd.DataFrame(
        season_records
    )

    season_records_df = (
        season_records_df.sort_values(
            [
                "season",
                "wins",
                "win_pct",
                "point_diff",
            ],
            ascending=[
                True,
                False,
                False,
                False,
            ],
        )
        .reset_index(drop=True)
    )

    return season_records_df


def build_streaks(results, managers):
    """
    Calculate each manager's longest winning streak,
    longest losing streak, and current streak.
    """

    streak_records = []

    results_sorted = results.sort_values(
        ["season", "week"]
    ).reset_index(drop=True)

    for manager in managers:
        manager_games = results_sorted[
            (results_sorted["manager_1"] == manager)
            | (results_sorted["manager_2"] == manager)
        ].copy()

        outcomes = []

        for _, game in manager_games.iterrows():
            if game["winner"] == manager:
                outcomes.append("W")
            elif game["loser"] == manager:
                outcomes.append("L")
            else:
                outcomes.append("T")

        longest_win_streak = 0
        longest_loss_streak = 0

        current_win_streak = 0
        current_loss_streak = 0

        for outcome in outcomes:
            if outcome == "W":
                current_win_streak += 1
                current_loss_streak = 0

                longest_win_streak = max(
                    longest_win_streak,
                    current_win_streak,
                )

            elif outcome == "L":
                current_loss_streak += 1
                current_win_streak = 0

                longest_loss_streak = max(
                    longest_loss_streak,
                    current_loss_streak,
                )

            else:
                current_win_streak = 0
                current_loss_streak = 0

        current_streak = 0
        current_streak_type = None

        if outcomes:
            last_outcome = outcomes[-1]

            if last_outcome in ("W", "L"):
                current_streak_type = last_outcome

                for outcome in reversed(outcomes):
                    if outcome == last_outcome:
                        current_streak += 1
                    else:
                        break

        streak_records.append(
            {
                "manager": manager,
                "longest_win_streak": int(
                    longest_win_streak
                ),
                "longest_loss_streak": int(
                    longest_loss_streak
                ),
                "current_streak_type": current_streak_type,
                "current_streak": int(current_streak),
            }
        )

    return pd.DataFrame(streak_records)

def build_rivalries(results, managers):
    """
    Build rivalry-level statistics for every unique
    franchise matchup.
    """

    rivalry_records = []

    results_sorted = results.sort_values(
        ["season", "week"]
    ).reset_index(drop=True)

    for i, manager_1 in enumerate(managers):

        for manager_2 in managers[i + 1:]:

            matchup_games = results_sorted[
                (
                    (results_sorted["manager_1"] == manager_1)
                    & (results_sorted["manager_2"] == manager_2)
                )
                |
                (
                    (results_sorted["manager_1"] == manager_2)
                    & (results_sorted["manager_2"] == manager_1)
                )
            ].copy()

            if matchup_games.empty:
                continue

            # --------------------------------------------------
            # Overall record
            # --------------------------------------------------

            manager_1_wins = int(
                (matchup_games["winner"] == manager_1).sum()
            )

            manager_2_wins = int(
                (matchup_games["winner"] == manager_2).sum()
            )

            ties = int(
                matchup_games["winner"].isna().sum()
            )

            total_games = len(matchup_games)

            # --------------------------------------------------
            # Points
            # --------------------------------------------------

            manager_1_points = (
                matchup_games.loc[
                    matchup_games["manager_1"] == manager_1,
                    "score_1",
                ].sum()
                +
                matchup_games.loc[
                    matchup_games["manager_2"] == manager_1,
                    "score_2",
                ].sum()
            )

            manager_2_points = (
                matchup_games.loc[
                    matchup_games["manager_1"] == manager_2,
                    "score_1",
                ].sum()
                +
                matchup_games.loc[
                    matchup_games["manager_2"] == manager_2,
                    "score_2",
                ].sum()
            )

            avg_manager_1_score = (
                manager_1_points / total_games
            )

            avg_manager_2_score = (
                manager_2_points / total_games
            )

            combined_points = (
                manager_1_points
                + manager_2_points
            )

            avg_combined_score = (
                combined_points / total_games
            )

            # --------------------------------------------------
            # Closest game
            # --------------------------------------------------

            non_ties = matchup_games[
                matchup_games["margin"] > 0
            ]

            if not non_ties.empty:
                closest_game = non_ties.loc[
                    non_ties["margin"].idxmin()
                ]
            else:
                closest_game = matchup_games.iloc[0]

            # --------------------------------------------------
            # Biggest blowout
            # --------------------------------------------------

            biggest_blowout = matchup_games.loc[
                matchup_games["margin"].idxmax()
            ]

            # --------------------------------------------------
            # Highest scoring meeting
            # --------------------------------------------------

            highest_scoring_game = matchup_games.loc[
                matchup_games["total_points"].idxmax()
            ]

            # --------------------------------------------------
            # Postseason meetings
            # --------------------------------------------------

            postseason_games = matchup_games[
                matchup_games["phase"] == "Postseason"
            ]

            postseason_meetings = len(
                postseason_games
            )

            manager_1_postseason_wins = int(
                (
                    postseason_games["winner"]
                    == manager_1
                ).sum()
            )

            manager_2_postseason_wins = int(
                (
                    postseason_games["winner"]
                    == manager_2
                ).sum()
            )

            # --------------------------------------------------
            # Current rivalry streak
            # --------------------------------------------------

            outcomes = []

            for _, game in matchup_games.iterrows():

                if game["winner"] == manager_1:
                    outcomes.append(manager_1)

                elif game["winner"] == manager_2:
                    outcomes.append(manager_2)

                else:
                    outcomes.append(None)

            current_streak_manager = None
            current_streak = 0

            if outcomes:

                last_winner = outcomes[-1]

                if last_winner is not None:

                    current_streak_manager = last_winner

                    for winner in reversed(outcomes):

                        if winner == last_winner:
                            current_streak += 1
                        else:
                            break

            # --------------------------------------------------
            # Longest rivalry streak
            # --------------------------------------------------

            longest_streak_manager = None
            longest_streak = 0

            active_manager = None
            active_streak = 0

            for winner in outcomes:

                if winner is None:
                    active_manager = None
                    active_streak = 0
                    continue

                if winner == active_manager:
                    active_streak += 1

                else:
                    active_manager = winner
                    active_streak = 1

                if active_streak > longest_streak:
                    longest_streak = active_streak
                    longest_streak_manager = active_manager

            # --------------------------------------------------
            # Game history
            # --------------------------------------------------

            game_history = []

            for _, game in matchup_games.iterrows():

                if game["manager_1"] == manager_1:

                    manager_1_score = float(
                        game["score_1"]
                    )

                    manager_2_score = float(
                        game["score_2"]
                    )

                else:

                    manager_1_score = float(
                        game["score_2"]
                    )

                    manager_2_score = float(
                        game["score_1"]
                    )

                game_history.append(
                    {
                        "season": int(
                            game["season"]
                        ),
                        "week": int(
                            game["week"]
                        ),
                        "phase": game["phase"],
                        "manager_1_score": round(
                            manager_1_score,
                            2,
                        ),
                        "manager_2_score": round(
                            manager_2_score,
                            2,
                        ),
                        "winner": game["winner"],
                        "margin": float(
                            game["margin"]
                        ),
                        "total_points": float(
                            game["total_points"]
                        ),
                    }
                )

            # --------------------------------------------------
            # Rivalry record
            # --------------------------------------------------

            rivalry_records.append(
                {
                    "manager_1": manager_1,
                    "manager_2": manager_2,

                    "games": int(
                        total_games
                    ),

                    "manager_1_wins": manager_1_wins,
                    "manager_2_wins": manager_2_wins,
                    "ties": ties,

                    "manager_1_points": round(
                        manager_1_points,
                        2,
                    ),

                    "manager_2_points": round(
                        manager_2_points,
                        2,
                    ),

                    "point_diff": round(
                        manager_1_points
                        - manager_2_points,
                        2,
                    ),

                    "avg_manager_1_score": round(
                        avg_manager_1_score,
                        2,
                    ),

                    "avg_manager_2_score": round(
                        avg_manager_2_score,
                        2,
                    ),

                    "avg_combined_score": round(
                        avg_combined_score,
                        2,
                    ),

                    "postseason_meetings": int(
                        postseason_meetings
                    ),

                    "manager_1_postseason_wins": (
                        manager_1_postseason_wins
                    ),

                    "manager_2_postseason_wins": (
                        manager_2_postseason_wins
                    ),

                    "current_streak_manager": (
                        current_streak_manager
                    ),

                    "current_streak": int(
                        current_streak
                    ),

                    "longest_streak_manager": (
                        longest_streak_manager
                    ),

                    "longest_streak": int(
                        longest_streak
                    ),

                    "closest_game": {
                        "season": int(
                            closest_game["season"]
                        ),
                        "week": int(
                            closest_game["week"]
                        ),
                        "phase": (
                            closest_game["phase"]
                        ),
                        "winner": (
                            closest_game["winner"]
                        ),
                        "margin": float(
                            closest_game["margin"]
                        ),
                        "score_1": float(
                            closest_game["score_1"]
                        ),
                        "score_2": float(
                            closest_game["score_2"]
                        ),
                        "manager_1": (
                            closest_game["manager_1"]
                        ),
                        "manager_2": (
                            closest_game["manager_2"]
                        ),
                    },

                    "biggest_blowout": {
                        "season": int(
                            biggest_blowout["season"]
                        ),
                        "week": int(
                            biggest_blowout["week"]
                        ),
                        "phase": (
                            biggest_blowout["phase"]
                        ),
                        "winner": (
                            biggest_blowout["winner"]
                        ),
                        "margin": float(
                            biggest_blowout["margin"]
                        ),
                        "score_1": float(
                            biggest_blowout["score_1"]
                        ),
                        "score_2": float(
                            biggest_blowout["score_2"]
                        ),
                        "manager_1": (
                            biggest_blowout["manager_1"]
                        ),
                        "manager_2": (
                            biggest_blowout["manager_2"]
                        ),
                    },

                    "highest_scoring_game": {
                        "season": int(
                            highest_scoring_game[
                                "season"
                            ]
                        ),
                        "week": int(
                            highest_scoring_game[
                                "week"
                            ]
                        ),
                        "phase": (
                            highest_scoring_game[
                                "phase"
                            ]
                        ),
                        "total_points": float(
                            highest_scoring_game[
                                "total_points"
                            ]
                        ),
                        "score_1": float(
                            highest_scoring_game[
                                "score_1"
                            ]
                        ),
                        "score_2": float(
                            highest_scoring_game[
                                "score_2"
                            ]
                        ),
                        "manager_1": (
                            highest_scoring_game[
                                "manager_1"
                            ]
                        ),
                        "manager_2": (
                            highest_scoring_game[
                                "manager_2"
                            ]
                        ),
                    },

                    "games_history": game_history,
                }
            )

    rivalries_df = pd.DataFrame(
        rivalry_records
    )

    rivalries_df = rivalries_df.sort_values(
        [
            "games",
            "manager_1",
            "manager_2",
        ],
        ascending=[
            False,
            True,
            True,
        ],
    ).reset_index(drop=True)

    return rivalries_df

# ==================================================
# Export files
# ==================================================


def export_data(
    standings_df,
    h2h_df,
    season_records_df,
    league_records,
    streaks_df,
    rivalries_df,
):
    """Export all dashboard data files."""

    files = {
        "standings": DATA_DIR / "standings.json",
        "h2h": DATA_DIR / "h2h.json",
        "seasons": DATA_DIR / "seasons.json",
        "records": DATA_DIR / "records.json",
        "streaks": DATA_DIR / "streaks.json",
        "rivalries": DATA_DIR / "rivalries.json",
    }

    standings_df.to_json(
        files["standings"],
        orient="records",
        indent=2,
    )

    h2h_df.to_json(
        files["h2h"],
        orient="records",
        indent=2,
    )

    season_records_df.to_json(
        files["seasons"],
        orient="records",
        indent=2,
    )

    with open(
        files["records"],
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            league_records,
            file,
            indent=2,
        )

    streaks_df.to_json(
    files["streaks"],
    orient="records",
    indent=2,
    )

    rivalries_df.to_json(
    files["rivalries"],
    orient="records",
    indent=2,
)

    return files


# ==================================================
# Console output
# ==================================================

def print_summary(
    games,
    managers,
    results,
    standings_df,
    h2h_matrix,
    season_records_df,
    exported_files,
):

    print()
    print("DIAMOND DYNASTY STATS")
    print("=====================")

    print()
    print(
        f"Completed games: "
        f"{len(results)}"
    )

    print(
        f"Franchises: "
        f"{len(managers)}"
    )

    seasons = [
        int(season)
        for season
        in sorted(
            games["season"].unique()
        )
    ]

    print(
        f"Seasons: "
        f"{seasons}"
    )

    print()
    print("ALL-TIME STANDINGS")
    print("------------------")

    print(
        standings_df[
            [
                "manager",
                "wins",
                "losses",
                "win_pct",
                "points_for",
                "points_against",
                "point_diff",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print("HEAD-TO-HEAD MATRIX")
    print("-------------------")

    print(
        h2h_matrix.to_string()
    )

    print()
    print("SEASON RECORDS")
    print("--------------")

    print(
        season_records_df[
            [
                "season",
                "manager",
                "wins",
                "losses",
                "points_for",
                "point_diff",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print(
        "Website stat files created:"
    )

    for path in exported_files.values():
        print(path)


# ==================================================
# Main
# ==================================================

def main():

    games = load_games()

    managers = get_managers(
        games
    )

    results = build_game_results(
        games
    )

    standings_df = (
        build_all_time_standings(
            results,
            managers,
        )
    )

    h2h_df = build_h2h(
        results,
        managers,
    )

    h2h_matrix = (
        build_h2h_matrix(
            h2h_df,
            managers,
        )
    )

    season_records_df = (
        build_season_records(
            results,
            managers,
        )
    )

    league_records = build_league_records(
    results,
    season_records_df,
)
    streaks_df = build_streaks(
    results,
    managers,
)

    rivalries_df = build_rivalries(
    results,
    managers,
)
    
    exported_files = export_data(
        standings_df,
        h2h_df,
        season_records_df,
        league_records,
        streaks_df,
        rivalries_df,
    )

    print_summary(
        games,
        managers,
        results,
        standings_df,
        h2h_matrix,
        season_records_df,
        exported_files,
    )



def build_league_records(results, season_records_df):
    """Build league-wide single-game and single-season records."""

    biggest_blowout = results.loc[
        results["margin"].idxmax()
    ]

    non_ties = results[
        results["margin"] > 0
    ]

    closest_game = non_ties.loc[
        non_ties["margin"].idxmin()
    ]

    highest_scoring_game = results.loc[
        results["total_points"].idxmax()
    ]

    lowest_scoring_game = results.loc[
        results["total_points"].idxmin()
    ]

    score_rows = []

    for _, game in results.iterrows():

        score_rows.append(
            {
                "season": int(game["season"]),
                "week": int(game["week"]),
                "phase": game["phase"],
                "manager": game["manager_1"],
                "opponent": game["manager_2"],
                "score": float(game["score_1"]),
                "opponent_score": float(game["score_2"]),
            }
        )

        score_rows.append(
            {
                "season": int(game["season"]),
                "week": int(game["week"]),
                "phase": game["phase"],
                "manager": game["manager_2"],
                "opponent": game["manager_1"],
                "score": float(game["score_2"]),
                "opponent_score": float(game["score_1"]),
            }
        )

    team_scores = pd.DataFrame(score_rows)

    highest_team_score = team_scores.loc[
        team_scores["score"].idxmax()
    ]

    lowest_team_score = team_scores.loc[
        team_scores["score"].idxmin()
    ]

    most_points_season = season_records_df.loc[
        season_records_df["points_for"].idxmax()
    ]

    best_win_pct_season = season_records_df.sort_values(
        ["win_pct", "wins", "point_diff"],
        ascending=[False, False, False],
    ).iloc[0]

    best_point_diff_season = season_records_df.loc[
        season_records_df["point_diff"].idxmax()
    ]

    worst_point_diff_season = season_records_df.loc[
        season_records_df["point_diff"].idxmin()
    ]

    return {
        "biggest_blowout": {
            "season": int(biggest_blowout["season"]),
            "week": int(biggest_blowout["week"]),
            "phase": biggest_blowout["phase"],
            "winner": biggest_blowout["winner"],
            "loser": biggest_blowout["loser"],
            "manager_1": biggest_blowout["manager_1"],
            "manager_2": biggest_blowout["manager_2"],
            "score_1": float(biggest_blowout["score_1"]),
            "score_2": float(biggest_blowout["score_2"]),
            "margin": float(biggest_blowout["margin"]),
        },

        "closest_game": {
            "season": int(closest_game["season"]),
            "week": int(closest_game["week"]),
            "phase": closest_game["phase"],
            "winner": closest_game["winner"],
            "loser": closest_game["loser"],
            "manager_1": closest_game["manager_1"],
            "manager_2": closest_game["manager_2"],
            "score_1": float(closest_game["score_1"]),
            "score_2": float(closest_game["score_2"]),
            "margin": float(closest_game["margin"]),
        },

        "highest_scoring_game": {
            "season": int(highest_scoring_game["season"]),
            "week": int(highest_scoring_game["week"]),
            "phase": highest_scoring_game["phase"],
            "manager_1": highest_scoring_game["manager_1"],
            "manager_2": highest_scoring_game["manager_2"],
            "score_1": float(highest_scoring_game["score_1"]),
            "score_2": float(highest_scoring_game["score_2"]),
            "total_points": float(
                highest_scoring_game["total_points"]
            ),
        },

        "lowest_scoring_game": {
            "season": int(lowest_scoring_game["season"]),
            "week": int(lowest_scoring_game["week"]),
            "phase": lowest_scoring_game["phase"],
            "manager_1": lowest_scoring_game["manager_1"],
            "manager_2": lowest_scoring_game["manager_2"],
            "score_1": float(lowest_scoring_game["score_1"]),
            "score_2": float(lowest_scoring_game["score_2"]),
            "total_points": float(
                lowest_scoring_game["total_points"]
            ),
        },

        "highest_team_score": {
            "season": int(highest_team_score["season"]),
            "week": int(highest_team_score["week"]),
            "phase": highest_team_score["phase"],
            "manager": highest_team_score["manager"],
            "opponent": highest_team_score["opponent"],
            "score": float(highest_team_score["score"]),
            "opponent_score": float(
                highest_team_score["opponent_score"]
            ),
        },

        "lowest_team_score": {
            "season": int(lowest_team_score["season"]),
            "week": int(lowest_team_score["week"]),
            "phase": lowest_team_score["phase"],
            "manager": lowest_team_score["manager"],
            "opponent": lowest_team_score["opponent"],
            "score": float(lowest_team_score["score"]),
            "opponent_score": float(
                lowest_team_score["opponent_score"]
            ),
        },

        "most_points_in_season": {
            "season": int(most_points_season["season"]),
            "manager": most_points_season["manager"],
            "points_for": float(
                most_points_season["points_for"]
            ),
            "wins": int(most_points_season["wins"]),
            "losses": int(most_points_season["losses"]),
        },

        "best_win_pct_season": {
            "season": int(best_win_pct_season["season"]),
            "manager": best_win_pct_season["manager"],
            "wins": int(best_win_pct_season["wins"]),
            "losses": int(best_win_pct_season["losses"]),
            "win_pct": float(
                best_win_pct_season["win_pct"]
            ),
        },

        "best_point_diff_season": {
            "season": int(best_point_diff_season["season"]),
            "manager": best_point_diff_season["manager"],
            "point_diff": float(
                best_point_diff_season["point_diff"]
            ),
        },

        "worst_point_diff_season": {
            "season": int(worst_point_diff_season["season"]),
            "manager": worst_point_diff_season["manager"],
            "point_diff": float(
                worst_point_diff_season["point_diff"]
            ),
        },
    }

if __name__ == "__main__":
    main()