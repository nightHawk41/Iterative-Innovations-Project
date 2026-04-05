import React, { useState } from "react";

function TransactionUpload() {
  const [file, setFile]         = useState(null);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState(null);
  const [uploading, setUploading] = useState(false);

  function handleFileChange(e) {
    setFile(e.target.files[0] ?? null);
    setResult(null);
    setError(null);
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) {
      setError("Please select a CSV file.");
      return;
    }
    if (!file.name.endsWith(".csv")) {
      setError("Only .csv files are accepted.");
      return;
    }
    setError(null);
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
        setError(data.error ?? "Upload failed. Please try again.");
      } else {
        setResult(data);
      }
    } catch (err) {
      setError("Network error. Is the backend running?");
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
              onChange={handleFileChange}
            />
          </div>
          {error && <div className="alert alert-danger py-2">{error}</div>}
          {result && (
            <div className="alert alert-success py-2">
              Processed <strong>{result.processed_count}</strong> transactions.
              {result.unresolved_amounts?.length > 0 && (
                <span className="ms-2 text-warning">
                  Unresolved amounts: {result.unresolved_amounts.join(", ")}
                </span>
              )}
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