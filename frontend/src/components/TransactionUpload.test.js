import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import TransactionUpload from "./TransactionUpload";
import { generateSalesReport } from "../utils/generateSalesReport";

jest.mock("../utils/generateSalesReport", () => ({
  generateSalesReport: jest.fn(),
}));

describe("TransactionUpload", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("restricts the file input to .csv", () => {
    render(<TransactionUpload onSuccess={jest.fn()} />);

    expect(screen.getByLabelText("Transaction CSV file")).toHaveAttribute("accept", ".csv");
    expect(screen.getByRole("button", { name: "Generate Sales Report" })).toBeDisabled();
  });

  it("shows an inline error when upload is clicked with no file", async () => {
    render(<TransactionUpload onSuccess={jest.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    expect(screen.getByText("Please select a CSV file.")).toBeInTheDocument();
  });

  it("sends the file as FormData with field name file and shows success with unresolved amounts", async () => {
    const onSuccess = jest.fn().mockResolvedValue(undefined);
    render(<TransactionUpload onSuccess={onSuccess} />);

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

    expect(onSuccess).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Generate Sales Report" })).toBeEnabled();
  });

  it("shows the API error text inline on HTTP 400 or 500", async () => {
    render(<TransactionUpload onSuccess={jest.fn()} />);

    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "CSV schema invalid." }),
    });

    const file = new File(["header\nvalue"], "transactions.csv", { type: "text/csv" });
    await userEvent.upload(screen.getByLabelText("Transaction CSV file"), file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    expect(await screen.findByText("CSV schema invalid.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate Sales Report" })).toBeDisabled();
  });

  it("shows the network error message inline", async () => {
    render(<TransactionUpload onSuccess={jest.fn()} />);

    global.fetch.mockRejectedValueOnce(new Error("network"));

    const file = new File(["header\nvalue"], "transactions.csv", { type: "text/csv" });
    await userEvent.upload(screen.getByLabelText("Transaction CSV file"), file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    expect(await screen.findByText("Network error. Is the backend running?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate Sales Report" })).toBeDisabled();
  });

  it("clear resets file input, feedback, and report button state", async () => {
    render(<TransactionUpload onSuccess={jest.fn()} />);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        processed_count: 2,
        updated_slots: [],
        unresolved_amounts: [],
      }),
    });

    const fileInput = screen.getByLabelText("Transaction CSV file");
    const file = new File(["header\nvalue"], "transactions.csv", { type: "text/csv" });
    await userEvent.upload(fileInput, file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    expect(await screen.findByText("✓ 2 transaction(s) processed.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate Sales Report" })).toBeEnabled();

    await userEvent.click(screen.getByRole("button", { name: "Clear" }));

    expect(fileInput).toHaveValue("");
    expect(screen.queryByText("✓ 2 transaction(s) processed.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generate Sales Report" })).toBeDisabled();
  });

  it("calls generateSalesReport when report button is enabled and clicked", async () => {
    generateSalesReport.mockResolvedValue(true);
    render(<TransactionUpload onSuccess={jest.fn()} />);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        processed_count: 1,
        updated_slots: [],
        unresolved_amounts: [],
      }),
    });

    const file = new File(["header\nvalue"], "transactions.csv", { type: "text/csv" });
    await userEvent.upload(screen.getByLabelText("Transaction CSV file"), file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Generate Sales Report" })).toBeEnabled();
    });

    await userEvent.click(screen.getByRole("button", { name: "Generate Sales Report" }));

    await waitFor(() => {
      expect(generateSalesReport).toHaveBeenCalledTimes(1);
    });
  });
});