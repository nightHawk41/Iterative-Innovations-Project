import { buildSalesReportHtml, generateSalesReport } from "./SalesReport";

describe("SalesReport", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("builds report HTML with required sections", () => {
    const html = buildSalesReportHtml({
      generated_at: "2026-04-23T14:30:00Z",
      source: "transaction_log",
      date_range: "3/10/2026 – 3/17/2026",
      total_revenue: 87.5,
      total_units: 42,
      unique_items: 8,
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
    });

    expect(html).toContain("Sales Report");
    expect(html).toContain("⬇ Download CSV");
    expect(html).toContain("✕ Close");
    expect(html).toContain("Total Revenue");
    expect(html).toContain("Units Sold");
    expect(html).toContain("Unique Items");
    expect(html).toContain("Top Selling Item");
    expect(html).toContain("Sales Breakdown by Item");
    expect(html).toContain("Rank,Slot ID,Item Name,Units Sold,Total Revenue,Avg Price");
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
            average_price: 2,
          },
        ],
      }),
    });

    const ok = await generateSalesReport({ onError: jest.fn() });

    expect(ok).toBe(true);
    expect(global.fetch).toHaveBeenCalledWith("/api/reports/sales");
    expect(openSpy).toHaveBeenCalled();
    expect(documentWrite).toHaveBeenCalledTimes(1);
    expect(documentWrite.mock.calls[0][0]).toContain("UMBC Vending — Sales Report");
    expect(documentClose).toHaveBeenCalledTimes(1);

    openSpy.mockRestore();
  });

  it("calls onError with API error message on HTTP failure", async () => {
    const onError = jest.fn();

    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "Sales data unavailable." }),
    });

    const ok = await generateSalesReport({ onError });

    expect(ok).toBe(false);
    expect(onError).toHaveBeenCalledWith("Sales data unavailable.");
  });
});