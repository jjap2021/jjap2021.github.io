import json
from pathlib import Path
from datetime import datetime, timezone

import requests


PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"

RAW_DIR = Path("data/raw/players")
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DIR / "players.json"
META_FILE = RAW_DIR / "players_meta.json"


def main():
    print("Fetching Sleeper NFL player directory...")

    response = requests.get(
        PLAYERS_URL,
        timeout=60,
    )
    response.raise_for_status()

    players = response.json()

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            players,
            f,
            indent=2,
        )

    metadata = {
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "player_count": len(players),
    }

    with META_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            metadata,
            f,
            indent=2,
        )

    print()
    print("=" * 60)
    print("PLAYER DIRECTORY UPDATED")
    print("=" * 60)
    print(f"Players: {len(players):,}")
    print(f"Saved:   {OUTPUT_FILE}")
    print(f"Meta:    {META_FILE}")


if __name__ == "__main__":
    main()