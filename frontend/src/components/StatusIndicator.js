import React from "react";

// Lowercase keys to match backend
const STATUS_STYLES = {
  green:  { bg: "success", label: "OK" },
  yellow: { bg: "warning", label: "Low" },
  red:    { bg: "danger",  label: "Critical" },
};

function StatusIndicator({ status_color }) {
  // SAFEGUARD: Normalize incoming prop
  const safeColor = (status_color || "red").toLowerCase();
  const style = STATUS_STYLES[safeColor] ?? STATUS_STYLES.red;
  
  return (
    <span className={`badge rounded-pill bg-${style.bg} status-badge`}>
      {style.label}
    </span>
  );
}

export default StatusIndicator;