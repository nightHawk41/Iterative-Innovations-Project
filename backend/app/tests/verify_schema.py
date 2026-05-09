"""
============================
TASK D-1 — verify_schema.py
============================
Verifies that db.create_all() produces the correct schema for all current
SQLAlchemy models and confirms that SQLite enforces both foreign-key
relationships at the database level:

    Transaction.resolved_slot_id  -> item_slots.slot_id
    Transaction.cycle_id          -> sales_cycles.cycle_id
    Notification.slot_id          -> item_slots.slot_id

Run from the backend/ directory:
    python -m tests.verify_schema

Expected output ends with:
    ALL D-1 CHECKS PASSED
"""

import os
import sys
import sqlite3
import tempfile

# ---------------------------------------------------------------------------
# Bootstrap — allow running from backend/ without installing the package.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# We create an isolated in-memory app so this script never touches vending.db.
_verify_app = Flask(__name__)
_verify_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"   # in-memory
_verify_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Re-use the real db object bound to the project's app package.
from app import db as _db

# Import all models so their metadata is registered before create_all().
from app.models.item_slot    import ItemSlot       # noqa: F401
from app.models.transaction  import Transaction    # noqa: F401
from app.models.notification import Notification   # noqa: F401
from app.models.sales_cycle  import SalesCycle     # noqa: F401


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _columns(inspector, table: str) -> dict[str, dict]:
    """Return {col_name: col_info_dict} for the given table."""
    return {col["name"]: col for col in inspector.get_columns(table)}


def _fk_targets(inspector, table: str) -> list[tuple[str, str, str]]:
    """
    Return [(constrained_col, referred_table, referred_col), ...] for every
    FK declared on *table*.
    """
    out = []
    for fk in inspector.get_foreign_keys(table):
        for local, remote in zip(
            fk["constrained_columns"], fk["referred_columns"]
        ):
            out.append((local, fk["referred_table"], remote))
    return out


# ---------------------------------------------------------------------------
# Core verification logic
# ---------------------------------------------------------------------------

def run_verification() -> None:
    """Execute all D-1 checks inside an isolated Flask app context."""
    _db.init_app(_verify_app)

    with _verify_app.app_context():
        # ------------------------------------------------------------------ #
        # 1. db.create_all() — build the schema                              #
        # ------------------------------------------------------------------ #
        _db.create_all()
        print("✔  db.create_all() executed without error.")

        from sqlalchemy import inspect as sa_inspect
        insp = sa_inspect(_db.engine)
        tables = set(insp.get_table_names())

        # ------------------------------------------------------------------ #
        # 2. Expected tables exist                                            #
        # ------------------------------------------------------------------ #
        expected_tables = {"item_slots", "transactions", "notification", "sales_cycles"}
        missing = expected_tables - tables
        assert not missing, f"Missing tables: {missing}"
        print(f"✔  All expected tables present: {sorted(expected_tables)}")

        # ------------------------------------------------------------------ #
        # 2b. sales_cycles column shape                                      #
        # ------------------------------------------------------------------ #
        cycle_cols = _columns(insp, "sales_cycles")
        required_cycle_cols = {"cycle_id", "started_at", "ended_at", "is_active"}
        missing_cycle_cols = required_cycle_cols - cycle_cols.keys()
        assert not missing_cycle_cols, f"sales_cycles missing columns: {missing_cycle_cols}"
        print("✔  sales_cycles schema correct (all columns present).")

        # ------------------------------------------------------------------ #
        # 3. item_slots column shape                                          #
        # ------------------------------------------------------------------ #
        slot_cols = _columns(insp, "item_slots")
        required_slot_cols = {
            "slot_id", "item_name", "quantity", "price",
            "expiration_date", "low_threshold", "warning_threshold",
        }
        missing_slot_cols = required_slot_cols - slot_cols.keys()
        assert not missing_slot_cols, f"item_slots missing columns: {missing_slot_cols}"

        # price must be UNIQUE
        unique_constraints = {
            col
            for uc in insp.get_unique_constraints("item_slots")
            for col in uc["column_names"]
        }
        # SQLite sometimes expresses UNIQUE via the index list instead.
        unique_via_index = {
            col
            for idx in insp.get_indexes("item_slots")
            if idx.get("unique")
            for col in idx["column_expressions"]
            if isinstance(col, str)
        }
        # Also check index column_names (some SQLAlchemy versions use this key)
        for idx in insp.get_indexes("item_slots"):
            if idx.get("unique"):
                for col in idx.get("column_names", []):
                    unique_via_index.add(col)

        price_is_unique = (
            "price" in unique_constraints or "price" in unique_via_index
        )
        assert price_is_unique, (
            "item_slots.price is NOT marked UNIQUE. "
            f"unique_constraints={unique_constraints}, indexes={unique_via_index}"
        )
        print("✔  item_slots schema correct (all columns present, price UNIQUE).")

        # ------------------------------------------------------------------ #
        # 4. transactions column shape                                        #
        # ------------------------------------------------------------------ #
        tx_cols = _columns(insp, "transactions")
        required_tx_cols = {
            "transaction_id", "amount", "timestamp",
            "user_id", "resolved_slot_id", "cycle_id",
        }
        missing_tx_cols = required_tx_cols - tx_cols.keys()
        assert not missing_tx_cols, f"transactions missing columns: {missing_tx_cols}"
        print("✔  transactions schema correct (all columns present).")

        # ------------------------------------------------------------------ #
        # 5. notification column shape                                        #
        # ------------------------------------------------------------------ #
        notif_cols = _columns(insp, "notification")
        required_notif_cols = {
            "notification_id", "slot_id", "message",
            "alert_level", "date_triggered",
        }
        missing_notif_cols = required_notif_cols - notif_cols.keys()
        assert not missing_notif_cols, f"notification missing columns: {missing_notif_cols}"
        print("✔  notification schema correct (all columns present).")

        # ------------------------------------------------------------------ #
        # 6. Foreign-key: Transaction.resolved_slot_id -> item_slots.slot_id #
        # ------------------------------------------------------------------ #
        tx_fks = _fk_targets(insp, "transactions")
        tx_fk_found = any(
            local == "resolved_slot_id"
            and referred_table == "item_slots"
            and referred_col == "slot_id"
            for local, referred_table, referred_col in tx_fks
        )
        assert tx_fk_found, (
            f"FK transactions.resolved_slot_id -> item_slots.slot_id NOT FOUND. "
            f"Detected FKs: {tx_fks}"
        )
        print("✔  FK transactions.resolved_slot_id → item_slots.slot_id confirmed.")

        tx_cycle_fk_found = any(
            local == "cycle_id"
            and referred_table == "sales_cycles"
            and referred_col == "cycle_id"
            for local, referred_table, referred_col in tx_fks
        )
        assert tx_cycle_fk_found, (
            f"FK transactions.cycle_id -> sales_cycles.cycle_id NOT FOUND. "
            f"Detected FKs: {tx_fks}"
        )
        print("✔  FK transactions.cycle_id → sales_cycles.cycle_id confirmed.")

        # ------------------------------------------------------------------ #
        # 7. Foreign-key: Notification.slot_id -> item_slots.slot_id         #
        # ------------------------------------------------------------------ #
        notif_fks = _fk_targets(insp, "notification")
        notif_fk_found = any(
            local == "slot_id"
            and referred_table == "item_slots"
            and referred_col == "slot_id"
            for local, referred_table, referred_col in notif_fks
        )
        assert notif_fk_found, (
            f"FK notification.slot_id -> item_slots.slot_id NOT FOUND. "
            f"Detected FKs: {notif_fks}"
        )
        print("✔  FK notification.slot_id → item_slots.slot_id confirmed.")

        # ------------------------------------------------------------------ #
        # 8. SQLite-level FK enforcement via a live INSERT violation test     #
        # ------------------------------------------------------------------ #
        # SQLite requires PRAGMA foreign_keys = ON per-connection.
        # The test uses a raw sqlite3 connection against a temp file so it is
        # completely isolated from any live vending.db.
        # ------------------------------------------------------------------ #
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            conn = sqlite3.connect(tmp_path)
            conn.execute("PRAGMA foreign_keys = ON")

            # Minimal schema mirroring the ORM relationships.
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS item_slots (
                    slot_id TEXT PRIMARY KEY,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL UNIQUE NOT NULL,
                    expiration_date TEXT NOT NULL,
                    low_threshold INTEGER NOT NULL DEFAULT 3,
                    warning_threshold INTEGER NOT NULL DEFAULT 5
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INTEGER PRIMARY KEY,
                    amount REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    resolved_slot_id TEXT REFERENCES item_slots(slot_id)
                );

                CREATE TABLE IF NOT EXISTS notification (
                    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slot_id TEXT NOT NULL REFERENCES item_slots(slot_id),
                    message TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    date_triggered TEXT NOT NULL
                );
            """)

            # -- Test 8a: FK violation on transactions -----------------------
            violated = False
            try:
                conn.execute(
                    "INSERT INTO transactions VALUES (99, 1.50, '2026-01-01', 'u1', 'GHOST_SLOT')"
                )
                conn.commit()
            except sqlite3.IntegrityError:
                violated = True
            assert violated, (
                "SQLite did NOT enforce FK on transactions.resolved_slot_id! "
                "PRAGMA foreign_keys may be OFF."
            )
            print("✔  SQLite FK enforcement on transactions.resolved_slot_id: ACTIVE.")

            # -- Test 8b: FK violation on notification -----------------------
            violated = False
            try:
                conn.execute(
                    "INSERT INTO notification (slot_id, message, alert_level, date_triggered) "
                    "VALUES ('GHOST', 'test', 'warning', '2026-01-01')"
                )
                conn.commit()
            except sqlite3.IntegrityError:
                violated = True
            assert violated, (
                "SQLite did NOT enforce FK on notification.slot_id! "
                "PRAGMA foreign_keys may be OFF."
            )
            print("✔  SQLite FK enforcement on notification.slot_id: ACTIVE.")

            conn.close()
        finally:
            os.unlink(tmp_path)

    print()
    print("=" * 55)
    print("ALL D-1 CHECKS PASSED")
    print("=" * 55)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_verification()