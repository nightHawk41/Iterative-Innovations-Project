import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import InventoryGrid from './components/InventoryGrid';
import PurchaseModal from './components/PurchaseModal';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [slots, setSlots]         = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [purchaseSubmitting, setPurchaseSubmitting] = useState(false);
  const [toast, setToast] = useState(null);

  function showToast(message, variant = 'success') {
    setToast({ message, variant });
  }

  useEffect(() => {
    if (!toast) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => setToast(null), 3000);
    return () => window.clearTimeout(timeoutId);
  }, [toast]);

  function closePurchaseModal() {
    setSelectedSlot(null);
  }

  function handleSlotSelect(slot) {
    setSelectedSlot(slot);
  }

  async function fetchInventory() {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/inventory');
      if (!response.ok) {
        throw new Error();
      }
      const data = await response.json();
      setSlots(data);
      return data;
    } catch (err) {
        setSlots([]);
        setError('Unable to load inventory. Please check that the backend is running.');
      return [];
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirmPurchase() {
    if (!selectedSlot) {
      return;
    }

    setPurchaseSubmitting(true);
    const slotToPurchase = selectedSlot;

    try {
      const response = await fetch('/api/purchase', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ slot_id: slotToPurchase.slot_id }),
      });

      if (response.status === 200) {
        closePurchaseModal();
        showToast(`✓ ${slotToPurchase.item_name} dispensed!`, 'success');
        await fetchInventory();
        return;
      }

      closePurchaseModal();
      if (response.status === 409) {
        showToast('This item is out of stock.', 'danger');
      } else if (response.status === 400) {
        showToast('This item is unavailable.', 'danger');
      } else {
        showToast('Purchase failed. Please try again.', 'danger');
      }
    } catch (err) {
      closePurchaseModal();
      showToast('Network error. Is the backend running?', 'danger');
    } finally {
      setPurchaseSubmitting(false);
    }
  }

  useEffect(() => { fetchInventory(); }, []);

  return (
    <div className="app-body">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        slots={slots}
        onRestockSuccess={fetchInventory}
      />
      <section className="machine-panel">
        <div className="machine-panel-header">UMBC Vending Machine</div>
        {error ? <div className="alert alert-danger m-3 mb-0">{error}</div> : null}
        {loading
          ? <div style={{ padding: '2rem', textAlign: 'center' }}>Loading…</div>
          : <InventoryGrid slots={slots} activeTab={activeTab} onSlotSelect={handleSlotSelect} />
        }
      </section>

      <PurchaseModal
        show={Boolean(selectedSlot)}
        slot={selectedSlot}
        submitting={purchaseSubmitting}
        onConfirm={handleConfirmPurchase}
        onHide={closePurchaseModal}
      />

      {toast ? (
        <div className={`app-toast app-toast-${toast.variant}`} role="status" aria-live="polite">
          {toast.message}
        </div>
      ) : null}
    </div>
  );
}

export default App;