import React, { useEffect, useState } from "react";
import InventoryGrid from "../components/InventoryGrid";
import AlertsBanner from "../components/AlertsBanner";
import PurchaseModal from "../components/PurchaseModal";

const EMPTY_SUMMARY = {
	total_slots: 0,
	healthy: 0,
	low_expiring: 0,
	critical_out: 0,
};

function computeSummaryFromSlots(slots) {
	let healthy = 0;
	let lowExpiring = 0;
	let criticalOut = 0;

	for (const slot of slots) {
		const quantity = Number(slot.quantity ?? 0);
		const daysUntilExpiry = Number(slot.days_until_expiry ?? -1);

		if (daysUntilExpiry <= 0 || quantity === 0) {
			criticalOut += 1;
		} else if (quantity <= 2 || daysUntilExpiry <= 2) {
			criticalOut += 1;
		} else if (quantity <= 5 || daysUntilExpiry <= 5) {
			lowExpiring += 1;
		} else {
			healthy += 1;
		}
	}

	return {
		total_slots: slots.length,
		healthy,
		low_expiring: lowExpiring,
		critical_out: criticalOut,
	};
}

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
	const [summary, setSummary] = useState(EMPTY_SUMMARY);
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
				const slotsData = Array.isArray(data) ? data : [];
				if (!isMounted) {
					return;
				}

				setSlots(slotsData);

				try {
					const summaryResponse = await fetch("/api/inventory/summary");
					if (!summaryResponse.ok) {
						throw new Error("Failed to load summary.");
					}

					const summaryData = await summaryResponse.json();
					if (!isMounted) {
						return;
					}

					setSummary({
						total_slots: Number(summaryData.total_slots ?? 0),
						healthy: Number(summaryData.healthy ?? 0),
						low_expiring: Number(summaryData.low_expiring ?? 0),
						critical_out: Number(summaryData.critical_out ?? 0),
					});
				} catch (summaryErr) {
					if (!isMounted) {
						return;
					}

					setSummary(computeSummaryFromSlots(slotsData));
				}
			} catch (err) {
				if (!isMounted) {
					return;
				}

				setSlots([]);
				setSummary(EMPTY_SUMMARY);
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
				const slotsData = Array.isArray(data) ? data : [];
				setSlots(slotsData);

				try {
					const summaryResponse = await fetch("/api/inventory/summary");
					if (!summaryResponse.ok) {
						throw new Error("Failed to load summary.");
					}

					const summaryData = await summaryResponse.json();
					setSummary({
						total_slots: Number(summaryData.total_slots ?? 0),
						healthy: Number(summaryData.healthy ?? 0),
						low_expiring: Number(summaryData.low_expiring ?? 0),
						critical_out: Number(summaryData.critical_out ?? 0),
					});
				} catch (summaryErr) {
					setSummary(computeSummaryFromSlots(slotsData));
				}
		} catch (err) {
			setSlots([]);
				setSummary(EMPTY_SUMMARY);
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

	const total = Number(summary.total_slots ?? slots.length);
	const healthy = Number(summary.healthy ?? 0);
	const warning = Number(summary.low_expiring ?? 0);
	const critical = Number(summary.critical_out ?? 0);

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