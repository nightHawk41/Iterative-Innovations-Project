import React from "react";
import InventoryGrid from "../components/InventoryGrid";
import mockInventory from "../data/mockInventory";

function DashboardPage() {
  return (
    <div>
      <h2 className="mb-4">Inventory Dashboard</h2>
      <InventoryGrid slots={mockInventory} />
    </div>
  );
}

export default DashboardPage;