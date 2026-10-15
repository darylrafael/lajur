# Packages: Cart & Menu Service

Direktori ini berisi logika bisnis murni (pure deterministic state machine):
- **Cart State Machine**: Satu-satunya komponen yang berhak mengubah keranjang pesanan (`add_item`, `remove_item`, `modify_item`, `undo`, `confirm`, `handoff`). Bebas efek samping I/O.
- **Menu Service**: Validasi menu, varian ukuran, modifier wajib/opsional, aturan paket hemat (combo slots), ketersediaan jam sarapan/reguler, dan status ketersediaan stok (86'd).

*Status: Dibuat di Minggu 1 (Dasar) & Minggu 3 (State Machine Lengkap).*
