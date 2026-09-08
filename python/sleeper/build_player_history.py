from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "assets" / "data" / "dynasty"

TRANSACTIONS_PATH = DATA_DIR / "transactions.json"
TRADE_HISTORY_PATH = DATA_DIR / "trade_history.json"

# Draft history support is optional because we may have named
# the generated draft file differently during exploration.
DRAFT_CANDIDATES = [
    DATA_DIR / "draft_history.json",
    DATA_DIR / "draft_picks.json",
    DATA_DIR / "draft_selections.json",
]

OUTPUT_PATH = DATA_DIR / "player_history.json"
INDEX_OUTPUT_PATH = DATA_DIR / "player_history_index.json"
STATS_OUTPUT_PATH = DATA_DIR / "player_history_stats.json"


# ============================================================
# BASIC HELPERS
# ============================================================

def load_json(path: Path, required: bool = True) -> Any:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Missing required file: {path}")

        return None

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def first_defined(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value

    return None


def as_list(value: Any) -> list:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def parse_timestamp(value: Any) -> int | None:
    """
    Convert several possible timestamp formats to milliseconds.
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        value = int(value)

        # Sleeper timestamps are often milliseconds already.
        if value > 10_000_000_000:
            return value

        return value * 1000

    if isinstance(value, str):
        stripped = value.strip()

        if not stripped:
            return None

        if stripped.isdigit():
            return parse_timestamp(int(stripped))

        try:
            dt = datetime.fromisoformat(
                stripped.replace("Z", "+00:00")
            )

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return int(dt.timestamp() * 1000)

        except ValueError:
            return None

    return None


def timestamp_to_iso(timestamp_ms: int | None) -> str | None:
    if timestamp_ms is None:
        return None

    dt = datetime.fromtimestamp(
        timestamp_ms / 1000,
        tz=timezone.utc,
    )

    return dt.isoformat()


def clean_name(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    return text if text else None


# ============================================================
# PLAYER HELPERS
# ============================================================

def player_id_from_asset(asset: dict) -> str | None:
    value = first_defined(
        asset.get("player_id"),
        asset.get("id"),
    )

    if value is None:
        return None

    return str(value)


def player_name_from_asset(asset: dict) -> str | None:
    return clean_name(
        first_defined(
            asset.get("name"),
            asset.get("full_name"),
            asset.get("player_name"),
        )
    )


def update_player_metadata(player: dict, asset: dict) -> None:
    """
    Fill missing player metadata without overwriting good values.
    """

    name = player_name_from_asset(asset)

    if name and not player.get("name"):
        player["name"] = name

    position = first_defined(
        asset.get("position"),
        asset.get("pos"),
    )

    if position and not player.get("position"):
        player["position"] = position

    team = first_defined(
        asset.get("team"),
        asset.get("nfl_team"),
    )

    if team and not player.get("nfl_team"):
        player["nfl_team"] = team


def create_player_record(player_id: str) -> dict:
    return {
        "player_id": player_id,
        "name": None,
        "position": None,
        "nfl_team": None,
        "draft_origin": None,
        "current_franchise": None,
        "franchises_owned_by": [],
        "transaction_count": 0,
        "trade_count": 0,
        "waiver_count": 0,
        "free_agent_count": 0,
        "drop_count": 0,
        "events": [],
    }


def get_player(
    players: dict[str, dict],
    player_id: str,
) -> dict:
    if player_id not in players:
        players[player_id] = create_player_record(player_id)

    return players[player_id]


# ============================================================
# EVENT HELPERS
# ============================================================

def add_event(
    player: dict,
    event: dict,
) -> None:
    player["events"].append(event)


def event_sort_key(event: dict) -> tuple:
    """
    Sort player events chronologically.

    Draft events do not currently have exact timestamps, so
    they are placed at the beginning of their draft season.
    All timestamped transactions then follow in true
    chronological order.
    """

    season = int(
        event.get("season")
        or 0
    )

    timestamp = event.get(
        "timestamp"
    )

    event_type = event.get(
        "type"
    )

    # Draft comes first within its season.
    if event_type == "draft":
        return (
            season,
            0,
            0,
        )

    # Transactions come after the draft and are ordered
    # using their real Sleeper timestamps.
    return (
        season,
        1,
        int(timestamp or 0),
    )


# ============================================================
# TRANSACTION PARSING
# ============================================================

def detect_transaction_type(transaction: dict) -> str:
    value = first_defined(
        transaction.get("type"),
        transaction.get("transaction_type"),
    )

    if value:
        return str(value).lower()

    return "unknown"


def get_transaction_timestamp(transaction: dict) -> int | None:
    return parse_timestamp(
        first_defined(
            transaction.get("created_timestamp"),
            transaction.get("created"),
            transaction.get("timestamp"),
        )
    )


def normalize_player_assets(value: Any) -> list[dict]:
    """
    Existing normalized transaction files should already contain
    player objects, but this keeps the parser defensive.
    """

    assets = []

    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                assets.append(item)

    elif isinstance(value, dict):
        # Could be:
        # {
        #   "player_id": {...}
        # }
        # or:
        # {
        #   "12345": 7
        # }
        for key, item in value.items():
            if isinstance(item, dict):
                asset = dict(item)

                asset.setdefault(
                    "player_id",
                    str(key),
                )

                assets.append(asset)

            else:
                assets.append(
                    {
                        "player_id": str(key),
                        "roster_id": item,
                    }
                )

    return assets


def process_trade(
    transaction: dict,
    players: dict[str, dict],
) -> None:
    timestamp = get_transaction_timestamp(transaction)

    season = first_defined(
        transaction.get("season"),
        transaction.get("league_season"),
    )

    transaction_id = first_defined(
        transaction.get("transaction_id"),
        transaction.get("id"),
    )

    adds = normalize_player_assets(
        transaction.get("adds")
    )

    drops = normalize_player_assets(
        transaction.get("drops")
    )

    added_by_player = {}

    for asset in adds:
        player_id = player_id_from_asset(asset)

        if player_id:
            added_by_player[player_id] = asset

    dropped_by_player = {}

    for asset in drops:
        player_id = player_id_from_asset(asset)

        if player_id:
            dropped_by_player[player_id] = asset

    all_player_ids = (
        set(added_by_player)
        | set(dropped_by_player)
    )

    for player_id in all_player_ids:
        add_asset = added_by_player.get(player_id, {})
        drop_asset = dropped_by_player.get(player_id, {})

        player = get_player(
            players,
            player_id,
        )

        update_player_metadata(
            player,
            add_asset or drop_asset,
        )

        from_franchise = first_defined(
            drop_asset.get("franchise"),
            drop_asset.get("manager"),
        )

        to_franchise = first_defined(
            add_asset.get("franchise"),
            add_asset.get("manager"),
        )

        event = {
            "type": "trade",
            "season": season,
            "timestamp": timestamp,
            "date": timestamp_to_iso(timestamp),
            "transaction_id": transaction_id,
            "from_franchise": from_franchise,
            "to_franchise": to_franchise,
        }

        add_event(
            player,
            event,
        )

        player["trade_count"] += 1
        player["transaction_count"] += 1


def process_non_trade(
    transaction: dict,
    players: dict[str, dict],
) -> None:
    transaction_type = detect_transaction_type(transaction)

    timestamp = get_transaction_timestamp(transaction)

    season = first_defined(
        transaction.get("season"),
        transaction.get("league_season"),
    )

    transaction_id = first_defined(
        transaction.get("transaction_id"),
        transaction.get("id"),
    )

    adds = normalize_player_assets(
        transaction.get("adds")
    )

    drops = normalize_player_assets(
        transaction.get("drops")
    )

    # --------------------------------------------------------
    # ADD EVENTS
    # --------------------------------------------------------

    for asset in adds:
        player_id = player_id_from_asset(asset)

        if not player_id:
            continue

        player = get_player(
            players,
            player_id,
        )

        update_player_metadata(
            player,
            asset,
        )

        franchise = first_defined(
            asset.get("franchise"),
            asset.get("manager"),
        )

        if transaction_type == "waiver":
            event_type = "waiver_add"
            player["waiver_count"] += 1

        else:
            event_type = "free_agent_add"
            player["free_agent_count"] += 1

        event = {
            "type": event_type,
            "season": season,
            "timestamp": timestamp,
            "date": timestamp_to_iso(timestamp),
            "transaction_id": transaction_id,
            "franchise": franchise,
        }

        add_event(
            player,
            event,
        )

        player["transaction_count"] += 1

    # --------------------------------------------------------
    # DROP EVENTS
    # --------------------------------------------------------

    for asset in drops:
        player_id = player_id_from_asset(asset)

        if not player_id:
            continue

        player = get_player(
            players,
            player_id,
        )

        update_player_metadata(
            player,
            asset,
        )

        franchise = first_defined(
            asset.get("franchise"),
            asset.get("manager"),
        )

        event = {
            "type": "drop",
            "season": season,
            "timestamp": timestamp,
            "date": timestamp_to_iso(timestamp),
            "transaction_id": transaction_id,
            "franchise": franchise,
            "transaction_type": transaction_type,
        }

        add_event(
            player,
            event,
        )

        player["drop_count"] += 1
        player["transaction_count"] += 1


def process_transactions(
    transactions: list[dict],
    players: dict[str, dict],
) -> None:
    for transaction in transactions:
        transaction_type = detect_transaction_type(
            transaction
        )

        if transaction_type == "trade":
            process_trade(
                transaction,
                players,
            )

        elif transaction_type in {
            "waiver",
            "free_agent",
            "free agent",
            "freeagent",
        }:
            process_non_trade(
                transaction,
                players,
            )


# ============================================================
# DRAFT HISTORY
# ============================================================

def find_draft_file() -> Path | None:
    for path in DRAFT_CANDIDATES:
        if path.exists():
            return path

    return None


def flatten_draft_data(data: Any) -> list[dict]:
    """
    Recursively search the draft-history JSON for actual
    draft-selection rows.

    A row is treated as a draft pick when it contains a
    player ID plus enough draft-related information to
    distinguish it from ordinary player metadata.
    """

    rows = []
    seen = set()

    def walk(value: Any) -> None:

        if isinstance(value, list):

            for item in value:
                walk(item)

            return

        if not isinstance(value, dict):
            return

        player_id = first_defined(
            value.get("player_id"),
            value.get("picked_player_id"),
        )

        has_draft_fields = any(
            key in value
            for key in (
                "display_pick",
                "pick_no",
                "pick_number",
                "overall_pick",
                "round",
                "draft_round",
                "drafted_by_franchise",
                "drafting_franchise",
                "original_franchise",
                "pick_id",
            )
        )

        if (
            player_id is not None
            and has_draft_fields
        ):

            signature = (
                str(player_id),
                first_defined(
                    value.get("season"),
                    value.get("draft_season"),
                ),
                first_defined(
                    value.get("round"),
                    value.get("draft_round"),
                ),
                first_defined(
                    value.get("pick_no"),
                    value.get("pick_number"),
                    value.get("overall_pick"),
                    value.get("display_pick"),
                ),
            )

            if signature not in seen:
                seen.add(signature)
                rows.append(value)

        for child in value.values():
            if isinstance(
                child,
                (dict, list),
            ):
                walk(child)

    walk(data)

    return rows


def process_drafts(
    draft_rows: list[dict],
    players: dict[str, dict],
) -> int:
    added = 0

    for row in draft_rows:
        player_id = first_defined(
            row.get("player_id"),
            row.get("picked_player_id"),
        )

        if player_id is None:
            continue

        player_id = str(player_id)

        player = get_player(
            players,
            player_id,
        )

        update_player_metadata(
            player,
            {
                "player_id": player_id,
                "name": first_defined(
                    row.get("player_name"),
                    row.get("name"),
                ),
                "position": row.get("position"),
                "team": first_defined(
                    row.get("nfl_team"),
                    row.get("team"),
                ),
            },
        )

        season = first_defined(
            row.get("season"),
            row.get("draft_season"),
        )

        round_number = first_defined(
            row.get("round"),
            row.get("draft_round"),
        )

        pick_number = first_defined(
            row.get("pick_no"),
            row.get("pick_number"),
            row.get("overall_pick"),
        )

        display_pick = first_defined(
            row.get("display_pick"),
            row.get("pick_label"),
        )

        franchise = first_defined(
            row.get("drafted_by_franchise"),
            row.get("franchise"),
            row.get("manager"),
            row.get("drafting_franchise"),
        )

        original_franchise = first_defined(
            row.get("original_franchise"),
            row.get("original_owner"),
        )

        draft_type = first_defined(
            row.get("draft_type"),
            row.get("type"),
        )

        event = {
            "type": "draft",
            "season": season,
            "timestamp": None,
            "date": None,
            "franchise": franchise,
            "original_franchise": original_franchise,
            "round": round_number,
            "pick_number": pick_number,
            "display_pick": display_pick,
            "draft_type": draft_type,
        }

        add_event(
            player,
            event,
        )

        if player["draft_origin"] is None:
            player["draft_origin"] = {
                "season": season,
                "franchise": franchise,
                "original_franchise": original_franchise,
                "round": round_number,
                "pick_number": pick_number,
                "display_pick": display_pick,
                "draft_type": draft_type,
            }

        added += 1

    return added


# ============================================================
# OWNERSHIP RECONSTRUCTION
# ============================================================

def update_ownership_from_event(
    current_owner: str | None,
    event: dict,
) -> str | None:
    event_type = event["type"]

    if event_type == "draft":
        return first_defined(
            event.get("franchise"),
            current_owner,
        )

    if event_type == "trade":
        return first_defined(
            event.get("to_franchise"),
            current_owner,
        )

    if event_type in {
        "waiver_add",
        "free_agent_add",
    }:
        return first_defined(
            event.get("franchise"),
            current_owner,
        )

    if event_type == "drop":
        franchise = event.get("franchise")

        if (
            franchise is None
            or franchise == current_owner
        ):
            return None

    return current_owner


def finalize_player(player: dict) -> None:
    player["events"].sort(
        key=event_sort_key
    )

    current_owner = None

    ownership_order = []

    for event in player["events"]:
        previous_owner = current_owner

        current_owner = update_ownership_from_event(
            current_owner,
            event,
        )

        if (
            current_owner
            and current_owner not in ownership_order
        ):
            ownership_order.append(
                current_owner
            )

        event["owner_before"] = previous_owner
        event["owner_after"] = current_owner

    player["current_franchise"] = current_owner

    player["franchises_owned_by"] = ownership_order

    player["franchise_count"] = len(
        ownership_order
    )

    player["event_count"] = len(
        player["events"]
    )


# ============================================================
# OUTPUT
# ============================================================

def build_index(
    players: list[dict],
) -> list[dict]:
    """
    Lightweight index for the website search box.
    """

    index = []

    for player in players:
        index.append(
            {
                "player_id": player["player_id"],
                "name": player["name"],
                "position": player["position"],
                "nfl_team": player["nfl_team"],
                "current_franchise": player[
                    "current_franchise"
                ],
                "transaction_count": player[
                    "transaction_count"
                ],
                "trade_count": player[
                    "trade_count"
                ],
                "franchise_count": player[
                    "franchise_count"
                ],
            }
        )

    return index


def build_stats(
    players: list[dict],
    draft_events_added: int,
) -> dict:
    players_with_history = [
        p for p in players
        if p["event_count"] > 0
    ]

    traded_players = [
        p for p in players
        if p["trade_count"] > 0
    ]

    most_traded = sorted(
        traded_players,
        key=lambda p: (
            p["trade_count"],
            p["transaction_count"],
        ),
        reverse=True,
    )[:20]

    most_moved = sorted(
        players_with_history,
        key=lambda p: (
            p["transaction_count"],
            p["event_count"],
        ),
        reverse=True,
    )[:20]

    return {
        "player_count": len(players),
        "players_with_history": len(
            players_with_history
        ),
        "players_ever_traded": len(
            traded_players
        ),
        "draft_events_added": draft_events_added,
        "most_traded_players": [
            {
                "player_id": p["player_id"],
                "name": p["name"],
                "trade_count": p["trade_count"],
                "transaction_count": p[
                    "transaction_count"
                ],
                "franchises_owned_by": p[
                    "franchises_owned_by"
                ],
            }
            for p in most_traded
        ],
        "most_active_player_histories": [
            {
                "player_id": p["player_id"],
                "name": p["name"],
                "event_count": p["event_count"],
                "transaction_count": p[
                    "transaction_count"
                ],
                "trade_count": p["trade_count"],
            }
            for p in most_moved
        ],
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print()
    print("=" * 70)
    print("DIAMOND DYNASTY PLAYER HISTORY")
    print("=" * 70)
    print()

    transactions = load_json(
        TRANSACTIONS_PATH
    )

    print(
        f"Loaded {len(transactions):,} transactions"
    )

    players: dict[str, dict] = {}

    process_transactions(
        transactions,
        players,
    )

    print(
        f"Players found from transactions: "
        f"{len(players):,}"
    )

    draft_events_added = 0

    draft_path = find_draft_file()

    if draft_path:
        print(
            f"Draft file found: "
            f"{draft_path.name}"
        )

        draft_data = load_json(
            draft_path
        )

        draft_rows = flatten_draft_data(
            draft_data
        )

        draft_events_added = process_drafts(
            draft_rows,
            players,
        )

        print(
            f"Draft events added: "
            f"{draft_events_added:,}"
        )

    else:
        print(
            "No generated draft history file found."
        )

        print(
            "Player histories will still be built "
            "from transactions."
        )

    player_list = list(
        players.values()
    )

    for player in player_list:
        finalize_player(
            player
        )

    player_list.sort(
        key=lambda p: (
            (
                p["name"]
                or ""
            ).lower(),
            p["player_id"],
        )
    )

    player_index = build_index(
        player_list
    )

    stats = build_stats(
        player_list,
        draft_events_added,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            player_list,
            f,
            indent=2,
            ensure_ascii=False,
        )

    with INDEX_OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            player_index,
            f,
            indent=2,
            ensure_ascii=False,
        )

    with STATS_OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            stats,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("OUTPUT")
    print("-" * 70)

    print(
        f"Player histories: "
        f"{len(player_list):,}"
    )

    print(
        f"Players ever traded: "
        f"{stats['players_ever_traded']:,}"
    )

    print(
        f"Draft events: "
        f"{draft_events_added:,}"
    )

    print()
    print(
        f"Created: "
        f"{OUTPUT_PATH.relative_to(ROOT)}"
    )

    print(
        f"Created: "
        f"{INDEX_OUTPUT_PATH.relative_to(ROOT)}"
    )

    print(
        f"Created: "
        f"{STATS_OUTPUT_PATH.relative_to(ROOT)}"
    )

    print()
    print("TOP TRADED PLAYERS")
    print("-" * 70)

    for row in stats[
        "most_traded_players"
    ][:10]:

        print(
            f"{row['name']}: "
            f"{row['trade_count']} trades"
        )

    print()


if __name__ == "__main__":
    main()