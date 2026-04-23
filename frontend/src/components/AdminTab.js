import React, { useState } from 'react';
import InventoryUpload from './InventoryUpload';
import TransactionUpload from './TransactionUpload';
import RestockForm from './RestockForm';

function AdminTab({ slots, onInventoryChange }) {
  const [openPanel, setOpenPanel] = useState(null);

  function togglePanel(name) {
    setOpenPanel((prev) => (prev === name ? null : name));
  }

  return (
    <div id="sidebar-admin">
      <AccordionPanel
        title="+ Manual Restock"
        isOpen={openPanel === 'restock'}
        onToggle={() => togglePanel('restock')}
      >
        <RestockForm slots={slots} onSuccess={onInventoryChange} />
      </AccordionPanel>

      <AccordionPanel
        title="Upload Transaction CSV"
        isOpen={openPanel === 'txn'}
        onToggle={() => togglePanel('txn')}
      >
        <TransactionUpload onSuccess={onInventoryChange} />
      </AccordionPanel>

      <AccordionPanel
        title="Upload New Inventory CSV"
        isOpen={openPanel === 'inv'}
        onToggle={() => togglePanel('inv')}
      >
        <InventoryUpload onInventoryUpdated={onInventoryChange} />
      </AccordionPanel>

      <hr className="panel-divider" />

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