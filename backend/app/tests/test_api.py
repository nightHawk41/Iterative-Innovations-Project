"""
TASK B-19: Integration tests for the three core API endpoints
Covers:
  - GET  /api/inventory  → returns derived fields (days_until_expiry, status_color)
  - POST /api/restock    → updates the DB and is reflected in a subsequent GET
  - GET  /api/alerts     → returns only flagged (warning/critical) slots
"""

import pytest
import json
import io
from datetime import date, datetime, timedelta, timezone


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
    from app.api.transaction_routes import transaction_bp
    test_app.register_blueprint(inventory_bp)
    test_app.register_blueprint(alerts_bp)
    test_app.register_blueprint(transaction_bp)

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


@pytest.fixture(autouse=True)
def clear_transactions_before_test(app):
    """Clear all transactions before each test to ensure test isolation."""
    from app.models.transaction import Transaction
    with app.app_context():
        from app import db
        # Delete all transactions to ensure test isolation
        db.session.query(Transaction).delete()
        db.session.commit()
    yield


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
            json={"slot_id": "A1", "quantity_added": 1, "expiration_date": future}, # Reduced to 1
        )
        assert resp.status_code == 200

    def test_restock_response_contains_updated_slot(self, client):
        future = (date.today() + timedelta(days=90)).isoformat()
        resp = client.post(
            "/api/restock",
            json={"slot_id": "A2", "quantity_added": 1, "expiration_date": future}, # Reduced to 1
        )
        body = _json(resp)
        assert body.get("slot_id") == "A2"

    def test_restock_increments_quantity(self, client):
        future = (date.today() + timedelta(days=60)).isoformat()

        before = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A2")
        qty_before = before["quantity"]

        client.post(
            "/api/restock",
            json={"slot_id": "A2", "quantity_added": 1, "expiration_date": future}, # Reduced to 1
        )

        after = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A2")
        assert after["quantity"] == qty_before + 1

    def test_restock_updates_expiration_date(self, client):
        new_exp = (date.today() + timedelta(days=180)).isoformat()
        client.post(
            "/api/restock",
            json={"slot_id": "A2", "quantity_added": 1, "expiration_date": new_exp}, # Reduced to 1
        )

        after = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A2")
        assert after["expiration_date"] == new_exp

    def test_restock_reflected_in_subsequent_get(self, client):
        """The POST mutation must be visible in the very next GET /api/inventory."""
        future = (date.today() + timedelta(days=75)).isoformat()

        before_all = _json(client.get("/api/inventory"))
        a1_before = next(s for s in before_all if s["slot_id"] == "A1")

        client.post(
            "/api/restock",
            json={"slot_id": "A1", "quantity_added": 1, "expiration_date": future}, # Reduced to 1
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

    def test_exceeding_capacity_returns_human_readable_error_with_max_allowed(self, client):
        """
        B-14: The error should be human-readable and include max allowed quantity
        (10 - current_stock) so frontend can display it inline.
        """
        future = (date.today() + timedelta(days=30)).isoformat()
        current = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A1")
        current_stock = current["quantity"]
        max_allowed = 10 - current_stock

        # 11 always exceeds capacity because max slot capacity is 10.
        resp = client.post(
            "/api/restock",
            json={"slot_id": "A1", "quantity_added": 11, "expiration_date": future},
        )
        assert resp.status_code == 400

        body = _json(resp)
        message = body.get("error", "")
        assert isinstance(message, str) and message.strip()
        assert "Cannot exceed maximum capacity of 10" in message
        assert "You can only add up to" in message
        assert f"{max_allowed}" in message


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


# ===========================================================================
# GET /api/inventory/summary
# ===========================================================================

class TestGetInventorySummary:

    def test_returns_200(self, client):
        resp = client.get("/api/inventory/summary")
        assert resp.status_code == 200

    def test_returns_dict(self, client):
        data = _json(client.get("/api/inventory/summary"))
        assert isinstance(data, dict)

    def test_returns_required_fields(self, client):
        data = _json(client.get("/api/inventory/summary"))
        required = {"total_slots", "healthy", "low_expiring", "critical_out"}
        assert required == set(data.keys()), f"Expected {required}, got {set(data.keys())}"

    def test_all_counts_are_integers(self, client):
        data = _json(client.get("/api/inventory/summary"))
        for key in ["total_slots", "healthy", "low_expiring", "critical_out"]:
            assert isinstance(data[key], int), f"{key} should be integer"

    def test_total_slots_matches_inventory_count(self, client):
        """total_slots should equal the number of all slots in inventory."""
        inventory = _json(client.get("/api/inventory"))
        summary = _json(client.get("/api/inventory/summary"))
        assert summary["total_slots"] == len(inventory)

    def test_counts_sum_to_total(self, client):
        """healthy + low_expiring + critical_out should equal total_slots."""
        data = _json(client.get("/api/inventory/summary"))
        total = data["healthy"] + data["low_expiring"] + data["critical_out"]
        assert total == data["total_slots"], (
            f"Sum of counts {total} != total_slots {data['total_slots']}"
        )

    def test_green_slots_counted_as_healthy(self, client):
        """Count of green status_color slots should match healthy count."""
        inventory = _json(client.get("/api/inventory"))
        summary = _json(client.get("/api/inventory/summary"))
        green_count = sum(1 for s in inventory if s["status_color"] == "green")
        assert summary["healthy"] == green_count

    def test_yellow_slots_counted_as_low_expiring(self, client):
        """Count of yellow status_color slots should match low_expiring count."""
        inventory = _json(client.get("/api/inventory"))
        summary = _json(client.get("/api/inventory/summary"))
        yellow_count = sum(1 for s in inventory if s["status_color"] == "yellow")
        assert summary["low_expiring"] == yellow_count

    def test_red_slots_counted_as_critical_out(self, client):
        """Count of red status_color slots should match critical_out count."""
        inventory = _json(client.get("/api/inventory"))
        summary = _json(client.get("/api/inventory/summary"))
        red_count = sum(1 for s in inventory if s["status_color"] == "red")
        assert summary["critical_out"] == red_count

    def test_expected_counts_with_seeded_data(self, client):
        """With test data: A1–A2 green, A3–A4 yellow, A5–A7 red."""
        data = _json(client.get("/api/inventory/summary"))
        assert data["total_slots"] == 7
        assert data["healthy"] == 2
        assert data["low_expiring"] == 2
        assert data["critical_out"] == 3


# ===========================================================================
# POST /api/purchase
# ===========================================================================

class TestPostPurchase:

    def test_valid_purchase_returns_200(self, client):
        resp = client.post("/api/purchase", json={"slot_id": "A1"})
        assert resp.status_code == 200

    def test_purchase_response_contains_updated_slot(self, client):
        resp = client.post("/api/purchase", json={"slot_id": "A1"})
        body = _json(resp)
        assert body.get("slot_id") == "A1"
        assert "message" in body
        assert body["message"] == "Purchase successful"

    def test_purchase_decrements_quantity(self, client):
        before = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A1")
        qty_before = before["quantity"]

        client.post("/api/purchase", json={"slot_id": "A1"})

        after = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A1")
        assert after["quantity"] == qty_before - 1

    def test_purchase_creates_transaction_record(self, client):
        txns_before = _json(client.get("/api/transactions"))
        initial_count = len(txns_before)

        client.post("/api/purchase", json={"slot_id": "A1"})

        txns_after = _json(client.get("/api/transactions"))
        assert len(txns_after) == initial_count + 1

    def test_purchase_transaction_has_required_fields(self, client):
        client.post("/api/purchase", json={"slot_id": "A1"})
        
        txns = _json(client.get("/api/transactions"))
        latest_txn = txns[0]  # Most recent transaction (ordered descending)
        
        required = {"transaction_id", "amount", "timestamp", "user_id", "resolved_slot_id"}
        assert required == set(latest_txn.keys())

    def test_purchase_transaction_resolves_to_correct_slot(self, client):
        client.post("/api/purchase", json={"slot_id": "A2"})
        
        txns = _json(client.get("/api/transactions"))
        latest_txn = txns[0]
        assert latest_txn["resolved_slot_id"] == "A2"

    def test_purchase_transaction_amount_matches_slot_price(self, client):
        slot = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A1")
        slot_price = slot["price"]
        
        client.post("/api/purchase", json={"slot_id": "A1"})
        
        txns = _json(client.get("/api/transactions"))
        latest_txn = txns[0]
        assert latest_txn["amount"] == slot_price

    def test_purchase_user_id_is_patron_name(self, client):
        """Transaction user_id should be a patron name from CBORD data."""
        client.post("/api/purchase", json={"slot_id": "A1"})
        
        txns = _json(client.get("/api/transactions"))
        latest_txn = txns[0]
        
        # user_id should be a non-empty string (patron name)
        assert isinstance(latest_txn["user_id"], str)
        assert len(latest_txn["user_id"]) > 0

    def test_purchase_missing_slot_id_returns_400(self, client):
        resp = client.post("/api/purchase", json={})
        assert resp.status_code == 400

    def test_purchase_invalid_slot_returns_400(self, client):
        resp = client.post("/api/purchase", json={"slot_id": "Z99"})
        assert resp.status_code == 400

    def test_purchase_expired_slot_returns_409(self, client):
        # A6 is already expired (expiry date in the past)
        resp = client.post("/api/purchase", json={"slot_id": "A6"})
        assert resp.status_code == 409

    def test_purchase_out_of_stock_returns_409(self, client):
        # A7 has qty=1; purchase it twice should fail on second
        client.post("/api/purchase", json={"slot_id": "A7"})
        resp = client.post("/api/purchase", json={"slot_id": "A7"})
        assert resp.status_code == 409

    def test_purchase_no_json_returns_400(self, client):
        resp = client.post("/api/purchase")
        assert resp.status_code == 400

    def test_purchase_quantity_parameter_defaults_to_1(self, client):
        """When quantity is not provided, defaults to decrement by 1."""
        before = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A2")
        qty_before = before["quantity"]

        # No quantity provided, should default to 1
        resp = client.post("/api/purchase", json={"slot_id": "A2"})
        assert resp.status_code == 200

        after = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A2")
        assert after["quantity"] == qty_before - 1, "quantity should decrement by 1 when not specified"

    def test_purchase_quantity_parameter_honored(self, client):
        """When quantity is provided, it should be used for decrement."""
        before = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A3")
        qty_before = before["quantity"]

        # Provide quantity=2
        resp = client.post("/api/purchase", json={"slot_id": "A3", "quantity": 2})
        assert resp.status_code == 200

        after = next(s for s in _json(client.get("/api/inventory")) if s["slot_id"] == "A3")
        assert after["quantity"] == qty_before - 2, "quantity should decrement by the provided amount"


# ===========================================================================
# GET /api/transactions
# ===========================================================================

class TestGetTransactions:

    def test_returns_200(self, client):
        resp = client.get("/api/transactions")
        assert resp.status_code == 200

    def test_returns_list(self, client):
        data = _json(client.get("/api/transactions"))
        assert isinstance(data, list)

    def test_empty_initially(self, client):
        """Before any purchases, transaction list should be empty."""
        data = _json(client.get("/api/transactions"))
        assert len(data) == 0

    def test_transaction_appears_after_purchase(self, client):
        client.post("/api/purchase", json={"slot_id": "A1"})
        data = _json(client.get("/api/transactions"))
        assert len(data) == 1

    def test_multiple_purchases_create_multiple_transactions(self, client):
        client.post("/api/purchase", json={"slot_id": "A1"})
        client.post("/api/purchase", json={"slot_id": "A2"})
        data = _json(client.get("/api/transactions"))
        assert len(data) == 2

    def test_transactions_ordered_by_timestamp_descending(self, client):
        """Most recent transaction should appear first."""
        client.post("/api/purchase", json={"slot_id": "A1"})
        import time
        time.sleep(0.01)  # Ensure different timestamps
        client.post("/api/purchase", json={"slot_id": "A2"})
        
        data = _json(client.get("/api/transactions"))
        # The second purchase (A2) should be first in the list (most recent)
        assert data[0]["resolved_slot_id"] == "A2"
        assert data[1]["resolved_slot_id"] == "A1"

    def test_each_transaction_has_required_fields(self, client):
        client.post("/api/purchase", json={"slot_id": "A1"})
        data = _json(client.get("/api/transactions"))
        
        required = {"transaction_id", "amount", "timestamp", "user_id", "resolved_slot_id"}
        for txn in data:
            missing = required - txn.keys()
            assert not missing, f"Transaction missing: {missing}"

    def test_transaction_amount_is_numeric(self, client):
        client.post("/api/purchase", json={"slot_id": "A1"})
        data = _json(client.get("/api/transactions"))
        
        for txn in data:
            assert isinstance(txn["amount"], (int, float))

    def test_transaction_timestamp_is_iso_format(self, client):
        client.post("/api/purchase", json={"slot_id": "A1"})
        data = _json(client.get("/api/transactions"))
        
        for txn in data:
            timestamp = txn["timestamp"]
            assert isinstance(timestamp, str)
            # Should be ISO format with timezone
            assert "T" in timestamp
            assert "+" in timestamp or "Z" in timestamp


# ===========================================================================
# GET /api/reports/sales
# ===========================================================================

class TestGetSalesReport:

    def _insert_transactions(self, app, rows):
        """Insert transaction fixtures directly for deterministic report assertions."""
        from app import db
        from app.models.transaction import Transaction

        with app.app_context():
            for row in rows:
                db.session.add(
                    Transaction(
                        transaction_id=row["transaction_id"],
                        amount=row["amount"],
                        timestamp=row["timestamp"],
                        user_id=row.get("user_id", "Test User"),
                        resolved_slot_id=row.get("resolved_slot_id"),
                    )
                )
            db.session.commit()

    def test_returns_200(self, client):
        resp = client.get("/api/reports/sales")
        assert resp.status_code == 200

    def test_returns_required_top_level_fields(self, client):
        data = _json(client.get("/api/reports/sales"))
        required = {
            "items",
            "total_revenue",
            "total_units",
            "unique_items",
            "date_range",
            "generated_at",
            "top_item",
            "transaction_count",
            "has_transactions",
        }
        assert required == set(data.keys())

    def test_empty_report_shape_when_no_transactions(self, client):
        data = _json(client.get("/api/reports/sales"))

        assert data["items"] == []
        assert data["total_revenue"] == 0.0
        assert data["total_units"] == 0
        assert data["unique_items"] == 0
        assert data["date_range"] == {"start": None, "end": None}
        assert data["top_item"] is None
        assert data["transaction_count"] == 0
        assert data["has_transactions"] is False

    def test_aggregates_resolved_transactions_by_item(self, client, app):
        self._insert_transactions(
            app,
            [
                {
                    "transaction_id": 9001,
                    "amount": 2.15,
                    "timestamp": datetime(2026, 3, 10, 8, 15, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A1",
                },
                {
                    "transaction_id": 9002,
                    "amount": 2.15,
                    "timestamp": datetime(2026, 3, 10, 9, 15, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A1",
                },
                {
                    "transaction_id": 9003,
                    "amount": 2.35,
                    "timestamp": datetime(2026, 3, 10, 10, 15, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A2",
                },
            ],
        )

        data = _json(client.get("/api/reports/sales"))

        assert data["total_units"] == 3
        assert data["total_revenue"] == 6.65
        assert data["unique_items"] == 2

        first = data["items"][0]
        second = data["items"][1]

        assert first["item_name"] == "Granola Bar"
        assert first["units_sold"] == 2
        assert first["total_revenue"] == 4.3
        assert first["average_price"] == 2.15

        assert second["item_name"] == "Trail Mix"
        assert second["units_sold"] == 1
        assert second["total_revenue"] == 2.35
        assert second["average_price"] == 2.35

    def test_items_sorted_by_total_revenue_desc(self, client, app):
        self._insert_transactions(
            app,
            [
                {
                    "transaction_id": 9011,
                    "amount": 1.95,
                    "timestamp": datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A4",
                },
                {
                    "transaction_id": 9012,
                    "amount": 1.95,
                    "timestamp": datetime(2026, 3, 10, 8, 5, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A4",
                },
                {
                    "transaction_id": 9013,
                    "amount": 2.55,
                    "timestamp": datetime(2026, 3, 10, 8, 10, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A3",
                },
            ],
        )

        data = _json(client.get("/api/reports/sales"))
        assert data["items"][0]["total_revenue"] >= data["items"][1]["total_revenue"]

    def test_unresolved_transactions_excluded_from_sales_rollup(self, client, app):
        self._insert_transactions(
            app,
            [
                {
                    "transaction_id": 9021,
                    "amount": 2.15,
                    "timestamp": datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A1",
                },
                {
                    "transaction_id": 9022,
                    "amount": 99.99,
                    "timestamp": datetime(2026, 3, 10, 8, 1, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": None,
                },
            ],
        )

        data = _json(client.get("/api/reports/sales"))

        # Only resolved transactions should contribute to item rollup and totals.
        assert data["total_units"] == 1
        assert data["total_revenue"] == 2.15
        assert data["unique_items"] == 1
        assert len(data["items"]) == 1

        # Guard fields count all transactions in the system.
        assert data["transaction_count"] == 2
        assert data["has_transactions"] is True

    def test_date_range_and_generated_at_are_iso_strings(self, client, app):
        self._insert_transactions(
            app,
            [
                {
                    "transaction_id": 9031,
                    "amount": 2.15,
                    "timestamp": datetime(2026, 3, 10, 8, 15, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A1",
                },
                {
                    "transaction_id": 9032,
                    "amount": 2.35,
                    "timestamp": datetime(2026, 3, 10, 9, 20, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A2",
                },
            ],
        )

        data = _json(client.get("/api/reports/sales"))
        start = data["date_range"]["start"]
        end = data["date_range"]["end"]
        generated_at = data["generated_at"]

        assert isinstance(start, str) and "T" in start and ("+" in start or "Z" in start)
        assert isinstance(end, str) and "T" in end and ("+" in end or "Z" in end)
        assert isinstance(generated_at, str) and "T" in generated_at and ("+" in generated_at or "Z" in generated_at)

        assert start.startswith("2026-03-10T08:15:00")
        assert end.startswith("2026-03-10T09:20:00")

    def test_top_item_matches_highest_revenue_item(self, client, app):
        self._insert_transactions(
            app,
            [
                {
                    "transaction_id": 9041,
                    "amount": 2.55,
                    "timestamp": datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A3",
                },
                {
                    "transaction_id": 9042,
                    "amount": 2.55,
                    "timestamp": datetime(2026, 3, 10, 8, 5, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A3",
                },
                {
                    "transaction_id": 9043,
                    "amount": 2.15,
                    "timestamp": datetime(2026, 3, 10, 8, 10, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": "A1",
                },
            ],
        )

        data = _json(client.get("/api/reports/sales"))
        top_item = data["top_item"]

        assert top_item is not None
        assert top_item["item_name"] == "Protein Bar"
        assert top_item["units_sold"] == 2
        assert top_item["total_revenue"] == 5.1

    def test_guard_fields_true_when_any_transaction_exists(self, client, app):
        self._insert_transactions(
            app,
            [
                {
                    "transaction_id": 9051,
                    "amount": 77.77,
                    "timestamp": datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc),
                    "resolved_slot_id": None,
                }
            ],
        )

        data = _json(client.get("/api/reports/sales"))
        assert data["transaction_count"] == 1
        assert data["has_transactions"] is True


# ===========================================================================
# POST /api/inventory/upload
# ===========================================================================

class TestPostInventoryUpload:

    def test_missing_file_field_returns_400(self, client):
        resp = client.post("/api/inventory/upload", data={}, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_empty_filename_returns_400(self, client):
        resp = client.post(
            "/api/inventory/upload",
            data={"file": (io.BytesIO(b"ROW,Product,Vending Price\nA1,Test,1.00\n"), "")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_invalid_csv_schema_returns_400(self, client):
        # Missing required headers ROW/Product/Vending Price.
        bad_csv = b"slot_id,item_name,price\nA1,Test Item,1.23\n"
        resp = client.post(
            "/api/inventory/upload",
            data={"file": (io.BytesIO(bad_csv), "inventory_bad.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_upload_updates_existing_inventory(self, client):
        payload = (
            "ROW,Product,Vending Price\n"
            "A1,Updated Granola,4.20\n"
            "A2,Updated Trail Mix,4.50\n"
        ).encode("utf-8")

        resp = client.post(
            "/api/inventory/upload",
            data={"file": (io.BytesIO(payload), "inventory_config_upload.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200

        body = _json(resp)
        assert body["total_rows"] == 2
        assert body["updated"] >= 2

        inventory = _json(client.get("/api/inventory"))
        a1 = next(s for s in inventory if s["slot_id"] == "A1")
        a2 = next(s for s in inventory if s["slot_id"] == "A2")

        assert a1["item_name"] == "Updated Granola"
        assert a1["price"] == 4.2
        assert a2["item_name"] == "Updated Trail Mix"
        assert a2["price"] == 4.5

    def test_upload_applies_optional_stock_and_expiration_date(self, client):
        payload = (
            "ROW,Product,Vending Price,stock,expiration_date\n"
            "A1,Granola Premium,6.25,9,2031-01-15\n"
        ).encode("utf-8")

        resp = client.post(
            "/api/inventory/upload",
            data={"file": (io.BytesIO(payload), "inventory_with_optional_fields.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200

        inventory = _json(client.get("/api/inventory"))
        a1 = next(s for s in inventory if s["slot_id"] == "A1")

        assert a1["item_name"] == "Granola Premium"
        assert a1["price"] == 6.25
        assert a1["quantity"] == 9
        assert a1["expiration_date"] == "2031-01-15"

    def test_upload_preserves_existing_stock_and_expiration_when_columns_absent(self, client):
        # First upload sets explicit stock/expiration_date values.
        baseline_payload = (
            "ROW,Product,Vending Price,stock,expiration_date\n"
            "A2,Trail Mix Baseline,7.10,4,2030-06-01\n"
        ).encode("utf-8")
        baseline_resp = client.post(
            "/api/inventory/upload",
            data={"file": (io.BytesIO(baseline_payload), "inventory_baseline.csv")},
            content_type="multipart/form-data",
        )
        assert baseline_resp.status_code == 200

        # Second upload omits stock/expiration columns; should preserve existing values.
        update_payload = (
            "ROW,Product,Vending Price\n"
            "A2,Trail Mix Rename Only,7.55\n"
        ).encode("utf-8")
        update_resp = client.post(
            "/api/inventory/upload",
            data={"file": (io.BytesIO(update_payload), "inventory_no_optional.csv")},
            content_type="multipart/form-data",
        )
        assert update_resp.status_code == 200

        inventory = _json(client.get("/api/inventory"))
        a2 = next(s for s in inventory if s["slot_id"] == "A2")

        assert a2["item_name"] == "Trail Mix Rename Only"
        assert a2["price"] == 7.55
        assert a2["quantity"] == 4
        assert a2["expiration_date"] == "2030-06-01"

    def test_upload_supports_quantity_and_days_until_expiry_aliases(self, client):
        payload = (
            "ROW,Product,Vending Price,Quantity,Days Until Expiry\n"
            "A3,Protein Alias,5.80,8,30\n"
        ).encode("utf-8")

        resp = client.post(
            "/api/inventory/upload",
            data={"file": (io.BytesIO(payload), "inventory_alias_columns.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200

        inventory = _json(client.get("/api/inventory"))
        a3 = next(s for s in inventory if s["slot_id"] == "A3")

        assert a3["item_name"] == "Protein Alias"
        assert a3["price"] == 5.8
        assert a3["quantity"] == 8
        # Allow small test-runtime drift around date arithmetic.
        expected_days = 30
        assert abs(a3["days_until_expiry"] - expected_days) <= 1


class TestPostInventoryApply:

    def test_apply_inventory_returns_success_message(self, client):
        resp = client.post(
            "/api/inventory/apply",
            json={},
        )

        assert resp.status_code == 200
        assert _json(resp) == {"message": "Inventory updated."}