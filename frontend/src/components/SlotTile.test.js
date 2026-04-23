import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import SlotTile, { getColorClass } from './SlotTile';

jest.mock('./PurchaseModal', () => function MockPurchaseModal({ slot, onConfirm, onHide }) {
  return (
    <div>
      <h3>Confirm Purchase</h3>
      <div>Slot: {slot.slot_id}</div>
      <button onClick={onConfirm}>Confirm</button>
      <button onClick={onHide}>Cancel</button>
    </div>
  );
});

const baseSlot = {
  slot_id: 'A1',
  item_name: 'Granola Bar',
  quantity: 8,
  price: 2.15,
  days_until_expiry: 10,
  status_color: 'red',
};

describe('SlotTile', () => {
  it('computes color class from quantity and days_until_expiry (not status_color)', () => {
    expect(getColorClass(8, 10)).toBe('green');
    expect(getColorClass(4, 5)).toBe('yellow');
    expect(getColorClass(2, 10)).toBe('red');
    expect(getColorClass(8, 0)).toBe('disabled');
  });

  it('disabled tiles do not respond to clicks', async () => {
    render(
      <SlotTile
        slot={{ ...baseSlot, quantity: 0, days_until_expiry: 12 }}
        onPurchaseSuccess={jest.fn()}
      />
    );

    await userEvent.click(screen.getByText('Granola Bar'));
    expect(screen.queryByText('Confirm Purchase')).not.toBeInTheDocument();
  });

  it('active tiles open PurchaseModal on click', async () => {
    render(<SlotTile slot={baseSlot} onPurchaseSuccess={jest.fn()} />);

    await userEvent.click(screen.getByRole('button'));
    expect(screen.getByText('Confirm Purchase')).toBeInTheDocument();
    expect(screen.getByText('Slot: A1')).toBeInTheDocument();
  });

  it('expired slots show warning text instead of days', () => {
    render(
      <SlotTile
        slot={{ ...baseSlot, days_until_expiry: 0 }}
        onPurchaseSuccess={jest.fn()}
      />
    );

    expect(screen.getByText('⚠ Expired')).toBeInTheDocument();
    expect(screen.queryByText(/Exp:/)).not.toBeInTheDocument();
  });
});
