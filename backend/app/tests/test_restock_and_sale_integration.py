"""
=================================================
TASK D-3 — test_restock_and_sale_integration.py
=================================================
Validates that a manual restock and a simulated CSV sale interact correctly
on the same slot.

Scenario:
  1.  Seed the database (only slot A1 for isolation).
  2.  Record the initial quantity / expiration of A1.
  3.  POST a restock to A1 (+5 units, new far-future expiry).
  4.  Assert the quantity and expiry date updated correctly.
  5.  Run a simulated CSV sale that resolves to A1 (amount = $2.15).
  6.  Assert quantity decremented by 1 from the post-restock value.
  7.  Assert the expiration date was NOT changed by the sale.
  8.  Verify the Transaction row was persisted with resolved_slot_id = 'A1'.
  9.  Verify that attempting to over-sell raises ConcurrencyError (D-2 path).

Run from the backend/ directory:
    python -m tests.test_restock_and_sale_integration

Expected output ends with:
    ✅  ALL D-3 CHECKS PASSED
"""

from __future__ import annotations

import os
import sys
import csv
import tempfile
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Path bootstrap — allow running from backend/ without installing the package.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask
from app import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"   # isolated, in-memory
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["TESTING"] = True

# Import all models before create_all so their metadata is registered.
from app.models.item_slot    import ItemSlot       # noqa: F401
from app.models.transaction  import Transaction    # noqa: F401
from app.models.notification import Notification   # noqa: F401


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_single_slot(slot_id="A1", item_name="Granola Bar", price=2.15, qty=6):
    """Insert one ItemSlot row for use in D-3 tests."""
    slot = ItemSlot()
    slot.slot_id         = slot_id
    slot.item_name       = item_name
    slot.price           = price
    slot.quantity        = qty
    slot.expiration_date = date.today() + timedelta(days=30)
    db.session.add(slot)
    db.session.commit()
    return slot


def _make_mock_csv(transaction_id: int, amount: float, patron: str = "Test User") -> str:
    """
    Write a minimal CBORD-format CSV to a temp file and return the path.
    The caller is responsible for deleting the file.
    """
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline=""
    )
    writer = csv.DictWriter(tmp, fieldnames=[
        "Transaction Date", "Location", "SV&C Plan",
        "Primary Key", "Patron Name", "Tran Amt",
        "Amt Remain", "Tax", "Period",
    ])
    writer.writeheader()
    writer.writerow({
        "Transaction Date": "3/1/2026",
        "Location":         "1499 Lib_Sup",
        "SV&C Plan":        "35 RETRIEVER",
        "Primary Key":      str(transaction_id),
        "Patron Name":      patron,
        "Tran Amt":         str(amount),
        "Amt Remain":       "100.00",
        "Tax":              "0.00",
        "Period":           "2 - Lunch",
    })
    tmp.close()
    return tmp.name


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_integration_test() -> None:
    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Local imports — require app context.
        from app.services.inventory_service   import InventoryService, ConcurrencyError
        from app.services.transaction_processor import TransactionProcessor
        from app.repositories.item_slot_repository import ItemSlotRepository
        from app.repositories.transaction_repository import TransactionRepository

        svc        = InventoryService()
        processor  = TransactionProcessor()
        slot_repo  = ItemSlotRepository()
        tx_repo    = TransactionRepository()

        # ------------------------------------------------------------------ #
        # Step 1 — Seed a single slot                                        #
        # ------------------------------------------------------------------ #
        seed = _seed_single_slot(slot_id="A1", price=2.15, qty=6)
        initial_qty  = seed.quantity
        initial_exp  = seed.expiration_date
        print(f"✔  [Step 1] Seeded slot A1: qty={initial_qty}, expiry={initial_exp}")

        # ------------------------------------------------------------------ #
        # Step 2 — Manual restock                                             #
        # ------------------------------------------------------------------ #
        restock_qty  = 5
        new_expiry   = (date.today() + timedelta(days=90)).isoformat()
        updated      = svc.restock_slot("A1", restock_qty, new_expiry)

        expected_qty_after_restock = initial_qty + restock_qty
        assert updated["quantity"] == expected_qty_after_restock, (
            f"After restock: expected qty={expected_qty_after_restock}, "
            f"got {updated['quantity']}"
        )
        assert updated["expiration_date"] == new_expiry, (
            f"After restock: expected expiry={new_expiry}, "
            f"got {updated['expiration_date']}"
        )
        print(
            f"✔  [Step 2] Restock applied: qty={updated['quantity']}, "
            f"expiry={updated['expiration_date']}"
        )

        # ------------------------------------------------------------------ #
        # Step 3 — Simulated CSV sale that resolves to A1 (amount=$2.15)    #
        # ------------------------------------------------------------------ #
        csv_path = _make_mock_csv(transaction_id=1001, amount=2.15)
        try:
            rows    = processor.parse_csv(csv_path)
            summary = processor.process_transactions(rows)
        finally:
            os.unlink(csv_path)

        assert summary["processed_count"] == 1, (
            f"Expected 1 processed sale, got {summary['processed_count']}. "
            f"Unresolved: {summary['unresolved_amounts']}"
        )
        assert len(summary["unresolved_amounts"]) == 0, (
            f"Sale should have been resolved; unresolved={summary['unresolved_amounts']}"
        )
        print(
            f"✔  [Step 3] CSV sale processed: {summary['processed_count']} row, "
            f"0 unresolved"
        )

        # ------------------------------------------------------------------ #
        # Step 4 — Quantity decremented by 1, expiry unchanged               #
        # ------------------------------------------------------------------ #
        slot_after_sale = slot_repo.get_by_id("A1")
        expected_qty_after_sale = expected_qty_after_restock - 1

        assert slot_after_sale.quantity == expected_qty_after_sale, (
            f"After sale: expected qty={expected_qty_after_sale}, "
            f"got {slot_after_sale.quantity}"
        )
        assert slot_after_sale.expiration_date.isoformat() == new_expiry, (
            f"Sale must NOT change expiry date. "
            f"Expected {new_expiry}, got {slot_after_sale.expiration_date}"
        )
        print(
            f"✔  [Step 4] Post-sale state correct: qty={slot_after_sale.quantity}, "
            f"expiry={slot_after_sale.expiration_date} (unchanged)"
        )

        # ------------------------------------------------------------------ #
        # Step 5 — Transaction row persisted with resolved_slot_id='A1'     #
        # ------------------------------------------------------------------ #
        tx = tx_repo.get_by_id(1001)
        assert tx is not None, "Transaction #1001 not found in DB."
        assert tx.resolved_slot_id == "A1", (
            f"Transaction.resolved_slot_id should be 'A1', got '{tx.resolved_slot_id}'"
        )
        assert round(tx.amount, 2) == 2.15, (
            f"Transaction.amount should be 2.15, got {tx.amount}"
        )
        print(
            f"✔  [Step 5] Transaction row persisted: "
            f"id={tx.transaction_id}, amount={tx.amount}, "
            f"resolved_slot_id={tx.resolved_slot_id}"
        )

        # ------------------------------------------------------------------ #
        # Step 6 — Multiple sales drain stock; ConcurrencyError on 0 qty    #
        # ------------------------------------------------------------------ #
        # Drain the remaining stock via service calls directly (no CSV needed).
        remaining = slot_after_sale.quantity   # e.g. 10

        for i in range(remaining):
            tx_drain = Transaction()
            tx_drain.transaction_id = 2000 + i
            tx_drain.amount         = 2.15
            tx_drain.user_id        = f"drain_user_{i}"
            from datetime import datetime, timezone
            tx_drain.timestamp      = datetime.now(timezone.utc)
            svc.apply_sale(tx_drain)

        slot_empty = slot_repo.get_by_id("A1")
        assert slot_empty.quantity == 0, (
            f"Expected qty=0 after draining, got {slot_empty.quantity}"
        )
        print(f"✔  [Step 6] Stock drained to 0 via {remaining} sales.")

        # Now a further sale must raise ConcurrencyError (D-2).
        import traceback
        raised_409 = False
        try:
            tx_extra = Transaction()
            tx_extra.transaction_id = 9999
            tx_extra.amount         = 2.15
            tx_extra.user_id        = "over_sell_user"
            from datetime import datetime, timezone
            tx_extra.timestamp      = datetime.now(timezone.utc)
            svc.apply_sale(tx_extra)
        except ConcurrencyError as exc:
            raised_409 = True
            print(f"✔  [Step 6] ConcurrencyError correctly raised for 0-stock slot:")
            print(f"           '{exc}'")

        assert raised_409, (
            "Expected ConcurrencyError when selling from a 0-stock slot, "
            "but no error was raised (D-2 safeguard not working)."
        )

    print()
    print("=" * 55)
    print("✅  ALL D-3 CHECKS PASSED")
    print("=" * 55)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_integration_test()