import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import RestockForm from './RestockForm';
import { showToast } from '../utils/toast';

jest.mock('../utils/toast', () => ({
  showToast: jest.fn(),
}));

const slots = [
  {
    slot_id: 'A1',
    item_name: 'Bic Comfort Pens',
    quantity: 8,
  },
  {
    slot_id: 'A2',
    item_name: 'Trail Mix',
    quantity: 4,
  },
];

describe('RestockForm', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('validates all three fields simultaneously on submit', async () => {
    render(<RestockForm slots={slots} onSuccess={jest.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Restock' }));

    expect(screen.getByText('Please select a slot.')).toBeInTheDocument();
    expect(screen.getByText('Quantity is required.')).toBeInTheDocument();
    expect(screen.getByText('Expiration date is required.')).toBeInTheDocument();
  });

  it('enforces dynamic max quantity based on selected slot', async () => {
    render(<RestockForm slots={slots} onSuccess={jest.fn()} />);

    await userEvent.selectOptions(screen.getByLabelText('Slot ID'), 'A1');
    await userEvent.type(screen.getByLabelText('Qty Added'), '3');
    await userEvent.type(screen.getByLabelText('Exp Date'), '2026-12-01');
    await userEvent.click(screen.getByRole('button', { name: 'Restock' }));

    expect(screen.getByText('Quantity cannot exceed 2.')).toBeInTheDocument();
  });

  it('sends restock request, clears form, calls onSuccess, and shows toast on success', async () => {
    const onSuccess = jest.fn().mockResolvedValue(undefined);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ message: 'Restocked' }),
    });

    render(<RestockForm slots={slots} onSuccess={onSuccess} />);

    await userEvent.selectOptions(screen.getByLabelText('Slot ID'), 'A1');
    await userEvent.type(screen.getByLabelText('Qty Added'), '2');
    await userEvent.type(screen.getByLabelText('Exp Date'), '2026-12-01');
    await userEvent.click(screen.getByRole('button', { name: 'Restock' }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/restock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          slot_id: 'A1',
          quantity_added: 2,
          expiration_date: '2026-12-01',
        }),
      });
      expect(onSuccess).toHaveBeenCalledTimes(1);
      expect(showToast).toHaveBeenCalledWith('✓ Bic Comfort Pens restocked (+2)');
    });

    expect(screen.getByLabelText('Slot ID')).toHaveValue('');
    expect(screen.getByLabelText('Qty Added')).toHaveValue(null);
    expect(screen.getByLabelText('Exp Date')).toHaveValue('');
  });

  it('shows API error inline on HTTP 400', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ error: 'Cannot exceed capacity.' }),
    });

    render(<RestockForm slots={slots} onSuccess={jest.fn()} />);

    await userEvent.selectOptions(screen.getByLabelText('Slot ID'), 'A2');
    await userEvent.type(screen.getByLabelText('Qty Added'), '1');
    await userEvent.type(screen.getByLabelText('Exp Date'), '2026-12-01');
    await userEvent.click(screen.getByRole('button', { name: 'Restock' }));

    expect(await screen.findByText('Cannot exceed capacity.')).toBeInTheDocument();
  });

  it('shows fixed concurrency message on HTTP 409', async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: async () => ({ error: 'conflict' }),
    });

    render(<RestockForm slots={slots} onSuccess={jest.fn()} />);

    await userEvent.selectOptions(screen.getByLabelText('Slot ID'), 'A2');
    await userEvent.type(screen.getByLabelText('Qty Added'), '1');
    await userEvent.type(screen.getByLabelText('Exp Date'), '2026-12-01');
    await userEvent.click(screen.getByRole('button', { name: 'Restock' }));

    expect(
      await screen.findByText('This slot was recently modified. Please try again.')
    ).toBeInTheDocument();
  });

  it('shows network error inline when request fails', async () => {
    global.fetch.mockRejectedValueOnce(new Error('network'));

    render(<RestockForm slots={slots} onSuccess={jest.fn()} />);

    await userEvent.selectOptions(screen.getByLabelText('Slot ID'), 'A2');
    await userEvent.type(screen.getByLabelText('Qty Added'), '1');
    await userEvent.type(screen.getByLabelText('Exp Date'), '2026-12-01');
    await userEvent.click(screen.getByRole('button', { name: 'Restock' }));

    expect(await screen.findByText('Network error. Is the backend running?')).toBeInTheDocument();
  });
});
