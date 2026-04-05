import React from "react";
import StatusIndicator from "./StatusIndicator";

function SlotCard({ slot_id, item_name, quantity, price, days_until_expiration, status }) {
  return (
    <div className="card h-100 slot-card">
      <div className="card-body d-flex flex-column gap-1">
        <div className="d-flex justify-content-between align-items-start">
          <span className="slot-id text-muted small">{slot_id}</span>
          <StatusIndicator status={status} />
        </div>
        <h6 className="card-title mb-1">{item_name}</h6>
        <p className="card-text mb-0 small">Qty: <strong>{quantity}</strong></p>
        <p className="card-text mb-0 small">Price: <strong>${price.toFixed(2)}</strong></p>
        <p className="card-text small">
          Expires in: <strong>{days_until_expiration} day{days_until_expiration !== 1 ? "s" : ""}</strong>
        </p>
      </div>
    </div>
  );
}

export default SlotCard;