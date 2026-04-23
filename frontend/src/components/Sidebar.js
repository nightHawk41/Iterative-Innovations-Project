import React from 'react';
import AdminTab from './AdminTab';
import DashboardTab from './DashboardTab';

function Sidebar({ activeTab, setActiveTab, slots, onInventoryChange, onShowToast }) {
  function handleHelpClick() {
    onShowToast?.('Help: Green = healthy, Yellow = low/expiring, Red = critical/expired.', 'success');
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
            onShowToast={onShowToast}
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