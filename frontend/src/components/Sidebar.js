import React, { useState, useEffect } from 'react';
import AlertsBanner from './AlertsBanner';
import TransactionUpload from './TransactionUpload';
import RestockModal from './RestockModal';
import mockInventory from '../data/mockInventory';

function Sidebar({ activeTab, setActiveTab, slots, onRestockSuccess }) {
  // slots and onRestockSuccess are passed down from App.js,
  // which now owns the shared inventory state.
  const [showModal, setShowModal] = useState(false);

  const total    = slots.length;
  const critical = slots.filter(s => (s.status_color || '').toLowerCase() === 'red').length;
  const warning  = slots.filter(s => (s.status_color || '').toLowerCase() === 'yellow').length;
  const healthy  = slots.filter(s => (s.status_color || '').toLowerCase() === 'green').length;

  return (
    <aside className="sidebar">
      <div className="nav-tabs">
        <button
          className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button
          className={`nav-tab ${activeTab === 'admin' ? 'active' : ''}`}
          onClick={() => setActiveTab('admin')}
        >
          Admin Panel
        </button>
      </div>

      {activeTab === 'dashboard' && (
        <div className="sidebar-content" id="sidebar-dashboard">
          <div className="stat-card">
            <span>Total Slots</span>
            <span className="stat-value">{total}</span>
          </div>
          <div className="stat-card healthy">
            <span>Healthy</span>
            <span className="stat-value">{healthy}</span>
          </div>
          <div className="stat-card warning">
            <span>Low / Expiring</span>
            <span className="stat-value">{warning}</span>
          </div>
          <div className="stat-card critical">
            <span>Critical / Out</span>
            <span className="stat-value">{critical}</span>
          </div>
          <AlertsBanner />
        </div>
      )}

      {activeTab === 'admin' && (
        <div className="sidebar-content" id="sidebar-admin">
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            + Manual Restock
          </button>
          <TransactionUpload />
        </div>
      )}

      <div className="sidebar-footer">
        {/* Task F-6: Reload / Help buttons go here */}
      </div>

      <RestockModal
        show={showModal}
        onHide={() => setShowModal(false)}
        slots={slots}
        onRestockSuccess={onRestockSuccess}
      />
    </aside>
  );
}

export default Sidebar;