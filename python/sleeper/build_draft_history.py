import json
from pathlib import Path


RAW_DRAFT_DIR = Path("data/raw/drafts")
PLAYER_FILE = Path("data/raw/players/players.json")
OUTPUT_DIR = Path("assets/data/dynasty")
RAW_TRANSACTION_DIR = Path("data/raw/transactions")

DRAFT_HISTORY_FILE = OUTPUT_DIR / "draft_history.json"
DRAFT_SUMMARY_FILE = OUTPUT_DIR / "draft_summary.json"


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


def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def franchise_name(roster_id):
    if roster_id is None:
        return None

    try:
        roster_id = int(roster_id)
    except (TypeError, ValueError):
        return None

    return FRANCHISES.get(
        roster_id,
        f"Unknown Roster {roster_id}",
    )


def player_name(player_id, players):
    player = players.get(str(player_id), {})

    if player.get("full_name"):
        return player["full_name"]

    first = player.get("first_name") or ""
    last = player.get("last_name") or ""

    name = f"{first} {last}".strip()

    return name or str(player_id)


def make_pick_id(
    season,
    round_number,
    original_roster_id,
):
    return (
        f"PICK-{season}"
        f"-R{round_number}"
        f"-F{original_roster_id}"
    )


def get_slot_to_roster(draft, season):
    """
    Determine the ORIGINAL franchise attached to each
    draft slot.

    Sleeper draft_order maps:
        user_id -> draft_slot

    The season's rosters.json maps:
        owner_id -> roster_id

    Combining the two gives:
        draft_slot -> original roster_id
    """

    draft_order = draft.get("draft_order") or {}

    rosters_file = (
        RAW_TRANSACTION_DIR
        / str(season)
        / "rosters.json"
    )

    if not rosters_file.exists():
        raise FileNotFoundError(
            f"{rosters_file} not found"
        )

    rosters = load_json(rosters_file)

    owner_to_roster = {}

    for roster in rosters:
        owner_id = roster.get("owner_id")
        roster_id = roster.get("roster_id")

        if owner_id is None or roster_id is None:
            continue

        owner_to_roster[str(owner_id)] = int(
            roster_id
        )

    slot_to_roster = {}

    for user_id, slot in draft_order.items():
        roster_id = owner_to_roster.get(
            str(user_id)
        )

        if roster_id is None:
            print(
                f"WARNING: Could not resolve "
                f"user {user_id} in {season}"
            )
            continue

        slot_to_roster[int(slot)] = roster_id

    return slot_to_roster


def find_completed_draft(season):
    """
    Find the draft for a season that actually contains picks.

    2022 is the startup draft.
    2023+ are expected to be rookie drafts.
    """

    season_dir = RAW_DRAFT_DIR / str(season)

    drafts_file = season_dir / "drafts.json"

    if not drafts_file.exists():
        return None, []

    drafts = load_json(drafts_file)

    candidates = []

    for draft in drafts:
        draft_id = draft["draft_id"]

        picks_file = (
            season_dir
            / f"{draft_id}_picks.json"
        )

        if not picks_file.exists():
            continue

        picks = load_json(picks_file)

        # Ignore empty draft objects.
        if not picks:
            continue

        candidates.append(
            (draft, picks)
        )

    if not candidates:
        return None, []

    # For now there should be one actual populated draft
    # per season. If multiple exist, prefer the one with
    # the most selections.
    candidates.sort(
        key=lambda item: len(item[1]),
        reverse=True,
    )

    return candidates[0]


def build_draft(season, draft, picks, players):
    slot_to_roster = get_slot_to_roster(
    draft,
    season,
)

    draft_type = draft.get("type")
    rounds = (
        draft.get("settings", {})
        .get("rounds")
    )

    is_startup = (
        season == 2022
        and draft_type == "snake"
    )

    selections = []

    for pick in picks:
        draft_slot = int(
            pick["draft_slot"]
        )

        round_number = int(
            pick["round"]
        )

        actual_roster_id = pick.get(
            "roster_id"
        )

        if actual_roster_id is not None:
            actual_roster_id = int(
                actual_roster_id
            )

        original_roster_id = (
            slot_to_roster.get(draft_slot)
        )

        # For safety, if Sleeper doesn't provide
        # slot_to_roster_id, fall back to actual roster.
        if original_roster_id is None:
            original_roster_id = (
                actual_roster_id
            )

        player_id = str(
            pick["player_id"]
        )

        player = players.get(
            player_id,
            {}
        )

        pick_id = None

        # Startup picks are not dynasty rookie-pick assets,
        # so don't assign our traded-pick IDs to 2022.
        if not is_startup:
            pick_id = make_pick_id(
                season,
                round_number,
                original_roster_id,
            )

        overall_pick = int(
            pick["pick_no"]
        )

        display_pick = (
            f"{round_number}."
            f"{draft_slot:02d}"
        )

        selections.append({
            "pick_id":
                pick_id,

            "season":
                season,

            "draft_id":
                draft["draft_id"],

            "round":
                round_number,

            "draft_slot":
                draft_slot,

            "overall_pick":
                overall_pick,

            "display_pick":
                display_pick,

            "original_roster_id":
                original_roster_id,

            "original_franchise":
                franchise_name(
                    original_roster_id
                ),

            "drafted_by_roster_id":
                actual_roster_id,

            "drafted_by_franchise":
                franchise_name(
                    actual_roster_id
                ),

            "picked_by_user_id":
                pick.get("picked_by"),

            "player_id":
                player_id,

            "player_name":
                player_name(
                    player_id,
                    players
                ),

            "position":
                player.get(
                    "position"
                )
                or pick.get(
                    "metadata",
                    {}
                ).get("position"),

            "nfl_team":
                player.get("team"),

            "is_traded_pick":
                (
                    original_roster_id
                    != actual_roster_id
                ),

            "is_startup":
                is_startup,
        })

    return {
        "season":
            season,

        "draft_id":
            draft["draft_id"],

        "type":
            draft_type,

        "status":
            draft.get("status"),

        "rounds":
            rounds,

        "is_startup":
            is_startup,

        "selection_count":
            len(selections),

        "selections":
            selections,
    }


def main():
    if not PLAYER_FILE.exists():
        raise FileNotFoundError(
            "Player directory not found. "
            "Run update_players.py first."
        )

    players = load_json(
        PLAYER_FILE
    )

    print(
        f"Loaded {len(players):,} "
        f"Sleeper players"
    )

    draft_history = []

    all_rookie_selections = []

    for season in SEASONS:
        draft, picks = (
            find_completed_draft(season)
        )

        if not draft:
            print(
                f"{season}: "
                f"No populated draft found"
            )
            continue

        built = build_draft(
            season,
            draft,
            picks,
            players,
        )

        draft_history.append(
            built
        )

        if not built["is_startup"]:
            all_rookie_selections.extend(
                built["selections"]
            )

        traded_count = sum(
            1
            for selection
            in built["selections"]
            if selection[
                "is_traded_pick"
            ]
        )

        label = (
            "Startup"
            if built["is_startup"]
            else "Rookie"
        )

        print(
            f"{season}: "
            f"{label} draft | "
            f"{built['selection_count']} picks | "
            f"{traded_count} traded slots"
        )

    save_json(
        DRAFT_HISTORY_FILE,
        draft_history,
    )

    summary = {
        "drafts":
            len(draft_history),

        "rookie_draft_selections":
            len(
                all_rookie_selections
            ),

        "rookie_seasons":
            [
                draft["season"]
                for draft in draft_history
                if not draft["is_startup"]
            ],

        "traded_rookie_selections":
            sum(
                1
                for selection
                in all_rookie_selections
                if selection[
                    "is_traded_pick"
                ]
            ),
    }

    save_json(
        DRAFT_SUMMARY_FILE,
        summary,
    )

    print()
    print("=" * 60)
    print("DRAFT HISTORY COMPLETE")
    print("=" * 60)

    print(
        f"Drafts:                    "
        f"{summary['drafts']}"
    )

    print(
        f"Rookie draft selections:   "
        f"{summary['rookie_draft_selections']}"
    )

    print(
        f"Traded rookie selections:  "
        f"{summary['traded_rookie_selections']}"
    )

    print()
    print("SAMPLE TRADED ROOKIE PICKS")
    print("-" * 60)

    examples = [
        selection
        for selection
        in all_rookie_selections
        if selection[
            "is_traded_pick"
        ]
    ][:10]

    for pick in examples:
        print(
            f"{pick['pick_id']:<22} "
            f"{pick['display_pick']} "
            f"{pick['player_name']} | "
            f"{pick['original_franchise']} "
            f"-> "
            f"{pick['drafted_by_franchise']}"
        )


if __name__ == "__main__":
    main()