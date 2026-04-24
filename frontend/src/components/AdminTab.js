import React, { useState } from 'react';
import InventoryUpload from './InventoryUpload';
import TransactionUpload from './TransactionUpload';
import RestockForm from './RestockForm';
import { generateSalesReport } from '../utils/generateSalesReport';

function AdminTab({ slots, onInventoryChange, hasTransactions, onTransactionAdded }) {
  const [restockOpen, setRestockOpen] = useState(false);
  const [txnOpen, setTxnOpen] = useState(false);
  const [invOpen, setInvOpen] = useState(false);

  return (
    <div id="sidebar-admin">
      <AccordionPanel
        title="+ Manual Restock"
        isOpen={restockOpen}
        onToggle={() => setRestockOpen(prev => !prev)}
      >
        <RestockForm slots={slots} onSuccess={onInventoryChange} />
      </AccordionPanel>

      <AccordionPanel
        title="Upload CBORD Transactions"
        isOpen={txnOpen}
        onToggle={() => setTxnOpen(prev => !prev)}
      >
        <TransactionUpload onSuccess={onInventoryChange} onUploadSuccess={onTransactionAdded} />
      </AccordionPanel>

      <AccordionPanel
        title="Upload New Inventory"
        isOpen={invOpen}
        onToggle={() => setInvOpen(prev => !prev)}
      >
        <InventoryUpload onSuccess={onInventoryChange} />
      </AccordionPanel>

      <hr className="panel-divider" />

      <button
        className="full-width-btn"
        onClick={generateSalesReport}
        disabled={!hasTransactions}
      >
        📊 Generate Sales Report
      </button>

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