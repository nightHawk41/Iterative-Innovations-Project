from flask import Blueprint, jsonify, request
from app.api import error_response
from app.services.inventory_service import InventoryService
 
inventory_bp = Blueprint("inventory", __name__)
_service = InventoryService()


# ---------------------------------------------------------------------------
# GET /api/inventory
# ---------------------------------------------------------------------------

@inventory_bp.route("/api/inventory", methods=["GET"])
def get_inventory():
    """
    Return a JSON array of all vending slots.
 
    Each object includes:
        slot_id, item_name, quantity, price, expiration_date,
        days_until_expiry, status_color
 
    Response: 200 OK  — always returns a list (empty if no slots seeded).
    """
    slots = _service.get_inventory()
    return jsonify(slots), 200

# ---------------------------------------------------------------------------
# POST /api/restock
# ---------------------------------------------------------------------------
 
@inventory_bp.route("/api/restock", methods=["POST"])
def restock_slot():
    """
    Restock a single slot with additional quantity and a new expiration date.
 
    Expected JSON body:
        {
            "slot_id":        "<string>",   e.g. "A1"
            "quantity_added": <int>,        must be > 0
            "expiration_date": "<string>"   must be a future date, format YYYY-MM-DD
        }
 
    Success  → 200  { ...updated slot dict..., "message": "Restock successful" }
    Failure  → 400  { "error": "<descriptive message>", "status": 400 }
    """
    body = request.get_json(silent=True)
 
    # -----------------------------------------------------------------------
    # 1. Validate that a JSON body was provided and required fields are present
    # -----------------------------------------------------------------------
    if not body:
        return error_response("Request body must be valid JSON.", 400)
 
    missing = [f for f in ("slot_id", "quantity_added", "expiration_date") if f not in body]
    if missing:
        return error_response(f"Missing required field(s): {', '.join(missing)}.", 400)
 
    slot_id        = body["slot_id"]
    quantity_added = body["quantity_added"]
    expiration_date = body["expiration_date"]
 
    # -----------------------------------------------------------------------
    # 2. Basic type validation before handing off to the service layer
    # -----------------------------------------------------------------------
    if not isinstance(slot_id, str) or not slot_id.strip():
        return error_response("slot_id must be a non-empty string.", 400)
 
    if not isinstance(quantity_added, int) or isinstance(quantity_added, bool):
        return error_response("quantity_added must be an integer.", 400)
 
    if quantity_added <= 0:
        return error_response("quantity_added must be greater than 0.", 400)
 
    if not isinstance(expiration_date, str) or not expiration_date.strip():
        return error_response("expiration_date must be a non-empty string in YYYY-MM-DD format.", 400)
 
    # -----------------------------------------------------------------------
    # 3. Delegate to InventoryService — it performs remaining domain validation
    #    (slot existence, date in the future, stock constraints)
    # -----------------------------------------------------------------------
    try:
        updated_slot = _service.restock_slot(
            slot_id=slot_id.strip(),
            quantity_added=quantity_added,
            expiration_date=expiration_date.strip(),
        )
    except LookupError as exc:
        return error_response(str(exc), 400)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"Unexpected error: {exc}", 400)
 
    # -----------------------------------------------------------------------
    # 4. Return updated slot data alongside a success message
    # -----------------------------------------------------------------------
    return jsonify({**updated_slot, "message": "Restock successful"}), 200