from datetime import datetime, timezone
from app import db

VALID_ALERT_LEVELS = {"warning", "critical"}

class Notification(db.Model):
    __tablename__ = "notification"

    notification_id = db.Column(
        db.Integer, 
        primary_key=True, 
        autoincrement=True
        )
    
    slot_id = db.Column(
        db.String(5), 
        db.ForeignKey("item_slot.slot_id"), 
        nullable=False
        )
    
    message = db.Column(
        db.String(100), 
        nullable=False
        )
    
    alert_level = db.Column(
        db.String(10), 
        nullable=False
        )   # "warning" | "critical"
    
    date_triggered = db.Column(
        db.DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc)
        )

    def __init__(self, slot_id: str, message: str, alert_level: str, date_triggered=None):
        if alert_level not in VALID_ALERT_LEVELS:
            raise ValueError(f"alert_level must be one of {VALID_ALERT_LEVELS}, got '{alert_level}'.")
        self.slot_id = slot_id
        self.message = message
        self.alert_level = alert_level
        self.date_triggered = date_triggered or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "notification_id": self.notification_id,
            "slot_id": self.slot_id,
            "message": self.message,
            "alert_level": self.alert_level,
            "date_triggered": self.date_triggered.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Notification [{self.alert_level.upper()}] slot={self.slot_id} | {self.message}>"