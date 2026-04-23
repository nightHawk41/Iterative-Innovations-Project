import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import SlotCard from "./SlotCard";

describe("SlotCard", () => {
  it("calls onSelect when an active slot is clicked", async () => {
    const handleSelect = jest.fn();

    render(
      <SlotCard
        slot_id="A1"
        item_name="Granola Bar"
        quantity={8}
        price={2.15}
        days_until_expiry={10}
        status_color="green"
        onSelect={handleSelect}
      />
    );

    await userEvent.click(screen.getByRole("button"));
    expect(handleSelect).toHaveBeenCalledTimes(1);
  });

  it("does nothing when a disabled slot is clicked", async () => {
    const handleSelect = jest.fn();

    render(
      <SlotCard
        slot_id="A1"
        item_name="Granola Bar"
        quantity={0}
        price={2.15}
        days_until_expiry={10}
        status_color="red"
        onSelect={handleSelect}
      />
    );

    await userEvent.click(screen.getByText("Granola Bar"));
    expect(handleSelect).not.toHaveBeenCalled();
  });
});