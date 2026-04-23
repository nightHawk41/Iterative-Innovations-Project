"""
=======================================
backend/app/api/transaction_routes.py
=======================================
Flask Blueprint for transaction processing endpoints.

Covers Task B-15 (POST /api/transactions/process) and the D-2 requirement
that ConcurrencyError (out-of-stock race condition) maps to HTTP 409 Conflict.
"""

import os
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


# ---------------------------------------------------------------------------
# POST /api/transactions/process
# ---------------------------------------------------------------------------

@transaction_bp.route("/api/transactions/process", methods=["POST"])
def process_transactions():
    """
    Accept either:
        (a) a CSV file upload  (multipart/form-data, field name = "file"), or
        (b) a JSON body        ({ "rows": [ ... ] })

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

            import tempfile
            with tempfile.NamedTemporaryFile(
                suffix=".csv", delete=False, mode="wb"
            ) as tmp:
                uploaded.save(tmp)
                tmp_path = tmp.name

            try:
                rows    = _processor.parse_csv(tmp_path)
                summary = _processor.process_transactions(rows)
            finally:
                os.unlink(tmp_path)

            return jsonify(summary), 200

        # ------------------------------------------------------------------ #
        # (b) JSON rows list                                                  #
        # ------------------------------------------------------------------ #
        body = request.get_json(silent=True)
        if body and "rows" in body:
            rows    = body["rows"]
            summary = _processor.process_transactions(rows)
            return jsonify(summary), 200

        # ------------------------------------------------------------------ #
        # (c) Default mock CSV                                                #
        # ------------------------------------------------------------------ #
        rows    = _processor.parse_csv(DEFAULT_MOCK)
        summary = _processor.process_transactions(rows)
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
    """
    Returns aggregated sales metrics from resolved transactions.

    Includes B-11 availability guard fields:
        - transaction_count (all transactions)
        - has_transactions  (transaction_count > 0)

    Response (200):
        {
            "items": [
                {
                    "item_name": "Chips",
                    "units_sold": 12,
                    "total_revenue": 18.0,
                    "average_price": 1.5
                }
            ],
            "total_revenue": 18.0,
            "total_units": 12,
            "unique_items": 1,
            "date_range": {
                "start": "2026-04-23T09:00:00+00:00",
                "end": "2026-04-23T12:00:00+00:00"
            },
            "generated_at": "2026-04-23T12:01:00+00:00",
            "top_item": {
                "item_name": "Chips",
                "units_sold": 12,
                "total_revenue": 18.0,
                "average_price": 1.5
            },
            "transaction_count": 15,
            "has_transactions": true
        }
    """
    try:
        from app.models.item_slot import ItemSlot
        from app.models.transaction import Transaction

        # B-11: availability guard for frontend button state.
        transaction_count = db.session.query(func.count(Transaction.transaction_id)).scalar() or 0

        # Only resolved rows contribute to sales rollups.
        rows = (
            db.session.query(
                ItemSlot.item_name.label("item_name"),
                func.count(Transaction.transaction_id).label("units_sold"),
                func.sum(Transaction.amount).label("total_revenue"),
                func.avg(Transaction.amount).label("average_price"),
            )
            .join(ItemSlot, Transaction.resolved_slot_id == ItemSlot.slot_id)
            .filter(Transaction.resolved_slot_id.isnot(None))
            .group_by(ItemSlot.item_name)
            .order_by(func.sum(Transaction.amount).desc(), ItemSlot.item_name.asc())
            .all()
        )

        items = []
        for row in rows:
            items.append(
                {
                    "item_name": row.item_name,
                    "units_sold": int(row.units_sold or 0),
                    "total_revenue": round(float(row.total_revenue or 0.0), 2),
                    "average_price": round(float(row.average_price or 0.0), 2),
                }
            )

        totals = (
            db.session.query(
                func.count(Transaction.transaction_id).label("total_units"),
                func.sum(Transaction.amount).label("total_revenue"),
                func.min(Transaction.timestamp).label("start_ts"),
                func.max(Transaction.timestamp).label("end_ts"),
            )
            .filter(Transaction.resolved_slot_id.isnot(None))
            .one()
        )

        total_units = int(totals.total_units or 0)
        total_revenue = round(float(totals.total_revenue or 0.0), 2)

        start_ts = totals.start_ts
        end_ts = totals.end_ts
        if start_ts and start_ts.tzinfo is None:
            start_ts = start_ts.replace(tzinfo=timezone.utc)
        if end_ts and end_ts.tzinfo is None:
            end_ts = end_ts.replace(tzinfo=timezone.utc)

        date_range = {
            "start": start_ts.isoformat() if start_ts else None,
            "end": end_ts.isoformat() if end_ts else None,
        }

        generated_at = datetime.now(timezone.utc).isoformat()
        top_item = items[0] if items else None

        return jsonify(
            {
                "items": items,
                "total_revenue": total_revenue,
                "total_units": total_units,
                "unique_items": len(items),
                "date_range": date_range,
                "generated_at": generated_at,
                "top_item": top_item,
                "transaction_count": int(transaction_count),
                "has_transactions": bool(transaction_count > 0),
            }
        ), 200

    except Exception as exc:
        return jsonify({"error": str(exc), "status": 500}), 500