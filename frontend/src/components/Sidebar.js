import React, { useState } from 'react';
import AlertsBanner from './AlertsBanner';
import InventoryUpload from './InventoryUpload';
import { generateSalesReport } from './SalesReport';
import TransactionUpload from './TransactionUpload';
import RestockModal from './RestockModal';

function Sidebar({ activeTab, setActiveTab, slots, summary, onRestockSuccess, onInventoryRefresh, onShowToast }) {
  // slots and onRestockSuccess are passed down from App.js,
  // which now owns the shared inventory state.
  const [showModal, setShowModal] = useState(false);
  const [reportReady, setReportReady] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  async function handleGenerateSalesReport() {
    setReportLoading(true);
    await generateSalesReport({
      onError: (message) => onShowToast?.(message, 'danger'),
    });
    setReportLoading(false);
  }

  const total = Number(summary?.total_slots ?? slots.length);
  const healthy = Number(summary?.healthy ?? 0);
  const warning = Number(summary?.low_expiring ?? 0);
  const critical = Number(summary?.critical_out ?? 0);

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
          <TransactionUpload onReportReady={setReportReady} />
          <InventoryUpload onInventoryUpdated={onInventoryRefresh} onShowToast={onShowToast} />
          <button
            className="btn btn-outline-secondary mt-3"
            disabled={!reportReady || reportLoading}
            onClick={handleGenerateSalesReport}
          >
            {reportLoading ? 'Generating…' : 'Generate Sales Report'}
          </button>
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
        onShowToast={onShowToast}
      />
    </aside>
  );
}

export default Sidebar;