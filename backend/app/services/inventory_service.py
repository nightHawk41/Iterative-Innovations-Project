"""
==========================================
inventory_service.py (updated)
==========================================
Adds optimistic concurrency safeguards to every inventory write:
 
* restock_slot()  — re-reads the slot row inside the active DB transaction
                    before writing; raises ConcurrencyError (HTTP 409) if the
                    row was modified between the read and the write attempt.
 
* apply_sale()    — re-reads the slot row inside the active DB transaction and
                    raises ConcurrencyError (HTTP 409) if decrementing would
                    push quantity below zero (stock went to 0 between the
                    service call and the DB write).

* purchase_slot() — validates stock and expiry, decrements inventory, and
                    appends a Transaction record for sales reporting (B-3).
                    Raises ConcurrencyError (HTTP 409) for out-of-stock or
                    expired slots.
 
All write methods roll back on any exception, keeping the DB in a consistent state.
 
The ConcurrencyError is caught by the API layer (inventory_routes.py /
transaction_routes.py) and translated to a 409 Conflict response.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models.item_slot   import ItemSlot
from app.models.transaction import Transaction
from app.repositories.item_slot_repository  import ItemSlotRepository
from app.services.mapping_service import MappingService


# ---------------------------------------------------------------------------
# Custom exception — signals a 409 Conflict to the API layer
# ---------------------------------------------------------------------------

class ConcurrencyError(RuntimeError):
    """
    Raised when an inventory write cannot be completed safely because the
    slot's state was modified between the caller's read and the attempted
    write.  The API layer should translate this into HTTP 409 Conflict.
    """


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class InventoryService:
    """Application service that owns inventory reads and mutations."""

    def __init__(
        self,
        repository: Optional[ItemSlotRepository] = None,
        mapping_service: Optional[MappingService] = None,
    ):
        self._repo    = repository    or ItemSlotRepository()
        self._mapping = mapping_service or MappingService(self._repo)

    # ------------------------------------------------------------------
    # Read-only
    # ------------------------------------------------------------------

    def get_inventory(self) -> list[dict]:
        """Return all slots serialized for API responses."""
        return [slot.to_dict() for slot in self._repo.get_all()]

    # ------------------------------------------------------------------
    # Restock  (D-2 safeguard applied)
    # ------------------------------------------------------------------

    def restock_slot(
        self,
        slot_id: str,
        quantity_added: int,
        expiration_date: str,
    ) -> dict:
        """
        Restock one slot and return the updated slot payload.

        Concurrency safeguard (D-2):
            The slot row is re-read with FOR-UPDATE semantics inside the
            active session *before* mutating it.  If the row has been
            deleted between the caller's initial lookup and this write,
            a ConcurrencyError is raised (→ HTTP 409).

        Validation:
            - slot_id must exist
            - quantity_added must be > 0
            - expiration_date must be a valid future date
        """
        if quantity_added is None or quantity_added <= 0:
            raise ValueError("quantity_added must be a positive integer.")

        parsed_expiration = self._parse_expiration_date(expiration_date)
        if parsed_expiration <= date.today():
            raise ValueError("expiration_date must be a future date.")

        # Initial existence check (before opening the write transaction).
        initial = self._repo.get_by_id(slot_id)
        if initial is None:
            raise LookupError(f"Slot '{slot_id}' was not found.")

        try:
            # ----------------------------------------------------------------
            # D-2: Re-read the row inside the same DB transaction to detect
            # concurrent modifications before we commit our write.
            # ----------------------------------------------------------------
            fresh_slot = db.session.get(ItemSlot, slot_id)

            if fresh_slot is None:
                # Row was deleted between the initial check and now.
                raise ConcurrencyError(
                    f"Slot '{slot_id}' no longer exists — "
                    "it may have been deleted by a concurrent request.  "
                    "Retry the operation."
                )

            fresh_slot.restock(quantity_added, parsed_expiration)
            db.session.commit()

        except ConcurrencyError:
            db.session.rollback()
            raise
        except (ValueError, SQLAlchemyError) as exc:
            db.session.rollback()
            raise exc

        return fresh_slot.to_dict()

    # ------------------------------------------------------------------
    # Apply sale  (D-2 safeguard applied + Batch Safe)
    # ------------------------------------------------------------------

    def apply_sale(self, transaction: Transaction) -> dict:
        """
        Resolve a sale by amount, decrement inventory by 1, and return
        the updated slot dict.

        Uses session.flush() instead of commit() to allow batch processing
        without stale reads, deferring the final commit or rollback to the caller.
        """
        if transaction is None:
            raise ValueError("transaction is required.")

        # 1. Resolve the slot via price mapping.
        # This raises LookupError if no price matches.
        slot = self._mapping.resolve_slot_by_amount(transaction.amount)

        # ----------------------------------------------------------------
        # D-2: Re-read the row inside the current session so we see the
        # freshest quantity value flushed by the previous CSV row.
        # ----------------------------------------------------------------
        fresh_slot = db.session.get(ItemSlot, slot.slot_id)

        if fresh_slot is None:
            raise ConcurrencyError(
                f"Slot '{slot.slot_id}' disappeared during the sale."
            )

        # 2. Prevent Negative Inventory
        if fresh_slot.quantity <= 0:
            raise ValueError(
                f"Cannot process sale for ${transaction.amount}. Slot '{fresh_slot.slot_id}' "
                f"({fresh_slot.item_name}) is out of stock (quantity={fresh_slot.quantity})."
            )

        # 3. Decrement the stock using the model's logic
        fresh_slot.decrement_stock(1)
        transaction.resolved_slot_id = fresh_slot.slot_id

        db.session.add(fresh_slot)
        db.session.add(transaction)

        # 4. CRITICAL: Flush instead of Commit!
        # Pushes changes to the DB for the next row to see, but doesn't finalize.
        db.session.flush()

        return fresh_slot.to_dict()

    # ------------------------------------------------------------------
    # Purchase  (B-1, D-2 safeguard applied)
    # ------------------------------------------------------------------

    def purchase_slot(self, slot_id: str, quantity: int) -> dict:
        """
        Process a direct slot purchase:
          - Validates the slot exists, has stock, and is not expired.
          - Decrements inventory by quantity.
          - Appends a Transaction record for sales reporting (B-3).
          - Returns the updated slot dict.

        Raises:
            LookupError      — unknown slot_id             (→ HTTP 400)
            ValueError       — bad quantity                (→ HTTP 400)
            ConcurrencyError — out-of-stock, expired, or
                               race condition              (→ HTTP 409)
        """
        if quantity is None or quantity <= 0:
            raise ValueError("quantity must be a positive integer.")

        # Initial existence check (outside the write transaction).
        if self._repo.get_by_id(slot_id) is None:
            raise LookupError(f"Slot '{slot_id}' was not found.")

        try:
            # D-2: Re-read the row inside the active session to see the
            # freshest state before we commit our write.
            fresh_slot = db.session.get(ItemSlot, slot_id)

            if fresh_slot is None:
                raise ConcurrencyError(
                    f"Slot '{slot_id}' no longer exists — "
                    "it may have been removed by a concurrent request. Retry."
                )

            if fresh_slot.quantity <= 0:
                raise ConcurrencyError(
                    f"Slot '{slot_id}' ({fresh_slot.item_name}) is out of stock."
                )

            if fresh_slot.days_until_expiration() <= 0:
                raise ConcurrencyError(
                    f"Slot '{slot_id}' ({fresh_slot.item_name}) has expired "
                    "and cannot be purchased."
                )

            # Decrement stock (raises ValueError if somehow goes negative).
            fresh_slot.decrement_stock(quantity)

            # Record a transaction for sales reporting (B-3).
            # transaction_id: random 31-bit int avoids autoincrement=False constraint.
            # txn = Transaction(
            #     transaction_id=uuid.uuid4().int & 0x7FFFFFFF,
            #     amount=round(fresh_slot.price * quantity, 2),
            #     user_id="purchase",
            #     resolved_slot_id=fresh_slot.slot_id,
            # )
            txn = Transaction()
            txn.transaction_id  = uuid.uuid4().int & 0x7FFFFFFF
            txn.amount          = round(fresh_slot.price * quantity, 2)
            txn.user_id         = "purchase"
            txn.resolved_slot_id = fresh_slot.slot_id


            db.session.add(fresh_slot)
            db.session.add(txn)
            db.session.commit()

        except (ConcurrencyError, ValueError):
            db.session.rollback()
            raise
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise ConcurrencyError(
                f"Database conflict while purchasing slot '{slot_id}'. "
                "Retry the operation."
            ) from exc

        return fresh_slot.to_dict()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_expiration_date(value) -> date:
        """Accept date objects or ISO date strings and return a date object."""
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValueError(
                    "expiration_date must be in 'YYYY-MM-DD' format."
                ) from exc
        raise ValueError("expiration_date must be a date or YYYY-MM-DD string.")