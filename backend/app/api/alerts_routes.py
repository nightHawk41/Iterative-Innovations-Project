from flask import Blueprint, jsonify
from app.services.alert_service import AlertService

alerts_bp = Blueprint("alerts", __name__)
_service = AlertService()


# ---------------------------------------------------------------------------
# GET /api/alerts
# ---------------------------------------------------------------------------

@alerts_bp.route("/api/alerts", methods=["GET"])
def get_alerts():
    """
    Return a JSON array of all slots currently in warning or critical state.
    Green (healthy) slots are excluded.

    Each object includes:
        slot_id, item_name, quantity, days_until_expiration,
        alert_level ("warning" | "critical"), reason

    Response: 200 OK  — always returns a list (empty when everything is healthy).
    """
    alerts = _service.get_active_alerts()
    return jsonify(alerts), 200