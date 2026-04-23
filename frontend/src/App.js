import React, { useState, useEffect } from 'react';
import AppHeader from './components/AppHeader';
import Sidebar from './components/Sidebar';
import MachinePanel from './components/MachinePanel';
import Toast from './components/Toast';
import { showToast } from './utils/toast';
import './App.css';

const EMPTY_SUMMARY = {
  total_slots: 0,
  healthy: 0,
  low_expiring: 0,
  critical_out: 0,
};

function computeSummaryFromSlots(slots) {
  let healthy = 0;
  let lowExpiring = 0;
  let criticalOut = 0;

  for (const slot of slots) {
    const quantity = Number(slot.quantity ?? 0);
    const daysUntilExpiry = Number(slot.days_until_expiry ?? -1);

    if (daysUntilExpiry <= 0 || quantity === 0) {
      criticalOut += 1;
    } else if (quantity <= 2 || daysUntilExpiry <= 2) {
      criticalOut += 1;
    } else if (quantity <= 5 || daysUntilExpiry <= 5) {
      lowExpiring += 1;
    } else {
      healthy += 1;
    }
  }

  return {
    total_slots: slots.length,
    healthy,
    low_expiring: lowExpiring,
    critical_out: criticalOut,
  };
}

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [slots, setSlots]         = useState([]);
  const [summary, setSummary]     = useState(EMPTY_SUMMARY);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');

  async function fetchInventorySummary(fallbackSlots = []) {
    try {
      const summaryResponse = await fetch('/api/inventory/summary');
      if (!summaryResponse.ok) {
        throw new Error();
      }

      const summaryData = await summaryResponse.json();
      setSummary({
        total_slots: Number(summaryData.total_slots ?? 0),
        healthy: Number(summaryData.healthy ?? 0),
        low_expiring: Number(summaryData.low_expiring ?? 0),
        critical_out: Number(summaryData.critical_out ?? 0),
      });
    } catch (err) {
      setSummary(computeSummaryFromSlots(fallbackSlots));
    }
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
      const slotsData = Array.isArray(data) ? data : [];
      setSlots(slotsData);
      await fetchInventorySummary(slotsData);
      return data;
    } catch (err) {
        setSlots([]);
        setSummary(EMPTY_SUMMARY);
        setError('Unable to load inventory. Please check that the backend is running.');
      return [];
    } finally {
      setLoading(false);
    }
  }

  async function handleSlotPurchase(slotToPurchase) {
    if (!slotToPurchase) {
      return;
    }

    try {
      const response = await fetch('/api/purchase', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ slot_id: slotToPurchase.slot_id }),
      });

      if (response.status === 200) {
        showToast(`✓ ${slotToPurchase.item_name} dispensed!`);
        await fetchInventory();
        return;
      }

      if (response.status === 409) {
        showToast('This item is out of stock.');
      } else if (response.status === 400) {
        showToast('This item is unavailable.');
      } else {
        showToast('Purchase failed. Please try again.');
      }
    } catch (err) {
      showToast('Network error. Is the backend running?');
    }
  }

  useEffect(() => { fetchInventory(); }, []);

  return (
    <div className="app-wrapper">
      <AppHeader />

      <div className="app-body">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          slots={slots}
          summary={summary}
          onInventoryChange={fetchInventory}
        />

        {error ? <div className="alert alert-danger m-3 mb-0">{error}</div> : null}
        {loading
          ? (
            <section className="machine-panel">
              <div className="machine-panel-header">UMBC Vending Machine</div>
              <div style={{ padding: '2rem', textAlign: 'center' }}>Loading…</div>
            </section>
          )
          : <MachinePanel slots={slots} onPurchaseSuccess={handleSlotPurchase} />
        }
      </div>
      <Toast />
    </div>
  );
}

export default App;