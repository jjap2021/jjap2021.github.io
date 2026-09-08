import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone


RAW_DIR = Path("data/raw/transactions")
OUTPUT_DIR = Path("assets/data/dynasty")
PLAYERS_FILE = Path("data/raw/players/players.json")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Roster IDs have remained stable throughout Diamond Dynasty history.
FRANCHISES = {
    1: "Danthecan",
    2: "steeeeeeeeeve",
    3: "PhillyBooBird",
    4: "ComradeCMP",
    5: "etmoyer",
    6: "RJRJRJ123",
    7: "jackpotFTW",
    8: "Pnewport",
    9: "acricci",
    10: "Mummanator",
}


SEASONS = [2022, 2023, 2024, 2025, 2026]


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def franchise_name(roster_id):
    if roster_id is None:
        return None

    try:
        roster_id = int(roster_id)
    except (TypeError, ValueError):
        return None

    return FRANCHISES.get(
        roster_id,
        f"Unknown Roster {roster_id}"
    )


def make_pick_id(pick):
    """
    Stable ID based on:
    season + round + ORIGINAL franchise.

    Sleeper's roster_id on a traded pick represents
    the original owner's roster.
    """
    season = pick.get("season")
    round_number = pick.get("round")
    original_roster = pick.get("roster_id")

    if not all([
        season,
        round_number,
        original_roster
    ]):
        return None

    return (
        f"PICK-{season}"
        f"-R{round_number}"
        f"-F{original_roster}"
    )


def timestamp_to_iso(timestamp):
    if not timestamp:
        return None

    # Sleeper timestamps are milliseconds.
    dt = datetime.fromtimestamp(
        timestamp / 1000,
        tz=timezone.utc
    )

    return dt.isoformat()


def normalize_pick(pick):
    return {
        "pick_id": make_pick_id(pick),
        "season": int(pick["season"])
        if pick.get("season")
        else None,
        "round": pick.get("round"),

        "original_roster_id": pick.get("roster_id"),
        "original_franchise": franchise_name(
            pick.get("roster_id")
        ),

        "previous_owner_roster_id":
            pick.get("previous_owner_id"),
        "previous_owner_franchise":
            franchise_name(
                pick.get("previous_owner_id")
            ),

        "new_owner_roster_id":
            pick.get("owner_id"),
        "new_owner_franchise":
            franchise_name(
                pick.get("owner_id")
            ),
    }

def load_players():
    if not PLAYERS_FILE.exists():
        raise FileNotFoundError(
            "Player directory not found. "
            "Run python/sleeper/update_players.py first."
        )

    return load_json(PLAYERS_FILE)


def player_name(player_id, players):
    if player_id is None:
        return None

    player_id = str(player_id)

    player = players.get(player_id)

    if not player:
        # Sleeper can also use team-defense IDs like "PHI".
        return player_id

    full_name = player.get("full_name")

    if full_name:
        return full_name

    first_name = player.get("first_name") or ""
    last_name = player.get("last_name") or ""

    combined = f"{first_name} {last_name}".strip()

    return combined or player_id


def normalize_player(player_id, roster_id, players):
    player_id = str(player_id)

    player = players.get(player_id, {})

    return {
        "player_id": player_id,
        "name": player_name(
            player_id,
            players,
        ),

        "position": player.get("position"),
        "team": player.get("team"),

        "roster_id": roster_id,
        "franchise": franchise_name(
            roster_id
        ),
    }

def normalize_transaction(
    transaction,
    league_season,
    players,
):
    roster_ids = transaction.get("roster_ids") or []

    franchises = [
        franchise_name(roster_id)
        for roster_id in roster_ids
    ]

    adds = transaction.get("adds") or {}
    drops = transaction.get("drops") or {}

    normalized_adds = [
        normalize_player(
            player_id,
            roster_id,
            players,
        )
        for player_id, roster_id
        in adds.items()
    ]

    normalized_drops = [
        normalize_player(
            player_id,
            roster_id,
            players,
        )
        for player_id, roster_id
        in drops.items()
    ]

    picks = [
        normalize_pick(pick)
        for pick in transaction.get("draft_picks", [])
    ]

    waiver_budget = []

    for budget_move in transaction.get(
        "waiver_budget",
        []
    ):
        waiver_budget.append({
            "sender_roster_id":
                budget_move.get("sender"),
            "sender_franchise":
                franchise_name(
                    budget_move.get("sender")
                ),
            "receiver_roster_id":
                budget_move.get("receiver"),
            "receiver_franchise":
                franchise_name(
                    budget_move.get("receiver")
                ),
            "amount": budget_move.get("amount"),
        })

    return {
        "transaction_id":
            transaction.get("transaction_id"),

        "league_season": league_season,
        "week": transaction.get("requested_week"),
        "leg": transaction.get("leg"),

        "type": transaction.get("type"),
        "status": transaction.get("status"),

        "created_timestamp":
            transaction.get("created"),
        "created":
            timestamp_to_iso(
                transaction.get("created")
            ),

        "status_updated_timestamp":
            transaction.get("status_updated"),
        "status_updated":
            timestamp_to_iso(
                transaction.get("status_updated")
            ),

        "creator_user_id":
            transaction.get("creator"),

        "roster_ids": roster_ids,
        "franchises": franchises,

        "adds": normalized_adds,
        "drops": normalized_drops,
        "draft_picks": picks,
        "waiver_budget": waiver_budget,

        "settings":
            transaction.get("settings") or {},
    }


def main():
    # Load Sleeper player directory once.
    players = load_players()

    print(
        f"Loaded {len(players):,} "
        f"Sleeper players"
    )
    print()

    all_transactions = []
    all_trades = []
    all_waivers = []
    all_free_agents = []

    pick_events = []

    season_summary = []

    for season in SEASONS:
        path = (
            RAW_DIR
            / str(season)
            / "transactions.json"
        )

        if not path.exists():
            print(f"Skipping {season}: file not found")
            continue

        raw_transactions = load_json(path)

        normalized = []

        for transaction in raw_transactions:
            if transaction.get("status") != "complete":
                continue

            item = normalize_transaction(
                transaction,
                season,
                players,
            )

            normalized.append(item)
            all_transactions.append(item)

            transaction_type = item["type"]

            if transaction_type == "trade":
                all_trades.append(item)

            elif transaction_type == "waiver":
                all_waivers.append(item)

            elif transaction_type == "free_agent":
                all_free_agents.append(item)

            for pick in item["draft_picks"]:
                pick_events.append({
                    "transaction_id":
                        item["transaction_id"],
                    "league_season":
                        season,
                    "week":
                        item["week"],
                    "created":
                        item["created"],
                    **pick,
                })

        trades = [
            t for t in normalized
            if t["type"] == "trade"
        ]

        waivers = [
            t for t in normalized
            if t["type"] == "waiver"
        ]

        free_agents = [
            t for t in normalized
            if t["type"] == "free_agent"
        ]

        season_summary.append({
            "season": season,
            "transactions": len(normalized),
            "trades": len(trades),
            "waivers": len(waivers),
            "free_agents": len(free_agents),
        })

    # Sort everything chronologically.
    all_transactions.sort(
        key=lambda x: (
            x["created_timestamp"] or 0
        )
    )

    all_trades.sort(
        key=lambda x: (
            x["created_timestamp"] or 0
        )
    )

    all_waivers.sort(
        key=lambda x: (
            x["created_timestamp"] or 0
        )
    )

    all_free_agents.sort(
        key=lambda x: (
            x["created_timestamp"] or 0
        )
    )

    pick_events.sort(
        key=lambda x: (
            x["created"] or ""
        )
    )

    outputs = {
        "transactions.json":
            all_transactions,

        "trades.json":
            all_trades,

        "waivers.json":
            all_waivers,

        "free_agents.json":
            all_free_agents,

        "pick_transactions.json":
            pick_events,

        "transaction_summary.json":
            season_summary,
    }

    for filename, data in outputs.items():
        output_path = OUTPUT_DIR / filename

        with output_path.open(
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                indent=2
            )

        print(
            f"Created {output_path} "
            f"({len(data)} records)"
        )

    print()
    print("=" * 60)
    print("TRANSACTION DATA COMPLETE")
    print("=" * 60)

    print(
        f"Transactions: {len(all_transactions)}"
    )
    print(
        f"Trades:       {len(all_trades)}"
    )
    print(
        f"Waivers:      {len(all_waivers)}"
    )
    print(
        f"Free agents:  {len(all_free_agents)}"
    )
    print(
        f"Pick events:  {len(pick_events)}"
    )

    unique_picks = {
        event["pick_id"]
        for event in pick_events
        if event["pick_id"]
    }

    print(
        f"Unique picks traded: {len(unique_picks)}"
    )

    print()
    print("TRADES BY SEASON")
    print("-" * 60)

    trade_counts = defaultdict(int)

    for trade in all_trades:
        trade_counts[
            trade["league_season"]
        ] += 1

    for season in SEASONS:
        print(
            f"{season}: "
            f"{trade_counts[season]}"
        )


if __name__ == "__main__":
    main()