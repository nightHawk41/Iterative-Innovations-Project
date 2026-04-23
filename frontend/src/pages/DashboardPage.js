import React, { useEffect, useState } from "react";
import InventoryGrid from "../components/InventoryGrid";
import AlertsBanner from "../components/AlertsBanner";
import PurchaseModal from "../components/PurchaseModal";

function StatCard({ label, value, colorClass }) {
	return (
		<div className="col">
			<div className={`stat-card border-top border-4 ${colorClass}`}>
				<div className="stat-value">{value}</div>
				<div className="stat-label">{label}</div>
			</div>
		</div>
	);
}

function DashboardPage() {
	const [slots, setSlots] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState("");
	const [selectedSlot, setSelectedSlot] = useState(null);
	const [purchaseSubmitting, setPurchaseSubmitting] = useState(false);
	const [toast, setToast] = useState(null);

	function showToast(message, variant = "success") {
		setToast({ message, variant });
	}

	useEffect(() => {
		if (!toast) {
			return undefined;
		}

		const timeoutId = window.setTimeout(() => setToast(null), 3000);
		return () => window.clearTimeout(timeoutId);
	}, [toast]);

	useEffect(() => {
		let isMounted = true;

		async function fetchInventory() {
			setLoading(true);
			setError("");

			try {
				const response = await fetch("/api/inventory");
				if (!response.ok) {
					throw new Error("Failed to load inventory.");
				}

				const data = await response.json();
				if (!isMounted) {
					return;
				}

				setSlots(Array.isArray(data) ? data : []);
			} catch (err) {
				if (!isMounted) {
					return;
				}

				setSlots([]);
				setError("Unable to load inventory. Please check that the backend is running.");
			} finally {
				if (isMounted) {
					setLoading(false);
				}
			}
		}

		fetchInventory();

		return () => {
			isMounted = false;
		};
	}, []);

	async function refreshInventory() {
		setLoading(true);
		setError("");

		try {
			const response = await fetch("/api/inventory");
			if (!response.ok) {
				throw new Error("Failed to load inventory.");
			}

			const data = await response.json();
			setSlots(Array.isArray(data) ? data : []);
		} catch (err) {
			setSlots([]);
			setError("Unable to load inventory. Please check that the backend is running.");
		} finally {
			setLoading(false);
		}
	}

	function closePurchaseModal() {
		setSelectedSlot(null);
	}

	async function handleConfirmPurchase() {
		if (!selectedSlot) {
			return;
		}

		setPurchaseSubmitting(true);
		const slotToPurchase = selectedSlot;

		try {
			const response = await fetch("/api/purchase", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ slot_id: slotToPurchase.slot_id }),
			});

			if (response.status === 200) {
				closePurchaseModal();
				showToast(`✓ ${slotToPurchase.item_name} dispensed!`, "success");
				await refreshInventory();
				return;
			}

			closePurchaseModal();
			if (response.status === 409) {
				showToast("This item is out of stock.", "danger");
			} else if (response.status === 400) {
				showToast("This item is unavailable.", "danger");
			} else {
				showToast("Purchase failed. Please try again.", "danger");
			}
		} catch (err) {
			closePurchaseModal();
			showToast("Network error. Is the backend running?", "danger");
		} finally {
			setPurchaseSubmitting(false);
		}
	}

	const total = slots.length;
	const critical = slots.filter((slot) => (slot.status_color || "").toLowerCase() === "red").length;
	const warning = slots.filter((slot) => (slot.status_color || "").toLowerCase() === "yellow").length;
	const healthy = slots.filter((slot) => (slot.status_color || "").toLowerCase() === "green").length;

	return (
		<div>
			<div className="page-header mb-4">
				<h2 className="mb-0">Inventory Dashboard</h2>
				<p className="text-muted mb-0">Read-only view — use Admin Panel to make changes.</p>
			</div>

			<div className="row row-cols-2 row-cols-md-4 g-3 mb-4">
				<StatCard label="Total Slots" value={total} colorClass="border-secondary" />
				<StatCard label="Healthy" value={healthy} colorClass="border-success" />
				<StatCard label="Low / Expiring" value={warning} colorClass="border-warning" />
				<StatCard label="Critical" value={critical} colorClass="border-danger" />
			</div>

			{error ? (
				<div className="alert alert-danger" role="alert">
					{error}
				</div>
			) : null}

			<AlertsBanner />

			{loading ? (
				<div className="text-center py-5 text-muted">Loading inventory…</div>
			) : (
				<InventoryGrid slots={slots} onSlotSelect={setSelectedSlot} />
			)}

			<PurchaseModal
				show={Boolean(selectedSlot)}
				slot={selectedSlot}
				submitting={purchaseSubmitting}
				onConfirm={handleConfirmPurchase}
				onHide={closePurchaseModal}
			/>

			{toast ? (
				<div className={`app-toast app-toast-${toast.variant}`} role="status" aria-live="polite">
					{toast.message}
				</div>
			) : null}
		</div>
	);
}

export default DashboardPage;