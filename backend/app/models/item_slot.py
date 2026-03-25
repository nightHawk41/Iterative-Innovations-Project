from datetime import date
from app import db

class ItemSlot(db.Model):
    __tablename__ = 'item_slots'

    slot_id = db.Column(db.String(5), primary_key=True)
    item_name = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False, unique=True)
    expiration_date = db.Column(db.Date, nullable=False)
    low_threshold = db.Column(db.Integer, nullable=False, default=3)
    warning_threshold = db.Column(db.Integer, nullable=False, default=5)

    # --- relationships ---
    transactions = db.relationship('Transaction', backref='slot', lazy=True)
    notifications = db.relationship('Notification', backref='slot', lazy=True)

    # ------------------
    # Derived helpers
    # ------------------

    def days_until_expiration(self) -> int:
        """Return days remaining until expiration. Negative means already expired."""
        return (self.expiration_date - date.today()).days
    
    def is_critical(self) -> bool:
        """True if quantity is at or below low_threshold OR expiry is within 2 days."""
        return self.quantity <= self.low_threshold or self.days_until_expiration() <= 2
    
    def is_warning(self) -> bool:
        """True if quantity is at or below warning_threshold OR expiry is within 5 days."""
        return self.quantity <= self.warning_threshold or self.days_until_expiration() <= 5
    
    def status_color(self) -> str:
        """Return 'red' for critical, 'yellow' for warning, else 'green'."""
        if self.is_critical():
            return 'red'
        if self.is_warning():
            return 'yellow'
        return 'green'

    # ------------------
    # Mutating methods
    # ------------------
    def decrement_stock(self, count: int = 1) -> None:
        """Decrements quantity by count. 
        Rasises ValueError if result would drop below zero."""
        if self.quantity - count < 0:
            raise ValueError(f"Cannot decrement slot {self.slot_id} by {count}."
                             f"Only {self.quantity} left units remain."
                             )
        self.quantity -= count

    def restock(self, amount: int, new_expiration_date: date) -> None:
        """
        Adds amount to quantity and updates the expiration date.
        Raises ValueError if amount is not a positive integer.
        """
        if amount <= 0:
            raise ValueError("Restock amount must be a positive integer.")
        self.quantity += amount
        self.expiration_date = new_expiration_date

    # ---------------
    # Serialization
    # ---------------
    def to_dict(self) -> dict:
        """Serializes all fields including derived days_until_expiration and status_color."""
        return {
            "slot_id": self.slot_id,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "price": self.price,
            "expiration_date": self.expiration_date.isoformat(),
            "low_threshold": self.low_threshold,
            "warning_threshold": self.warning_threshold,
            "days_until_expiry": self.days_until_expiration(),
            "status_color": self.status_color(),
        }

    def __repr__(self) -> str:
        return f"<ItemSlot {self.slot_id} | {self.item_name} | qty={self.quantity} | {self.status_color()}>"
