import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import Sidebar from "./Sidebar";
import { showToast } from "../utils/toast";

jest.mock("../utils/toast", () => ({
  showToast: jest.fn(),
}));

describe("Sidebar", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("enables the Generate Sales Report button after a successful transaction CSV upload", async () => {
    const onTransactionAdded = jest.fn();

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        processed_count: 24,
        updated_slots: [],
        unresolved_amounts: [],
      }),
    });

    const { rerender } = render(
      <Sidebar
        activeTab="admin"
        setActiveTab={jest.fn()}
        slots={[]}
        onInventoryChange={jest.fn()}
        hasTransactions={false}
        onTransactionAdded={onTransactionAdded}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "Upload CBORD Transactions" }));

    const reportButton = screen.getByRole("button", { name: /Generate Sales Report/ });
    expect(reportButton).toBeDisabled();

    const file = new File(["header\nvalue"], "transactions.csv", { type: "text/csv" });
    await userEvent.upload(screen.getByLabelText("Transaction CSV file"), file);

    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    await waitFor(() => {
      expect(onTransactionAdded).toHaveBeenCalledTimes(1);
    });

    rerender(
      <Sidebar
        activeTab="admin"
        setActiveTab={jest.fn()}
        slots={[]}
        onInventoryChange={jest.fn()}
        hasTransactions={true}
        onTransactionAdded={onTransactionAdded}
      />
    );

    expect(screen.getByRole("button", { name: /Generate Sales Report/ })).toBeEnabled();
  });

  it("calls GET /api/reports/sales and opens a report window when Generate Sales Report is clicked", async () => {
    const popup = {
      document: {
        write: jest.fn(),
        close: jest.fn(),
      },
    };
    const openSpy = jest.spyOn(window, "open").mockReturnValue(popup);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        generated_at: "2026-04-23T14:30:00Z",
        source: "transaction_log",
        date_range: { start: "2026-03-10T00:00:00Z", end: "2026-03-17T00:00:00Z" },
        total_revenue: 87.5,
        total_units: 42,
        unique_items: 1,
        top_item: {
          item_name: "Soda",
          slot_id: "A1",
          units: 12,
          revenue: 24,
        },
        items: [
          {
            rank: 1,
            slot_id: "A1",
            item_name: "Soda",
            units_sold: 12,
            total_revenue: 24,
            avg_price: 2,
          },
        ],
      }),
    });

    render(
      <Sidebar
        activeTab="admin"
        setActiveTab={jest.fn()}
        slots={[]}
        onInventoryChange={jest.fn()}
        hasTransactions={true}
        onTransactionAdded={jest.fn()}
      />
    );

    const reportButton = screen.getByRole("button", { name: /Generate Sales Report/ });
    expect(reportButton).toBeEnabled();

    await userEvent.click(reportButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/api/reports/sales");
      expect(openSpy).toHaveBeenCalled();
      expect(popup.document.write).toHaveBeenCalledTimes(1);
    });

    openSpy.mockRestore();
  });

  it("shows an error toast when report generation API fails", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "Report failed." }),
    });

    render(
      <Sidebar
        activeTab="admin"
        setActiveTab={jest.fn()}
        slots={[]}
        onInventoryChange={jest.fn()}
        hasTransactions={true}
        onTransactionAdded={jest.fn()}
      />
    );

    const reportButton = screen.getByRole("button", { name: /Generate Sales Report/ });
    expect(reportButton).toBeEnabled();

    await userEvent.click(reportButton);

    await waitFor(() => {
      expect(showToast).toHaveBeenCalledWith("Report failed.");
    });
  });

  it("renders the inventory upload panel in the admin sidebar", async () => {
    render(
      <Sidebar
        activeTab="admin"
        setActiveTab={jest.fn()}
        slots={[]}
        onInventoryChange={jest.fn()}
        hasTransactions={false}
        onTransactionAdded={jest.fn()}
      />
    );

    expect(screen.getByRole("button", { name: "Upload New Inventory" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Upload New Inventory" }));
    expect(screen.getByRole("button", { name: /Update Inventory/ })).toBeDisabled();
  });

  it("allows opening multiple admin accordion panels and updates toggle arrows", async () => {
    render(
      <Sidebar
        activeTab="admin"
        setActiveTab={jest.fn()}
        slots={[]}
        onInventoryChange={jest.fn()}
        hasTransactions={false}
        onTransactionAdded={jest.fn()}
      />
    );

    const restockHeader = screen.getByRole("button", { name: /\+ Manual Restock/ });
    const transactionHeader = screen.getByRole("button", { name: /Upload CBORD Transactions/ });

    expect(restockHeader).toHaveTextContent("▸");
    expect(transactionHeader).toHaveTextContent("▸");
    expect(screen.queryByLabelText("Slot ID")).not.toBeInTheDocument();

    await userEvent.click(restockHeader);
    expect(restockHeader).toHaveTextContent("▾");
    expect(screen.getByLabelText("Slot ID")).toBeInTheDocument();
    expect(screen.getByLabelText("Qty Added")).toBeInTheDocument();
    expect(screen.getByLabelText("Exp Date")).toBeInTheDocument();

    await userEvent.click(transactionHeader);
    expect(transactionHeader).toHaveTextContent("▾");
    expect(restockHeader).toHaveTextContent("▾");
    expect(screen.getByLabelText("Slot ID")).toBeInTheDocument();
    expect(screen.getByLabelText("Transaction CSV file")).toBeInTheDocument();
  });

  it("computes dashboard stat cards from slot thresholds (not status_color)", () => {
    render(
      <Sidebar
        activeTab="dashboard"
        setActiveTab={jest.fn()}
        slots={[
          { slot_id: "A1", quantity: 8, days_until_expiry: 10, status_color: "red" },
          { slot_id: "A2", quantity: 4, days_until_expiry: 9, status_color: "green" },
          { slot_id: "A3", quantity: 2, days_until_expiry: 9, status_color: "green" },
          { slot_id: "A4", quantity: 7, days_until_expiry: 0, status_color: "green" },
        ]}
        onInventoryChange={jest.fn()}
      />
    );

    expect(screen.getByText("Total Slots").nextSibling).toHaveTextContent("4");
    expect(screen.getByText("Healthy").nextSibling).toHaveTextContent("1");
    expect(screen.getByText("Low / Expiring").nextSibling).toHaveTextContent("1");
    expect(screen.getByText("Critical / Out").nextSibling).toHaveTextContent("2");
  });

  it("calls onInventoryChange when Reload is clicked", async () => {
    const onInventoryChange = jest.fn();

    render(
      <Sidebar
        activeTab="dashboard"
        setActiveTab={jest.fn()}
        slots={[]}
        onInventoryChange={onInventoryChange}
        hasTransactions={false}
        onTransactionAdded={jest.fn()}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "Reload" }));
    expect(onInventoryChange).toHaveBeenCalledTimes(1);
  });

  it("opens the help window when Help is clicked", async () => {
    const popup = {
      document: {
        write: jest.fn(),
        close: jest.fn(),
      },
    };
    const openSpy = jest.spyOn(window, "open").mockReturnValue(popup);

    render(
      <Sidebar
        activeTab="dashboard"
        setActiveTab={jest.fn()}
        slots={[]}
        onInventoryChange={jest.fn()}
        hasTransactions={false}
        onTransactionAdded={jest.fn()}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "Help" }));

    expect(openSpy).toHaveBeenCalledTimes(1);
    expect(popup.document.write).toHaveBeenCalledTimes(1);
    expect(popup.document.close).toHaveBeenCalledTimes(1);

    openSpy.mockRestore();
  });
});