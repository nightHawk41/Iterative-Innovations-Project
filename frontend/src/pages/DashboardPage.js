import React from "react";
import InventoryGrid from "../components/InventoryGrid";
import AlertsBanner from "../components/AlertsBanner";
import mockInventory from "../data/mockInventory";

function StatCard({ label, value, colorClass }) {
  return (
    <div className="col">
      <div className={`stat-card border-top border-4 ${colorClass}`}>
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}

function DashboardPage() {
  const total    = mockInventory.length;
  const critical = mockInventory.filter((s) => s.status === "Red").length;
  const warning  = mockInventory.filter((s) => s.status === "Yellow").length;
  const healthy  = mockInventory.filter((s) => s.status === "Green").length;

  return (
    <div>
      <div className="page-header mb-4">
        <h2 className="mb-0">Inventory Dashboard</h2>
        <p className="text-muted mb-0">Read-only view — use Admin Panel to make changes.</p>
      </div>

      {/* Stats summary bar */}
      <div className="row row-cols-2 row-cols-md-4 g-3 mb-4">
        <StatCard label="Total Slots"   value={total}    colorClass="border-secondary" />
        <StatCard label="Healthy"       value={healthy}  colorClass="border-success" />
        <StatCard label="Low / Expiring" value={warning} colorClass="border-warning" />
        <StatCard label="Critical"      value={critical} colorClass="border-danger" />
      </div>

      <AlertsBanner />
      <InventoryGrid slots={mockInventory} />
    </div>
  );
}

export default DashboardPage;