import React from "react";

// Maps status string to Bootstrap badge color classes.
const STATUS_STYLES = {
  Green:  { bg: "success", label: "In Stock" },
  Yellow: { bg: "warning", label: "Low / Expiring" },
  Red:    { bg: "danger",  label: "Critical" },
};

function StatusIndicator({ status }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES["Red"];
  return (
    <span className={`badge bg-${style.bg}`}>
      {style.label}
    </span>
  );
}

export default StatusIndicator;