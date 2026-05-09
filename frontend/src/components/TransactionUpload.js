import React, { useState } from "react";

function TransactionUpload({ onSuccess, onUploadSuccess }) {
  const [file, setFile]         = useState(null);
  const [feedback, setFeedback] = useState({ message: "", type: "" });
  const [uploading, setUploading] = useState(false);
  const [simulateTime, setSimulateTime] = useState(false);

  function clearState() {
    setFile(null);
    setFeedback({ message: "", type: "" });
    setSimulateTime(false);
  }

  function handleFileChange(e) {
    setFile(e.target.files[0] ?? null);
    setFeedback({ message: "", type: "" });
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) {
      setFeedback({ type: "error", message: "Please select a CSV file." });
      return;
    }
    if (!file.name.endsWith(".csv")) {
      setFeedback({ type: "error", message: "Only .csv files are accepted." });
      return;
    }
    setFeedback({ message: "", type: "" });
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("simulate_time", simulateTime ? "true" : "false");
      const response = await fetch("/api/transactions/process", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        setFeedback({ type: "error", message: data.error ?? "Upload failed. Please try again." });
      } else {
        const unresolved = Array.isArray(data.unresolved_amounts) ? data.unresolved_amounts : [];
        const unresolvedSuffix = unresolved.length > 0
          ? ` ${unresolved.length} unresolved amount(s): ${unresolved.join(", ")}.`
          : "";

        setFeedback({
          type: "success",
          message: `✓ ${data.processed_count} transaction(s) processed.${unresolvedSuffix}`,
        });
        await onSuccess?.();
        onUploadSuccess?.();
      }
    } catch (err) {
      setFeedback({ type: "error", message: "Network error. Is the backend running?" });
    } finally {
      setUploading(false);
    }
  }

  return (
    <form onSubmit={handleUpload}>
      <div className="mb-3">
        <input
          className="form-control"
          type="file"
          accept=".csv"
          aria-label="Transaction CSV file"
          onChange={handleFileChange}
        />
      </div>

      <div className="form-check mb-3">
        <input
          id="simulate-time-mode"
          className="form-check-input"
          type="checkbox"
          checked={simulateTime}
          onChange={(e) => setSimulateTime(e.target.checked)}
          disabled={uploading}
        />
        <label className="form-check-label" htmlFor="simulate-time-mode">
          Historical replay mode
        </label>
      </div>

      <div className="btn-row">
        <button
          type="submit"
          className="btn primary"
          disabled={uploading}
        >
          {uploading ? "Processing…" : "Upload & Process"}
        </button>
        <button
          type="button"
          className="btn"
          disabled={uploading}
          onClick={clearState}
        >
          Clear
        </button>
      </div>

      {feedback.message ? (
        <div className={`csv-feedback ${feedback.type === "success" ? "success" : "error"}`}>
          {feedback.message}
        </div>
      ) : null}
    </form>
  );
}

export default TransactionUpload;