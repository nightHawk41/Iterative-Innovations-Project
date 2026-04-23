import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import InventoryUpload from "./InventoryUpload";
import { showToast } from "../utils/toast";

jest.mock("../utils/toast", () => ({
  showToast: jest.fn(),
}));

describe("InventoryUpload", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("restricts the file input to .csv and keeps Update Inventory disabled by default", () => {
    render(<InventoryUpload onInventoryUpdated={jest.fn()} />);

    expect(screen.getByLabelText("Inventory CSV file")).toHaveAttribute("accept", ".csv");
    expect(screen.getByRole("button", { name: "Update Inventory" })).toBeDisabled();
  });

  it("uploads the csv with FormData field name file and enables Update Inventory on success", async () => {
    render(<InventoryUpload onInventoryUpdated={jest.fn()} />);

    global.fetch.mockImplementationOnce(async (url, options) => {
      expect(url).toBe("/api/inventory/upload");
      expect(options.method).toBe("POST");
      expect(options.body).toBeInstanceOf(FormData);
      expect(options.body.get("file").name).toBe("inventory.csv");

      return {
        ok: true,
        json: async () => ({
          added: 0,
          updated: 24,
          skipped: 0,
          total_rows: 24,
        }),
      };
    });

    const file = new File(["ROW,Product,Vending Price\nA1,Snack,2.50"], "inventory.csv", {
      type: "text/csv",
    });

    await userEvent.upload(screen.getByLabelText("Inventory CSV file"), file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    expect(await screen.findByText("✓ 24 slot(s) ready to update.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Update Inventory" })).toBeEnabled();
  });

  it("calls apply, refreshes inventory, shows a toast, and resets the panel", async () => {
    const onInventoryUpdated = jest.fn().mockResolvedValue([]);

    render(<InventoryUpload onInventoryUpdated={onInventoryUpdated} />);

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          added: 0,
          updated: 24,
          skipped: 0,
          total_rows: 24,
        }),
      })
      .mockImplementationOnce(async (url, options) => {
        expect(url).toBe("/api/inventory/apply");
        expect(options.method).toBe("POST");
        expect(options.headers).toEqual({ "Content-Type": "application/json" });
        expect(options.body).toBe("{}");

        return {
          ok: true,
          json: async () => ({ message: "Inventory updated." }),
        };
      });

    const fileInput = screen.getByLabelText("Inventory CSV file");
    const file = new File(["ROW,Product,Vending Price\nA1,Snack,2.50"], "inventory.csv", {
      type: "text/csv",
    });

    await userEvent.upload(fileInput, file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Update Inventory" })).toBeEnabled();
    });

    await userEvent.click(screen.getByRole("button", { name: "Update Inventory" }));

    await waitFor(() => {
      expect(onInventoryUpdated).toHaveBeenCalledTimes(1);
    });

    expect(showToast).toHaveBeenCalledWith("✓ Inventory updated.");
    expect(screen.getByRole("button", { name: "Update Inventory" })).toBeDisabled();
    expect(fileInput).toHaveValue("");
    expect(screen.queryByText("✓ 24 slot(s) ready to update.")).not.toBeInTheDocument();
  });

  it("clear resets the selected file, feedback, and update button state", async () => {
    render(<InventoryUpload onInventoryUpdated={jest.fn()} />);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        added: 0,
        updated: 24,
        skipped: 0,
        total_rows: 24,
      }),
    });

    const fileInput = screen.getByLabelText("Inventory CSV file");
    const file = new File(["ROW,Product,Vending Price\nA1,Snack,2.50"], "inventory.csv", {
      type: "text/csv",
    });

    await userEvent.upload(fileInput, file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));
    expect(await screen.findByText("✓ 24 slot(s) ready to update.")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Clear" }));

    expect(fileInput).toHaveValue("");
    expect(screen.queryByText("✓ 24 slot(s) ready to update.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Update Inventory" })).toBeDisabled();
  });

  it("shows the API error inline and keeps Update Inventory disabled", async () => {
    render(<InventoryUpload onInventoryUpdated={jest.fn()} />);

    global.fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "CSV schema invalid." }),
    });

    const file = new File(["bad"], "inventory.csv", { type: "text/csv" });
    await userEvent.upload(screen.getByLabelText("Inventory CSV file"), file);
    await userEvent.click(screen.getByRole("button", { name: "Upload & Process" }));

    expect(await screen.findByText("CSV schema invalid.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Update Inventory" })).toBeDisabled();
  });
});