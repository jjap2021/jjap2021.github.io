import json
from pathlib import Path


DATA_DIR = Path("assets/data/dynasty")

RESOLVED_LINEAGE_FILE = (
    DATA_DIR / "resolved_pick_lineage.json"
)

TRADE_HISTORY_FILE = (
    DATA_DIR / "trade_history.json"
)

OUTPUT_FILE = (
    DATA_DIR / "pick_butterfly.json"
)

SUMMARY_FILE = (
    DATA_DIR / "pick_butterfly_stats.json"
)


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def build_trade_lookup(trades):
    return {
        trade["transaction_id"]: trade
        for trade in trades
    }


def summarize_trade(trade):
    if not trade:
        return None

    teams = []

    for team in trade.get("teams", []):
        teams.append({
            "roster_id":
                team["roster_id"],

            "franchise":
                team["franchise"],

            "received":
                team.get("received", []),

            "sent":
                team.get("sent", []),
        })

    return {
        "transaction_id":
            trade["transaction_id"],

        "season":
            trade["season"],

        "week":
            trade["week"],

        "created":
            trade["created"],

        "teams":
            teams,
    }


def build_butterfly(
    lineage,
    trade_lookup,
):
    movement_history = []

    for movement in lineage.get(
        "movements",
        []
    ):
        transaction_id = movement.get(
            "transaction_id"
        )

        trade = trade_lookup.get(
            transaction_id
        )

        movement_history.append({
            "transaction_id":
                transaction_id,

            "league_season":
                movement.get(
                    "league_season"
                ),

            "week":
                movement.get("week"),

            "created":
                movement.get("created"),

            "from_roster_id":
                movement.get(
                    "from_roster_id"
                ),

            "from_franchise":
                movement.get(
                    "from_franchise"
                ),

            "to_roster_id":
                movement.get(
                    "to_roster_id"
                ),

            "to_franchise":
                movement.get(
                    "to_franchise"
                ),

            "trade":
                summarize_trade(trade),
        })

    draft = lineage.get("draft")

    return {
        "pick_id":
            lineage["pick_id"],

        "pick_season":
            lineage["pick_season"],

        "round":
            lineage["round"],

        "original_roster_id":
            lineage["original_roster_id"],

        "original_franchise":
            lineage["original_franchise"],

        "current_roster_id":
            lineage["current_roster_id"],

        "current_franchise":
            lineage["current_franchise"],

        "times_traded":
            lineage["times_traded"],

        "draft_resolved":
            lineage["draft_resolved"],

        "draft":
            draft,

        "movements":
            movement_history,
    }


def main():
    if not RESOLVED_LINEAGE_FILE.exists():
        raise FileNotFoundError(
            f"{RESOLVED_LINEAGE_FILE} not found"
        )

    if not TRADE_HISTORY_FILE.exists():
        raise FileNotFoundError(
            f"{TRADE_HISTORY_FILE} not found"
        )

    lineages = load_json(
        RESOLVED_LINEAGE_FILE
    )

    trades = load_json(
        TRADE_HISTORY_FILE
    )

    print(
        f"Loaded {len(lineages)} "
        f"resolved pick lineages"
    )

    print(
        f"Loaded {len(trades)} "
        f"trade records"
    )

    trade_lookup = (
        build_trade_lookup(trades)
    )

    butterfly = [
        build_butterfly(
            lineage,
            trade_lookup,
        )
        for lineage in lineages
    ]

    butterfly.sort(
        key=lambda x: (
            -x["times_traded"],
            x["pick_season"],
            x["round"],
            x["original_roster_id"],
        )
    )

    save_json(
        OUTPUT_FILE,
        butterfly,
    )

    resolved = [
        item
        for item in butterfly
        if item["draft_resolved"]
    ]

    unresolved = [
        item
        for item in butterfly
        if not item["draft_resolved"]
    ]

    stats = {
        "total_pick_assets":
            len(butterfly),

        "resolved":
            len(resolved),

        "unresolved":
            len(unresolved),

        "total_movements":
            sum(
                item["times_traded"]
                for item in butterfly
            ),

        "most_traded_pick":
            (
                butterfly[0]["pick_id"]
                if butterfly
                else None
            ),

        "most_traded_pick_count":
            (
                butterfly[0]["times_traded"]
                if butterfly
                else 0
            ),
    }

    save_json(
        SUMMARY_FILE,
        stats,
    )

    print()
    print(
        f"Created {OUTPUT_FILE}"
    )

    print(
        f"Created {SUMMARY_FILE}"
    )

    print()
    print("=" * 60)
    print("PICK BUTTERFLY DATA COMPLETE")
    print("=" * 60)

    print(
        f"Pick assets:       "
        f"{stats['total_pick_assets']}"
    )

    print(
        f"Resolved:          "
        f"{stats['resolved']}"
    )

    print(
        f"Unresolved:        "
        f"{stats['unresolved']}"
    )

    print(
        f"Total movements:   "
        f"{stats['total_movements']}"
    )

    print(
        f"Most traded pick:  "
        f"{stats['most_traded_pick']} "
        f"({stats['most_traded_pick_count']}x)"
    )

    print()
    print("TOP PICK CHAINS")
    print("-" * 60)

    for item in butterfly[:10]:
        if item["draft_resolved"]:
            ending = (
                f"{item['draft']['display_pick']} "
                f"{item['draft']['player_name']}"
            )
        else:
            ending = "Future pick"

        print()
        print(
            f"{item['pick_id']} | "
            f"{item['times_traded']} trades | "
            f"{ending}"
        )

        for movement in item["movements"]:
            print(
                f"    "
                f"{movement['from_franchise']} "
                f"-> "
                f"{movement['to_franchise']} "
                f"({movement['created'][:10]})"
            )


if __name__ == "__main__":
    main()