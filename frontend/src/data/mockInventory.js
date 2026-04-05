// Mock inventory — swap for live GET /api/inventory call in Task F-8 integration step.
// Status is derived from quantity vs thresholds and days_until_expiration.
// low_threshold = 3 (Red), warning_threshold = 5 (Yellow), else Green.

const mockInventory = [
  // --- Row A ---
  { slot_id: "A1", item_name: "Bic Comfort Pens",               quantity: 10, price: 8.50, expiration_date: "2026-12-01", days_until_expiration: 240, status: "Green" },
  { slot_id: "A2", item_name: "Starbucks Frappuccino Vanilla",   quantity: 4,  price: 3.50, expiration_date: "2026-04-20", days_until_expiration: 15,  status: "Yellow" },
  { slot_id: "A3", item_name: "Flash Drive",                     quantity: 8,  price: 5.01, expiration_date: "2027-06-01", days_until_expiration: 422, status: "Green" },
  { slot_id: "A4", item_name: "Dunkin Iced Coffee Mocha",        quantity: 2,  price: 3.55, expiration_date: "2026-04-10", days_until_expiration: 5,   status: "Red" },
  { slot_id: "A5", item_name: "4 Expo Dry Erase",                quantity: 6,  price: 8.02, expiration_date: "2027-01-01", days_until_expiration: 271, status: "Green" },
  // --- Row B ---
  { slot_id: "B1", item_name: "Zebra Z-Grip Black Pen 2 Pack",   quantity: 5,  price: 3.01, expiration_date: "2026-09-15", days_until_expiration: 163, status: "Yellow" },
  { slot_id: "B2", item_name: "Dunkin Glazed Donut (Packaged)",  quantity: 1,  price: 2.10, expiration_date: "2026-04-07", days_until_expiration: 2,   status: "Red" },
  { slot_id: "B3", item_name: "Post-It",                         quantity: 9,  price: 4.50, expiration_date: "2027-03-01", days_until_expiration: 330, status: "Green" },
  { slot_id: "B4", item_name: "Starbucks Cake Pop",              quantity: 3,  price: 2.25, expiration_date: "2026-04-12", days_until_expiration: 7,   status: "Yellow" },
  { slot_id: "B5", item_name: "Papermate Pencil Pack",           quantity: 7,  price: 8.03, expiration_date: "2027-02-01", days_until_expiration: 302, status: "Green" },
  // --- Row C ---
  { slot_id: "C1", item_name: "First Aid Kit",                   quantity: 2,  price: 5.02, expiration_date: "2026-04-08", days_until_expiration: 3,   status: "Red" },
  { slot_id: "C2", item_name: "Doritos Nacho Cheese",            quantity: 6,  price: 1.75, expiration_date: "2026-07-20", days_until_expiration: 106, status: "Green" },
  { slot_id: "C5", item_name: "AA Batteries",                    quantity: 4,  price: 6.50, expiration_date: "2026-05-01", days_until_expiration: 26,  status: "Yellow" },
  // --- Row D ---
  { slot_id: "D1", item_name: "Tissues",                         quantity: 8,  price: 1.00, expiration_date: "2027-01-15", days_until_expiration: 285, status: "Green" },
  { slot_id: "D4", item_name: "Snickers Bar",                    quantity: 0,  price: 1.50, expiration_date: "2026-06-01", days_until_expiration: 57,  status: "Red" },
];

export default mockInventory;