import React from 'react';
import AdminTab from './AdminTab';
import DashboardTab from './DashboardTab';

function Sidebar({ activeTab, setActiveTab, slots, onInventoryChange, onReset, hasTransactions, onTransactionAdded }) {
  function closeProgram() {
    // Best-effort close for browser/electron contexts; browsers may block closing non-script-opened tabs.
    window.open('', '_self');
    window.close();
  }

  function openHelpWindow() {
    const helpHTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>UMBC Vending Inventory System - Help</title>
<style>
  :root {
    --gold: #f0a500;
    --black: #1a1a1a;
    --green: #4caf50;
    --yellow: #f5c518;
    --red: #e53935;
    --border: #999;
    --panel-bg: #e8e8e8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'IBM Plex Sans', sans-serif;
    background: #f5f3ef;
    color: var(--black);
    min-height: 100vh;
  }
  .top-bar {
    background: var(--black);
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 28px;
    position: sticky;
    top: 0;
    z-index: 10;
    border-bottom: 3px solid var(--gold);
  }
  .top-bar-left { display: flex; align-items: center; gap: 14px; }
  .top-bar-logo {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: -1px;
    color: var(--gold);
  }
  .top-bar-title {
    font-size: 0.9rem;
    color: #ccc;
    font-weight: 300;
    border-left: 1px solid #444;
    padding-left: 14px;
  }
  .close-btn {
    padding: 7px 18px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    background: transparent;
    color: #ccc;
    border: 1px solid #555;
    transition: background 0.15s;
  }
  .close-btn:hover { background: #333; color: white; }
  .help-body {
    max-width: 820px;
    margin: 36px auto;
    padding: 0 24px 60px;
  }
  .help-header {
    border-left: 5px solid var(--gold);
    padding: 16px 20px;
    background: white;
    margin-bottom: 28px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .help-header h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 6px;
  }
  .help-header p {
    font-size: 0.82rem;
    color: #555;
  }
  .section {
    background: white;
    border: 1px solid var(--border);
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  .section-title {
    background: var(--black);
    color: white;
    padding: 8px 14px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
  }
  .section-body { padding: 14px 18px; }
  .section-body p, .section-body li {
    font-size: 0.84rem;
    line-height: 1.7;
    color: #333;
  }
  .section-body ul { padding-left: 20px; margin-top: 6px; }
  .section-body li { margin-bottom: 4px; }
  .color-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
    font-size: 0.84rem;
  }
  .color-swatch {
    width: 36px;
    height: 36px;
    border: 1px solid #aaa;
    flex-shrink: 0;
  }
  .swatch-green  { background: #5db85d; }
  .swatch-yellow { background: var(--yellow); }
  .swatch-red    { background: var(--red); }
  .swatch-gray   { background: #aaa; }
  .color-desc strong { display: block; font-size: 0.82rem; }
  .color-desc span { font-size: 0.78rem; color: #555; }
  code {
    background: #eee;
    padding: 1px 5px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    border-radius: 2px;
  }
  .help-footer {
    text-align: center;
    font-size: 0.72rem;
    color: #999;
    padding-top: 20px;
    border-top: 1px solid var(--border);
  }
</style>
</head>
<body>

<div class="top-bar">
  <div class="top-bar-left">
    <span class="top-bar-logo">UMBC</span>
    <span class="top-bar-title">| Vending Inventory System - Help</span>
  </div>
  <button class="close-btn" onclick="window.close()">✕ Close</button>
</div>

<div class="help-body">

  <div class="help-header">
    <h1>How to Use the UMBC Vending Inventory System</h1>
    <p>This guide explains the system's rules, color codes, and administrative features.</p>
  </div>

  <div class="section">
    <div class="section-title">DASHBOARD - INVENTORY STATUS COLORS</div>
    <div class="section-body">
      <p>Every slot on the vending machine grid is color-coded to indicate its current inventory status. The color is determined by whichever condition, stock level or days until expiration, is most urgent.</p>
      <br>
      <div class="color-row">
        <div class="color-swatch swatch-green"></div>
        <div class="color-desc">
          <strong>Green - Healthy</strong>
          <span>Stock is greater than 5 units AND expiration is more than 5 days away.</span>
        </div>
      </div>
      <div class="color-row">
        <div class="color-swatch swatch-yellow"></div>
        <div class="color-desc">
          <strong>Yellow - Low / Expiring</strong>
          <span>Stock is 5 units or fewer OR expiration is 5 days or fewer away. Requires attention soon.</span>
        </div>
      </div>
      <div class="color-row">
        <div class="color-swatch swatch-red"></div>
        <div class="color-desc">
          <strong>Red - Critical</strong>
          <span>Stock is 2 units or fewer OR expiration is 2 days or fewer away. Requires immediate action.</span>
        </div>
      </div>
      <div class="color-row">
        <div class="color-swatch swatch-gray"></div>
        <div class="color-desc">
          <strong>Gray - Out of Stock / Expired</strong>
          <span>Stock is 0 OR the item has already expired. The slot is disabled and cannot be purchased.</span>
        </div>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">ADMIN PANEL - MANUAL RESTOCK</div>
    <div class="section-body">
      <ul>
        <li>Select a slot from the Slot ID dropdown. The dropdown shows the slot label and item name (e.g., A1 - Bic Comfort Pens).</li>
        <li>Enter a quantity to add. The maximum quantity you can add is <strong>10 minus the slot's current stock level</strong>. For example, if a slot has 3 items, you can add at most 7.</li>
        <li>Enter an expiration date for the restocked items. This will replace the slot's current expiration date.</li>
        <li>Click <strong>Restock</strong> to apply the changes. The machine grid will update immediately.</li>
        <li>Click <strong>Cancel</strong> to clear the form without making any changes.</li>
      </ul>
    </div>
  </div>

  <div class="section">
    <div class="section-title">ADMIN PANEL - UPLOAD NEW INVENTORY</div>
    <div class="section-body">
      <ul>
        <li>Upload a <code>.csv</code> file to update the item names, prices, stock levels, and expiration dates across all slots.</li>
        <li>The CSV must use the <code>Inventory_config.csv</code> format with three required columns: <code>ROW</code>, <code>Product</code>, and <code>Vending Price</code>.</li>
        <li>Two optional columns are supported: <code>stock</code> (integer 0-10) and <code>expiration_date</code> (YYYY-MM-DD). If either is omitted, the existing value for that slot is preserved.</li>
        <li>Every item must have a <strong>unique Vending Price</strong>. The system uses price to identify which item was sold in each campus card transaction.</li>
        <li>Stock values above 10 are automatically capped at 10.</li>
        <li>Past expiration dates will immediately mark the slot as expired and gray it out on the grid.</li>
        <li>Click <strong>Upload &amp; Process</strong> to validate the file. If valid, the 🔄 Update Inventory button will become active.</li>
        <li>Click <strong>🔄 Update Inventory</strong> to apply changes to the machine grid.</li>
        <li>Click <strong>Clear</strong> to reset the panel without applying any changes.</li>
      </ul>
    </div>
  </div>

  <div class="section">
    <div class="section-title">ADMIN PANEL - UPLOAD CBORD TRANSACTIONS</div>
    <div class="section-body">
      <ul>
        <li>Upload a <code>.csv</code> file that simulates the weekly Campus Card Report exported from the CBORD campus card system.</li>
        <li>The system identifies which item was sold in each row by matching the <code>Tran Amt</code> field against the vending machine's known price list. This works because every item has a unique price.</li>
        <li>Each matched row counts as one unit sold. Rows whose transaction amount does not match any known item price are skipped automatically.</li>
        <li>After a successful upload, the <strong>📊 Generate Sales Report</strong> button becomes active.</li>
        <li>Click <strong>Clear</strong> to reset the file input and feedback message.</li>
      </ul>
    </div>
  </div>

  <div class="section">
    <div class="section-title">ADMIN PANEL - GENERATE SALES REPORT</div>
    <div class="section-body">
      <ul>
        <li>The <strong>📊 Generate Sales Report</strong> button becomes active after at least one transaction has been recorded, either from a grid purchase or from a successfully uploaded CBORD transactions CSV.</li>
        <li>Clicking the button opens the Sales Report in a new browser window.</li>
        <li>The report shows Total Revenue, Units Sold, Unique Items, the top-selling item, and a full ranked breakdown table sorted by revenue.</li>
        <li>Click <strong>⬇ Download CSV</strong> inside the report window to save the report as a <code>.csv</code> file.</li>
        <li>Click <strong>⎘ Copy CSV</strong> inside the report window to copy the full sales report CSV to your clipboard.</li>
        <li>Click <strong>✕ Close</strong> inside the report window to close it and return to the Admin Panel.</li>
      </ul>
    </div>
  </div>

  <div class="section">
    <div class="section-title">PURCHASING - VIRTUAL VENDING MACHINE</div>
    <div class="section-body">
      <ul>
        <li>Purchases are only available from the <strong>Dashboard</strong> tab. The machine grid is non-interactive while the Admin Panel tab is active.</li>
        <li>Click any active (non-gray) slot to open the purchase confirmation dialog.</li>
        <li>The dialog shows the item name, slot ID, and price. Click <strong>Confirm</strong> to complete the purchase or <strong>Cancel</strong> to dismiss.</li>
        <li>Each confirmed purchase decrements that slot's stock by 1 and logs a transaction in the CBORD format for use in the Sales Report.</li>
        <li>Gray slots are out of stock or expired and cannot be purchased.</li>
      </ul>
    </div>
  </div>

  <div class="help-footer">
    UMBC Vending Inventory System &nbsp;·&nbsp; Help Guide
  </div>

</div>

</body>
</html>`;
    const win = window.open(
      '',
      '_blank',
      'width=860,height=720,scrollbars=yes,resizable=yes'
    );
    if (!win) {
      return;
    }
    win.document.write(helpHTML);
    win.document.close();
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
            hasTransactions={hasTransactions}
            onTransactionAdded={onTransactionAdded}
          />
        )}
      </div>

      <div className="sidebar-footer">
        <button className="btn" onClick={onReset}>Reload</button>
        <button className="btn" onClick={closeProgram}>Close</button>
        <button className="btn" onClick={openHelpWindow}>Help</button>
      </div>
    </aside>
  );
}

export default Sidebar;