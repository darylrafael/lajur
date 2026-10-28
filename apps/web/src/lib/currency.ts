/**
 * Currency formatting utility for Indonesian Rupiah (IDR).
 * Formats integer amounts into standard Indonesian currency representation.
 * Example: 38000 -> "Rp 38.000"
 */

const rupiahFormatter = new Intl.NumberFormat("id-ID", {
  style: "currency",
  currency: "IDR",
  maximumFractionDigits: 0,
});

export function formatRupiah(amount: number): string {
  if (isNaN(amount)) return "Rp 0";
  return rupiahFormatter.format(amount).replace(/\s+/g, " ");
}
