import React from "react";

const STATUS_STYLES = {
  Green:  { bg: "success", label: "OK" },
  Yellow: { bg: "warning", label: "Low" },
  Red:    { bg: "danger",  label: "Critical" },
};

function StatusIndicator({ status }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES["Red"];
  return (
    <span className={`badge rounded-pill bg-${style.bg} status-badge`}>
      {style.label}
    </span>
  );
}

export default StatusIndicator;