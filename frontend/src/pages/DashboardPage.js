import React, { useState, useEffect } from "react";
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
  const [slots, setSlots]     = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch("/api/inventory")
      .then((res) => {
        if (!res.ok) throw new Error("API unavailable");
        return res.json();
      })
      .then((data) => setSlots(data)) // Perfectly native data now!
      .catch(() => {
        setSlots(mockInventory);
      })
      .finally(() => setLoading(false));
  }, []);

  const total    = slots.length;
  // SAFEGUARD: Force .toLowerCase() just in case the data is ever messed up
  const critical = slots.filter((s) => (s.status_color || "").toLowerCase() === "red").length;
  const warning  = slots.filter((s) => (s.status_color || "").toLowerCase() === "yellow").length;
  const healthy  = slots.filter((s) => (s.status_color || "").toLowerCase() === "green").length;

  return (
    <div>
      <div className="page-header mb-4">
        <h2 className="mb-0">Inventory Dashboard</h2>
        <p className="text-muted mb-0">Read-only view — use Admin Panel to make changes.</p>
      </div>

      <div className="row row-cols-2 row-cols-md-4 g-3 mb-4">
        <StatCard label="Total Slots"    value={total}    colorClass="border-secondary" />
        <StatCard label="Healthy"        value={healthy}  colorClass="border-success" />
        <StatCard label="Low / Expiring" value={warning}  colorClass="border-warning" />
        <StatCard label="Critical"       value={critical} colorClass="border-danger" />
      </div>

      <AlertsBanner />

      {loading ? (
        <div className="text-center py-5 text-muted">Loading inventory…</div>
      ) : (
        <InventoryGrid slots={slots} />
      )}
    </div>
  );
}

export default DashboardPage;