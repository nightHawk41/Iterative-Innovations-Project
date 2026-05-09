"""
===================================
backend/app/tests/test_sales_cycles.py
===================================
Tests for sales cycle management and reporting isolation.

Covers:
- SalesCycle model CRUD operations
- CycleService.rotate_cycle() functionality
- Transaction assignment to cycles
- Sales report filtering by active cycle
- Inventory upload triggering cycle rotation
"""

import pytest
from datetime import datetime, timezone, date
from app import db
from app.models.sales_cycle import SalesCycle
from app.models.transaction import Transaction
from app.models.item_slot import ItemSlot
from app.services.cycle_service import CycleService
from app.services.transaction_processor import TransactionProcessor


class TestSalesCycleModel:
    """Tests for SalesCycle model basics."""
    
    def test_create_sales_cycle(self, app):
        """Test creating a new sales cycle."""
        with app.app_context():
            cycle = SalesCycle(
                started_at=datetime.now(timezone.utc),
                is_active=True
            )
            db.session.add(cycle)
            db.session.commit()
            
            assert cycle.cycle_id is not None
            assert cycle.is_active is True
            assert cycle.ended_at is None
    
    def test_sales_cycle_to_dict(self, app):
        """Test SalesCycle.to_dict() serialization."""
        with app.app_context():
            cycle = SalesCycle(
                started_at=datetime.now(timezone.utc),
                is_active=True
            )
            db.session.add(cycle)
            db.session.commit()
            
            cycle_dict = cycle.to_dict()
            assert cycle_dict['cycle_id'] == cycle.cycle_id
            assert cycle_dict['is_active'] is True
            assert cycle_dict['ended_at'] is None
            assert 'started_at' in cycle_dict


class TestCycleRotation:
    """Tests for CycleService.rotate_cycle()."""
    
    def test_rotate_cycle_closes_old_and_creates_new(self, app):
        """Test that rotate_cycle closes the old cycle and creates a new one."""
        with app.app_context():
            # Create an initial active cycle
            initial_cycle = SalesCycle(
                started_at=datetime.now(timezone.utc),
                is_active=True
            )
            db.session.add(initial_cycle)
            db.session.commit()
            initial_cycle_id = initial_cycle.cycle_id
            
            # Rotate the cycle
            new_cycle = CycleService.rotate_cycle()
            
            # Verify the old cycle is closed
            old_cycle = db.session.query(SalesCycle).filter_by(
                cycle_id=initial_cycle_id
            ).first()
            assert old_cycle.is_active is False
            assert old_cycle.ended_at is not None
            
            # Verify the new cycle is active
            assert new_cycle.is_active is True
            assert new_cycle.cycle_id != initial_cycle_id
            
            # Verify there's exactly one active cycle
            active_count = db.session.query(SalesCycle).filter_by(
                is_active=True
            ).count()
            assert active_count == 1
    
    def test_rotate_cycle_when_no_active_cycle_exists(self, app):
        """Test rotate_cycle when no active cycle exists yet."""
        with app.app_context():
            # No cycles exist initially
            assert db.session.query(SalesCycle).count() == 0
            
            # Rotate should create the first cycle
            new_cycle = CycleService.rotate_cycle()
            
            assert new_cycle is not None
            assert new_cycle.is_active is True
            assert db.session.query(SalesCycle).count() == 1


class TestTransactionCycleAssignment:
    """Tests for transaction assignment to sales cycles."""
    
    def test_transaction_assigned_to_active_cycle(self, app):
        """Test that processed transactions are assigned to the active cycle."""
        with app.app_context():
            # Create an active cycle
            active_cycle = SalesCycle(
                started_at=datetime.now(timezone.utc),
                is_active=True
            )
            db.session.add(active_cycle)
            db.session.commit()
            
            # Create a transaction manually (simulating what TransactionProcessor does)
            tx = Transaction()
            tx.transaction_id = 1001
            tx.amount = 2.50
            tx.user_id = "Test User"
            tx.timestamp = datetime.now(timezone.utc)
            tx.cycle_id = active_cycle.cycle_id
            
            db.session.add(tx)
            db.session.commit()
            
            # Verify transaction is linked to the cycle
            retrieved_tx = db.session.query(Transaction).filter_by(
                transaction_id=1001
            ).first()
            assert retrieved_tx.cycle_id == active_cycle.cycle_id
    
    def test_transaction_processor_assigns_cycle(self, app):
        """Test that TransactionProcessor assigns cycle_id to transactions."""
        with app.app_context():
            # Create an active cycle
            active_cycle = SalesCycle(
                started_at=datetime.now(timezone.utc),
                is_active=True
            )
            db.session.add(active_cycle)
            db.session.commit()
            
            # Create a simple item slot for price lookup
            slot = ItemSlot(
                slot_id="A1",
                item_name="Test Item",
                quantity=10,
                price=2.50,
                expiration_date=date(2026, 12, 31)
            )
            db.session.add(slot)
            db.session.commit()
            
            # Create a test transaction row
            row = {
                "Transaction Date": "3-10-2026",
                " Transaction Time": "8:15:00 AM",
                "Primary Key": "5001",
                "Patron Name": "John Doe",
                "Tran Amt": "2.50"
            }
            
            # Process the transaction
            processor = TransactionProcessor()
            tx = processor._build_transaction(row, active_cycle.cycle_id)
            
            # Verify cycle_id is assigned
            assert tx.cycle_id == active_cycle.cycle_id


class TestSalesReportFiltering:
    """Tests for sales report filtering by active cycle."""
    
    def test_sales_report_reflects_active_cycle_only(self, app):
        """Test that sales report includes only transactions from the active cycle."""
        with app.app_context():
            # Setup: Create cycle 1, add transactions, rotate to cycle 2
            cycle1 = SalesCycle(
                started_at=datetime.now(timezone.utc),
                is_active=True
            )
            db.session.add(cycle1)
            db.session.commit()
            
            # Add item slot
            slot = ItemSlot(
                slot_id="A1",
                item_name="Coffee",
                quantity=5,
                price=2.50,
                expiration_date=date(2026, 12, 31)
            )
            db.session.add(slot)
            db.session.commit()
            
            # Add transactions to cycle 1
            for i in range(3):
                tx = Transaction(
                    transaction_id=1000 + i,
                    amount=2.50,
                    user_id=f"User{i}",
                    timestamp=datetime.now(timezone.utc),
                    cycle_id=cycle1.cycle_id
                )
                db.session.add(tx)
            db.session.commit()
            
            # Verify cycle 1 has 3 transactions
            cycle1_txn_count = db.session.query(Transaction).filter_by(
                cycle_id=cycle1.cycle_id
            ).count()
            assert cycle1_txn_count == 3
            
            # Rotate to cycle 2
            cycle2 = CycleService.rotate_cycle()
            
            # Add transactions to cycle 2
            for i in range(2):
                tx = Transaction(
                    transaction_id=2000 + i,
                    amount=2.50,
                    user_id=f"User{i}",
                    timestamp=datetime.now(timezone.utc),
                    cycle_id=cycle2.cycle_id
                )
                db.session.add(tx)
            db.session.commit()
            
            # Verify cycle 2 has 2 transactions
            cycle2_txn_count = db.session.query(Transaction).filter_by(
                cycle_id=cycle2.cycle_id
            ).count()
            assert cycle2_txn_count == 2
            
            # Verify only cycle 2 is active
            active_cycle = db.session.query(SalesCycle).filter_by(
                is_active=True
            ).first()
            assert active_cycle.cycle_id == cycle2.cycle_id
            
            # Fetch active cycle transactions (simulating sales report logic)
            active_txns = db.session.query(Transaction).filter(
                Transaction.cycle_id == active_cycle.cycle_id
            ).all()
            assert len(active_txns) == 2
            
            # Verify old cycle transactions are not in the active report
            for txn in active_txns:
                assert txn.transaction_id >= 2000  # cycle 2 transactions


class TestInventoryUploadCycleRotation:
    """Tests for cycle rotation triggered by inventory upload."""
    
    def test_cycle_created_on_first_upload(self, app):
        """Test that a cycle is created when no cycle exists."""
        with app.app_context():
            # No cycles should exist initially
            assert db.session.query(SalesCycle).count() == 0
            
            # When TransactionProcessor runs (which happens after inventory upload),
            # it should create an active cycle
            processor = TransactionProcessor()
            active_cycle = processor._get_or_create_active_cycle()
            
            assert active_cycle is not None
            assert active_cycle.is_active is True
            assert db.session.query(SalesCycle).filter_by(
                is_active=True
            ).count() == 1
