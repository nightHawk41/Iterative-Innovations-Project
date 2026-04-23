import React from "react";

// Lowercase keys to match backend
const BORDER_COLOR = {
  green:  "#198754",
  yellow: "#ffc107",
  red:    "#dc3545",
};

// Use the exact prop names from the backend
function SlotCard({ slot_id, item_name, quantity, price, days_until_expiry, status_color, onSelect }) {
  // SAFEGUARD: Always force it to lowercase, fallback to "red" if missing
  const safeColor = (status_color || "red").toLowerCase();
  const disabled = quantity === 0 || days_until_expiry < 0;

  function handleActivate() {
    if (!disabled) {
      onSelect?.();
    }
  }

  return (
    <div
      className={`card h-100 slot-card${disabled ? " disabled" : " clickable"}`}
      style={{ borderLeft: `4px solid ${BORDER_COLOR[safeColor] ?? BORDER_COLOR.red}` }}
      role={disabled ? undefined : "button"}
      tabIndex={disabled ? -1 : 0}
      onClick={handleActivate}
      onKeyDown={(event) => {
        if ((event.key === "Enter" || event.key === " ") && !disabled) {
          event.preventDefault();
          handleActivate();
        }
      }}
      aria-disabled={disabled}
    >
      <div className="card-body d-flex flex-column p-2 gap-1">
        <div className="d-flex justify-content-between align-items-center">
          <span className="slot-id">{slot_id}</span>
          <span className={`status-badge status-badge--${safeColor}`}>{safeColor}</span>
        </div>
        <p className="card-title fw-semibold mb-1 slot-item-name">{item_name}</p>
        <div className="slot-quantity">{quantity}</div>
        <div className="slot-meta">
          <span>${price.toFixed(2)}</span>
          <span className={days_until_expiry <= 5 ? "text-danger" : "text-muted"}>
            {days_until_expiry}d exp
          </span>
        </div>
      </div>
    </div>
  );
}

export default SlotCard;