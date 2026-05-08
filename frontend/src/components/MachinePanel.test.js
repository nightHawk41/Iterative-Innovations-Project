import { render, screen } from '@testing-library/react';

import MachinePanel from './MachinePanel';

jest.mock('./SlotTile', () => function MockSlotTile({ slot }) {
  const { slot_id } = slot;
  return <div data-testid="slot-tile">{slot_id}</div>;
});

function makeSlots(count) {
  return Array.from({ length: count }, (_, index) => ({
    slot_id: `A${index + 1}`,
    item_name: `Item ${index + 1}`,
    quantity: 5,
    price: 1.25,
    days_until_expiry: 10,
    status_color: 'green',
  }));
}

describe('MachinePanel', () => {
  it('renders centered machine header and one slot tile per slot', () => {
    render(<MachinePanel slots={makeSlots(24)} onPurchaseSuccess={jest.fn()} />);

    expect(screen.getByText('UMBC Vending Machine')).toBeInTheDocument();
    expect(screen.getAllByTestId('slot-tile')).toHaveLength(24);
  });

  it('shows upload prompt when no inventory slots are available', () => {
    render(<MachinePanel slots={[]} onPurchaseSuccess={jest.fn()} />);

    expect(screen.getByText('Upload inventory to view the vending machine grid.')).toBeInTheDocument();
    expect(screen.queryAllByTestId('slot-tile')).toHaveLength(0);
  });
});
