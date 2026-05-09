from datetime import datetime, timezone
from app import db

class Transaction(db.Model):
    __tablename__ = 'transactions'

    # transaction_id is sourced from the CBORD CSV 'Primary Key' field — not auto-generated.
    transaction_id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=False
        ) 
    
    amount = db.Column(
        db.Float, 
        nullable=False
        )
    
    timestamp = db.Column(
        db.DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc)
        )
    
    user_id = db.Column(
        db.String(20), 
        nullable=False
        )
    
    resolved_slot_id = db.Column(
                           db.String(5),
                           db.ForeignKey("item_slots.slot_id"),  # matches ItemSlot.__tablename__
                           nullable=True   # nullable: mapping may fail for unknown prices
                       )
    
    cycle_id = db.Column(
        db.Integer,
        db.ForeignKey("sales_cycles.cycle_id"),
        nullable=True  # nullable during migration; will be populated by cycle rotation logic
    )
    
    def to_dict(self) -> dict:
        """Return a dictionary representation of the transaction."""
        # Ensure timestamp includes timezone info
        ts = self.timestamp
        if ts and ts.tzinfo is None:
            # If somehow timezone-naive, assume UTC
            ts = ts.replace(tzinfo=timezone.utc)
        
        return {
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'timestamp': ts.isoformat() if ts else None,
            'user_id': self.user_id,
            'resolved_slot_id': self.resolved_slot_id,
            'cycle_id': self.cycle_id
        }
    
    def __repr__(self) -> str:
        return (f"<Transaction id={self.transaction_id} | ${self.amount} | resolved_slot_id={self.resolved_slot_id}>")