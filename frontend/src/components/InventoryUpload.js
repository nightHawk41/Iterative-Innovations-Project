import React, { useRef, useState } from "react";
import { showToast } from "../utils/toast";

function InventoryUpload({ onInventoryUpdated }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [readyToApply, setReadyToApply] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [applying, setApplying] = useState(false);

  function resetPanel() {
    setFile(null);
    setFeedback(null);
    setReadyToApply(false);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  function handleFileChange(event) {
    setFile(event.target.files[0] ?? null);
    setFeedback(null);
    setReadyToApply(false);
  }

  async function handleUpload(event) {
    event.preventDefault();

    if (!file) {
      setFeedback({ type: "error", message: "Please select a CSV file." });
      setReadyToApply(false);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setFeedback({ type: "error", message: "Only .csv files are accepted." });
      setReadyToApply(false);
      return;
    }

    setUploading(true);
    setFeedback(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/inventory/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) {
        setFeedback({ type: "error", message: data.error ?? "Upload failed. Please try again." });
        setReadyToApply(false);
        return;
      }

      setFeedback({
        type: "success",
        message: `✓ ${data.total_rows} slot(s) ready to update.`,
      });
      setReadyToApply(true);
    } catch (error) {
      setFeedback({ type: "error", message: "Network error. Is the backend running?" });
      setReadyToApply(false);
    } finally {
      setUploading(false);
    }
  }

  async function handleApply() {
    if (!readyToApply) {
      return;
    }

    setApplying(true);

    try {
      const response = await fetch("/api/inventory/apply", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });
      const data = await response.json();

      if (!response.ok) {
        setFeedback({ type: "error", message: data.error ?? "Inventory update failed. Please try again." });
        setReadyToApply(false);
        return;
      }

      showToast("✓ Inventory updated.");
      await onInventoryUpdated?.();
      resetPanel();
    } catch (error) {
      setFeedback({ type: "error", message: "Network error. Is the backend running?" });
      setReadyToApply(false);
    } finally {
      setApplying(false);
    }
  }

  return (
    <div className="card mt-4">
      <div className="card-header fw-semibold">Upload New Inventory CSV</div>
      <div className="card-body">
        <div className="small text-muted mb-3">
          <div><strong>Required:</strong> ROW, Product, Vending Price</div>
          <div><strong>Optional:</strong> stock (integer 0–10), expiration_date (YYYY-MM-DD)</div>
        </div>

        <form onSubmit={handleUpload}>
          <div className="mb-3">
            <input
              ref={inputRef}
              className="form-control"
              type="file"
              accept=".csv"
              aria-label="Inventory CSV file"
              onChange={handleFileChange}
            />
          </div>

          <div className="d-flex gap-2 mb-3">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={uploading || applying}
            >
              {uploading ? "Processing…" : "Upload & Process"}
            </button>
            <button
              type="button"
              className="btn btn-outline-secondary"
              disabled={uploading || applying}
              onClick={resetPanel}
            >
              Clear
            </button>
          </div>

          {feedback && (
            <div className={`alert py-2 ${feedback.type === "success" ? "alert-success" : "alert-danger"}`}>
              {feedback.message}
            </div>
          )}

          <hr />

          <button
            type="button"
            className="btn btn-primary"
            disabled={!readyToApply || uploading || applying}
            onClick={handleApply}
          >
            {applying ? "Updating…" : "Update Inventory"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default InventoryUpload;