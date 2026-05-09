from datetime import datetime, timezone
from app import db


class SalesCycle(db.Model):
    """
    Represents a sales reporting cycle tied to an inventory batch.
    
    When a new inventory is uploaded, the current active cycle is closed
    (ended_at is set, is_active = False) and a new cycle is created.
    
    This allows sales reports to be scoped to specific inventory batches,
    enabling multi-cycle historical reporting and archive management.
    """
    __tablename__ = 'sales_cycles'
    
    cycle_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    
    started_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    ended_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )
    
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    
    # Relationship to transactions in this cycle
    transactions = db.relationship(
        'Transaction',
        backref='sales_cycle',
        lazy=True,
        foreign_keys='Transaction.cycle_id'
    )
    
    def to_dict(self) -> dict:
        """Return a dictionary representation of the sales cycle."""
        return {
            'cycle_id': self.cycle_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'is_active': self.is_active,
            'transaction_count': len(self.transactions) if self.transactions else 0
        }
