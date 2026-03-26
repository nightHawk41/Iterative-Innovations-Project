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
    
    def to_dict(self) -> dict:
        """Return a dictionary representation of the transaction."""
        return {
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'resolved_slot_id': self.resolved_slot_id
        }
    
    def __repr__(self) -> str:
        return (f"<Transaction id={self.transaction_id} | ${self.amount} | resolved_slot_id={self.resolved_slot_id}>")