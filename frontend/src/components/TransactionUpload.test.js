import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import TransactionUpload from "./TransactionUpload";

describe("TransactionUpload", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("restricts the file input to .csv", () => {
    render(<TransactionUpload onReportReady={jest.fn()} />);

    expect(screen.getByLabelText("Transaction CSV file")).toHaveAttribute("accept", ".csv");
  });

  it("shows an inline error when upload is clicked with no file", async () => {
    render(<TransactionUpload onReportReady={jest.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    expect(screen.getByText("Please select a CSV file.")).toBeInTheDocument();
  });

  it("sends the file as FormData with field name file and shows success with unresolved amounts", async () => {
    const onReportReady = jest.fn();
    render(<TransactionUpload onReportReady={onReportReady} />);

    global.fetch.mockImplementationOnce(async (url, options) => {
      expect(url).toBe("/api/transactions/process");
      expect(options.method).toBe("POST");
      expect(options.body).toBeInstanceOf(FormData);
      expect(options.body.get("file").name).toBe("transactions.csv");

      return {
        ok: true,
        json: async () => ({
          processed_count: 24,
          updated_slots: [],
          unresolved_amounts: [1.99, 4.5],
        }),
      };
    });

    const file = new File(["header\nvalue"], "transactions.csv", { type: "text/csv" });
    await userEvent.upload(screen.getByLabelText("Transaction CSV file"), file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    await waitFor(() => {
      expect(
        screen.getByText("✓ 24 transaction(s) processed. 2 unresolved amount(s): 1.99, 4.5.")
      ).toBeInTheDocument();
    });

    expect(onReportReady).toHaveBeenCalledWith(true);
  });

  it("shows the API error text inline on HTTP 400 or 500", async () => {
    const onReportReady = jest.fn();
    render(<TransactionUpload onReportReady={onReportReady} />);

    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "CSV schema invalid." }),
    });

    const file = new File(["header\nvalue"], "transactions.csv", { type: "text/csv" });
    await userEvent.upload(screen.getByLabelText("Transaction CSV file"), file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    expect(await screen.findByText("CSV schema invalid.")).toBeInTheDocument();
    expect(onReportReady).toHaveBeenCalledWith(false);
  });

  it("shows the network error message inline", async () => {
    const onReportReady = jest.fn();
    render(<TransactionUpload onReportReady={onReportReady} />);

    global.fetch.mockRejectedValueOnce(new Error("network"));

    const file = new File(["header\nvalue"], "transactions.csv", { type: "text/csv" });
    await userEvent.upload(screen.getByLabelText("Transaction CSV file"), file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    expect(await screen.findByText("Network error. Is the backend running?")).toBeInTheDocument();
    expect(onReportReady).toHaveBeenCalledWith(false);
  });
});