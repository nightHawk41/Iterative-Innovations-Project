"""
=======================================
backend/app/api/transaction_routes.py
=======================================
Flask Blueprint for transaction processing endpoints.

Covers Task B-15 (POST /api/transactions/process) and the D-2 requirement
that ConcurrencyError (out-of-stock race condition) maps to HTTP 409 Conflict.
"""

import os
from collections import defaultdict
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app import db
from app.services.inventory_service  import ConcurrencyError
from app.services.transaction_processor import TransactionProcessor

transaction_bp = Blueprint("transactions", __name__)
_processor     = TransactionProcessor()

# Default mock path — used when no file is uploaded and no JSON is provided.
DEFAULT_MOCK = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "transaction_stream_mock.csv")
)


def _empty_sales_report(cycle=None):
    return {
        "cycle_id": cycle.cycle_id if cycle else None,
        "items": [],
        "total_revenue": 0.0,
        "total_units": 0,
        "unique_items": 0,
        "date_range": {"start": None, "end": None},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_item": None,
        "unresolved_count": 0,
        "transaction_count": 0,
        "has_transactions": False,
    }


def _coerce_bool(value, default: bool = False) -> bool:
    """Parse common bool-like values from query/form/json payloads."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _build_sales_report_for_cycle(cycle):
    from app.models.item_slot import ItemSlot
    from app.models.transaction import Transaction

    if not cycle:
        return _empty_sales_report(None)

    transaction_count = db.session.query(func.count(Transaction.transaction_id)).filter(
        Transaction.cycle_id == cycle.cycle_id
    ).scalar() or 0

    if transaction_count == 0:
        empty = _empty_sales_report(cycle)
        empty["transaction_count"] = 0
        return empty

    price_map = {}
    for slot in db.session.query(ItemSlot).all():
        price_key = round(float(slot.price), 2)
        price_map[price_key] = {
            "slot_id": slot.slot_id,
            "item_name": slot.item_name,
        }

    grouped = defaultdict(lambda: {"units_sold": 0, "total_revenue": 0.0})
    transactions = db.session.query(Transaction).filter(
        Transaction.cycle_id == cycle.cycle_id
    ).order_by(Transaction.timestamp.asc()).all()

    for transaction in transactions:
        price_key = round(float(transaction.amount), 2)
        match = price_map.get(price_key)

        if match:
            slot_id = match["slot_id"]
            item_name = match["item_name"]
        else:
            slot_id = "Unknown"
            item_name = f"Unresolved (${price_key:.2f})"

        key = (slot_id, item_name)
        grouped[key]["units_sold"] += 1
        grouped[key]["total_revenue"] += float(transaction.amount)

    items = []
    for (slot_id, item_name), aggregate in grouped.items():
        units_sold = int(aggregate["units_sold"])
        total_item_revenue = round(float(aggregate["total_revenue"]), 2)
        avg_price = round(total_item_revenue / units_sold, 2) if units_sold else 0.0
        items.append(
            {
                "slot_id": slot_id,
                "item_name": item_name,
                "units_sold": units_sold,
                "total_revenue": total_item_revenue,
                "avg_price": avg_price,
                "average_price": avg_price,
            }
        )

    items.sort(key=lambda x: (-x["total_revenue"], x["item_name"]))
    for idx, item in enumerate(items, start=1):
        item["rank"] = idx

    unresolved_count = sum(1 for item in items if item["slot_id"] == "Unknown")
    total_units = len(transactions)
    total_revenue = round(sum(float(tx.amount) for tx in transactions), 2)

    start_ts = transactions[0].timestamp if transactions else None
    end_ts = transactions[-1].timestamp if transactions else None
    if start_ts and start_ts.tzinfo is None:
        start_ts = start_ts.replace(tzinfo=timezone.utc)
    if end_ts and end_ts.tzinfo is None:
        end_ts = end_ts.replace(tzinfo=timezone.utc)

    date_range = {
        "start": start_ts.isoformat() if start_ts else None,
        "end": end_ts.isoformat() if end_ts else None,
    }

    generated_at = datetime.now(timezone.utc).isoformat()
    top_item = None
    ranked_resolved_items = [item for item in items if item["slot_id"] != "Unknown"]
    if ranked_resolved_items:
        lead = ranked_resolved_items[0]
        top_item = {
            "slot_id": lead["slot_id"],
            "item_name": lead["item_name"],
            "units": lead["units_sold"],
            "revenue": lead["total_revenue"],
            "units_sold": lead["units_sold"],
            "total_revenue": lead["total_revenue"],
            "avg_price": lead["avg_price"],
            "average_price": lead["average_price"],
        }

    return {
        "cycle_id": cycle.cycle_id,
        "items": items,
        "total_revenue": total_revenue,
        "total_units": total_units,
        "unique_items": len(items),
        "date_range": date_range,
        "generated_at": generated_at,
        "top_item": top_item,
        "unresolved_count": unresolved_count,
        "transaction_count": int(transaction_count),
        "has_transactions": bool(transaction_count > 0),
    }


def _sales_cycle_history_item(cycle):
    report = _build_sales_report_for_cycle(cycle)
    return {
        "cycle_id": report["cycle_id"],
        "started_at": cycle.started_at.isoformat() if cycle.started_at else None,
        "ended_at": cycle.ended_at.isoformat() if cycle.ended_at else None,
        "is_active": cycle.is_active,
        "transaction_count": report["transaction_count"],
        "total_units": report["total_units"],
        "total_revenue": report["total_revenue"],
        "unique_items": report["unique_items"],
        "unresolved_count": report["unresolved_count"],
        "top_item": report["top_item"],
    }


# ---------------------------------------------------------------------------
# POST /api/transactions/process
# ---------------------------------------------------------------------------

@transaction_bp.route("/api/transactions/process", methods=["POST"])
def process_transactions():
    """
    Accept either:
        (a) a CSV file upload  (multipart/form-data, field name = "file"), or
        (b) a JSON body        ({ "rows": [ ... ] })

    Optional mode switch:
        simulate_time=true will replay timestamps in chronological order and
        advance a simulated inventory clock across date boundaries.

    If neither is provided the default mock CSV is used.

    Returns the processing summary:
        {
            "processed_count":    <int>,
            "updated_slots":      [ ... ],
            "unresolved_amounts": [ ... ]
        }

    HTTP status codes:
        200 — processed (even if some rows were unresolved)
        409 — ConcurrencyError (D-2): a sale hit an out-of-stock slot
        400 — bad input
        500 — unexpected server error
    """
    try:
        # ------------------------------------------------------------------ #
        # (a) CSV file upload                                                 #
        # ------------------------------------------------------------------ #
        if "file" in request.files:
            uploaded = request.files["file"]
            if not uploaded.filename:
                return jsonify({"error": "Uploaded file has no filename.", "status": 400}), 400

            simulate_time = _coerce_bool(request.form.get("simulate_time"), default=False)

            import tempfile
            with tempfile.NamedTemporaryFile(
                suffix=".csv", delete=False, mode="wb"
            ) as tmp:
                uploaded.save(tmp)
                tmp_path = tmp.name

            try:
                rows    = _processor.parse_csv(tmp_path)
                summary = _processor.process_transactions(rows, simulate_time=simulate_time)
            finally:
                os.unlink(tmp_path)

            return jsonify(summary), 200

        # ------------------------------------------------------------------ #
        # (b) JSON rows list                                                  #
        # ------------------------------------------------------------------ #
        body = request.get_json(silent=True)
        if body and "rows" in body:
            rows    = body["rows"]
            simulate_time = _coerce_bool(body.get("simulate_time"), default=False)
            summary = _processor.process_transactions(rows, simulate_time=simulate_time)
            return jsonify(summary), 200

        # ------------------------------------------------------------------ #
        # (c) Default mock CSV                                                #
        # ------------------------------------------------------------------ #
        rows    = _processor.parse_csv(DEFAULT_MOCK)
        summary = _processor.process_transactions(rows, simulate_time=False)
        return jsonify(summary), 200

    # D-2: optimistic concurrency guard — out-of-stock race
    except ConcurrencyError as exc:
        return jsonify({"error": str(exc), "status": 409}), 409

    except (FileNotFoundError, ValueError) as exc:
        return jsonify({"error": str(exc), "status": 400}), 400

    except Exception as exc:
        return jsonify({"error": str(exc), "status": 500}), 500


# ---------------------------------------------------------------------------
# GET /api/transactions
# ---------------------------------------------------------------------------

@transaction_bp.route("/api/transactions", methods=["GET"])
def get_transactions():
    """
    Returns all Transaction rows ordered by timestamp descending.

    Each transaction includes:
        transaction_id, amount, timestamp, user_id, resolved_slot_id

    Response (200):
        [
            {
                "transaction_id": 1001,
                "amount": 2.50,
                "timestamp": "2026-04-23T10:30:00+00:00",
                "user_id": "Jane Doe",
                "resolved_slot_id": "A1"
            },
            ...
        ]
    """
    try:
        from app.models.transaction import Transaction
        
        # Fetch all transactions ordered by timestamp descending
        transactions = Transaction.query.order_by(
            Transaction.timestamp.desc()
        ).all()
        
        # Serialize to dict list
        result = [txn.to_dict() for txn in transactions]
        return jsonify(result), 200
        
    except Exception as exc:
        return jsonify({"error": str(exc), "status": 500}), 500


# ---------------------------------------------------------------------------
# GET /api/reports/sales
# ---------------------------------------------------------------------------

@transaction_bp.route("/api/reports/sales", methods=["GET"])
def get_sales_report():
    try:
        from app.models.sales_cycle import SalesCycle

        cycle_id = request.args.get("cycle_id", type=int)
        if cycle_id is not None:
            cycle = db.session.get(SalesCycle, cycle_id)
            if not cycle:
                return jsonify({"error": f"Sales cycle {cycle_id} was not found.", "status": 404}), 404
        else:
            cycle = db.session.query(SalesCycle).filter_by(is_active=True).first()

        return jsonify(_build_sales_report_for_cycle(cycle)), 200

    except Exception as exc:
        return jsonify({"error": str(exc), "status": 500}), 500


# ---------------------------------------------------------------------------
# GET /api/reports/sales/history
# ---------------------------------------------------------------------------

@transaction_bp.route("/api/reports/sales/history", methods=["GET"])
def get_sales_report_history():
    try:
        from app.models.sales_cycle import SalesCycle

        cycles = db.session.query(SalesCycle).order_by(SalesCycle.started_at.desc()).all()
        return jsonify({
            "cycles": [_sales_cycle_history_item(cycle) for cycle in cycles],
        }), 200

    except Exception as exc:
        return jsonify({"error": str(exc), "status": 500}), 500