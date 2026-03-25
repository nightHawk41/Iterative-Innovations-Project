import csv
import os
from datetime import date, timedelta
from app import db
from app.models.item_slot import ItemSlot

DEFAULT_INVENTORY_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "inventory_config.csv")
)

# ---------------------------------------------------------------------------
# Test quantities and expiry offsets keyed by column number (1–10).
# This gives a predictable status distribution across every row:
#   Columns 1–5  → Green  (healthy stock, expiry far out)
#   Columns 6–7  → Yellow (qty at warning threshold OR expiry within 5 days)
#   Columns 8–10 → Red    (qty at low threshold OR expiry within 2 days)
# ---------------------------------------------------------------------------

COLUMN_TEST_PROFILE = {
    1:  (10, 120),
    2:  (9,  120),
    3:  (8,   90),
    4:  (7,   90),
    5:  (6,   60),
    6:  (5,    4),   # Yellow: qty=warning_threshold AND expiry within 5 days
    7:  (4,    3),   # Yellow: qty<warning_threshold
    8:  (3,    1),   # Red:    qty=low_threshold AND expiry within 2 days
    9:  (2,   -1),   # Red:    qty<low_threshold AND already expired
    10: (1,   -3),   # Red:    qty well below threshold AND already expired
}


def _resolve_config_path(config_path: str | None = None) -> str:
    """Return the inventory config path with optional override support."""
    if config_path:
        return os.path.abspath(config_path)

    env_override = os.getenv("INVENTORY_CONFIG_PATH")
    if env_override:
        return os.path.abspath(env_override)

    return DEFAULT_INVENTORY_CONFIG_PATH


def _parse_inventory_config(config_path: str | None = None) -> list[dict]:
    """
    Reads inventory_config.csv and returns a list of dicts with keys:
      slot_id, item_name, price
    Raises FileNotFoundError if the file is missing.
    """
    path = _resolve_config_path(config_path)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"inventory_config.csv not found at: {path}\n"
            "Ensure the file exists before running the seed."
        )

    items = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            slot_id = row["ROW"].strip()
            item_name = row["Product"].strip()
            price = float(row["Vending Price"].strip())

            if not slot_id or not item_name:
                continue

            items.append({"slot_id": slot_id, "item_name": item_name, "price": price})
    return items


def _get_column(slot_id: str) -> int:
    """
    Extracts the column number from a slot_id like 'A7' -> 7, 'K10' -> 10.
    """
    return int(slot_id[1:])


def seed_database(config_path: str | None = None, update_existing: bool = False) -> dict:
    """
    Populates the ItemSlot table by reading slot/product/price data from
    inventory_config.csv, then applying test quantities and expiry offsets
    based on column position for status color coverage.

    - If update_existing=False, existing slots are skipped.
    - If update_existing=True, existing slots are updated from CSV.

    Returns a summary dict for API/CLI reporting.
    """
    today = date.today()

    try:
        config_rows = _parse_inventory_config(config_path)
    except FileNotFoundError as e:
        print(f"[seed] ERROR: {e}")
        return {
            "added": 0,
            "updated": 0,
            "skipped": 0,
            "total_rows": 0,
            "config_path": _resolve_config_path(config_path),
            "error": str(e),
        }

    added = 0
    updated = 0
    skipped = 0

    for entry in config_rows:
        slot_id = entry["slot_id"]

        col = _get_column(slot_id)
        quantity, expiry_offset = COLUMN_TEST_PROFILE.get(col, (6, 60))

        existing = db.session.get(ItemSlot, slot_id)
        if existing:
            if not update_existing:
                skipped += 1
                continue

            existing.item_name = entry["item_name"]
            existing.price = entry["price"]
            existing.quantity = quantity
            existing.expiration_date = today + timedelta(days=expiry_offset)
            updated += 1
            continue

        new_slot = ItemSlot()
        new_slot.slot_id = slot_id
        new_slot.item_name = entry["item_name"]
        new_slot.price = entry["price"]
        new_slot.quantity = quantity
        new_slot.expiration_date = today + timedelta(days=expiry_offset)

        db.session.add(new_slot)
        added += 1

    db.session.commit()

    summary = {
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "total_rows": len(config_rows),
        "config_path": _resolve_config_path(config_path),
    }
    print(
        "[seed] Done - "
        f"{added} added, {updated} updated, {skipped} skipped "
        f"from {summary['total_rows']} row(s)."
    )
    return summary


if __name__ == "__main__":
    from app.server import app

    with app.app_context():
        seed_database()