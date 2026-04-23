import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import PurchaseModal from './PurchaseModal';
import { showToast } from '../utils/toast';

jest.mock('../utils/toast', () => ({
  showToast: jest.fn(),
}));

const slot = {
  slot_id: 'A1',
  item_name: 'Granola Bar',
  price: 2.15,
};

describe('PurchaseModal', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('renders as fixed overlay with item details', () => {
    render(<PurchaseModal slot={slot} onClose={jest.fn()} onSuccess={jest.fn()} />);

    expect(screen.getByText('Confirm Purchase')).toBeInTheDocument();
    expect(screen.getByText(/Purchase Granola Bar/)).toBeInTheDocument();
    expect(screen.getByText(/Slot A1/)).toBeInTheDocument();
    expect(screen.getByText(/\$2.15/)).toBeInTheDocument();
  });

  it('disables Confirm while request is in flight', async () => {
    let resolveFetch;
    global.fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve;
        })
    );

    render(<PurchaseModal slot={slot} onClose={jest.fn()} onSuccess={jest.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }));
    expect(screen.getByRole('button', { name: 'Processing…' })).toBeDisabled();

    resolveFetch({ ok: true, status: 200, json: async () => ({}) });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Confirm' })).toBeEnabled();
    });
  });

  it('handles HTTP 200 by toasting success and calling onSuccess', async () => {
    const onSuccess = jest.fn().mockResolvedValue(undefined);

    global.fetch.mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({}) });

    render(<PurchaseModal slot={slot} onClose={jest.fn()} onSuccess={onSuccess} />);

    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/purchase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot_id: 'A1' }),
      });
      expect(showToast).toHaveBeenCalledWith('✓ Granola Bar dispensed!');
      expect(onSuccess).toHaveBeenCalledTimes(1);
    });
  });

  it('handles HTTP 409 by toasting out-of-stock and closing', async () => {
    const onClose = jest.fn();

    global.fetch.mockResolvedValueOnce({ ok: false, status: 409, json: async () => ({}) });

    render(<PurchaseModal slot={slot} onClose={onClose} onSuccess={jest.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(showToast).toHaveBeenCalledWith('This item is out of stock.');
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  it('handles HTTP 400 by toasting unavailable and closing', async () => {
    const onClose = jest.fn();

    global.fetch.mockResolvedValueOnce({ ok: false, status: 400, json: async () => ({}) });

    render(<PurchaseModal slot={slot} onClose={onClose} onSuccess={jest.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(showToast).toHaveBeenCalledWith('This item is unavailable.');
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  it('handles network errors by toasting and closing', async () => {
    const onClose = jest.fn();

    global.fetch.mockRejectedValueOnce(new Error('network'));

    render(<PurchaseModal slot={slot} onClose={onClose} onSuccess={jest.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(showToast).toHaveBeenCalledWith('Network error. Is the backend running?');
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  it('cancel always closes without calling API', async () => {
    const onClose = jest.fn();

    render(<PurchaseModal slot={slot} onClose={onClose} onSuccess={jest.fn()} />);

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(global.fetch).not.toHaveBeenCalled();
  });
});
