"""
Test suite for the CBORD transaction builder utility.
"""

import pytest
from app.services.cbord_transaction_builder import (
    build_cbord_transaction,
    reset_pk_counter,
    PATRON_NAMES,
    SVANDC_PLANS,
    PERIODS,
)


class TestCBORDTransactionBuilder:
    
    def test_build_transaction_returns_transaction_object(self):
        """build_cbord_transaction should return a Transaction instance."""
        from app.models.transaction import Transaction
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.50)
        assert isinstance(txn, Transaction)
    
    def test_build_transaction_sets_amount(self):
        """Transaction amount should match the provided price."""
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.50)
        assert txn.amount == 2.50
    
    def test_build_transaction_sets_amount_rounded(self):
        """Transaction amount should be rounded to 2 decimal places."""
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.5555)
        assert txn.amount == 2.56
    
    def test_build_transaction_auto_increments_pk(self):
        """Transaction IDs should auto-increment."""
        reset_pk_counter(1000)
        
        txn1 = build_cbord_transaction(2.50)
        txn2 = build_cbord_transaction(3.00)
        
        assert txn1.transaction_id == 1000
        assert txn2.transaction_id == 1001
    
    def test_build_transaction_assigns_patron_name(self):
        """user_id should be a patron name from the predefined list."""
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.50)
        assert txn.user_id in PATRON_NAMES
    
    def test_build_transaction_has_timestamp(self):
        """Transaction should have a non-null timestamp."""
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.50)
        assert txn.timestamp is not None
    
    def test_build_transaction_resolved_slot_id_none_initially(self):
        """resolved_slot_id should be None initially (to be filled by caller)."""
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.50)
        assert txn.resolved_slot_id is None
    
    def test_build_transaction_cbord_metadata_stored(self):
        """Transaction should have CBORD metadata attached."""
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.50)
        assert hasattr(txn, '_cbord_metadata')
        assert 'primary_key' in txn._cbord_metadata
        assert 'patron_name' in txn._cbord_metadata
        assert 'svandc_plan' in txn._cbord_metadata
        assert 'period' in txn._cbord_metadata
        assert 'location' in txn._cbord_metadata
        assert 'stat' in txn._cbord_metadata
    
    def test_build_transaction_svandc_plan_valid(self):
        """CBORD metadata should include a valid SV&C plan."""
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.50)
        assert txn._cbord_metadata['svandc_plan'] in SVANDC_PLANS
    
    def test_build_transaction_period_valid(self):
        """CBORD metadata should include a valid period."""
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.50)
        assert txn._cbord_metadata['period'] in PERIODS
    
    def test_build_transaction_location_hardcoded(self):
        """Location should always be hardcoded to 1499 Lib_Sup."""
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.50)
        assert txn._cbord_metadata['location'] == "1499 Lib_Sup"
    
    def test_build_transaction_stat_hardcoded(self):
        """Stat should always be hardcoded to C."""
        reset_pk_counter(1000)
        
        txn = build_cbord_transaction(2.50)
        assert txn._cbord_metadata['stat'] == "C"
    
    def test_reset_pk_counter_resets_sequence(self):
        """reset_pk_counter should reset the auto-increment sequence."""
        reset_pk_counter(2000)
        
        txn1 = build_cbord_transaction(2.50)
        assert txn1.transaction_id == 2000
        
        reset_pk_counter(3000)
        txn2 = build_cbord_transaction(3.00)
        assert txn2.transaction_id == 3000
    
    def test_multiple_transactions_have_different_patron_names(self):
        """Multiple transactions might have different patron names (randomized)."""
        reset_pk_counter(1000)
        
        # Run multiple times to increase chance of different names
        names_seen = set()
        for _ in range(20):
            txn = build_cbord_transaction(2.50)
            names_seen.add(txn.user_id)
        
        # Should see multiple different names over 20 iterations
        # (statistically very unlikely to see the same name 20 times in a row)
        assert len(names_seen) >= 2, "Should see multiple different patron names"
