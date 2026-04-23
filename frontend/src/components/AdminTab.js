import React, { useState } from 'react';
import InventoryUpload from './InventoryUpload';
import { generateSalesReport } from './SalesReport';
import TransactionUpload from './TransactionUpload';
import RestockModal from './RestockModal';
import { showToast } from '../utils/toast';

function AdminTab({ slots, onInventoryChange }) {
  const [openPanel, setOpenPanel] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [reportReady, setReportReady] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  function togglePanel(name) {
    setOpenPanel((prev) => (prev === name ? null : name));
  }

  async function handleGenerateSalesReport() {
    setReportLoading(true);
    await generateSalesReport({
      onError: (message) => showToast(message),
    });
    setReportLoading(false);
  }

  return (
    <div id="sidebar-admin">
      <AccordionPanel
        title="+ Manual Restock"
        isOpen={openPanel === 'restock'}
        onToggle={() => togglePanel('restock')}
      >
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          Open Restock Form
        </button>
      </AccordionPanel>

      <AccordionPanel
        title="Upload Transaction CSV"
        isOpen={openPanel === 'txn'}
        onToggle={() => togglePanel('txn')}
      >
        <TransactionUpload onReportReady={setReportReady} />
      </AccordionPanel>

      <AccordionPanel
        title="Upload New Inventory CSV"
        isOpen={openPanel === 'inv'}
        onToggle={() => togglePanel('inv')}
      >
        <InventoryUpload onInventoryUpdated={onInventoryChange} />
      </AccordionPanel>

      <hr className="panel-divider" />

      <button
        className="btn btn-outline-secondary mt-3"
        disabled={!reportReady || reportLoading}
        onClick={handleGenerateSalesReport}
      >
        {reportLoading ? 'Generating…' : 'Generate Sales Report'}
      </button>

      <RestockModal
        show={showModal}
        onHide={() => setShowModal(false)}
        slots={slots}
        onRestockSuccess={onInventoryChange}
      />
    </div>
  );
}

function AccordionPanel({ title, isOpen, onToggle, children }) {
  return (
    <div className="panel-box">
      <button type="button" className="panel-box-header" onClick={onToggle}>
        <span>{title}</span>
        <span className="toggle-btn" aria-hidden="true">{isOpen ? '▾' : '▸'}</span>
      </button>
      {isOpen && <div className="panel-box-body">{children}</div>}
    </div>
  );
}

export default AdminTab;