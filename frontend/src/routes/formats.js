export function formatPrice(value) {
  if (value) return `$${value.toLocaleString()}`;
  return null;
}
export function formatPcs(value) {
  if (value) return value.toLocaleString() + " pcs.";
  return null;
}

export function formatTradableRestriction(value) {
  if (value === -1) return "🚫Not tradable (Sell only) ";
  if (value === null) return "✅No";
  return `🔒${value} days`;
}

export function formatMarketableRestriction(value) {
  if (value === null || value === 0) return "✅No";
  return `🔒${value} days`;
}

export function formatCommodity(value) {
  return value ? "Yes" : "No"
}
