import React, { useState, useEffect } from "react";
import mockInventory from "../data/mockInventory";

function AlertsBanner() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetch("/api/alerts")
      .then((res) => {
        if (!res.ok) throw new Error("API unavailable");
        return res.json();
      })
      .then((data) => setAlerts(data))
      .catch(() => {
        // Derive alerts from mock data until backend is connected
        const derived = mockInventory
          .filter((s) => {
            const color = (s.status_color || "").toLowerCase();
            return color === "red" || color === "yellow";
          })
          .map((s) => {
            const color = (s.status_color || "").toLowerCase();
            return {
              slot_id: s.slot_id,
              item_name: s.item_name,
              alert_level: color === "red" ? "critical" : "warning",
              reason:
                s.quantity <= 3
                  ? "Low stock"
                  : `Expires in ${s.days_until_expiry} days`,
            };
          });
        setAlerts(derived);
      });
  }, []);

  if (alerts.length === 0) return null;

  // SAFEGUARD: Ensure filter looks for lowercase
  const critical = alerts.filter((a) => (a.alert_level || "").toLowerCase() === "critical");
  const warnings = alerts.filter((a) => (a.alert_level || "").toLowerCase() === "warning");

  return (
    <div className="mb-4">
      {critical.length > 0 && (
        <div className="alert alert-danger py-2" role="alert">
          <strong>Critical ({critical.length}):</strong>{" "}
          {critical.map((a) => `${a.slot_id} — ${a.item_name} (${a.reason})`).join(" · ")}
        </div>
      )}
      {warnings.length > 0 && (
        <div className="alert alert-warning py-2" role="alert">
          <strong>Warning ({warnings.length}):</strong>{" "}
          {warnings.map((a) => `${a.slot_id} — ${a.item_name} (${a.reason})`).join(" · ")}
        </div>
      )}
    </div>
  );
}

export default AlertsBanner;