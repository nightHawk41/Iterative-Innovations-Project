// import React, { useState, useEffect } from "react";
// import InventoryGrid from "../components/InventoryGrid";
// import RestockModal from "../components/RestockModal";
// import TransactionUpload from "../components/TransactionUpload";
// import mockInventory from "../data/mockInventory";

// function AdminPage() {
//   const [slots, setSlots]         = useState([]);
//   const [loading, setLoading]     = useState(true);
//   const [showModal, setShowModal] = useState(false);

//   function fetchInventory() {
//     setLoading(true);
//     fetch("/api/inventory")
//       .then((res) => {
//         if (!res.ok) throw new Error("API unavailable");
//         return res.json();
//       })
//       .then((data) => setSlots(data))
//       .catch(() => setSlots(mockInventory))
//       .finally(() => setLoading(false));
//   }

//   useEffect(() => { fetchInventory(); }, []);

//   return (
//     <div>
//       <div className="page-header mb-4">
//         <div>
//           <h2 className="mb-0">Admin Panel</h2>
//           <p className="text-muted mb-0">Manage inventory restocks and process transaction logs.</p>
//         </div>
//         <button className="btn btn-primary" onClick={() => setShowModal(true)}>
//           + Manual Restock
//         </button>
//       </div>

//       {loading ? (
//         <div className="text-center py-5 text-muted">Loading inventory…</div>
//       ) : (
//         <InventoryGrid slots={slots} />
//       )}

//       <TransactionUpload />

//       <RestockModal
//         show={showModal}
//         onHide={() => setShowModal(false)}
//         slots={slots}
//         onRestockSuccess={fetchInventory}
//       />
//     </div>
//   );
// }

// export default AdminPage;