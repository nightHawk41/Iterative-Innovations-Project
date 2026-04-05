import React from "react";
import StatusIndicator from "./StatusIndicator";

const BORDER_COLOR = {
  Green:  "#198754",
  Yellow: "#ffc107",
  Red:    "#dc3545",
};

function SlotCard({ slot_id, item_name, quantity, price, days_until_expiration, status }) {
  return (
    <div
      className="card h-100 slot-card"
      style={{ borderLeft: `4px solid ${BORDER_COLOR[status] ?? BORDER_COLOR.Red}` }}
    >
      <div className="card-body d-flex flex-column p-2 gap-1">
        <div className="d-flex justify-content-between align-items-center">
          <span className="slot-id">{slot_id}</span>
          <StatusIndicator status={status} />
        </div>
        <p className="card-title fw-semibold mb-1 slot-item-name">{item_name}</p>
        <div className="slot-quantity">{quantity}</div>
        <div className="slot-meta">
          <span>${price.toFixed(2)}</span>
          <span className={days_until_expiration <= 5 ? "text-danger" : "text-muted"}>
            {days_until_expiration}d exp
          </span>
        </div>
      </div>
    </div>
  );
}

export default SlotCard;