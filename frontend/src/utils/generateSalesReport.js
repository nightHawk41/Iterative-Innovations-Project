import { showToast } from "./toast";

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function toMoney(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(2) : "0.00";
}

function formatDate(value) {
  if (!value) {
    return null;
  }

  const d = new Date(value);
  if (Number.isNaN(d.getTime())) {
    return String(value);
  }

  return d.toLocaleDateString("en-US");
}

function formatDateRange(dateRange) {
  if (!dateRange) {
    return "N/A";
  }

  if (typeof dateRange === "string") {
    return dateRange;
  }

  const start = formatDate(dateRange.start);
  const end = formatDate(dateRange.end);

  if (!start && !end) {
    return "N/A";
  }

  if (start && end && start !== end) {
    return `${start} – ${end}`;
  }

  return start || end || "N/A";
}

function normalizeItems(items) {
  if (!Array.isArray(items)) {
    return [];
  }

  return items.map((item, index) => {
    const units = Number(item.units_sold ?? item.units ?? 0);
    const revenue = Number(item.total_revenue ?? item.revenue ?? 0);
    const avgPriceRaw = item.avg_price ?? item.average_price;
    const avgPrice = Number(avgPriceRaw ?? (units > 0 ? revenue / units : 0));

    return {
      rank: Number(item.rank ?? index + 1),
      slot_id: item.slot_id ?? "—",
      item_name: item.item_name ?? "Unknown",
      units_sold: Number.isFinite(units) ? units : 0,
      total_revenue: Number.isFinite(revenue) ? revenue : 0,
      avg_price: Number.isFinite(avgPrice) ? avgPrice : 0,
    };
  });
}

function buildSalesReportHtml(data) {
  const generatedAt = data.generated_at
    ? new Date(data.generated_at).toLocaleString("en-US")
    : new Date().toLocaleString("en-US");

  const dateRange = formatDateRange(data.date_range);
  const items = normalizeItems(data.items);
  const topItem = data.top_item
    ? {
        item_name: data.top_item.item_name ?? "Unknown",
        slot_id: data.top_item.slot_id ?? "—",
        units: Number(data.top_item.units ?? data.top_item.units_sold ?? 0),
        revenue: Number(data.top_item.revenue ?? data.top_item.total_revenue ?? 0),
      }
    : null;

  const totalRevenue = Number(data.total_revenue ?? 0);
  const totalUnits = Number(data.total_units ?? 0);
  const uniqueItems = Number(data.unique_items ?? items.length);

  const tableRows = items
    .map(
      (item) => `
        <tr>
            <td>${item.rank}</td>
            <td>${escapeHtml(item.slot_id)}</td>
            <td>${escapeHtml(item.item_name)}</td>
            <td>${item.units_sold}</td>
            <td class="revenue-cell">$${toMoney(item.total_revenue)}</td>
            <td>$${toMoney(item.avg_price)}</td>
        </tr>`
    )
    .join("");

  const csvLines = [
    "UMBC Vending Inventory System - Sales Report",
    `Generated:,${generatedAt}`,
    `Date Range:,${dateRange}`,
    "",
    "Rank,Slot ID,Item Name,Units Sold,Total Revenue,Avg Price",
    ...items.map((item) =>
      [
        item.rank,
        item.slot_id,
        item.item_name,
        item.units_sold,
        `$${toMoney(item.total_revenue)}`,
        `$${toMoney(item.avg_price)}`,
      ].join(",")
    ),
    "",
    `TOTAL,,,${totalUnits},$${toMoney(totalRevenue)},`,
  ].join("\n");

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>UMBC Sales Report</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
    :root {
        --gold: #f0a500;
        --black: #111;
        --bg: #f5f3ef;
        --panel: #fff;
        --border: #ddd;
        --muted: #777;
        --green: #2d7a2d;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'IBM Plex Sans', sans-serif; background: var(--bg); color: var(--black); min-height: 100vh; }

    .top-bar {
        background: var(--black);
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 28px;
        position: sticky;
        top: 0;
        z-index: 10;
        border-bottom: 3px solid var(--gold);
    }
    .top-bar-left { display: flex; align-items: center; gap: 14px; }
    .top-bar-logo { font-family: 'IBM Plex Mono', monospace; font-size: 1.3rem; font-weight: 700; letter-spacing: -1px; color: var(--gold); }
    .top-bar-title { font-size: 0.9rem; color: #ccc; font-weight: 300; border-left: 1px solid #444; padding-left: 14px; }
    .top-bar-actions { display: flex; gap: 10px; }

    .action-btn {
        padding: 7px 18px;
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        border: none;
        transition: background 0.15s;
    }
    .action-btn.download { background: var(--gold); color: var(--black); }
    .action-btn.download:hover { background: #d49200; }
    .action-btn.close-btn { background: transparent; color: #ccc; border: 1px solid #555; }
    .action-btn.close-btn:hover { background: #333; color: white; }

    .report-body { max-width: 900px; margin: 36px auto; padding: 0 24px 60px; }

    .report-header {
        border-left: 5px solid var(--gold);
        padding: 16px 20px;
        background: var(--panel);
        margin-bottom: 28px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .report-header h1 { font-family: 'IBM Plex Mono', monospace; font-size: 1.4rem; font-weight: 700; margin-bottom: 6px; }
    .report-meta { font-size: 0.78rem; color: var(--muted); display: flex; gap: 24px; flex-wrap: wrap; margin-top: 8px; }
    .report-meta span strong { color: var(--black); }

    .summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 28px; }
    .summary-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-top: 3px solid var(--gold);
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .summary-card .label { font-size: 0.73rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; font-weight: 600; }
    .summary-card .value { font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; font-weight: 700; }
    .summary-card .sub { font-size: 0.72rem; color: var(--muted); margin-top: 4px; }

    .callout {
        background: var(--black);
        color: white;
        padding: 16px 20px;
        margin-bottom: 28px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .callout-icon { font-size: 1.5rem; }
    .callout-text .label { font-size: 0.7rem; color: var(--gold); font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; }
    .callout-text .value { font-family: 'IBM Plex Mono', monospace; font-size: 1.05rem; font-weight: 600; margin-top: 2px; }
    .callout-text .sub { font-size: 0.75rem; color: #aaa; margin-top: 2px; }

    .section-title { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }

    .table-wrap { background: var(--panel); border: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 28px; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
    thead tr { background: var(--black); color: white; }
    thead th { padding: 10px 14px; text-align: left; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.04em; }
    tbody tr { border-bottom: 1px solid var(--border); }
    tbody tr:last-child { border-bottom: none; }
    tbody tr:nth-child(even) { background: #fafafa; }
    tbody tr:first-child td { font-weight: 600; }
    td { padding: 9px 14px; }
    td:first-child { font-family: 'IBM Plex Mono', monospace; color: var(--muted); font-size: 0.75rem; }
    .revenue-cell { color: var(--green); font-weight: 600; font-family: 'IBM Plex Mono', monospace; }
    tfoot tr { background: #f0ece4; border-top: 2px solid var(--gold); }
    tfoot td { padding: 10px 14px; font-weight: 700; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; }

    .report-footer { text-align: center; font-size: 0.72rem; color: var(--muted); padding-top: 20px; border-top: 1px solid var(--border); }
</style>
</head>
<body>

<div class="top-bar">
    <div class="top-bar-left">
        <span class="top-bar-logo">UMBC</span>
        <span class="top-bar-title">| Sales Report</span>
    </div>
    <div class="top-bar-actions">
        <button class="action-btn download" onclick="downloadCSV()">⬇ Download CSV</button>
        <button class="action-btn close-btn" onclick="window.close()">✕ Close</button>
    </div>
</div>

<div class="report-body">
    <div class="report-header">
        <h1>UMBC Vending — Sales Report</h1>
        <div class="report-meta">
            <span><strong>Generated:</strong> ${escapeHtml(generatedAt)}</span>
            <span><strong>Date Range:</strong> ${escapeHtml(dateRange)}</span>
        </div>
    </div>

    <div class="summary-grid">
        <div class="summary-card">
            <div class="label">Total Revenue</div>
            <div class="value">$${toMoney(totalRevenue)}</div>
            <div class="sub">across all transactions</div>
        </div>
        <div class="summary-card">
            <div class="label">Units Sold</div>
            <div class="value">${Number.isFinite(totalUnits) ? totalUnits : 0}</div>
            <div class="sub">total items dispensed</div>
        </div>
        <div class="summary-card">
            <div class="label">Unique Items</div>
            <div class="value">${Number.isFinite(uniqueItems) ? uniqueItems : 0}</div>
            <div class="sub">distinct products sold</div>
        </div>
    </div>

    ${topItem ? `
    <div class="callout">
        <div class="callout-icon">🏆</div>
        <div class="callout-text">
            <div class="label">Top Selling Item</div>
            <div class="value">${escapeHtml(topItem.item_name)} (Slot ${escapeHtml(topItem.slot_id)})</div>
            <div class="sub">${Number.isFinite(topItem.units) ? topItem.units : 0} units &nbsp;·&nbsp; $${toMoney(topItem.revenue)} revenue</div>
        </div>
    </div>` : ""}

    <div class="section-title">Sales Breakdown by Item</div>
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>#</th><th>Slot ID</th><th>Item Name</th>
                    <th>Units Sold</th><th>Total Revenue</th><th>Avg Price</th>
                </tr>
            </thead>
            <tbody>${tableRows}</tbody>
            <tfoot>
                <tr>
                    <td colspan="3">TOTAL</td>
                    <td>${Number.isFinite(totalUnits) ? totalUnits : 0}</td>
                    <td>$${toMoney(totalRevenue)}</td>
                    <td>—</td>
                </tr>
            </tfoot>
        </table>
    </div>

    <div class="report-footer">
        UMBC Vending Inventory System &nbsp;·&nbsp; Generated ${escapeHtml(generatedAt)}
    </div>
</div>

<script>
const csvContent = ${JSON.stringify(csvLines)};
function downloadCSV() {
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "umbc_sales_report.csv";
    a.click();
    URL.revokeObjectURL(url);
}
<\/script>
</body>
</html>`;
}

export async function generateSalesReport() {
  try {
    const response = await fetch("/api/reports/sales");
    const data = await response.json();

    if (!response.ok) {
      showToast(data?.error || "Failed to generate sales report.");
      return false;
    }

    const win = window.open("", "_blank", "width=960,height=700,scrollbars=yes,resizable=yes");
    if (!win) {
      showToast("Unable to open sales report window. Please allow popups.");
      return false;
    }

    const reportHtml = buildSalesReportHtml(data);
    win.document.write(reportHtml);
    win.document.close();
    return true;
  } catch (error) {
    showToast(error?.message || "Failed to generate sales report.");
    return false;
  }
}
