import csv
import os
import random
from datetime import date, datetime, timedelta
from app import db
from app.models.item_slot import ItemSlot

DEFAULT_INVENTORY_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "inventory_config.csv")
)


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
            slot_id, item_name, price, stock, expiration_date

        Optional CSV columns supported:
            - stock (or Quantity)
            - expiration_date (or Days Until Expiry)

        If optional fields are absent in a row, they are returned as None.
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

        if not reader.fieldnames:
            raise ValueError("Inventory CSV has no header row.")

        field_map = {name.strip().lower(): name for name in reader.fieldnames if name}
        row_col = field_map.get("row")
        product_col = field_map.get("product")
        price_col = field_map.get("vending price")

        if not row_col or not product_col or not price_col:
            raise KeyError("CSV must include required columns: ROW, Product, Vending Price")

        stock_col = field_map.get("stock") or field_map.get("quantity")
        exp_date_col = field_map.get("expiration_date") or field_map.get("expiration date")
        days_until_col = field_map.get("days until expiry") or field_map.get("days_until_expiry")

        today = date.today()

        for row in reader:
            slot_id = row[row_col].strip()
            item_name = row[product_col].strip()
            price = float(row[price_col].strip())

            if not slot_id or not item_name:
                continue

            stock = None
            expiration_date = None

            if stock_col:
                raw_stock = str(row.get(stock_col, "")).strip()
                if raw_stock:
                    stock = int(raw_stock)

            if exp_date_col:
                raw_date = str(row.get(exp_date_col, "")).strip()
                if raw_date:
                    expiration_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            elif days_until_col:
                raw_days = str(row.get(days_until_col, "")).strip()
                if raw_days:
                    expiration_date = today + timedelta(days=int(raw_days))

            items.append(
                {
                    "slot_id": slot_id,
                    "item_name": item_name,
                    "price": price,
                    "stock": stock,
                    "expiration_date": expiration_date,
                }
            )
    return items


def seed_database(config_path: str | None = None, update_existing: bool = False) -> dict:
    """
        Populates the ItemSlot table by reading slot/product/price data from
        inventory_config.csv.

        Behavior for quantity/expiration:
            - If CSV row provides optional stock and/or expiration_date, use them.
            - If optional values are absent:
                    * new slots get random quantity (0–10) and random expiry offset (-2 to 30 days)
                    * existing slots get random quantity (0–10) and random expiry offset (-2 to 30 days)

    - If update_existing=False, existing slots are skipped.
    - If update_existing=True, existing slots are updated from CSV.

    Returns a summary dict for API/CLI reporting.
    """
    today = date.today()

    try:
        config_rows = _parse_inventory_config(config_path)
    except (FileNotFoundError, KeyError, ValueError) as e:
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

        csv_stock = entry.get("stock")
        csv_expiration_date = entry.get("expiration_date")

        existing = db.session.get(ItemSlot, slot_id)
        if existing:
            if not update_existing:
                skipped += 1
                continue

            existing.item_name = entry["item_name"]
            existing.price = entry["price"]
            if csv_stock is not None:
                existing.quantity = csv_stock
            else:
                existing.quantity = random.randint(0, 10)
            if csv_expiration_date is not None:
                existing.expiration_date = csv_expiration_date
            else:
                expiry_offset = random.randint(-2, 30)
                existing.expiration_date = today + timedelta(days=expiry_offset)
            updated += 1
            continue

        quantity = csv_stock if csv_stock is not None else random.randint(0, 10)
        if csv_expiration_date is not None:
            expiration_date = csv_expiration_date
        else:
            expiry_offset = random.randint(-2, 30)
            expiration_date = today + timedelta(days=expiry_offset)

        new_slot = ItemSlot()
        new_slot.slot_id = slot_id
        new_slot.item_name = entry["item_name"]
        new_slot.price = entry["price"]
        new_slot.quantity = quantity
        new_slot.expiration_date = expiration_date

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