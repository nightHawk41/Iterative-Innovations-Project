from datetime import datetime
from app import db

class Transaction(db.Model):
    __tablename__ = 'transactions'

    transaction_id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.String(20), nullable=False)
    resolved_slot_id = db.Column(
                           db.String(5),
                           db.ForeignKey("item_slot.slot_id"),
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