import json
import requests
from pathlib import Path


TRANSACTION_DIR = Path("data/raw/transactions")
OUTPUT_DIR = Path("data/raw/drafts")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEASONS = [2022, 2023, 2024, 2025, 2026]


def get_json(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    summary = []

    for season in SEASONS:
        league_file = (
            TRANSACTION_DIR
            / str(season)
            / "league.json"
        )

        if not league_file.exists():
            print(
                f"Skipping {season}: "
                f"league.json not found"
            )
            continue

        league = load_json(league_file)

        league_id = league["league_id"]

        print()
        print("=" * 60)
        print(f"SEASON {season}")
        print(f"League ID: {league_id}")
        print("=" * 60)

        drafts = get_json(
            f"https://api.sleeper.app/v1/"
            f"league/{league_id}/drafts"
        )

        print(
            f"Drafts found: {len(drafts)}"
        )

        season_dir = OUTPUT_DIR / str(season)
        season_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        with (
            season_dir / "drafts.json"
        ).open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                drafts,
                f,
                indent=2,
            )

        season_picks = []

        for draft in drafts:
            draft_id = draft["draft_id"]

            picks = get_json(
                f"https://api.sleeper.app/v1/"
                f"draft/{draft_id}/picks"
            )

            print()
            print(
                f"Draft {draft_id}"
            )
            print(
                f"Type:   {draft.get('type')}"
            )
            print(
                f"Status: {draft.get('status')}"
            )
            print(
                f"Rounds: {draft.get('settings', {}).get('rounds')}"
            )
            print(
                f"Picks:  {len(picks)}"
            )

            draft_record = {
                "draft_id": draft_id,
                "season": season,
                "type": draft.get("type"),
                "status": draft.get("status"),
                "rounds": (
                    draft.get(
                        "settings",
                        {}
                    ).get("rounds")
                ),
                "picks": picks,
            }

            season_picks.append(
                draft_record
            )

            picks_file = (
                season_dir
                / f"{draft_id}_picks.json"
            )

            with picks_file.open(
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(
                    picks,
                    f,
                    indent=2,
                )

            if picks:
                print()
                print("FIRST PICK")
                print("-" * 60)
                print(
                    json.dumps(
                        picks[0],
                        indent=2,
                    )
                )

        summary.append({
            "season": season,
            "league_id": league_id,
            "draft_count": len(drafts),
            "drafts": [
                {
                    "draft_id":
                        d["draft_id"],
                    "status":
                        d.get("status"),
                    "type":
                        d.get("type"),
                }
                for d in drafts
            ],
        })

        with (
            season_dir
            / "draft_results.json"
        ).open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                season_picks,
                f,
                indent=2,
            )

    with (
        OUTPUT_DIR
        / "draft_summary.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary,
            f,
            indent=2,
        )

    print()
    print("=" * 60)
    print("DRAFT EXPLORATION COMPLETE")
    print("=" * 60)

    for row in summary:
        print(
            f"{row['season']}: "
            f"{row['draft_count']} drafts"
        )


if __name__ == "__main__":
    main()