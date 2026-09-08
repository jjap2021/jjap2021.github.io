import json
from collections import defaultdict, Counter
from pathlib import Path


DATA_DIR = Path("assets/data/dynasty")

PICK_EVENTS_FILE = DATA_DIR / "pick_transactions.json"
PICK_LINEAGE_FILE = DATA_DIR / "pick_lineage.json"
PICK_STATS_FILE = DATA_DIR / "pick_lineage_stats.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def build_lineage(events):
    grouped = defaultdict(list)

    for event in events:
        pick_id = event.get("pick_id")

        if not pick_id:
            continue

        grouped[pick_id].append(event)

    lineages = []

    for pick_id, pick_events in grouped.items():
        pick_events.sort(
            key=lambda x: x.get("created") or ""
        )

        first = pick_events[0]
        last = pick_events[-1]

        movements = []

        for event in pick_events:
            movements.append({
                "transaction_id":
                    event.get("transaction_id"),

                "league_season":
                    event.get("league_season"),

                "week":
                    event.get("week"),

                "created":
                    event.get("created"),

                "from_roster_id":
                    event.get(
                        "previous_owner_roster_id"
                    ),

                "from_franchise":
                    event.get(
                        "previous_owner_franchise"
                    ),

                "to_roster_id":
                    event.get(
                        "new_owner_roster_id"
                    ),

                "to_franchise":
                    event.get(
                        "new_owner_franchise"
                    ),
            })

        lineages.append({
            "pick_id": pick_id,

            "pick_season":
                first.get("season"),

            "round":
                first.get("round"),

            "original_roster_id":
                first.get(
                    "original_roster_id"
                ),

            "original_franchise":
                first.get(
                    "original_franchise"
                ),

            "current_roster_id":
                last.get(
                    "new_owner_roster_id"
                ),

            "current_franchise":
                last.get(
                    "new_owner_franchise"
                ),

            "times_traded":
                len(movements),

            "movements":
                movements,
        })

    lineages.sort(
        key=lambda x: (
            x["pick_season"] or 0,
            x["round"] or 0,
            x["original_roster_id"] or 0,
        )
    )

    return lineages


def validate_lineage(lineage):
    """
    Check whether each transfer starts with the owner
    who received the pick in the previous transfer.

    Example:
        A -> B
        B -> C       valid

        A -> B
        C -> D       broken
    """

    movements = lineage["movements"]

    problems = []

    for i in range(1, len(movements)):
        previous = movements[i - 1]
        current = movements[i]

        previous_receiver = (
            previous["to_roster_id"]
        )

        current_sender = (
            current["from_roster_id"]
        )

        if previous_receiver != current_sender:
            problems.append({
                "movement_index": i,

                "expected_sender":
                    previous_receiver,

                "actual_sender":
                    current_sender,

                "previous_transaction":
                    previous["transaction_id"],

                "current_transaction":
                    current["transaction_id"],
            })

    return problems


def build_stats(lineages):
    trade_frequency = Counter(
        lineage["times_traded"]
        for lineage in lineages
    )

    by_round = Counter(
        lineage["round"]
        for lineage in lineages
    )

    by_original_franchise = Counter(
        lineage["original_franchise"]
        for lineage in lineages
    )

    most_traded = sorted(
        lineages,
        key=lambda x: (
            -x["times_traded"],
            x["pick_id"],
        )
    )

    return {
        "unique_picks":
            len(lineages),

        "total_movements":
            sum(
                lineage["times_traded"]
                for lineage in lineages
            ),

        "trade_frequency": [
            {
                "times_traded": count,
                "picks": number,
            }
            for count, number
            in sorted(
                trade_frequency.items()
            )
        ],

        "by_round": [
            {
                "round": round_number,
                "picks": count,
            }
            for round_number, count
            in sorted(by_round.items())
        ],

        "by_original_franchise": [
            {
                "franchise": franchise,
                "picks": count,
            }
            for franchise, count
            in sorted(
                by_original_franchise.items(),
                key=lambda x: (
                    -x[1],
                    x[0].lower(),
                )
            )
        ],

        "most_traded_picks":
            most_traded[:10],
    }


def main():
    if not PICK_EVENTS_FILE.exists():
        raise FileNotFoundError(
            f"{PICK_EVENTS_FILE} not found. "
            "Run build_transactions.py first."
        )

    events = load_json(
        PICK_EVENTS_FILE
    )

    print(
        f"Loaded {len(events)} "
        f"pick movement events"
    )

    lineages = build_lineage(events)

    print(
        f"Built {len(lineages)} "
        f"unique pick lineages"
    )

    broken = []

    for lineage in lineages:
        problems = validate_lineage(
            lineage
        )

        if problems:
            broken.append({
                "pick_id":
                    lineage["pick_id"],

                "problems":
                    problems,
            })

    stats = build_stats(lineages)

    save_json(
        PICK_LINEAGE_FILE,
        lineages
    )

    save_json(
        PICK_STATS_FILE,
        stats
    )

    print()
    print(
        f"Created {PICK_LINEAGE_FILE}"
    )
    print(
        f"Created {PICK_STATS_FILE}"
    )

    print()
    print("=" * 60)
    print("PICK LINEAGE COMPLETE")
    print("=" * 60)

    print(
        f"Unique picks:       "
        f"{stats['unique_picks']}"
    )

    print(
        f"Total movements:    "
        f"{stats['total_movements']}"
    )

    print(
        f"Broken lineages:    "
        f"{len(broken)}"
    )

    print()
    print("TRADE FREQUENCY")
    print("-" * 60)

    for row in stats[
        "trade_frequency"
    ]:
        print(
            f"Traded "
            f"{row['times_traded']}x: "
            f"{row['picks']} picks"
        )

    print()
    print("MOST-TRADED PICKS")
    print("-" * 60)

    for pick in stats[
        "most_traded_picks"
    ]:
        print(
            f"{pick['pick_id']:<22} "
            f"{pick['times_traded']} trades | "
            f"{pick['original_franchise']}"
        )

        for movement in pick[
            "movements"
        ]:
            print(
                f"    "
                f"{movement['from_franchise']} "
                f"-> "
                f"{movement['to_franchise']} "
                f"({movement['created'][:10]})"
            )

    if broken:
        print()
        print("WARNING: BROKEN LINEAGES")
        print("-" * 60)

        for item in broken:
            print(item["pick_id"])

            for problem in item[
                "problems"
            ]:
                print(
                    f"    Expected roster "
                    f"{problem['expected_sender']}, "
                    f"got "
                    f"{problem['actual_sender']}"
                )


if __name__ == "__main__":
    main()