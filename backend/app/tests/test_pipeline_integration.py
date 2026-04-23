import pytest
from datetime import date, datetime, timedelta, timezone
from app import db
from app.models.item_slot import ItemSlot
from app.services.transaction_processor import TransactionProcessor, DEFAULT_MOCK_PATH


# ===========================================================================
# B-07: Verify _parse_timestamp handles all supported formats
# ===========================================================================

class TestParseTimestamp:

    def test_slash_24hr(self):
        """Standard 24-hour slash format."""
        dt = TransactionProcessor._parse_timestamp("10/01/2026 14:30:00")
        assert dt == datetime(2026, 10, 1, 14, 30, 0, tzinfo=timezone.utc)

    def test_slash_12hr_am(self):
        """Slash-separated 12-hour AM/PM format."""
        dt = TransactionProcessor._parse_timestamp("3/25/2026 8:15:00 AM")
        assert dt.hour == 8
        assert dt.minute == 15
        assert dt.tzinfo is not None

    def test_slash_12hr_pm(self):
        """Slash-separated 12-hour PM."""
        dt = TransactionProcessor._parse_timestamp("3/25/2026 11:42:19 PM")
        assert dt.hour == 23
        assert dt.minute == 42
        assert dt.second == 19

    def test_dash_date_with_12hr_time(self):
        """M-D-YYYY combined with H:MM:SS AM/PM — the mock CSV format."""
        dt = TransactionProcessor._parse_timestamp("3-10-2026 8:15:00 AM")
        assert dt == datetime(2026, 3, 10, 8, 15, 0, tzinfo=timezone.utc)

    def test_dash_date_with_24hr_time(self):
        """M-D-YYYY with 24-hour time."""
        dt = TransactionProcessor._parse_timestamp("3-10-2026 20:30:00")
        assert dt == datetime(2026, 3, 10, 20, 30, 0, tzinfo=timezone.utc)

    def test_dash_date_only(self):
        """M-D-YYYY with no time component."""
        dt = TransactionProcessor._parse_timestamp("3-10-2026")
        assert dt.year == 2026
        assert dt.month == 3
        assert dt.day == 10
        assert dt.tzinfo is not None

    def test_iso_date_only(self):
        """ISO YYYY-MM-DD date only."""
        dt = TransactionProcessor._parse_timestamp("2026-03-10")
        assert dt.year == 2026
        assert dt.month == 3
        assert dt.day == 10

    def test_unparseable_returns_utc_now(self):
        """Completely unparseable string should fall back to UTC now."""
        before = datetime.now(timezone.utc)
        dt = TransactionProcessor._parse_timestamp("not-a-date")
        after = datetime.now(timezone.utc)
        assert before <= dt <= after
        assert dt.tzinfo is not None

    def test_result_is_always_timezone_aware(self):
        """All parsed timestamps must carry timezone info."""
        for raw in ("3-10-2026 8:15:00 AM", "10/01/2026 14:00:00", "2026-01-01"):
            dt = TransactionProcessor._parse_timestamp(raw)
            assert dt.tzinfo is not None, f"No tzinfo for '{raw}'"


# ===========================================================================
# B-07: Verify parse_csv correctly reads the mock CBORD CSV structure
# ===========================================================================

class TestParseCsv:

    def test_parse_csv_returns_correct_row_count(self):
        """The mock CSV has 26 data rows (excluding header)."""
        processor = TransactionProcessor()
        rows = processor.parse_csv(DEFAULT_MOCK_PATH)
        assert len(rows) == 26

    def test_parse_csv_has_required_columns(self):
        """Every row must contain the four required columns."""
        processor = TransactionProcessor()
        rows = processor.parse_csv(DEFAULT_MOCK_PATH)
        required = {"Transaction Date", "Primary Key", "Patron Name", "Tran Amt"}
        for row in rows:
            assert required.issubset(row.keys()), f"Missing columns in row: {row}"

    def test_parse_csv_has_time_column(self):
        """The mock CSV has a separate ' Transaction Time' column."""
        processor = TransactionProcessor()
        rows = processor.parse_csv(DEFAULT_MOCK_PATH)
        # The leading space is part of the column name due to CSV formatting
        assert " Transaction Time" in rows[0], "Expected ' Transaction Time' column"

    def test_parse_csv_date_format_is_dash_separated(self):
        """Date values in mock CSV use M-D-YYYY format with dashes."""
        processor = TransactionProcessor()
        rows = processor.parse_csv(DEFAULT_MOCK_PATH)
        date_val = rows[0]["Transaction Date"].strip()
        assert "-" in date_val, f"Expected dash-separated date, got: '{date_val}'"
        assert "/" not in date_val, "Date should not use slashes"

    def test_parse_csv_time_is_ampm_format(self):
        """Time values use H:MM:SS AM/PM format."""
        processor = TransactionProcessor()
        rows = processor.parse_csv(DEFAULT_MOCK_PATH)
        time_val = rows[0][" Transaction Time"].strip()
        assert "AM" in time_val or "PM" in time_val, f"Expected AM/PM time, got: '{time_val}'"

    def test_parse_csv_primary_keys_are_integers(self):
        """Primary Key values should be parseable as integers."""
        processor = TransactionProcessor()
        rows = processor.parse_csv(DEFAULT_MOCK_PATH)
        for row in rows:
            pk = row["Primary Key"].strip()
            assert pk.isdigit(), f"Primary Key is not an integer: '{pk}'"

    def test_parse_csv_amounts_are_floats(self):
        """Tran Amt values should be parseable as floats."""
        processor = TransactionProcessor()
        rows = processor.parse_csv(DEFAULT_MOCK_PATH)
        for row in rows:
            try:
                float(row["Tran Amt"].strip())
            except ValueError:
                raise AssertionError(f"Tran Amt not parseable as float: '{row['Tran Amt']}'")


# ===========================================================================
# B-07: End-to-end pipeline test using the mock CBORD CSV
# ===========================================================================

def test_mock_cbord_csv_parsed_end_to_end(app):
    """
    Full end-to-end test: parse the mock CSV, combine date+time columns,
    and verify timestamps are correctly parsed with AM/PM and dash-separated
    date format. Uses an in-memory DB with slots priced to match mock amounts.
    """
    import os
    mock_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..", "..", "data", "transaction_stream_mock.csv"
        )
    )

    with app.app_context():
        # Seed slots with prices matching all four amounts in the mock CSV:
        # 1.50, 3.05, 3.50, 8.03
        future = date.today() + timedelta(days=90)
        slots = [
            ItemSlot(slot_id="A1", item_name="Chips",      quantity=10, price=1.50, expiration_date=future),
            ItemSlot(slot_id="A2", item_name="Energy Bar", quantity=10, price=3.05, expiration_date=future),
            ItemSlot(slot_id="A3", item_name="Soda",       quantity=10, price=3.50, expiration_date=future),
            ItemSlot(slot_id="A4", item_name="Sandwich",   quantity=10, price=8.03, expiration_date=future),
        ]
        db.session.add_all(slots)
        db.session.commit()

        processor = TransactionProcessor()

        # Step 1: verify parse_csv can read all 26 rows
        rows = processor.parse_csv(mock_path)
        assert len(rows) == 26, f"Expected 26 rows, got {len(rows)}"

        # Step 2: verify each row's combined timestamp parses correctly
        for i, row in enumerate(rows):
            date_raw = row["Transaction Date"].strip()
            time_raw = row.get(" Transaction Time", "").strip()
            combined = f"{date_raw} {time_raw}" if time_raw else date_raw
            dt = TransactionProcessor._parse_timestamp(combined)

            assert dt.tzinfo is not None, f"Row {i}: timestamp missing timezone"
            assert dt.year == 2026, f"Row {i}: unexpected year in '{combined}'"
            assert dt.month == 3,  f"Row {i}: unexpected month in '{combined}'"

        # Step 3: run the full pipeline and verify it completes without error
        summary = processor.process_transactions(rows)

        # All 26 rows have known amounts (1.50 or 3.05) → should all resolve
        assert summary["processed_count"] == 26, (
            f"Expected 26 processed, got {summary['processed_count']}. "
            f"Unresolved: {summary['unresolved_amounts']}"
        )
        assert summary["unresolved_amounts"] == [], (
            f"Unexpected unresolved amounts: {summary['unresolved_amounts']}"
        )


def test_mock_cbord_csv_transaction_timestamps_are_correct(app):
    """
    Verify that persisted Transaction records have the correct parsed timestamp,
    not a fallback 'now()' value — proving _parse_timestamp handled the format.
    """
    import os
    from app.models.transaction import Transaction

    mock_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..", "..", "data", "transaction_stream_mock.csv"
        )
    )

    with app.app_context():
        slot = ItemSlot(
            slot_id="A1", item_name="Chips", quantity=10, price=1.50,
            expiration_date=date.today() + timedelta(days=90),
        )
        db.session.add(slot)
        db.session.commit()

        processor = TransactionProcessor()
        rows = processor.parse_csv(mock_path)

        # Only process the 1.50 rows (first 8 rows in the mock CSV)
        rows_150 = [r for r in rows if r["Tran Amt"].strip() == "1.50"]
        processor.process_transactions(rows_150)

        # Fetch all persisted transactions and verify they have a date in March 2026
        txns = Transaction.query.all()
        assert len(txns) > 0, "No transactions were persisted"

        for txn in txns:
            ts = txn.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            # The mock CSV date is 3-10-2026; confirm it's not today (fallback)
            assert ts.year  == 2026, f"Unexpected year {ts.year} — timestamp fallback?"
            assert ts.month == 3,    f"Unexpected month {ts.month} — timestamp fallback?"
            assert ts.day   == 10,   f"Unexpected day {ts.day} — timestamp fallback?"
# Use 'app' instead of 'client' here!
def test_full_csv_to_database_pipeline(app):
    
    # Use 'app.app_context()' here!
    with app.app_context():
        # 1. Setup Database with test items
        slot_a = ItemSlot(
            slot_id="A1", item_name="Chips", quantity=2, price=1.50, 
            expiration_date=date.today() + timedelta(days=30)
        )
        slot_b = ItemSlot(
            slot_id="B1", item_name="Soda", quantity=5, price=2.00, 
            expiration_date=date.today() + timedelta(days=30)
        )
        
        db.session.add_all([slot_a, slot_b])
        db.session.commit()

        # 2. Create Mock CSV Data
        # We are simulating 4 transactions passing through the CSV log
        mock_csv_rows = [
            # Row 1: Valid sale ($1.50). Chips drop 2 -> 1
            {"Transaction Date": "10/01/2026", "Primary Key": "1001", "Patron Name": "User1", "Tran Amt": "1.50"}, 
            
            # Row 2: Valid sale ($1.50). Chips drop 1 -> 0
            {"Transaction Date": "10/01/2026", "Primary Key": "1002", "Patron Name": "User2", "Tran Amt": "1.50"}, 
            
            # Row 3: INVALID sale ($1.50). Chips are at 0! Should gracefully fail and skip.
            {"Transaction Date": "10/01/2026", "Primary Key": "1003", "Patron Name": "User3", "Tran Amt": "1.50"}, 
            
            # Row 4: Valid sale ($2.00). Soda drops 5 -> 4
            {"Transaction Date": "10/01/2026", "Primary Key": "1004", "Patron Name": "User4", "Tran Amt": "2.00"}, 
        ]

        # 3. Run the Pipeline
        processor = TransactionProcessor()
        summary = processor.process_transactions(mock_csv_rows)

        # 4. Assert Results
        # Out of 4 rows, only 3 should have successfully processed
        assert summary["processed_count"] == 3  
        assert len(summary["unresolved_amounts"]) == 0 
        
        # 5. Verify the Final Database State
        # We fetch the slots fresh from the database to guarantee the commit worked
        final_slot_a = db.session.get(ItemSlot, "A1")
        final_slot_b = db.session.get(ItemSlot, "B1")
        
        # Chips should be exactly 0 (it protected itself from going negative)
        assert final_slot_a.quantity == 0
        
        # Soda should be exactly 4 (it processed correctly after the Chips failed)
        assert final_slot_b.quantity == 4

def test_parse_timestamp_ampm():
    raw = "3/25/2026 11:42:19 PM"
    dt = TransactionProcessor._parse_timestamp(raw)
    assert dt.year == 2026
    assert dt.month == 3
    assert dt.day == 25
    assert dt.hour == 23
    assert dt.minute == 42
    assert dt.second == 19
    assert dt.tzinfo is not None