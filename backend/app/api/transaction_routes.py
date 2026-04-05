"""
=======================================
backend/app/api/transaction_routes.py
=======================================
Flask Blueprint for transaction processing endpoints.

Covers Task B-15 (POST /api/transactions/process) and the D-2 requirement
that ConcurrencyError (out-of-stock race condition) maps to HTTP 409 Conflict.
"""

import os

from flask import Blueprint, jsonify, request

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