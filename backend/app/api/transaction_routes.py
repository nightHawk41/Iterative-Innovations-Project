import os
import tempfile

from flask import Blueprint, jsonify, request
from app.api import error_response
from app.services.transaction_processor import TransactionProcessor, DEFAULT_MOCK_PATH

transaction_bp = Blueprint("transactions", __name__)
_processor = TransactionProcessor()


# ---------------------------------------------------------------------------
# POST /api/transactions/process
# ---------------------------------------------------------------------------

@transaction_bp.route("/api/transactions/process", methods=["POST"])
def process_transactions():
    """
    Ingest and process CBORD-format transaction data.

    Accepts one of three input modes (checked in order):

    1. CSV file upload  (multipart/form-data, field name: "file")
       curl -X POST /api/transactions/process -F "file=@transaction_stream_mock.csv"

    2. JSON rows list  (application/json, body: { "rows": [...] })
       Useful for testing — pass raw row dicts that match the CSV column names.

    3. No body / empty body  — runs against the default mock file on disk.
       Useful for a one-click demo trigger from the admin dashboard.

    Response: 200 OK
    {
        "processed_count":    <int>,
        "updated_slots":      [ {...}, ... ],
        "unresolved_amounts": [ <float>, ... ]
    }

    Error: 400  { "error": "<message>", "status": 400 }
    """

    # ------------------------------------------------------------------
    # Mode 1: CSV file upload
    # ------------------------------------------------------------------
    if "file" in request.files:
        uploaded = request.files["file"]

        if not uploaded.filename:
            return error_response("Uploaded file has no filename.", 400)

        if not uploaded.filename.lower().endswith(".csv"):
            return error_response("Uploaded file must be a .csv file.", 400)

        # Write to a temp file so parse_csv() can use its filepath-based API.
        tmp_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".csv", delete=False
            ) as tmp:
                tmp_path = tmp.name
                uploaded.save(tmp)

            rows = _processor.parse_csv(tmp_path)
        except (FileNotFoundError, ValueError) as exc:
            return error_response(str(exc), 400)
        finally:
            # Always clean up the temp file.
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        summary = _processor.process_transactions(rows)
        return jsonify(summary), 200

    # ------------------------------------------------------------------
    # Mode 2: JSON rows list
    # ------------------------------------------------------------------
    body = request.get_json(silent=True)
    if body is not None:
        rows = body.get("rows")
        if not isinstance(rows, list):
            return error_response(
                "JSON body must contain a 'rows' key with a list of transaction dicts.",
                400,
            )

        if len(rows) == 0:
            return error_response("'rows' list must not be empty.", 400)

        try:
            summary = _processor.process_transactions(rows)
        except Exception as exc:
            return error_response(f"Processing failed: {exc}", 400)

        return jsonify(summary), 200

    # ------------------------------------------------------------------
    # Mode 3: No body — run against the default mock file
    # ------------------------------------------------------------------
    if not os.path.exists(DEFAULT_MOCK_PATH):
        return error_response(
            "No input provided and the default mock file was not found at: "
            f"{DEFAULT_MOCK_PATH}",
            400,
        )

    try:
        summary = _processor.run_from_default_mock()
    except (FileNotFoundError, ValueError) as exc:
        return error_response(str(exc), 400)

    return jsonify(summary), 200