import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PLAYER_HISTORY_PATH = (
    ROOT
    / "assets"
    / "data"
    / "dynasty"
    / "player_history.json"
)


def load_players():
    with PLAYER_HISTORY_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def find_players(players, query):
    query = query.lower()

    return [
        player
        for player in players
        if query in (
            player.get("name")
            or ""
        ).lower()
    ]


def print_player(player):
    print()
    print("=" * 80)
    print(
        player.get("name")
        or "Unknown Player"
    )
    print("=" * 80)

    print(
        f"Player ID: "
        f"{player.get('player_id')}"
    )

    print(
        f"Position: "
        f"{player.get('position')}"
    )

    print(
        f"NFL Team: "
        f"{player.get('nfl_team')}"
    )

    print(
        f"Current Franchise: "
        f"{player.get('current_franchise')}"
    )

    print(
        "Franchises Owned By: "
        + " -> ".join(
            player.get(
                "franchises_owned_by",
                [],
            )
        )
    )

    print(
        f"Trades: "
        f"{player.get('trade_count', 0)}"
    )

    print(
        f"Waiver Adds: "
        f"{player.get('waiver_count', 0)}"
    )

    print(
        f"Free Agent Adds: "
        f"{player.get('free_agent_count', 0)}"
    )

    print(
        f"Drops: "
        f"{player.get('drop_count', 0)}"
    )

    draft_origin = player.get(
        "draft_origin"
    )

    if draft_origin:
        print()
        print("DRAFT ORIGIN")
        print("-" * 80)

        print(
            f"Season: "
            f"{draft_origin.get('season')}"
        )

        print(
            f"Drafted By: "
            f"{draft_origin.get('franchise')}"
        )

        print(
            f"Original Franchise: "
            f"{draft_origin.get('original_franchise')}"
        )

        print(
            f"Round: "
            f"{draft_origin.get('round')}"
        )

        print(
            f"Pick: "
            f"{draft_origin.get('display_pick')}"
        )

    print()
    print("TIMELINE")
    print("-" * 80)

    for event in player.get(
        "events",
        []
    ):
        event_type = event.get(
            "type"
        )

        season = event.get(
            "season"
        )

        date = (
            event.get("date")
            or "No date"
        )

        print()
        print(
            f"{season} | "
            f"{event_type.upper()} | "
            f"{date}"
        )

        if event_type == "draft":
            print(
                f"  Drafted by: "
                f"{event.get('franchise')}"
            )

            print(
                f"  Original franchise: "
                f"{event.get('original_franchise')}"
            )

            print(
                f"  Pick: "
                f"{event.get('display_pick')}"
            )

        elif event_type == "trade":
            print(
                f"  "
                f"{event.get('from_franchise')}"
                f" -> "
                f"{event.get('to_franchise')}"
            )

        elif event_type in {
            "waiver_add",
            "free_agent_add",
        }:
            print(
                f"  Added by: "
                f"{event.get('franchise')}"
            )

        elif event_type == "drop":
            print(
                f"  Dropped by: "
                f"{event.get('franchise')}"
            )

        print(
            f"  Owner before: "
            f"{event.get('owner_before')}"
        )

        print(
            f"  Owner after: "
            f"{event.get('owner_after')}"
        )

    print()


def main():
    if len(sys.argv) < 2:
        print(
            'Usage: '
            'python inspect_player_history.py '
            '"Player Name"'
        )
        return

    query = " ".join(
        sys.argv[1:]
    )

    players = load_players()

    matches = find_players(
        players,
        query,
    )

    if not matches:
        print(
            f'No players found matching '
            f'"{query}"'
        )
        return

    if len(matches) > 1:
        print(
            f'Found {len(matches)} matches:'
        )

        for player in matches:
            print(
                f"- {player.get('name')} "
                f"({player.get('player_id')})"
            )

        return

    print_player(
        matches[0]
    )


if __name__ == "__main__":
    main()