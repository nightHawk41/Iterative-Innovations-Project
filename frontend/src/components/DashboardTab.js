import React from 'react';

function StatCard({ label, value, colorClass }) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <span className={`stat-value ${colorClass || ''}`}>{value}</span>
    </div>
  );
}

function DashboardTab({ slots }) {
  let healthy = 0;
  let warning = 0;
  let critical = 0;

  for (const slot of slots) {
    const c = Number(slot.quantity ?? 0);
    const d = Number(slot.days_until_expiry ?? -1);

    if (d <= 0 || c === 0) critical += 1;
    else if (c <= 2 || d <= 2) critical += 1;
    else if (c <= 5 || d <= 5) warning += 1;
    else healthy += 1;
  }

  return (
    <div id="sidebar-dashboard">
      <p className="sidebar-desc">Overview and quick stats.</p>
      <StatCard label="Total Slots" value={slots.length} colorClass="total" />
      <StatCard label="Healthy" value={healthy} colorClass="healthy" />
      <StatCard label="Low / Expiring" value={warning} colorClass="warning" />
      <StatCard label="Critical / Out" value={critical} colorClass="critical" />
    </div>
  );
}

export default DashboardTab;