import csv
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from app import db

#from app.models.item_slot import ItemSlot
from app.models.transaction import Transaction
from app.models.sales_cycle import SalesCycle
from app.repositories.transaction_repository import TransactionRepository
from app.services.inventory_service import InventoryService

logger = logging.getLogger(__name__)

# Path to the default mock CBORD transaction stream.
DEFAULT_MOCK_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "transaction_stream_mock.csv")
)

# ---------------------------------------------------------------------------
# Column name constants — match the headers in transaction_stream_mock.csv
# ---------------------------------------------------------------------------
COL_DATE      = "Transaction Date"
COL_TIME      = " Transaction Time"   # leading space: CSV header has ", Transaction Time"
COL_PRIMARY   = "Primary Key"
COL_PATRON    = "Patron Name"
COL_TRAN_AMT  = "Tran Amt"


class TransactionProcessor:
    """
    Ingests CBORD-style CSV transaction logs, maps each row to an ItemSlot
    via amount-based price matching, decrements inventory, and persists
    every transaction — resolved or not — for auditing.

    Unresolved rows (unknown price) are logged and counted but never
    silently dropped.
    """

    def __init__(
        self,
        inventory_service: Optional[InventoryService] = None,
        transaction_repository: Optional[TransactionRepository] = None,
    ):
        self._inventory = inventory_service or InventoryService()
        self._tx_repo   = transaction_repository or TransactionRepository()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_csv(self, filepath: str) -> list[dict]:
        """
        Read a CBORD-format CSV file and return a list of raw row dicts.

        Uses the exact column names from transaction_stream_mock.csv:
            Transaction Date, Primary Key, Patron Name, Tran Amt

        Raises:
            FileNotFoundError if the file does not exist.
            ValueError if required columns are missing from the header.
        """
        path = os.path.abspath(filepath)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Transaction CSV not found at: {path}"
            )

        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self._validate_headers(list(reader.fieldnames or []), path)
            for row in reader:
                rows.append(dict(row))

        logger.info("[TransactionProcessor] Parsed %d row(s) from %s", len(rows), path)
        return rows
    
    def process_transactions(self, rows: list[dict]) -> dict:
        """"
        Process a list of raw CSV row dicts produced by parse_csv().
        Wraps the entire process in a single transaction, relying on 
        InventoryService to flush row-by-row to avoid stale reads.
        
        Assigns each transaction to the currently active sales cycle.
        """
        processed_count = 0
        updated_slots: list[dict] = []
        unresolved_amounts: list[float] = []
        
        # Get or create the active sales cycle
        active_cycle = self._get_or_create_active_cycle()
        if not active_cycle:
            raise RuntimeError("Failed to get or create active sales cycle")

        try:
            for row in rows:
                tx = self._build_transaction(row, active_cycle.cycle_id)
                if tx is None:
                    continue  # skip malformed rows but keep going

                try:
                    # Apply the sale (flushes the DB automatically per row)
                    updated_slot = self._inventory.apply_sale(tx)
                    updated_slots.append(updated_slot)
                    processed_count += 1

                except LookupError as exe:
                    # Price did not match any slot — persist unresolved for audit.
                    logger.warning(
                        "[TransactionProcessor] Unresolved amount $%.2f", tx.amount
                    )
                    self._tx_repo.save(tx)
                    db.session.flush() # Flush this audit record too
                    unresolved_amounts.append(round(tx.amount, 2))

                except ValueError as exc:
                    # Reached 0 inventory. Catch it, log it, but DO NOT abort the loop!
                    logger.error(
                        "[TransactionProcessor] Skipping tx_id=%s ($%.2f): %s",
                        tx.transaction_id, tx.amount, exc,
                    )
            
            # If we successfully processed the entire CSV without a catastrophic crash,
            # we permanently write all flushed changes to the database.
            db.session.commit()

        except Exception as exc:
            # Massive system failure (e.g., database disconnected mid-batch)
            db.session.rollback()
            logger.critical(
                "[TransactionProcessor] Catastrophic failure during batch. Rolling back all CSV rows. Error: %s", str(exc)
            )
            raise exc # Re-raise to alert the caller
        
        summary = {
            "processed_count":    processed_count,
            "updated_slots":      updated_slots,
            "unresolved_amounts": unresolved_amounts,
        }
        
        logger.info(
            "[TransactionProcessor] Done — %d processed, %d unresolved.",
            processed_count, len(unresolved_amounts)
        )
        return summary




    # ------------------------------------------------------------------
    # Convenience: run the full pipeline against the default mock file
    # ------------------------------------------------------------------

    def run_from_default_mock(self) -> dict:
        """Parse and process the default transaction_stream_mock.csv in one call."""
        rows = self.parse_csv(DEFAULT_MOCK_PATH)
        return self.process_transactions(rows)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_transaction(self, row: dict, cycle_id: int) -> Optional[Transaction]:
        """
        Convert one raw CSV row dict into a Transaction model instance.

        Returns None (and logs a warning) if any required field is missing
        or cannot be parsed, so a single bad row never aborts the batch.
        
        Assigns the provided cycle_id to the transaction.
        """
        try:
            transaction_id = int(str(row[COL_PRIMARY]).strip())
            amount         = round(float(str(row[COL_TRAN_AMT]).strip()), 2)
            user_id        = str(row[COL_PATRON]).strip()[:20]  # VARCHAR(20) limit

            # Combine date and time columns when both are present.
            # transaction_stream_mock.csv splits the timestamp across two columns:
            #   "Transaction Date"  → "3-10-2026"
            #   " Transaction Time" → " 8:15:00 AM"
            date_raw = str(row[COL_DATE]).strip()
            time_raw = str(row.get(COL_TIME, "")).strip()
            raw_ts   = f"{date_raw} {time_raw}" if time_raw else date_raw
            timestamp = self._parse_timestamp(raw_ts)
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning(
                "[TransactionProcessor] Skipping malformed row %s: %s", row, exc
            )
            return None

        tx = Transaction()
        tx.transaction_id = transaction_id
        tx.amount         = amount
        tx.user_id        = user_id
        tx.timestamp      = timestamp
        tx.resolved_slot_id = None  # set by InventoryService.apply_sale on success
        tx.cycle_id       = cycle_id  # Assign to active sales cycle
        return tx

    @staticmethod
    def _parse_timestamp(raw: str) -> datetime:
        """
        Parse CBORD date strings.
        Falls back to a UTC-aware now() if parsing fails so the row is
        not thrown away over a date formatting quirk.
        """
        for fmt in (
            "%m-%d-%Y %I:%M:%S %p",  # 3-10-2026 8:15:00 AM  (mock CSV combined)
            "%m-%d-%Y %H:%M:%S",     # 3-10-2026 08:15:00
            "%m-%d-%Y",              # 3-10-2026 (date only)
            "%m/%d/%Y %I:%M:%S %p",  # 3/10/2026 8:15:00 AM  (slash variant)
            "%m/%d/%Y %H:%M:%S",     # 3/10/2026 08:15:00
            "%m/%d/%Y",              # 3/10/2026
            "%Y-%m-%d",              # 2026-03-10
        ):
            try:
                naive = datetime.strptime(raw, fmt)
                return naive.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        logger.warning(
            "[TransactionProcessor] Could not parse date '%s'; using UTC now.", raw
        )
        return datetime.now(timezone.utc)


    @staticmethod
    def _validate_headers(fieldnames: list, path: str) -> None:
        """Raise ValueError if any required column is absent from the CSV header."""
        required = {COL_DATE, COL_PRIMARY, COL_PATRON, COL_TRAN_AMT}
        missing  = required - set(fieldnames)
        if missing:
            raise ValueError(
                f"CSV at '{path}' is missing required column(s): {missing}. "
                f"Expected headers matching transaction_stream_mock.csv."
            )

    @staticmethod
    def _get_or_create_active_cycle() -> Optional[SalesCycle]:
        """
        Get the currently active sales cycle, or create one if none exists.
        
        Returns the active SalesCycle or None if creation failed.
        """
        # Try to find an existing active cycle
        active_cycle = db.session.query(SalesCycle).filter_by(is_active=True).first()
        
        if active_cycle:
            return active_cycle
        
        # No active cycle exists; create one
        try:
            new_cycle = SalesCycle(
                started_at=datetime.now(timezone.utc),
                is_active=True
            )
            db.session.add(new_cycle)
            db.session.flush()  # Get the cycle_id without committing the full transaction
            logger.info(
                "[TransactionProcessor] Created new active sales cycle: cycle_id=%d", 
                new_cycle.cycle_id
            )
            return new_cycle
        except Exception as exc:
            logger.error(
                "[TransactionProcessor] Failed to create new sales cycle: %s", exc
            )
            return None
