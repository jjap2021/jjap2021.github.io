import json
import requests
from pathlib import Path


CURRENT_LEAGUE_ID = "1312085809582579712"

OUTPUT_DIR = Path("data/raw/transactions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_json(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def get_league(league_id):
    return get_json(
        f"https://api.sleeper.app/v1/league/{league_id}"
    )


def get_transactions(league_id):
    transactions = []

    for week in range(1, 19):
        url = (
            f"https://api.sleeper.app/v1/league/"
            f"{league_id}/transactions/{week}"
        )

        week_transactions = get_json(url)

        for transaction in week_transactions:
            transaction["requested_week"] = week

        transactions.extend(week_transactions)

    return transactions


def get_traded_picks(league_id):
    return get_json(
        f"https://api.sleeper.app/v1/league/"
        f"{league_id}/traded_picks"
    )


def get_rosters(league_id):
    return get_json(
        f"https://api.sleeper.app/v1/league/"
        f"{league_id}/rosters"
    )


def main():
    league_id = CURRENT_LEAGUE_ID

    seasons = []

    while league_id:
        league = get_league(league_id)

        season = int(league["season"])

        print()
        print("=" * 60)
        print(f"SEASON {season}")
        print(f"League ID: {league_id}")
        print("=" * 60)

        transactions = get_transactions(league_id)
        traded_picks = get_traded_picks(league_id)
        rosters = get_rosters(league_id)

        completed = [
            t for t in transactions
            if t.get("status") == "complete"
        ]

        trades = [
            t for t in completed
            if t.get("type") == "trade"
        ]

        waivers = [
            t for t in completed
            if t.get("type") == "waiver"
        ]

        free_agents = [
            t for t in completed
            if t.get("type") == "free_agent"
        ]

        print(f"Transactions: {len(completed)}")
        print(f"Trades:       {len(trades)}")
        print(f"Waivers:      {len(waivers)}")
        print(f"Free agents:  {len(free_agents)}")
        print(f"Traded picks: {len(traded_picks)}")

        print()
        print("ROSTERS")
        print("-" * 60)

        for roster in rosters:
            print(
                f"Roster {roster['roster_id']}: "
                f"owner_id={roster.get('owner_id')}"
            )

        season_dir = OUTPUT_DIR / str(season)
        season_dir.mkdir(parents=True, exist_ok=True)

        with (season_dir / "league.json").open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(league, f, indent=2)

        with (season_dir / "transactions.json").open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(transactions, f, indent=2)

        with (season_dir / "traded_picks.json").open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(traded_picks, f, indent=2)

        with (season_dir / "rosters.json").open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(rosters, f, indent=2)

        seasons.append(
            {
                "season": season,
                "league_id": league_id,
                "transactions": len(completed),
                "trades": len(trades),
                "waivers": len(waivers),
                "free_agents": len(free_agents),
                "traded_picks": len(traded_picks),
            }
        )

        previous_league_id = league.get("previous_league_id")

        if (
            not previous_league_id
            or previous_league_id == "0"
            or season <= 2022
        ):
            break

        league_id = previous_league_id

    with (OUTPUT_DIR / "seasons_summary.json").open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(seasons, f, indent=2)

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)

    for row in seasons:
        print(
            f"{row['season']}: "
            f"{row['trades']} trades, "
            f"{row['waivers']} waivers, "
            f"{row['free_agents']} free agents, "
            f"{row['traded_picks']} traded picks"
        )


if __name__ == "__main__":
    main()