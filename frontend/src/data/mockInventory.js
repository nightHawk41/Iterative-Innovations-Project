// Mock inventory — matches inventory_config.csv exactly (6 rows × 4 slots).
// Status rules (from ItemSlot model):
//   red:    quantity <= 3  OR  days_until_expiry <= 2
//   yellow: quantity <= 5  OR  days_until_expiry <= 5
//   green:  otherwise

const mockInventory = [
  // --- Row A ---
  { slot_id: "A1", item_name: "Bic Comfort Pens",              quantity: 10, price: 8.50,  expiration_date: "2026-12-01", days_until_expiry: 240, status_color: "green"  },
  { slot_id: "A2", item_name: "Starbucks Frappuccino Vanilla", quantity: 4,  price: 3.50,  expiration_date: "2026-07-01", days_until_expiry: 87,  status_color: "yellow" },
  { slot_id: "A3", item_name: "Flash Drive",                   quantity: 8,  price: 5.01,  expiration_date: "2027-06-01", days_until_expiry: 422, status_color: "green"  },
  { slot_id: "A4", item_name: "4 Expo Dry Erase",              quantity: 7,  price: 8.02,  expiration_date: "2026-04-10", days_until_expiry: 5,   status_color: "yellow" },

  // --- Row B ---
  { slot_id: "B1", item_name: "Zebra Z-Grip Black Pen 2 Pack", quantity: 9,  price: 3.01,  expiration_date: "2026-09-15", days_until_expiry: 163, status_color: "green"  },
  { slot_id: "B2", item_name: "Dunkin Glazed Donut (Packaged)",quantity: 2,  price: 2.10,  expiration_date: "2026-06-01", days_until_expiry: 57,  status_color: "red"    },
  { slot_id: "B3", item_name: "Post-It",                       quantity: 6,  price: 4.50,  expiration_date: "2027-03-01", days_until_expiry: 330, status_color: "green"  },
  { slot_id: "B4", item_name: "Papermate Pencil Pack",         quantity: 5,  price: 8.03,  expiration_date: "2026-05-01", days_until_expiry: 26,  status_color: "yellow" },

  // --- Row C ---
  { slot_id: "C1", item_name: "First Aid Kit",                 quantity: 1,  price: 5.02,  expiration_date: "2026-04-07", days_until_expiry: 2,   status_color: "red"    },
  { slot_id: "C2", item_name: "AA Batteries",                  quantity: 8,  price: 6.50,  expiration_date: "2026-07-20", days_until_expiry: 106, status_color: "green"  },
  { slot_id: "C3", item_name: "Index Cards",                   quantity: 5,  price: 3.03,  expiration_date: "2026-08-01", days_until_expiry: 118, status_color: "yellow" },
  { slot_id: "C4", item_name: "AAA Batteries",                 quantity: 7,  price: 6.51,  expiration_date: "2027-01-01", days_until_expiry: 271, status_color: "green"  },

  // --- Row D ---
  { slot_id: "D1", item_name: "Tissues",                       quantity: 9,  price: 1.00,  expiration_date: "2027-01-15", days_until_expiry: 285, status_color: "green"  },
  { slot_id: "D2", item_name: "Afrin",                         quantity: 4,  price: 13.01, expiration_date: "2026-06-15", days_until_expiry: 71,  status_color: "yellow" },
  { slot_id: "D3", item_name: "DayQuil",                       quantity: 8,  price: 5.03,  expiration_date: "2026-10-01", days_until_expiry: 179, status_color: "green"  },
  { slot_id: "D4", item_name: "Snickers Bar",                  quantity: 0,  price: 1.50,  expiration_date: "2026-06-01", days_until_expiry: 57,  status_color: "red"    },

  // --- Row E ---
  { slot_id: "E1", item_name: "Tylenol",                       quantity: 7,  price: 3.04,  expiration_date: "2026-11-01", days_until_expiry: 210, status_color: "green"  },
  { slot_id: "E2", item_name: "Skittles Original",             quantity: 6,  price: 1.53,  expiration_date: "2026-08-15", days_until_expiry: 132, status_color: "green"  },
  { slot_id: "E3", item_name: "Advil",                         quantity: 3,  price: 3.05,  expiration_date: "2026-09-01", days_until_expiry: 149, status_color: "red"    },
  { slot_id: "E4", item_name: "Starburst",                     quantity: 4,  price: 1.54,  expiration_date: "2026-04-09", days_until_expiry: 4,   status_color: "yellow" },

  // --- Row F ---
  { slot_id: "F1", item_name: "Doritos Nacho Cheese",          quantity: 6,  price: 1.75,  expiration_date: "2026-07-20", days_until_expiry: 106, status_color: "green" },
  { slot_id: "F2", item_name: "Pop-Tarts Strawberry",          quantity: 5,  price: 2.05,  expiration_date: "2026-05-20", days_until_expiry: 45,  status_color: "yellow" },
  { slot_id: "F3", item_name: "My Way",                        quantity: 8,  price: 13.02, expiration_date: "2027-04-01", days_until_expiry: 361, status_color: "green"  },
  { slot_id: "F4", item_name: "Dunkin Iced Coffee Mocha",      quantity: 2,  price: 3.55,  expiration_date: "2026-04-10", days_until_expiry: 5,   status_color: "red" },
];

export default mockInventory;