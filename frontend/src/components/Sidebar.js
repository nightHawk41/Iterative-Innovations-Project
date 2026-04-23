import React from 'react';
import AdminTab from './AdminTab';
import DashboardTab from './DashboardTab';
import { showToast } from '../utils/toast';

function Sidebar({ activeTab, setActiveTab, slots, onInventoryChange }) {
  function handleHelpClick() {
    showToast('Help: Green = healthy, Yellow = low/expiring, Red = critical/expired.');
  }

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

      <div className="sidebar-content">
        {activeTab === 'dashboard' && <DashboardTab slots={slots} />}
        {activeTab === 'admin' && (
          <AdminTab
            slots={slots}
            onInventoryChange={onInventoryChange}
          />
        )}
      </div>

      <div className="sidebar-footer">
        <button className="btn" onClick={onInventoryChange}>Reload</button>
        <button className="btn" onClick={handleHelpClick}>Help</button>
      </div>
    </aside>
  );
}

export default Sidebar;