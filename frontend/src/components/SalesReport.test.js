import { generateSalesReport } from "../utils/generateSalesReport";
import { showToast } from "../utils/toast";

jest.mock("../utils/toast", () => ({
  showToast: jest.fn(),
}));

describe("SalesReport", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("fetches report data and opens a popup window on success", async () => {
    const documentWrite = jest.fn();
    const documentClose = jest.fn();
    const openSpy = jest.spyOn(window, "open").mockReturnValue({
      document: {
        write: documentWrite,
        close: documentClose,
      },
    });

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        generated_at: "2026-04-23T14:30:00Z",
        source: "transaction_log",
        date_range: { start: "2026-03-10T00:00:00Z", end: "2026-03-17T00:00:00Z" },
        total_revenue: 87.5,
        total_units: 42,
        unique_items: 1,
        unresolved_count: 0,
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

    const ok = await generateSalesReport();

    expect(ok).toBe(true);
    expect(global.fetch).toHaveBeenCalledWith("/api/reports/sales");
    expect(openSpy).toHaveBeenCalled();
    expect(documentWrite).toHaveBeenCalledTimes(1);
    const html = documentWrite.mock.calls[0][0];
    expect(html).toContain("| Sales Report");
    expect(html).toContain("downloadCSV()");
    expect(html).toContain("window.close()");
    expect(html).toContain("Total Revenue");
    expect(html).toContain("copyCSV()");
    expect(html).toContain("Copy CSV");
    expect(html).not.toContain("transaction(s) could not be matched");
    expect(documentClose).toHaveBeenCalledTimes(1);

    openSpy.mockRestore();
  });

  it("shows unresolved warning block when unresolved_count is greater than zero", async () => {
    const documentWrite = jest.fn();
    const documentClose = jest.fn();
    const openSpy = jest.spyOn(window, "open").mockReturnValue({
      document: {
        write: documentWrite,
        close: documentClose,
      },
    });

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        generated_at: "2026-04-23T14:30:00Z",
        date_range: { start: "2026-03-10T00:00:00Z", end: "2026-03-17T00:00:00Z" },
        total_revenue: 99.99,
        total_units: 1,
        unique_items: 1,
        unresolved_count: 1,
        top_item: null,
        items: [
          {
            rank: 1,
            slot_id: "Unknown",
            item_name: "Unresolved ($99.99)",
            units_sold: 1,
            total_revenue: 99.99,
            avg_price: 99.99,
          },
        ],
      }),
    });

    const ok = await generateSalesReport();

    expect(ok).toBe(true);
    const html = documentWrite.mock.calls[0][0];
    expect(html).toContain("unresolved-warning");
    expect(html).toContain("1 transaction(s) could not be matched");

    openSpy.mockRestore();
  });

  it("shows toast with API error message on HTTP failure", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "Sales data unavailable." }),
    });

    const ok = await generateSalesReport();

    expect(ok).toBe(false);
    expect(showToast).toHaveBeenCalledWith("Sales data unavailable.");
  });

  it("shows toast on network failure", async () => {
    global.fetch.mockRejectedValueOnce(new Error("Network down"));

    const ok = await generateSalesReport();

    expect(ok).toBe(false);
    expect(showToast).toHaveBeenCalledWith("Network down");
  });
});