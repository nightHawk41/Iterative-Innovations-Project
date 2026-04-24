import React, { useState } from 'react';
import PurchaseModal from './PurchaseModal';

export function getColorClass(quantity, days) {
  if (days <= 0 || quantity === 0) return 'disabled';
  if (quantity <= 2 || days <= 2) return 'red';
  if (quantity <= 5 || days <= 5) return 'yellow';
  return 'green';
}

function SlotTile({ slot, onPurchaseSuccess, adminMode = false }) {
  const [showModal, setShowModal] = useState(false);

  const colorClass = getColorClass(slot.quantity, slot.days_until_expiry);
  const isDisabled = colorClass === 'disabled';
  const isExpired = slot.days_until_expiry <= 0;

  return (
    <>
      <div
        className={`slot-tile ${colorClass}`}
        onClick={isDisabled || adminMode ? undefined : () => setShowModal(true)}
        style={{ cursor: isDisabled || adminMode ? 'not-allowed' : 'pointer' }}
        role={isDisabled || adminMode ? undefined : 'button'}
        tabIndex={isDisabled || adminMode ? -1 : 0}
      >
        <div className="slot-id">{slot.slot_id}</div>
        <div className="slot-name">{slot.item_name}</div>
        <div className="slot-price">${Number(slot.price).toFixed(2)}</div>
        <div className="slot-stock">Stock: {slot.quantity}</div>
        <div className="slot-exp">
          {isExpired ? '⚠ Expired' : `Exp: ${slot.days_until_expiry}d`}
        </div>
      </div>

      {showModal && (
        <PurchaseModal
          slot={slot}
          onClose={() => setShowModal(false)}
          onSuccess={async () => {
            setShowModal(false);
            await onPurchaseSuccess?.();
          }}
        />
      )}
    </>
  );
}

export default SlotTile;
