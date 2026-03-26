from app import db
from app.models.transaction import Transaction

class TransactionRepository:
    """Repository wrapper for Transaction persistence and lookup operations."""

    def __init__(self, session=None):
        # Allow injection for tests; default to Flask-SQLAlchemy session.
        self.session = session or db.session

    def get_all(self) -> list[Transaction]:
        """Return all transactions ordered by timestamp descending."""
        return Transaction.query.order_by(Transaction.timestamp.desc()).all()

    def save(self, transaction: Transaction, commit: bool = True) -> Transaction:
        """Persist a new Transaction instance."""
        self.session.add(transaction)
        if commit:
            self.session.commit()
        return transaction
    
    def get_unresolved(self) -> list[Transaction]:
        """Return transactions that could not be mapped to a slot yet.
        unresolved == resolved_slot_id is NULL."""
        return (
            Transaction.query
            .filter_by(resolved_slot_id=None)
            .order_by(Transaction.timestamp.desc())
            .all()
        )
    
    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """Return one transaction by primary key, or None when not found."""
        if not transaction_id:
            return None
        return self.session.get(Transaction, transaction_id)
    
    def delete_by_id(self, transaction_id: int, commit: bool = True) -> bool:
        """Delete one transaction by id. Returns True if deleted, else False."""
        tx = self.get_by_id(transaction_id)
        if not tx:
            return False
        self.session.delete(tx)
        if commit:
            self.session.commit()
        return True
