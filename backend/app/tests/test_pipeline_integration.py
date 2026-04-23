import pytest
from datetime import date, timedelta
from app import db
from app.models.item_slot import ItemSlot
from app.services.transaction_processor import TransactionProcessor

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