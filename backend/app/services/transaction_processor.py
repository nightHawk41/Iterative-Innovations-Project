import csv
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from app.models.transaction import Transaction
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
        """
        Process a list of raw CSV row dicts produced by parse_csv().

        For each row:
          1. Build a Transaction object from the CBORD fields.
          2. Attempt to resolve the slot via InventoryService.apply_sale().
          3. On LookupError (unknown price): persist the transaction with
             resolved_slot_id=None and record the amount as unresolved.
          4. On any other error: log and skip the row (data integrity guard).

        Returns a summary dict:
            processed_count   — rows successfully resolved and applied
            updated_slots     — list of updated slot dicts (one per resolved row)
            unresolved_amounts — list of amounts that could not be mapped
        """
        processed_count    = 0
        updated_slots:      list[dict]  = []
        unresolved_amounts: list[float] = []

        for row in rows:
            tx = self._build_transaction(row)
            if tx is None:
                continue  # row had unparseable data — already logged

            try:
                updated_slot = self._inventory.apply_sale(tx)
                updated_slots.append(updated_slot)
                processed_count += 1

            except LookupError as exc:
                # Price did not match any slot — persist unresolved for audit.
                logger.warning(
                    "[TransactionProcessor] Unresolved amount $%.2f (tx_id=%s): %s",
                    tx.amount, tx.transaction_id, exc,
                )
                self._tx_repo.save(tx)
                unresolved_amounts.append(round(tx.amount, 2))

            except ValueError as exc:
                # Stock went to zero or other domain violation.
                logger.error(
                    "[TransactionProcessor] Skipping tx_id=%s ($%.2f): %s",
                    tx.transaction_id, tx.amount, exc,
                )

        summary = {
            "processed_count":    processed_count,
            "updated_slots":      updated_slots,
            "unresolved_amounts": unresolved_amounts,
        }
        logger.info(
            "[TransactionProcessor] Done — %d processed, %d unresolved out of %d row(s).",
            processed_count, len(unresolved_amounts), len(rows),
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

    def _build_transaction(self, row: dict) -> Optional[Transaction]:
        """
        Convert one raw CSV row dict into a Transaction model instance.

        Returns None (and logs a warning) if any required field is missing
        or cannot be parsed, so a single bad row never aborts the batch.
        """
        try:
            transaction_id = int(str(row[COL_PRIMARY]).strip())
            amount         = round(float(str(row[COL_TRAN_AMT]).strip()), 2)
            user_id        = str(row[COL_PATRON]).strip()[:20]  # VARCHAR(20) limit
            timestamp      = self._parse_timestamp(str(row[COL_DATE]).strip())
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
        return tx

    @staticmethod
    def _parse_timestamp(raw: str) -> datetime:
        """
        Parse CBORD date strings.  The mock CSV uses M/D/YYYY format.
        Falls back to a UTC-aware now() if parsing fails so the row is
        not thrown away over a date formatting quirk.
        """
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S"):
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
