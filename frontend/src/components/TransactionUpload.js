import React, { useState } from "react";

function TransactionUpload({ onReportReady }) {
  const [file, setFile]         = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [uploading, setUploading] = useState(false);

  function handleFileChange(e) {
    setFile(e.target.files[0] ?? null);
    setFeedback(null);
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
    setFeedback(null);
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch("/api/transactions/process", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        onReportReady?.(false);
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
        onReportReady?.(true);
      }
    } catch (err) {
      onReportReady?.(false);
      setFeedback({ type: "error", message: "Network error. Is the backend running?" });
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="card mt-4">
      <div className="card-header fw-semibold">Upload Transaction CSV</div>
      <div className="card-body">
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
          {feedback && (
            <div className={`alert py-2 ${feedback.type === "success" ? "alert-success" : "alert-danger"}`}>
              {feedback.message}
            </div>
          )}
          <button
            type="submit"
            className="btn btn-outline-primary"
            disabled={uploading}
          >
            {uploading ? "Processing…" : "Upload & Process"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default TransactionUpload;