import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import DashboardPage from "./DashboardPage";

jest.mock("../components/AlertsBanner", () => function AlertsBanner() {
  return <div data-testid="alerts-banner" />;
});

jest.mock("../components/InventoryGrid", () => function InventoryGrid({ slots, onSlotSelect }) {
  return (
    <div data-testid="inventory-grid">
      <span data-testid="slot-count">{slots.length}</span>
      <span data-testid="slot-name">{slots[0]?.item_name || ""}</span>
      {slots.map((slot) => {
        const disabled = slot.quantity === 0 || slot.days_until_expiry < 0;
        return (
          <button
            key={slot.slot_id}
            type="button"
            onClick={() => {
              if (!disabled) {
                onSlotSelect?.(slot);
              }
            }}
          >
            {slot.slot_id}
          </button>
        );
      })}
    </div>
  );
});

const baseSlot = {
  slot_id: "A1",
  item_name: "Granola Bar",
  quantity: 8,
  price: 2.15,
  expiration_date: "2026-12-01",
  days_until_expiry: 60,
  status_color: "green",
};

describe("DashboardPage", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("stores and renders the API response array on successful fetch", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [baseSlot],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_slots: 1,
          healthy: 1,
          low_expiring: 0,
          critical_out: 0,
        }),
      });

    render(<DashboardPage />);

    expect(screen.getByText("Loading inventory…")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("slot-count")).toHaveTextContent("1");
    });

    expect(global.fetch).toHaveBeenCalledWith("/api/inventory");
    expect(global.fetch).toHaveBeenCalledWith("/api/inventory/summary");
    expect(screen.getByTestId("slot-name")).toHaveTextContent("Granola Bar");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("sets slots to empty and shows an error message when fetch fails", async () => {
    global.fetch.mockRejectedValueOnce(new Error("network"));

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Unable to load inventory. Please check that the backend is running."
    );
    expect(screen.getByTestId("slot-count")).toHaveTextContent("0");
    expect(screen.getByTestId("slot-name")).toHaveTextContent("");
  });

  it("opens the purchase modal with correct item details and confirms purchase successfully", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [baseSlot],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_slots: 1,
          healthy: 1,
          low_expiring: 0,
          critical_out: 0,
        }),
      })
      .mockResolvedValueOnce({
        status: 200,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ ...baseSlot, quantity: 7 }],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_slots: 1,
          healthy: 1,
          low_expiring: 0,
          critical_out: 0,
        }),
      });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("A1")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("A1"));

    expect(screen.getByText("Confirm Purchase")).toBeInTheDocument();
    expect(screen.getAllByText("Granola Bar")[1]).toBeInTheDocument();
    expect(screen.getByText(/Slot: A1/)).toBeInTheDocument();
    expect(screen.getByText(/Price: \$2.15/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/api/purchase", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ slot_id: "A1" }),
      });
    });

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("✓ Granola Bar dispensed!");
    });

    expect(global.fetch).toHaveBeenCalledWith("/api/inventory");
    expect(screen.queryByText("Confirm Purchase")).not.toBeInTheDocument();
  });

  it("shows an out of stock toast on HTTP 409", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [baseSlot],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_slots: 1,
          healthy: 1,
          low_expiring: 0,
          critical_out: 0,
        }),
      })
      .mockResolvedValueOnce({
        status: 409,
      });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("A1")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("A1"));
    await userEvent.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("This item is out of stock.");
    });
    expect(screen.queryByText("Confirm Purchase")).not.toBeInTheDocument();
  });

  it("shows an unavailable toast on HTTP 400", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [baseSlot],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_slots: 1,
          healthy: 1,
          low_expiring: 0,
          critical_out: 0,
        }),
      })
      .mockResolvedValueOnce({
        status: 400,
      });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("A1")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("A1"));
    await userEvent.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("This item is unavailable.");
    });
  });

  it("shows a network error toast when the purchase request fails", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [baseSlot],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_slots: 1,
          healthy: 1,
          low_expiring: 0,
          critical_out: 0,
        }),
      })
      .mockRejectedValueOnce(new Error("network"));

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("A1")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("A1"));
    await userEvent.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent("Network error. Is the backend running?");
    });
  });

  it("uses inventory summary endpoint values for stat cards", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          { ...baseSlot, status_color: "green" },
          { ...baseSlot, slot_id: "A2", status_color: "green" },
        ],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total_slots: 2,
          healthy: 0,
          low_expiring: 1,
          critical_out: 1,
        }),
      });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Total Slots")).toBeInTheDocument();
    });

    const totalLabel = screen.getByText("Total Slots");
    const healthyLabel = screen.getByText("Healthy");
    const warningLabel = screen.getByText("Low / Expiring");
    const criticalLabel = screen.getByText("Critical");

    await waitFor(() => {
      expect(totalLabel.previousSibling).toHaveTextContent("2");
      expect(healthyLabel.previousSibling).toHaveTextContent("0");
      expect(warningLabel.previousSibling).toHaveTextContent("1");
      expect(criticalLabel.previousSibling).toHaveTextContent("1");
    });
  });
});