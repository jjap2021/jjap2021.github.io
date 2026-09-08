import json
from collections import Counter, defaultdict
from pathlib import Path


DATA_DIR = Path("assets/data/dynasty")

TRADES_FILE = DATA_DIR / "trades.json"
TRADE_HISTORY_FILE = DATA_DIR / "trade_history.json"
TRADE_STATS_FILE = DATA_DIR / "trade_stats.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def player_asset(player):
    return {
        "type": "player",
        "player_id": player["player_id"],
        "name": player["name"],
        "position": player.get("position"),
    }


def pick_asset(pick):
    return {
        "type": "pick",
        "pick_id": pick["pick_id"],
        "season": pick["season"],
        "round": pick["round"],
        "original_roster_id": pick["original_roster_id"],
        "original_franchise": pick["original_franchise"],
    }


def build_trade(trade):
    """
    Convert a normalized Sleeper trade into explicit franchise sides.

    For players:
        adds = receiving franchise
        drops = sending franchise

    For picks:
        previous_owner = sending franchise
        new_owner = receiving franchise
    """

    sides = {}

    for roster_id, franchise in zip(
        trade["roster_ids"],
        trade["franchises"],
    ):
        sides[int(roster_id)] = {
            "roster_id": int(roster_id),
            "franchise": franchise,
            "received": [],
            "sent": [],
        }

    # Players received
    for player in trade["adds"]:
        roster_id = int(player["roster_id"])

        if roster_id not in sides:
            sides[roster_id] = {
                "roster_id": roster_id,
                "franchise": player["franchise"],
                "received": [],
                "sent": [],
            }

        sides[roster_id]["received"].append(
            player_asset(player)
        )

    # Players sent
    for player in trade["drops"]:
        roster_id = int(player["roster_id"])

        if roster_id not in sides:
            sides[roster_id] = {
                "roster_id": roster_id,
                "franchise": player["franchise"],
                "received": [],
                "sent": [],
            }

        sides[roster_id]["sent"].append(
            player_asset(player)
        )

    # Draft picks
    for pick in trade["draft_picks"]:
        asset = pick_asset(pick)

        previous_owner = pick.get(
            "previous_owner_roster_id"
        )
        new_owner = pick.get(
            "new_owner_roster_id"
        )

        if previous_owner is not None:
            previous_owner = int(previous_owner)

            if previous_owner not in sides:
                sides[previous_owner] = {
                    "roster_id": previous_owner,
                    "franchise":
                        pick["previous_owner_franchise"],
                    "received": [],
                    "sent": [],
                }

            sides[previous_owner]["sent"].append(
                asset
            )

        if new_owner is not None:
            new_owner = int(new_owner)

            if new_owner not in sides:
                sides[new_owner] = {
                    "roster_id": new_owner,
                    "franchise":
                        pick["new_owner_franchise"],
                    "received": [],
                    "sent": [],
                }

            sides[new_owner]["received"].append(
                asset
            )

    # FAAB exchanged in trades.
    for budget_move in trade.get(
        "waiver_budget",
        []
    ):
        sender = budget_move.get(
            "sender_roster_id"
        )
        receiver = budget_move.get(
            "receiver_roster_id"
        )
        amount = budget_move.get("amount")

        asset = {
            "type": "faab",
            "amount": amount,
        }

        if sender is not None:
            sender = int(sender)

            if sender in sides:
                sides[sender]["sent"].append(
                    asset.copy()
                )

        if receiver is not None:
            receiver = int(receiver)

            if receiver in sides:
                sides[receiver]["received"].append(
                    asset.copy()
                )

    teams = sorted(
        sides.values(),
        key=lambda x: x["roster_id"]
    )

    return {
        "transaction_id":
            trade["transaction_id"],

        "season":
            trade["league_season"],

        "week":
            trade["week"],

        "leg":
            trade["leg"],

        "created":
            trade["created"],

        "created_timestamp":
            trade["created_timestamp"],

        "team_count":
            len(teams),

        "is_multi_team":
            len(teams) > 2,

        "teams":
            teams,
    }


def build_trade_history(trades):
    history = [
        build_trade(trade)
        for trade in trades
    ]

    history.sort(
        key=lambda x:
            x["created_timestamp"] or 0
    )

    return history


def build_franchise_stats(history):
    stats = defaultdict(
        lambda: {
            "trades": 0,
            "players_acquired": 0,
            "players_traded_away": 0,
            "picks_acquired": 0,
            "picks_traded_away": 0,
            "faab_acquired": 0,
            "faab_traded_away": 0,
            "multi_team_trades": 0,
        }
    )

    for trade in history:
        for team in trade["teams"]:
            franchise = team["franchise"]

            stats[franchise]["trades"] += 1

            if trade["is_multi_team"]:
                stats[franchise][
                    "multi_team_trades"
                ] += 1

            for asset in team["received"]:
                if asset["type"] == "player":
                    stats[franchise][
                        "players_acquired"
                    ] += 1

                elif asset["type"] == "pick":
                    stats[franchise][
                        "picks_acquired"
                    ] += 1

                elif asset["type"] == "faab":
                    stats[franchise][
                        "faab_acquired"
                    ] += asset.get(
                        "amount", 0
                    ) or 0

            for asset in team["sent"]:
                if asset["type"] == "player":
                    stats[franchise][
                        "players_traded_away"
                    ] += 1

                elif asset["type"] == "pick":
                    stats[franchise][
                        "picks_traded_away"
                    ] += 1

                elif asset["type"] == "faab":
                    stats[franchise][
                        "faab_traded_away"
                    ] += asset.get(
                        "amount", 0
                    ) or 0

    rows = []

    for franchise, values in stats.items():
        rows.append({
            "franchise": franchise,
            **values,
        })

    rows.sort(
        key=lambda x: (
            -x["trades"],
            x["franchise"].lower(),
        )
    )

    return rows


def build_season_stats(history):
    counts = Counter(
        trade["season"]
        for trade in history
    )

    return [
        {
            "season": season,
            "trades": counts[season],
        }
        for season in sorted(counts)
    ]


def build_trade_partners(history):
    """
    Count how many trades each pair of franchises
    participated in together.

    Works for both 2-team and multi-team trades.
    """

    pair_counts = Counter()

    for trade in history:
        franchises = sorted({
            team["franchise"]
            for team in trade["teams"]
        })

        for i in range(len(franchises)):
            for j in range(
                i + 1,
                len(franchises)
            ):
                pair = (
                    franchises[i],
                    franchises[j],
                )

                pair_counts[pair] += 1

    rows = []

    for (
        franchise_1,
        franchise_2
    ), count in pair_counts.items():

        rows.append({
            "franchise_1":
                franchise_1,
            "franchise_2":
                franchise_2,
            "trades":
                count,
        })

    rows.sort(
        key=lambda x: (
            -x["trades"],
            x["franchise_1"].lower(),
            x["franchise_2"].lower(),
        )
    )

    return rows


def build_player_trade_counts(history):
    acquired = Counter()
    sent = Counter()

    player_info = {}

    for trade in history:
        for team in trade["teams"]:
            for asset in team["received"]:
                if asset["type"] != "player":
                    continue

                player_id = asset["player_id"]

                acquired[player_id] += 1

                player_info[player_id] = {
                    "player_id": player_id,
                    "name": asset["name"],
                    "position":
                        asset.get("position"),
                }

            for asset in team["sent"]:
                if asset["type"] != "player":
                    continue

                player_id = asset["player_id"]

                sent[player_id] += 1

                player_info[player_id] = {
                    "player_id": player_id,
                    "name": asset["name"],
                    "position":
                        asset.get("position"),
                }

    rows = []

    all_player_ids = (
        set(acquired)
        | set(sent)
    )

    for player_id in all_player_ids:
        info = player_info[player_id]

        rows.append({
            **info,
            "times_acquired":
                acquired[player_id],
            "times_traded_away":
                sent[player_id],

            # Each completed player transfer should
            # normally appear once on each side.
            "trade_movements":
                max(
                    acquired[player_id],
                    sent[player_id],
                ),
        })

    rows.sort(
        key=lambda x: (
            -x["trade_movements"],
            x["name"].lower(),
        )
    )

    return rows


def build_pick_stats(history):
    acquired = Counter()
    sent = Counter()

    for trade in history:
        for team in trade["teams"]:
            franchise = team["franchise"]

            for asset in team["received"]:
                if asset["type"] == "pick":
                    acquired[franchise] += 1

            for asset in team["sent"]:
                if asset["type"] == "pick":
                    sent[franchise] += 1

    franchises = sorted(
        set(acquired)
        | set(sent)
    )

    return [
        {
            "franchise": franchise,
            "picks_acquired":
                acquired[franchise],
            "picks_traded_away":
                sent[franchise],
            "net_pick_movements":
                acquired[franchise]
                - sent[franchise],
        }
        for franchise in franchises
    ]


def build_summary(history):
    multi_team = [
        trade
        for trade in history
        if trade["is_multi_team"]
    ]

    return {
        "total_trades":
            len(history),

        "multi_team_trades":
            len(multi_team),

        "two_team_trades":
            len(history)
            - len(multi_team),

        "seasons":
            sorted({
                trade["season"]
                for trade in history
            }),
    }


def main():
    if not TRADES_FILE.exists():
        raise FileNotFoundError(
            f"{TRADES_FILE} not found. "
            "Run build_transactions.py first."
        )

    trades = load_json(TRADES_FILE)

    print(
        f"Loaded {len(trades)} "
        f"normalized trades"
    )

    history = build_trade_history(
        trades
    )

    franchise_stats = (
        build_franchise_stats(history)
    )

    season_stats = (
        build_season_stats(history)
    )

    trade_partners = (
        build_trade_partners(history)
    )

    player_trade_counts = (
        build_player_trade_counts(history)
    )

    pick_stats = (
        build_pick_stats(history)
    )

    summary = build_summary(history)

    trade_stats = {
        "summary":
            summary,

        "by_franchise":
            franchise_stats,

        "by_season":
            season_stats,

        "trade_partners":
            trade_partners,

        "player_trade_counts":
            player_trade_counts,

        "pick_stats":
            pick_stats,
    }

    save_json(
        TRADE_HISTORY_FILE,
        history
    )

    save_json(
        TRADE_STATS_FILE,
        trade_stats
    )

    print()
    print(
        f"Created {TRADE_HISTORY_FILE} "
        f"({len(history)} trades)"
    )

    print(
        f"Created {TRADE_STATS_FILE}"
    )

    print()
    print("=" * 60)
    print("TRADE ANALYTICS COMPLETE")
    print("=" * 60)

    print(
        f"Total trades:      "
        f"{summary['total_trades']}"
    )

    print(
        f"Two-team trades:   "
        f"{summary['two_team_trades']}"
    )

    print(
        f"Multi-team trades: "
        f"{summary['multi_team_trades']}"
    )

    print()
    print("TRADES BY FRANCHISE")
    print("-" * 60)

    for row in franchise_stats:
        print(
            f"{row['franchise']:<18} "
            f"{row['trades']:>3} trades | "
            f"{row['players_acquired']:>3} players in | "
            f"{row['picks_acquired']:>3} picks in"
        )

    print()
    print("MOST FREQUENT TRADE PARTNERS")
    print("-" * 60)

    for row in trade_partners[:10]:
        print(
            f"{row['franchise_1']} ↔ "
            f"{row['franchise_2']}: "
            f"{row['trades']}"
        )

    print()
    print("MOST-TRADED PLAYERS")
    print("-" * 60)

    for row in player_trade_counts[:10]:
        print(
            f"{row['name']:<25} "
            f"{row['trade_movements']}"
        )


if __name__ == "__main__":
    main()