import React, { useRef, useState } from "react";
import { showToast } from "../utils/toast";

function InventoryUpload({ onSuccess }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [feedback, setFeedback] = useState({ message: "", type: "" });
  const [updateEnabled, setUpdateEnabled] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [applying, setApplying] = useState(false);

  function resetPanel() {
    setFile(null);
    setFeedback({ message: "", type: "" });
    setUpdateEnabled(false);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  function handleFileChange(event) {
    setFile(event.target.files[0] ?? null);
    setFeedback({ message: "", type: "" });
    setUpdateEnabled(false);
  }

  async function handleUpload(event) {
    event.preventDefault();

    if (!file) {
      setFeedback({ type: "error", message: "Please select a CSV file." });
      setUpdateEnabled(false);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setFeedback({ type: "error", message: "Only .csv files are accepted." });
      setUpdateEnabled(false);
      return;
    }

    setUploading(true);
    setFeedback({ message: "", type: "" });

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
        setUpdateEnabled(false);
        return;
      }

      setFeedback({
        type: "success",
        message: `✓ ${data.total_rows} slot(s) ready to update.`,
      });
      setUpdateEnabled(true);
    } catch (error) {
      setFeedback({ type: "error", message: "Network error. Is the backend running?" });
      setUpdateEnabled(false);
    } finally {
      setUploading(false);
    }
  }

  async function handleApply() {
    if (!updateEnabled) {
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
        showToast(data.error ?? "Inventory update failed. Please try again.");
        return;
      }

      showToast("✓ Inventory updated.");
      await onSuccess?.();
      resetPanel();
    } catch (error) {
      showToast("Network error. Is the backend running?");
    } finally {
      setApplying(false);
    }
  }

  return (
    <form onSubmit={handleUpload}>
      <div className="csv-hint">
        <div><strong>Required:</strong> ROW, Product, Vending Price</div>
        <div><strong>Optional:</strong> stock (integer 0-10), expiration_date (YYYY-MM-DD)</div>
      </div>

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

      <div className="btn-row">
        <button
          type="submit"
          className="btn primary"
          disabled={uploading || applying}
        >
          {uploading ? "Processing…" : "Upload & Process"}
        </button>
        <button
          type="button"
          className="btn"
          disabled={uploading || applying}
          onClick={resetPanel}
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
        disabled={!updateEnabled || uploading || applying}
        onClick={handleApply}
      >
        {applying ? "Updating..." : "Update Inventory"}
      </button>
    </form>
  );
}

export default InventoryUpload;