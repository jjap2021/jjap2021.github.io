import json
from pathlib import Path


DATA_DIR = Path("assets/data/dynasty")

LINEAGE_FILE = DATA_DIR / "pick_lineage.json"
DRAFT_HISTORY_FILE = DATA_DIR / "draft_history.json"

OUTPUT_FILE = DATA_DIR / "resolved_pick_lineage.json"
STATS_FILE = DATA_DIR / "resolved_pick_lineage_stats.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def build_draft_pick_lookup(draft_history):
    """
    Build:
        pick_id -> resolved draft selection
    """

    lookup = {}

    for draft in draft_history:
        if draft.get("is_startup"):
            continue

        for selection in draft.get(
            "selections",
            []
        ):
            pick_id = selection.get("pick_id")

            if not pick_id:
                continue

            lookup[pick_id] = selection

    return lookup


def resolve_lineage(
    lineage,
    draft_lookup,
):
    pick_id = lineage["pick_id"]

    draft = draft_lookup.get(pick_id)

    resolved = {
        **lineage,

        "draft_resolved":
            draft is not None,

        "draft":
            None,
    }

    if draft is None:
        return resolved

    resolved["draft"] = {
        "draft_id":
            draft["draft_id"],

        "season":
            draft["season"],

        "round":
            draft["round"],

        "draft_slot":
            draft["draft_slot"],

        "overall_pick":
            draft["overall_pick"],

        "display_pick":
            draft["display_pick"],

        "original_roster_id":
            draft["original_roster_id"],

        "original_franchise":
            draft["original_franchise"],

        "drafted_by_roster_id":
            draft["drafted_by_roster_id"],

        "drafted_by_franchise":
            draft["drafted_by_franchise"],

        "player_id":
            draft["player_id"],

        "player_name":
            draft["player_name"],

        "position":
            draft.get("position"),

        "nfl_team":
            draft.get("nfl_team"),

        "is_traded_pick":
            draft["is_traded_pick"],
    }

    return resolved


def validate_resolution(resolved):
    """
    Validate that the original franchise identity
    in lineage agrees with the draft resolver.
    """

    problems = []

    if not resolved["draft_resolved"]:
        return problems

    lineage_original = (
        resolved["original_roster_id"]
    )

    draft_original = (
        resolved["draft"][
            "original_roster_id"
        ]
    )

    if lineage_original != draft_original:
        problems.append({
            "type":
                "original_roster_mismatch",

            "lineage_original_roster_id":
                lineage_original,

            "draft_original_roster_id":
                draft_original,
        })

    movements = resolved.get(
        "movements",
        []
    )

    if movements:
        expected_final_owner = (
            movements[-1][
                "to_roster_id"
            ]
        )

        actual_drafted_by = (
            resolved["draft"][
                "drafted_by_roster_id"
            ]
        )

        if (
            expected_final_owner
            != actual_drafted_by
        ):
            problems.append({
                "type":
                    "final_owner_mismatch",

                "expected_final_owner":
                    expected_final_owner,

                "drafted_by_roster_id":
                    actual_drafted_by,
            })

    return problems


def main():
    if not LINEAGE_FILE.exists():
        raise FileNotFoundError(
            f"{LINEAGE_FILE} not found"
        )

    if not DRAFT_HISTORY_FILE.exists():
        raise FileNotFoundError(
            f"{DRAFT_HISTORY_FILE} not found"
        )

    lineages = load_json(
        LINEAGE_FILE
    )

    draft_history = load_json(
        DRAFT_HISTORY_FILE
    )

    print(
        f"Loaded {len(lineages)} "
        f"pick lineages"
    )

    draft_lookup = (
        build_draft_pick_lookup(
            draft_history
        )
    )

    print(
        f"Loaded {len(draft_lookup)} "
        f"rookie draft selections"
    )

    resolved = []
    problems = []

    for lineage in lineages:
        item = resolve_lineage(
            lineage,
            draft_lookup,
        )

        validation = (
            validate_resolution(item)
        )

        if validation:
            problems.append({
                "pick_id":
                    item["pick_id"],
                "problems":
                    validation,
            })

        resolved.append(item)

    save_json(
        OUTPUT_FILE,
        resolved,
    )

    resolved_count = sum(
        1
        for item in resolved
        if item["draft_resolved"]
    )

    unresolved_count = (
        len(resolved)
        - resolved_count
    )

    resolved_traded_picks = [
        item
        for item in resolved
        if (
            item["draft_resolved"]
            and item["draft"][
                "is_traded_pick"
            ]
        )
    ]

    stats = {
        "total_lineages":
            len(resolved),

        "resolved":
            resolved_count,

        "unresolved":
            unresolved_count,

        "resolved_traded_picks":
            len(
                resolved_traded_picks
            ),

        "validation_problems":
            len(problems),

        "unresolved_pick_ids": [
            item["pick_id"]
            for item in resolved
            if not item[
                "draft_resolved"
            ]
        ],
    }

    save_json(
        STATS_FILE,
        stats,
    )

    print()
    print(
        f"Created {OUTPUT_FILE}"
    )

    print(
        f"Created {STATS_FILE}"
    )

    print()
    print("=" * 60)
    print("PICK RESOLUTION COMPLETE")
    print("=" * 60)

    print(
        f"Total lineages:         "
        f"{stats['total_lineages']}"
    )

    print(
        f"Resolved:               "
        f"{stats['resolved']}"
    )

    print(
        f"Unresolved:             "
        f"{stats['unresolved']}"
    )

    print(
        f"Resolved traded picks:  "
        f"{stats['resolved_traded_picks']}"
    )

    print(
        f"Validation problems:    "
        f"{stats['validation_problems']}"
    )

    print()
    print("RESOLVED PICK EXAMPLES")
    print("-" * 60)

    examples = [
        item
        for item in resolved
        if item["draft_resolved"]
    ][:15]

    for item in examples:
        draft = item["draft"]

        print(
            f"{item['pick_id']:<22} "
            f"{draft['display_pick']} "
            f"{draft['player_name']} | "
            f"{item['original_franchise']} "
            f"-> "
            f"{draft['drafted_by_franchise']} | "
            f"{item['times_traded']} trades"
        )

    if stats["unresolved"]:
        print()
        print("UNRESOLVED PICKS")
        print("-" * 60)

        for pick_id in stats[
            "unresolved_pick_ids"
        ]:
            print(pick_id)

    if problems:
        print()
        print("VALIDATION PROBLEMS")
        print("-" * 60)

        for item in problems:
            print(item["pick_id"])

            for problem in item[
                "problems"
            ]:
                print(
                    f"    {problem}"
                )


if __name__ == "__main__":
    main()