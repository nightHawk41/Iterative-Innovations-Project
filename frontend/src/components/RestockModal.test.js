import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import RestockModal from "./RestockModal";
import { showToast } from "../utils/toast";

jest.mock("../utils/toast", () => ({
  showToast: jest.fn(),
}));

const slots = [
  {
    slot_id: "A1",
    item_name: "Bic Comfort Pens",
    quantity: 8,
    price: 8.5,
    expiration_date: "2026-12-01",
    days_until_expiry: 60,
    status_color: "green",
  },
  {
    slot_id: "A2",
    item_name: "Trail Mix",
    quantity: 4,
    price: 2.35,
    expiration_date: "2026-12-01",
    days_until_expiry: 45,
    status_color: "yellow",
  },
];

function renderRestockModal(overrides = {}) {
  const props = {
    show: true,
    onHide: jest.fn(),
    slots,
    onRestockSuccess: jest.fn().mockResolvedValue(undefined),
    ...overrides,
  };

  render(<RestockModal {...props} />);
  return props;
}

describe("RestockModal", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("shows live slot options with current stock levels", () => {
    renderRestockModal();

    expect(
      screen.getByRole("option", { name: "A1 — Bic Comfort Pens (Current: 8/10)" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: "A2 — Trail Mix (Current: 4/10)" })
    ).toBeInTheDocument();
  });

  it("uses a dynamic max quantity based on the selected slot", async () => {
    renderRestockModal();

    await userEvent.selectOptions(screen.getByLabelText("Slot ID"), "A1");
    const quantityInput = screen.getByLabelText("Quantity Added");

    await userEvent.type(quantityInput, "3");
    fireEvent.blur(quantityInput);

    expect(await screen.findByText("Quantity cannot exceed 2.")).toBeInTheDocument();
  });

  it("sends the exact POST body and triggers refresh and toast on success", async () => {
    const props = renderRestockModal();
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ message: "Restock successful" }),
    });

    await userEvent.selectOptions(screen.getByLabelText("Slot ID"), "A1");
    await userEvent.type(screen.getByLabelText("Quantity Added"), "2");
    await userEvent.type(screen.getByLabelText("Expiration Date"), "2026-12-01");

    await userEvent.click(screen.getByRole("button", { name: "Restock" }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/api/restock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slot_id: "A1",
          quantity_added: 2,
          expiration_date: "2026-12-01",
        }),
      });
    });

    await waitFor(() => {
      expect(props.onHide).toHaveBeenCalled();
      expect(props.onRestockSuccess).toHaveBeenCalled();
      expect(showToast).toHaveBeenCalledWith("✓ Slot A1 restocked successfully.");
    });
  });

  it("shows the API error inline on HTTP 400", async () => {
    renderRestockModal();
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ error: "Cannot exceed maximum capacity of 10. You can only add up to 2 more items." }),
    });

    await userEvent.selectOptions(screen.getByLabelText("Slot ID"), "A2");
    await userEvent.clear(screen.getByLabelText("Quantity Added"));
    await userEvent.type(screen.getByLabelText("Quantity Added"), "5");
    await userEvent.type(screen.getByLabelText("Expiration Date"), "2026-12-01");

    await userEvent.click(screen.getByRole("button", { name: "Restock" }));

    expect(
      await screen.findByText("Cannot exceed maximum capacity of 10. You can only add up to 2 more items.")
    ).toBeInTheDocument();
  });

  it("shows the fixed concurrency message on HTTP 409", async () => {
    renderRestockModal();
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: async () => ({ error: "backend conflict" }),
    });

    await userEvent.selectOptions(screen.getByLabelText("Slot ID"), "A2");
    await userEvent.clear(screen.getByLabelText("Quantity Added"));
    await userEvent.type(screen.getByLabelText("Quantity Added"), "1");
    await userEvent.type(screen.getByLabelText("Expiration Date"), "2026-12-01");

    await userEvent.click(screen.getByRole("button", { name: "Restock" }));

    expect(
      await screen.findByText("This slot was recently modified. Please try again.")
    ).toBeInTheDocument();
  });
});