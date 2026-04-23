import React, { useState } from 'react';
import { showToast } from '../utils/toast';

function PurchaseModal({ slot, onClose, onSuccess }) {
  const [submitting, setSubmitting] = useState(false);

  if (!slot) {
    return null;
  }

  async function handleConfirm() {
    setSubmitting(true);
    try {
      const res = await fetch('/api/purchase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot_id: slot.slot_id }),
      });

      if (res.ok) {
        showToast(`✓ ${slot.item_name} dispensed!`);
        await onSuccess?.();
      } else if (res.status === 409) {
        showToast('This item is out of stock.');
        onClose?.();
      } else {
        showToast('This item is unavailable.');
        onClose?.();
      }
    } catch {
      showToast('Network error. Is the backend running?');
      onClose?.();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Confirm Purchase</h3>
        <p>Purchase {slot.item_name} (Slot {slot.slot_id}) for ${slot.price.toFixed(2)}?</p>
        <div className="btn-row">
          <button className="btn primary" onClick={handleConfirm} disabled={submitting}>
            {submitting ? 'Processing…' : 'Confirm'}
          </button>
          <button className="btn" onClick={onClose} disabled={submitting}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default PurchaseModal;