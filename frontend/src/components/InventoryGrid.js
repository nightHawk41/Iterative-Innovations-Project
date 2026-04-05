import React from "react";
import SlotCard from "./SlotCard";

// Groups a flat array of slots into { A: [...], B: [...], ... }
function groupByRow(slots) {
  return slots.reduce((acc, slot) => {
    const row = slot.slot_id[0].toUpperCase();
    if (!acc[row]) acc[row] = [];
    acc[row].push(slot);
    return acc;
  }, {});
}

function InventoryGrid({ slots }) {
  if (!slots || slots.length === 0) {
    return <p className="text-muted">No inventory data available.</p>;
  }

  const grouped = groupByRow(slots);
  const rowLabels = Object.keys(grouped).sort();

  return (
    <div className="inventory-grid">
      {rowLabels.map((rowLabel) => (
        <div key={rowLabel} className="mb-4">
          <h6 className="row-label text-secondary fw-semibold mb-2">Row {rowLabel}</h6>
          <div className="row row-cols-2 row-cols-sm-3 row-cols-md-4 row-cols-lg-6 g-3">
            {grouped[rowLabel].map((slot) => (
              <div className="col" key={slot.slot_id}>
                <SlotCard
                  slot_id={slot.slot_id}
                  item_name={slot.item_name}
                  quantity={slot.quantity}
                  price={slot.price}
                  days_until_expiration={slot.days_until_expiration}
                  status={slot.status}
                />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default InventoryGrid;