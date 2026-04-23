import React, { useMemo, useState } from 'react';
import { showToast } from '../utils/toast';

function validateForm({ slotId, quantityAdded, expirationDate, maxQuantity }) {
  const errors = {
    slotId: '',
    quantityAdded: '',
    expirationDate: '',
  };

  if (!slotId) {
    errors.slotId = 'Please select a slot.';
  }

  if (quantityAdded === '') {
    errors.quantityAdded = 'Quantity is required.';
  } else {
    const qty = Number(quantityAdded);
    if (!Number.isInteger(qty)) {
      errors.quantityAdded = 'Quantity must be a whole number.';
    } else if (qty < 1) {
      errors.quantityAdded = 'Quantity must be at least 1.';
    } else if (qty > maxQuantity) {
      errors.quantityAdded = `Quantity cannot exceed ${maxQuantity}.`;
    }
  }

  if (!expirationDate) {
    errors.expirationDate = 'Expiration date is required.';
  }

  return errors;
}

function RestockForm({ slots, onSuccess }) {
  const [slotId, setSlotId] = useState('');
  const [quantityAdded, setQuantityAdded] = useState('');
  const [expirationDate, setExpirationDate] = useState('');
  const [errors, setErrors] = useState({
    slotId: '',
    quantityAdded: '',
    expirationDate: '',
  });
  const [apiError, setApiError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const selectedSlot = useMemo(
    () => slots.find((slot) => slot.slot_id === slotId) || null,
    [slots, slotId]
  );
  const maxQuantity = selectedSlot ? 10 - Number(selectedSlot.quantity ?? 0) : 10;

  async function handleSubmit(event) {
    event.preventDefault();
    setApiError('');

    const nextErrors = validateForm({ slotId, quantityAdded, expirationDate, maxQuantity });
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) {
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch('/api/restock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slot_id: slotId,
          quantity_added: Number(quantityAdded),
          expiration_date: expirationDate,
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        if (response.status === 409) {
          setApiError('This slot was recently modified. Please try again.');
        } else {
          setApiError(data.error || 'Restock failed. Please try again.');
        }
        return;
      }

      const successItemName = selectedSlot?.item_name || slotId;
      setSlotId('');
      setQuantityAdded('');
      setExpirationDate('');
      setErrors({ slotId: '', quantityAdded: '', expirationDate: '' });
      setApiError('');
      await onSuccess?.();
      showToast(`✓ ${successItemName} restocked (+${Number(quantityAdded)})`);
    } catch {
      setApiError('Network error. Is the backend running?');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="form-row">
        <label htmlFor="restock-slot-id">Slot ID</label>
        <select
          id="restock-slot-id"
          value={slotId}
          onChange={(event) => setSlotId(event.target.value)}
          disabled={submitting}
        >
          <option value="">-- Select a slot --</option>
          {slots.map((slot) => (
            <option key={slot.slot_id} value={slot.slot_id}>
              {slot.slot_id} — {slot.item_name} (Current: {slot.quantity}/10)
            </option>
          ))}
        </select>
      </div>
      <div className="field-error" style={{ display: errors.slotId ? 'block' : 'none' }}>
        {errors.slotId}
      </div>

      <div className="form-row">
        <label htmlFor="restock-quantity">Qty Added</label>
        <input
          id="restock-quantity"
          type="number"
          min="1"
          step="1"
          value={quantityAdded}
          onChange={(event) => setQuantityAdded(event.target.value)}
          disabled={submitting}
        />
      </div>
      <div className="field-error" style={{ display: errors.quantityAdded ? 'block' : 'none' }}>
        {errors.quantityAdded}
      </div>

      <div className="form-row">
        <label htmlFor="restock-exp-date">Exp Date</label>
        <input
          id="restock-exp-date"
          type="date"
          value={expirationDate}
          onChange={(event) => setExpirationDate(event.target.value)}
          disabled={submitting}
        />
      </div>
      <div className="field-error" style={{ display: errors.expirationDate ? 'block' : 'none' }}>
        {errors.expirationDate}
      </div>

      <div className="field-error" style={{ display: apiError ? 'block' : 'none' }}>
        {apiError}
      </div>

      <div className="btn-row">
        <button type="submit" className="btn primary" disabled={submitting}>
          {submitting ? 'Submitting…' : 'Restock'}
        </button>
      </div>
    </form>
  );
}

export default RestockForm;
