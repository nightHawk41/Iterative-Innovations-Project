"""
=======================================================
cbord_transaction_builder.py
=======================================================
Utility module for generating CBORD-style transaction records.

Mirrors the logTransaction() behavior from vending.html.
Generates randomized patron data for ad-hoc purchases from the vending grid.
"""

import random
from datetime import datetime, timezone
from app.models.transaction import Transaction
from app import db


# Predefined patron data lists (matching vending.html)
PATRON_NAMES = [
    "John Smith",
    "Jane Doe",
    "Robert Johnson",
    "Mary Williams",
    "Michael Brown",
    "Patricia Davis",
    "William Miller",
    "Linda Wilson",
    "David Moore",
    "Barbara Taylor",
]

SVANDC_PLANS = [
    "35 RETRIEVER",
    "45 DEPT.",
    "40 COMMUTER",
]

PERIODS = [
    "Breakfast",
    "Lunch",
    "Afternoon",
    "Dinner",
    "Evening",
]


# Sequence counter for auto-incrementing Primary Keys
_primary_key_counter = None


def _init_counter() -> None:
    """Initialize _primary_key_counter from the DB max transaction_id on first use."""
    global _primary_key_counter
    if _primary_key_counter is not None:
        return
    try:
        from sqlalchemy import func
        max_id = db.session.query(func.max(Transaction.transaction_id)).scalar()
        _primary_key_counter = (max_id + 1) if max_id is not None else 1000
    except Exception:
        _primary_key_counter = 1000


def reset_pk_counter(start_value: int = 1000) -> None:
    """Reset the primary key counter (useful for testing)."""
    global _primary_key_counter
    _primary_key_counter = start_value


def build_cbord_transaction(price: float) -> Transaction:
    """
    Build a CBORD-style transaction record with randomized patron data.
    
    Args:
        price: The transaction amount (from the slot's price).
    
    Returns:
        A Transaction object ready to be persisted, with:
        - transaction_id: auto-incrementing Primary Key
        - amount: the provided price
        - user_id: patron name (for identification)
        - timestamp: current UTC time
        - resolved_slot_id: None (to be filled by caller)
    
    The function generates:
        - Random Primary Key (auto-incrementing integer)
        - Random Patron Name from PATRON_NAMES
        - Random SV&C Plan (for logging/reference, stored in docstring)
        - Random Period (for logging/reference, stored in docstring)
        - Current timestamp as Transaction Date
        - Location hardcoded to 1499 Lib_Sup (for reference only)
        - Tran Amt set to the slot's price
        - Stat hardcoded to C (for reference only)
    """
    global _primary_key_counter
    _init_counter()

    # Auto-increment Primary Key
    transaction_id = _primary_key_counter
    _primary_key_counter += 1
    
    # Randomize patron data
    patron_name = random.choice(PATRON_NAMES)
    svandc_plan = random.choice(SVANDC_PLANS)
    period = random.choice(PERIODS)
    
    # Create transaction with CBORD data
    transaction = Transaction(
        transaction_id=transaction_id,
        amount=round(price, 2),
        timestamp=datetime.now(timezone.utc),
        user_id=patron_name,  # patron name identifies the user
        resolved_slot_id=None,  # to be filled by caller
    )
    
    # Store CBORD metadata in the transaction for potential future use
    # (e.g., for generating CBORD-formatted CSV exports)
    transaction._cbord_metadata = {
        "primary_key": transaction_id,
        "patron_name": patron_name,
        "svandc_plan": svandc_plan,
        "period": period,
        "location": "1499 Lib_Sup",
        "stat": "C",
    }
    
    return transaction
