import React, { useState } from "react";
import { generateSalesReport } from "./SalesReport";
import { showToast } from "../utils/toast";

function TransactionUpload({ onSuccess }) {
  const [file, setFile]         = useState(null);
  const [feedback, setFeedback] = useState({ message: "", type: "" });
  const [reportEnabled, setReportEnabled] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  function clearState() {
    setFile(null);
    setFeedback({ message: "", type: "" });
    setReportEnabled(false);
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
      const response = await fetch("/api/transactions/process", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        setReportEnabled(false);
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
        setReportEnabled(true);
        await onSuccess?.();
      }
    } catch (err) {
      setReportEnabled(false);
      setFeedback({ type: "error", message: "Network error. Is the backend running?" });
    } finally {
      setUploading(false);
    }
  }

  async function handleGenerateSalesReport() {
    setReportLoading(true);
    await generateSalesReport({
      onError: (message) => showToast(message),
    });
    setReportLoading(false);
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

      <div className="btn-row">
        <button
          type="submit"
          className="btn primary"
          disabled={uploading || reportLoading}
        >
          {uploading ? "Processing…" : "Upload & Process"}
        </button>
        <button
          type="button"
          className="btn"
          disabled={uploading || reportLoading}
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

      <hr className="panel-divider" />

      <button
        type="button"
        className="full-width-btn"
        disabled={!reportEnabled || reportLoading}
        onClick={handleGenerateSalesReport}
      >
        {reportLoading ? "Generating…" : "Generate Sales Report"}
      </button>
    </form>
  );
}

export default TransactionUpload;