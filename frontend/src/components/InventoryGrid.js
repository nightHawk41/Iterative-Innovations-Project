import React, { useState, useEffect } from "react";
import { Accordion } from "react-bootstrap";
import SlotCard from "./SlotCard";

function groupByRow(slots) {
  return slots.reduce((acc, slot) => {
    const row = slot.slot_id[0].toUpperCase();
    if (!acc[row]) acc[row] = [];
    acc[row].push(slot);
    return acc;
  }, {});
}

function rowSeverityClass(rowSlots) {
  if (rowSlots.some((s) => s.status === "Red"))    return "text-danger";
  if (rowSlots.some((s) => s.status === "Yellow")) return "text-warning";
  return "text-success";
}

function InventoryGrid({ slots }) {
  // Hook must come before any early return
  const [activeKeys, setActiveKeys] = useState([]);

  const grouped   = slots && slots.length > 0 ? groupByRow(slots) : {};
  const rowLabels = Object.keys(grouped).sort();

  // Sync open panels when slots/rows change (e.g. after live fetch)
  useEffect(() => {
    setActiveKeys(rowLabels);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slots]);

  if (!slots || slots.length === 0) {
    return <p className="text-muted fst-italic">No inventory data available.</p>;
  }

  function toggleRow(key) {
    setActiveKeys((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  }

  return (
    <div className="inventory-grid">
      <div className="d-flex gap-2 mb-3">
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={() => setActiveKeys(rowLabels)}
        >
          Expand All
        </button>
        <button
          className="btn btn-sm btn-outline-secondary"
          onClick={() => setActiveKeys([])}
        >
          Collapse All
        </button>
      </div>

      <Accordion activeKey={activeKeys} alwaysOpen>
        {rowLabels.map((rowLabel) => {
          const rowSlots    = grouped[rowLabel];
          const alertCount  = rowSlots.filter(
            (s) => s.status === "Red" || s.status === "Yellow"
          ).length;
          const severityClass = rowSeverityClass(rowSlots);

          return (
            <Accordion.Item eventKey={rowLabel} key={rowLabel} className="mb-2 border rounded">
              <Accordion.Header onClick={() => toggleRow(rowLabel)}>
                <div className="d-flex align-items-center gap-3 w-100 me-3">
                  <span className="accordion-row-label">Row {rowLabel}</span>
                  <span className="text-muted small">
                    {rowSlots.length} slot{rowSlots.length !== 1 ? "s" : ""}
                  </span>
                  {alertCount > 0 ? (
                    <span className={`small fw-semibold ${severityClass}`}>
                      ⚠ {alertCount} alert{alertCount !== 1 ? "s" : ""}
                    </span>
                  ) : (
                    <span className="small text-success fw-semibold">✓ All clear</span>
                  )}
                </div>
              </Accordion.Header>
              <Accordion.Body className="pt-3">
                <div className="row row-cols-2 row-cols-sm-3 row-cols-md-4 row-cols-lg-6 g-3">
                  {rowSlots.map((slot) => (
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
              </Accordion.Body>
            </Accordion.Item>
          );
        })}
      </Accordion>
    </div>
  );
}

export default InventoryGrid;