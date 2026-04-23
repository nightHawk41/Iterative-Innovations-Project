"""
=====================================
backend/app/api/inventory_routes.py
=====================================
Flask Blueprint for inventory-related endpoints.

Covers Tasks B-12 (GET /api/inventory), B-13 (POST /api/restock),
B-1 (POST /api/purchase), and the D-2 requirement that ConcurrencyError
maps to HTTP 409 Conflict.
"""

import os
import tempfile

from flask import Blueprint, jsonify, request

from app.services.inventory_service import ConcurrencyError, InventoryService
from app.utils.seed import seed_database

inventory_bp = Blueprint("inventory", __name__)
_service = InventoryService()


# ---------------------------------------------------------------------------
# GET /api/inventory
# ---------------------------------------------------------------------------

@inventory_bp.route("/api/inventory", methods=["GET"])
def get_inventory():
    """
    Returns a JSON array of all vending slots.

    Each object includes:
        slot_id, item_name, quantity, price, expiration_date,
        days_until_expiry, status_color
    """
    try:
        slots = _service.get_inventory()
        return jsonify(slots), 200
    except Exception as exc:
        return jsonify({"error": str(exc), "status": 500}), 500


# ---------------------------------------------------------------------------
# GET /api/inventory/summary
# ---------------------------------------------------------------------------

@inventory_bp.route("/api/inventory/summary", methods=["GET"])
def get_inventory_summary():
    """
    Returns a summary of inventory counts by status.

    Response (200):
        {
            "total_slots": 24,
            "healthy": 20,
            "low_expiring": 3,
            "critical_out": 1
        }

    The counts are based on slot status_color:
        - healthy: green slots (not low and not expiring soon)
        - low_expiring: yellow slots (low stock or expiring soon)
        - critical_out: red slots (critically low stock or expired)
    """
    try:
        slots = _service.get_inventory()
        
        total_slots = len(slots)
        healthy = sum(1 for slot in slots if slot.get("status_color") == "green")
        low_expiring = sum(1 for slot in slots if slot.get("status_color") == "yellow")
        critical_out = sum(1 for slot in slots if slot.get("status_color") == "red")
        
        return jsonify({
            "total_slots": total_slots,
            "healthy": healthy,
            "low_expiring": low_expiring,
            "critical_out": critical_out,
        }), 200
    except Exception as exc:
        return jsonify({"error": str(exc), "status": 500}), 500


# ---------------------------------------------------------------------------
# POST /api/inventory/upload
# ---------------------------------------------------------------------------

@inventory_bp.route("/api/inventory/upload", methods=["POST"])
def upload_inventory_csv():
    """
    Accepts a multipart CSV upload and updates inventory records from its rows.

    Expected columns:
      - ROW
      - Product
      - Vending Price

    Optional columns are handled in seed utilities (B-13).

    Success (200):
      {"added": int, "updated": int, "skipped": int, "total_rows": int, "config_path": str}

    Failure responses:
      400 — missing file, invalid csv schema/content, or seed error
      500 — unexpected server error
    """
    if "file" not in request.files:
        return jsonify({"error": "Missing required file field: file.", "status": 400}), 400

    uploaded = request.files["file"]
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "Uploaded file has no filename.", "status": 400}), 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="wb") as tmp:
            uploaded.save(tmp)
            tmp_path = tmp.name

        summary = seed_database(config_path=tmp_path, update_existing=True)
        if summary.get("error"):
            return jsonify({"error": summary["error"], "status": 400}), 400

        return jsonify(summary), 200

    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc), "status": 400}), 400

    except Exception as exc:
        return jsonify({"error": str(exc), "status": 500}), 500

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@inventory_bp.route("/api/inventory/apply", methods=["POST"])
def apply_inventory_upload():
    return jsonify({"message": "Inventory updated."}), 200


# ---------------------------------------------------------------------------
# POST /api/restock
# ---------------------------------------------------------------------------

@inventory_bp.route("/api/restock", methods=["POST"])
def restock_slot():
    """
    Restock a slot.

    Request body (JSON):
        {
            "slot_id":        "A3",
            "quantity_added": 5,
            "expiration_date": "2026-12-01"
        }

    Success (200):
        Updated slot dict  +  { "message": "Restock successful" }

    Failure responses:
        400 — validation error (bad quantity, past date, unknown slot)
        409 — ConcurrencyError (D-2): slot was concurrently modified
        500 — unexpected server error
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON.", "status": 400}), 400

    slot_id         = body.get("slot_id")
    quantity_added  = body.get("quantity_added")
    expiration_date = body.get("expiration_date")

    # --- Basic presence validation ----------------------------------------
    missing = [f for f, v in [
        ("slot_id", slot_id),
        ("quantity_added", quantity_added),
        ("expiration_date", expiration_date),
    ] if v is None]

    if missing:
        return jsonify({
            "error": f"Missing required field(s): {', '.join(missing)}",
            "status": 400,
        }), 400

    # --- Delegate to service (D-2 safeguard lives there) ------------------
    try:
        updated_slot = _service.restock_slot(slot_id, quantity_added, expiration_date)
        return jsonify({**updated_slot, "message": "Restock successful"}), 200

    except LookupError as exc:
        return jsonify({"error": str(exc), "status": 400}), 400

    except ValueError as exc:
        return jsonify({"error": str(exc), "status": 400}), 400

    # D-2: optimistic concurrency guard
    except ConcurrencyError as exc:
        return jsonify({"error": str(exc), "status": 409}), 409

    except Exception as exc:
        return jsonify({"error": str(exc), "status": 500}), 500
    

# ---------------------------------------------------------------------------
# POST /api/purchase
# ---------------------------------------------------------------------------

@inventory_bp.route("/api/purchase", methods=["POST"])
def purchase_slot():
    """
    Purchase one or more units from a slot.

    Request body (JSON):
        { "slot_id": "A1", "quantity": 1 }

    Success (200):
        Updated slot dict  +  { "message": "Purchase successful" }

    Failure responses:
        400 — missing/invalid fields, or unknown slot_id
        409 — ConcurrencyError (D-2): out-of-stock, expired, or race condition
        500 — unexpected server error
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON.", "status": 400}), 400

    slot_id  = body.get("slot_id")
    quantity = body.get("quantity", 1)

    if not slot_id:
        return jsonify({"error": "Missing required field: slot_id.", "status": 400}), 400
    
    if not isinstance(quantity, int) or isinstance(quantity, bool):
        return jsonify({"error": "quantity must be an integer.", "status": 400}), 400

    try:
        updated_slot = _service.purchase_slot(slot_id, quantity)
        return jsonify({**updated_slot, "message": "Purchase successful"}), 200

    except LookupError as exc:
        return jsonify({"error": str(exc), "status": 400}), 400

    except ValueError as exc:
        return jsonify({"error": str(exc), "status": 400}), 400

    # D-2: optimistic concurrency guard — out-of-stock, expired, or race
    except ConcurrencyError as exc:
        return jsonify({"error": str(exc), "status": 409}), 409

    except Exception as exc:
        return jsonify({"error": str(exc), "status": 500}), 500