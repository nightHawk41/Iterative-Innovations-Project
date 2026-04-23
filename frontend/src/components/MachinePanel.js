import React from 'react';
import SlotTile from './SlotTile';

function MachinePanel({ slots, onPurchaseSuccess }) {
  return (
    <section className="machine-panel">
      <div className="machine-panel-header">UMBC Vending Machine</div>
      <div className="machine-grid">
        {slots.map((slot) => (
          <SlotTile
            key={slot.slot_id}
            slot={slot}
            onPurchaseSuccess={onPurchaseSuccess}
          />
        ))}
      </div>
    </section>
  );
}

export default MachinePanel;
