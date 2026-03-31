from typing import Optional
from app.repositories.item_slot_repository import ItemSlotRepository


class AlertService:
    """
    Evaluates every slot's current state and returns only those that are
    in a warning or critical condition, with a human-readable reason.

    Alert levels come directly from ItemSlot's threshold logic:
      - critical: quantity <= low_threshold (3)  OR  days_until_expiration <= 2
      - warning:  quantity <= warning_threshold (5)  OR  days_until_expiration <= 5
    Critical takes priority — a slot is only labelled "warning" when it is NOT critical.
    """

    def __init__(self, repository: Optional[ItemSlotRepository] = None):
        self._repo = repository or ItemSlotRepository()

    def get_active_alerts(self) -> list[dict]:
        """
        Return a list of alert dicts for every slot that is in warning or critical state.
        Slots that are green (healthy) are excluded.

        Each dict contains:
            slot_id, item_name, quantity, days_until_expiration,
            alert_level ("warning" | "critical"), reason
        """
        alerts = []

        for slot in self._repo.get_all():
            if slot.is_critical():
                reason = self._build_reason(slot, level="critical")
                alerts.append({
                    "slot_id":               slot.slot_id,
                    "item_name":             slot.item_name,
                    "quantity":              slot.quantity,
                    "days_until_expiration": slot.days_until_expiration(),
                    "alert_level":           "critical",
                    "reason":                reason,
                })
            elif slot.is_warning():
                reason = self._build_reason(slot, level="warning")
                alerts.append({
                    "slot_id":               slot.slot_id,
                    "item_name":             slot.item_name,
                    "quantity":              slot.quantity,
                    "days_until_expiration": slot.days_until_expiration(),
                    "alert_level":           "warning",
                    "reason":                reason,
                })

        return alerts

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_reason(slot, level: str) -> str:
        """
        Compose a descriptive reason string based on which threshold(s) are breached.
        When both stock and expiry are problematic they are combined into one message.
        """
        days = slot.days_until_expiration()

        low_stock   = slot.quantity <= slot.low_threshold
        warn_stock  = slot.quantity <= slot.warning_threshold
        near_expiry = days <= 5
        crit_expiry = days <= 2

        reasons = []

        # Stock component
        if low_stock:
            reasons.append(f"Low stock ({slot.quantity} unit(s) remaining)")
        elif warn_stock:
            reasons.append(f"Stock nearing threshold ({slot.quantity} unit(s) remaining)")

        # Expiry component
        if crit_expiry and days < 0:
            reasons.append(f"Expired ({abs(days)} day(s) ago)")
        elif crit_expiry:
            reasons.append(f"Expires in {days} day(s)")
        elif near_expiry:
            reasons.append(f"Expires soon ({days} day(s) remaining)")

        return "; ".join(reasons) if reasons else level.capitalize()
