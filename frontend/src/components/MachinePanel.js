import React from 'react';
import SlotTile from './SlotTile';

function MachinePanel({ slots, onPurchaseSuccess, adminMode }) {
  const hasSlots = Array.isArray(slots) && slots.length > 0;

  return (
    <section className="machine-panel">
      <div className="machine-panel-header">UMBC Vending Machine</div>
      <div className="machine-grid">
        {hasSlots ? (
          slots.map((slot) => (
            <SlotTile
              key={slot.slot_id}
              slot={slot}
              onPurchaseSuccess={onPurchaseSuccess}
              adminMode={adminMode}
            />
          ))
        ) : (
          <div className="machine-grid-empty">
            Upload inventory to view the vending machine grid.
          </div>
        )}
      </div>
    </section>
  );
}

export default MachinePanel;
