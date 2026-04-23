import React, { useState } from "react";
import { showToast } from "../utils/toast";

function getTodayString() {
  return new Date().toISOString().split("T")[0];
}

// Validates a single field. Returns an error string or "".
function validateField(name, value, maxQuantity) {
  switch (name) {
    case "slotId":
      return value ? "" : "Please select a slot.";

    case "quantity": {
      if (!value && value !== 0) return "Quantity is required.";
      const qty = Number(value);
      if (isNaN(qty))              return "Quantity must be a number.";
      if (!Number.isInteger(qty))  return "Quantity must be a whole number (no decimals).";
      if (qty <= 0)                return "Quantity must be greater than 0.";

      // strict frontend validation
      if (maxQuantity !== undefined && qty > maxQuantity) return `Quantity cannot exceed ${maxQuantity}.`;
      
      return "";

    }

    case "expirationDate":
      if (!value)                    return "Expiration date is required.";
      if (value <= getTodayString()) return "Expiration date must be in the future.";
      return "";

    default:
      return "";
  }
}

// Validates all fields at once. Returns an errors object.
function validateAll(slotId, quantity, expirationDate, maxQuantity) {
  return {
    slotId:         validateField("slotId",         slotId),
    quantity:       validateField("quantity",       quantity, maxQuantity),
    expirationDate: validateField("expirationDate", expirationDate),
  };
}

function RestockModal({ show, onHide, slots, onRestockSuccess }) {
  const [slotId, setSlotId]          = useState("");
  const [quantity, setQuantity]      = useState("");
  const [expirationDate, setExpDate] = useState("");
  const [errors, setErrors]          = useState({});
  const [touched, setTouched]        = useState({});
  const [apiError, setApiError]      = useState(null);
  const [submitting, setSubmitting]  = useState(false);

  // Get the max quantity for the selected slot to enforce strict validation.
  const selectedSlot = slots.find((s) => s.slot_id === slotId);
  const maxQuantity = selectedSlot ? 10 - selectedSlot.quantity : 10;

  // Mark a field as touched and validate it immediately on blur.
  function handleBlur(name, value) {
    setTouched((prev) => ({ ...prev, [name]: true }));
    setErrors((prev) => ({ ...prev, [name]: validateField(name, value, maxQuantity) }));
  }

  //Update slot change handler to instantly clear/check quantity errors based on new slot capacity
  function handleSlotChange(e) {
    const newSlotId = e.target.value;
    setSlotId(newSlotId);

    // If quantity has been touched, re-validate it against the new slot's max capacity.
    if (touched.quantity) {
      const newSelectedSlot = slots.find((s) => s.slot_id === newSlotId);
      const newMaxQuantity = newSelectedSlot ? 10 - newSelectedSlot.quantity : 10;
      setErrors((prev) => ({ ...prev, quantity: validateField("quantity", quantity, newMaxQuantity) }));
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setApiError(null);

    // Mark all fields touched so all error messages become visible.
    setTouched({ slotId: true, quantity: true, expirationDate: true });

    const allErrors = validateAll(slotId, quantity, expirationDate, maxQuantity);
    setErrors(allErrors);

    if (Object.values(allErrors).some((msg) => msg !== "")) return;

    setSubmitting(true);
    try {
      const response = await fetch("/api/restock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slot_id:         slotId,
          quantity_added:  Number(quantity),
          expiration_date: expirationDate,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        if (response.status === 409) {
          setApiError("This slot was recently modified. Please try again.");
        } else {
          setApiError(data.error ?? "Restock failed. Please try again.");
        }
      } else {
        const successSlotId = slotId;
        handleClose();
        await onRestockSuccess?.();
        showToast(`✓ Slot ${successSlotId} restocked successfully.`);
      }
    } catch (err) {
      setApiError("Network error. Is the backend running?");
    } finally {
      setSubmitting(false);
    }
  }

  function handleClose() {
    setSlotId("");
    setQuantity("");
    setExpDate("");
    setErrors({});
    setTouched({});
    setApiError(null);
    onHide();
  }

  // Only show an error if the field has been visited.
  const showError = (name) => touched[name] && errors[name];

  return (
    <div className={`modal-overlay${show ? " modal-overlay--visible" : ""}`} style={{ display: show ? "flex" : "none" }}>
      <div className="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="restock-modal-title">
        <div className="modal-header">
          <h5 className="modal-title" id="restock-modal-title">Manual Restock</h5>
          <button type="button" className="btn-close" onClick={handleClose} aria-label="Close" />
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className="modal-body">
            {/* Slot ID */}
            <div className="form-group mb-3">
              <label htmlFor="slotId" className="form-label">Slot ID</label>
              <select
                id="slotId"
                className={`form-select${showError("slotId") ? " is-invalid" : ""}`}
                value={slotId}
                onChange={handleSlotChange}
                onBlur={(e) => handleBlur("slotId", e.target.value)}
              >
                <option value="">-- Select a slot --</option>
                {slots.map((slot) => (
                  <option key={slot.slot_id} value={slot.slot_id}>
                    {slot.slot_id} — {slot.item_name} (Current: {slot.quantity}/10)
                  </option>
                ))}
              </select>
              {showError("slotId") && (
                <div className="invalid-feedback" role="alert">{errors.slotId}</div>
              )}
            </div>

            {/* Quantity */}
            <div className="form-group mb-3">
              <label htmlFor="quantity" className="form-label">Quantity Added</label>
              <input
                id="quantity"
                type="number"
                min="1"
                step="1"
                placeholder="e.g. 5"
                className={`form-control${showError("quantity") ? " is-invalid" : ""}`}
                value={quantity}
                onChange={(e) => {
                  setQuantity(e.target.value);
                  if (touched.quantity) {
                    setErrors((prev) => ({ ...prev, quantity: validateField("quantity", e.target.value, maxQuantity) }));
                  }
                }}
                onBlur={(e) => handleBlur("quantity", e.target.value)}
              />
              {showError("quantity") && (
                <div className="invalid-feedback" role="alert">{errors.quantity}</div>
              )}
            </div>

            {/* Expiration Date */}
            <div className="form-group mb-3">
              <label htmlFor="expirationDate" className="form-label">Expiration Date</label>
              <input
                id="expirationDate"
                type="date"
                min={getTodayString()}
                className={`form-control${showError("expirationDate") ? " is-invalid" : ""}`}
                value={expirationDate}
                onChange={(e) => setExpDate(e.target.value)}
                onBlur={(e) => handleBlur("expirationDate", e.target.value)}
              />
              {showError("expirationDate") && (
                <div className="invalid-feedback" role="alert">{errors.expirationDate}</div>
              )}
            </div>
          </div>

          <div className="modal-footer">
            {apiError && (
              <div className="alert alert-danger w-100 mb-2" role="alert">
                {apiError}
              </div>
            )}
            <button type="button" className="btn btn-secondary" onClick={handleClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Submitting…" : "Restock"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default RestockModal;