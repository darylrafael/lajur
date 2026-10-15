# Eval: Harness, Datasets, and Reports

Direktori ini berisi seluruh infrastruktur evaluasi offline dan CI (*Eval-Driven Development*):
- `menu/`: Definisi data menu fiktif (`menu.json`) dan skema validasinya (`menu.schema.json`).
- `datasets/`: Dataset skenario pesanan berbasis JSONL (dev set dan held-out set).
- `noise/`: Profil dan sampel audio ambient (noise motor, jalan raya, helm filter) untuk pengujian ketahanan.
- `harness/`: Runner otomatis untuk intent eval teks dan audio end-to-end.
- `reports/`: Hasil mentah metrik evaluasi (OAR, SER, KER, latensi) yang diverifikasi.
- `scripts/`: Skrip validasi integritas dataset dan menu.

Lisensi dataset diatur terpisah di `LICENSE-DATA.md` (CDLA-Permissive-2.0).
