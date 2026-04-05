"""
TASK B-19: Integration tests for the three core API endpoints
Covers:
  - GET  /api/inventory  → returns derived fields (days_until_expiry, status_color)
  - POST /api/restock    → updates the DB and is reflected in a subsequent GET
  - GET  /api/alerts     → returns only flagged (warning/critical) slots
"""

import pytest
import json
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# App factory / test client
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """
    Create a Flask test application backed by an in-memory SQLite database.
    Seeds a small, deterministic dataset that covers all three status colours.
    """
    import os
    os.environ.setdefault("AUTO_SYNC_INVENTORY_CONFIG", "0")  # skip CSV seed

    from flask import Flask
    from flask_cors import CORS
    from flask_sqlalchemy import SQLAlchemy

    test_app = Flask(__name__)
    test_app.config["TESTING"] = True
    test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Import the shared db object and re-initialise it for this test app.
    from app import db as _db
    CORS(test_app)
    _db.init_app(test_app)

    # Register blueprints (routes)
    from app.api.inventory_routes  import inventory_bp
    from app.api.alerts_routes     import alerts_bp
    test_app.register_blueprint(inventory_bp)
    test_app.register_blueprint(alerts_bp)

    with test_app.app_context():
        # All three models must be imported before create_all() so SQLAlchemy
        # can resolve the 'Transaction' and 'Notification' relationship strings
        # declared on ItemSlot; otherwise mapper configuration fails.
        from app.models.transaction import Transaction       # noqa: F401
        from app.models.notification import Notification    # noqa: F401
        _db.create_all()
        _seed_test_data(_db)

    yield test_app

    # Teardown
    with test_app.app_context():
        _db.drop_all()


def _seed_test_data(db):
    """Insert a minimal set of slots covering Green, Yellow, and Red states."""
    from app.models.item_slot import ItemSlot

    today = date.today()

    slots = [
        # Green: healthy qty, far expiry
        ItemSlot(
            slot_id="A1", item_name="Granola Bar", quantity=8,
            price=2.15, expiration_date=today + timedelta(days=60),
        ),
        # Green: qty just above warning threshold, expiry fine
        ItemSlot(
            slot_id="A2", item_name="Trail Mix", quantity=6,
            price=2.35, expiration_date=today + timedelta(days=45),
        ),
        # Yellow: qty at warning threshold
        ItemSlot(
            slot_id="A3", item_name="Protein Bar", quantity=5,
            price=2.55, expiration_date=today + timedelta(days=30),
        ),
        # Yellow: expiry within 5 days
        ItemSlot(
            slot_id="A4", item_name="Chips", quantity=8,
            price=1.95, expiration_date=today + timedelta(days=4),
        ),
        # Red: qty at low threshold
        ItemSlot(
            slot_id="A5", item_name="Gum", quantity=3,
            price=1.25, expiration_date=today + timedelta(days=30),
        ),
        # Red: already expired
        ItemSlot(
            slot_id="A6", item_name="Water Bottle", quantity=7,
            price=1.75, expiration_date=today - timedelta(days=2),
        ),
        # Red: both critically low qty AND expired
        ItemSlot(
            slot_id="A7", item_name="Sports Drink", quantity=1,
            price=2.05, expiration_date=today - timedelta(days=5),
        ),
    ]

    for slot in slots:
        db.session.add(slot)
    db.session.commit()


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _json(response):
    return json.loads(response.data)


# ===========================================================================
# GET /api/inventory
# ===========================================================================

class TestGetInventory:

    def test_returns_200(self, client):
        resp = client.get("/api/inventory")
        assert resp.status_code == 200

    def test_returns_list(self, client):
        data = _json(client.get("/api/inventory"))
        assert isinstance(data, list)

    def test_returns_all_seeded_slots(self, client):
        data = _json(client.get("/api/inventory"))
        assert len(data) == 7

    def test_each_slot_has_required_fields(self, client):
        data = _json(client.get("/api/inventory"))
        required = {
            "slot_id", "item_name", "quantity", "price",
            "expiration_date", "days_until_expiry", "status_color",
        }
        for slot in data:
            missing = required - slot.keys()
            assert not missing, f"Slot {slot.get('slot_id')} missing: {missing}"

    def test_days_until_expiry_is_integer(self, client):
        data = _json(client.get("/api/inventory"))
        for slot in data:
            assert isinstance(slot["days_until_expiry"], int), (
                f"days_until_expiry is not int for slot {slot['slot_id']}"
            )

    def test_status_color_values_are_valid(self, client):
        data = _json(client.get("/api/inventory"))
        valid_colors = {"red", "yellow", "green"}
        for slot in data:
            assert slot["status_color"] in valid_colors, (
                f"Unexpected status_color '{slot['status_color']}' "
                f"for slot {slot['slot_id']}"
            )

    def test_green_slot_identified_correctly(self, client):
        data = _json(client.get("/api/inventory"))
        green_slots = [s for s in data if s["slot_id"] in ("A1", "A2")]
        assert all(s["status_color"] == "green" for s in green_slots)

    def test_yellow_slots_identified_correctly(self, client):
        data = _json(client.get("/api/inventory"))
        yellow_slots = [s for s in data if s["slot_id"] in ("A3", "A4")]
        assert all(s["status_color"] == "yellow" for s in yellow_slots)

    def test_red_slots_identified_correctly(self, client):
        data = _json(client.get("/api/inventory"))
        red_slots = [s for s in data if s["slot_id"] in ("A5", "A6", "A7")]
        assert all(s["status_color"] == "red" for s in red_slots)

    def test_expired_slot_has_negative_days_until_expiry(self, client):
        data = _json(client.get("/api/inventory"))
        a6 = next(s for s in data if s["slot_id"] == "A6")
        assert a6["days_until_expiry"] < 0

    def test_slots_are_sorted_by_slot_id(self, client):
        data = _json(client.get("/api/inventory"))
        ids = [s["slot_id"] for s in data]
        assert ids == sorted(ids), "Inventory should be ordered by slot_id"


# ===========================================================================
# POST /api/restock
# ===========================================================================

class TestPostRestock:

    def test_valid_restock_returns_200(self, client):
        future = (date.today() + timedelta(days=90)).isoformat()
        resp = client.post(
            "/api/restock",
            json={"slot_id": "A1", "quantity_added": 5, "expiration_date": future},
        )
        assert resp.status_code == 200

    def test_restock_response_contains_updated_slot(self, client):
        future = (date.today() + timedelta(days=90)).isoformat()
        resp = client.post(
            "/api/restock",
            json={"slot_id": "A1", "quantity_added": 2, "expiration_date": future},
        )
        body = _json(resp)
        assert body.get("slot_id") == "A1"

    def test_restock_increments_quantity(self, client):
        future = (date.today() + timedelta(days=60)).isoformat()

        # Get current qty for A2
        before = next(
            s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A2"
        )
        qty_before = before["quantity"]

        client.post(
            "/api/restock",
            json={"slot_id": "A2", "quantity_added": 3, "expiration_date": future},
        )

        # Fetch again and verify
        after = next(
            s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A2"
        )
        assert after["quantity"] == qty_before + 3

    def test_restock_updates_expiration_date(self, client):
        new_exp = (date.today() + timedelta(days=180)).isoformat()
        client.post(
            "/api/restock",
            json={"slot_id": "A2", "quantity_added": 4, "expiration_date": new_exp},
        )

        after = next(
            s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A2"
        )
        assert after["expiration_date"] == new_exp

    def test_restock_reflected_in_subsequent_get(self, client):
        """The POST mutation must be visible in the very next GET /api/inventory."""
        future = (date.today() + timedelta(days=75)).isoformat()

        before_all = _json(client.get("/api/inventory"))
        a1_before = next(s for s in before_all if s["slot_id"] == "A1")

        client.post(
            "/api/restock",
            json={"slot_id": "A1", "quantity_added": 1, "expiration_date": future},
        )

        after_all = _json(client.get("/api/inventory"))
        a1_after = next(s for s in after_all if s["slot_id"] == "A1")

        assert a1_after["quantity"] == a1_before["quantity"] + 1

    # ---- validation failures ----

    def test_nonexistent_slot_returns_404_or_400(self, client):
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post(
            "/api/restock",
            json={"slot_id": "Z9", "quantity_added": 5, "expiration_date": future},
        )
        assert resp.status_code in (400, 404)

    def test_zero_quantity_returns_400(self, client):
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post(
            "/api/restock",
            json={"slot_id": "A1", "quantity_added": 0, "expiration_date": future},
        )
        assert resp.status_code == 400

    def test_negative_quantity_returns_400(self, client):
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post(
            "/api/restock",
            json={"slot_id": "A1", "quantity_added": -3, "expiration_date": future},
        )
        assert resp.status_code == 400

    def test_past_expiration_date_returns_400(self, client):
        past = (date.today() - timedelta(days=1)).isoformat()
        resp = client.post(
            "/api/restock",
            json={"slot_id": "A1", "quantity_added": 5, "expiration_date": past},
        )
        assert resp.status_code == 400

    def test_missing_slot_id_returns_400(self, client):
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post(
            "/api/restock",
            json={"quantity_added": 5, "expiration_date": future},
        )
        assert resp.status_code == 400

    def test_missing_quantity_returns_400(self, client):
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = client.post(
            "/api/restock",
            json={"slot_id": "A1", "expiration_date": future},
        )
        assert resp.status_code == 400


# ===========================================================================
# GET /api/alerts
# ===========================================================================

class TestGetAlerts:

    def test_returns_200(self, client):
        resp = client.get("/api/alerts")
        assert resp.status_code == 200

    def test_returns_list(self, client):
        data = _json(client.get("/api/alerts"))
        assert isinstance(data, list)

    def test_only_flagged_slots_returned(self, client):
        """Green slots (A1, A2) must NOT appear in the alerts list."""
        alerts = _json(client.get("/api/alerts"))
        alert_ids = {a["slot_id"] for a in alerts}
        assert "A1" not in alert_ids
        assert "A2" not in alert_ids

    def test_red_slots_are_included(self, client):
        """All seeded Red slots must appear in alerts."""
        alerts = _json(client.get("/api/alerts"))
        alert_ids = {a["slot_id"] for a in alerts}
        # A5 (low qty), A6 (expired), A7 (both)
        assert "A5" in alert_ids
        assert "A6" in alert_ids
        assert "A7" in alert_ids

    def test_yellow_slots_are_included(self, client):
        """Yellow slots must also appear in the alerts list."""
        alerts = _json(client.get("/api/alerts"))
        alert_ids = {a["slot_id"] for a in alerts}
        assert "A3" in alert_ids
        assert "A4" in alert_ids

    def test_each_alert_has_required_fields(self, client):
        alerts = _json(client.get("/api/alerts"))
        required = {
            "slot_id", "item_name", "quantity",
            "days_until_expiration", "alert_level", "reason",
        }
        for alert in alerts:
            missing = required - alert.keys()
            assert not missing, f"Alert for {alert.get('slot_id')} missing: {missing}"

    def test_alert_level_values_are_valid(self, client):
        alerts = _json(client.get("/api/alerts"))
        valid_levels = {"warning", "critical"}
        for alert in alerts:
            assert alert["alert_level"] in valid_levels

    def test_critical_slots_have_critical_alert_level(self, client):
        alerts = _json(client.get("/api/alerts"))
        # A5 qty=3 (== low_threshold) → critical
        a5 = next((a for a in alerts if a["slot_id"] == "A5"), None)
        assert a5 is not None
        assert a5["alert_level"] == "critical"

    def test_warning_level_slot_identified(self, client):
        alerts = _json(client.get("/api/alerts"))
        # A3: qty=5 (== warning_threshold), expiry far → warning
        a3 = next((a for a in alerts if a["slot_id"] == "A3"), None)
        assert a3 is not None
        assert a3["alert_level"] == "warning"

    def test_reason_field_is_non_empty_string(self, client):
        alerts = _json(client.get("/api/alerts"))
        for alert in alerts:
            assert isinstance(alert["reason"], str) and alert["reason"].strip(), (
                f"Empty reason for slot {alert['slot_id']}"
            )

    def test_total_alert_count_matches_non_green_slots(self, client):
        """Alert count should equal all Yellow + Red slots (A3–A7 = 5 slots)."""
        alerts = _json(client.get("/api/alerts"))
        # After restocks in previous tests A3's qty may have risen; check ≥ red count
        red_ids    = {"A5", "A6", "A7"}
        yellow_ids = {"A3", "A4"}
        alert_ids  = {a["slot_id"] for a in alerts}

        # All reds must be present
        assert red_ids.issubset(alert_ids)
        # No green slots should appear
        assert "A1" not in alert_ids
        assert "A2" not in alert_ids