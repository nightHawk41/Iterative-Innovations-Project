import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import InventoryGrid from './components/InventoryGrid';
import mockInventory from './data/mockInventory';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [slots, setSlots]         = useState([]);
  const [loading, setLoading]     = useState(true);

  function fetchInventory() {
    setLoading(true);
    fetch('/api/inventory')
      .then(res => { if (!res.ok) throw new Error(); return res.json(); })
      .then(data => setSlots(data))
      .catch(() => setSlots(mockInventory))
      .finally(() => setLoading(false));
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
        {loading
          ? <div style={{ padding: '2rem', textAlign: 'center' }}>Loading…</div>
          : <InventoryGrid slots={slots} activeTab={activeTab} />
        }
      </section>
    </div>
  );
}

export default App;