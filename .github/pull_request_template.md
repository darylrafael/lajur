## Deskripsi Perubahan (PR Description)
<!-- Jelaskan secara singkat perubahan apa yang dilakukan dan mengapa (konteks keputusan teknik) -->

## Tipe Perubahan
- [ ] `feat`: Fitur baru
- [ ] `fix`: Perbaikan bug
- [ ] `eval`: Pembaruan dataset atau harness evaluasi
- [ ] `spike`: Hasil eksperimen atau investigasi teknis
- [ ] `docs`: Pembaruan dokumentasi atau ADR
- [ ] `refactor`: Refactoring tanpa mengubah fungsionalitas

## Definition of Done (§12.4 Checklist)
Sebelum PR ini dapat di-merge ke branch `main`, seluruh checklist berikut WAJIB terpenuhi:

- [ ] **Lint & Tests**: Linting, typecheck, dan seluruh automated test (unit/integration) hijau di CI.
- [ ] **Eval Suite**: Evaluasi relevan dijalankan; skor akurasi (OAR/KER) tidak turun melebihi batas toleransi.
- [ ] **Real Device Verification**: Telah diuji manual pada **perangkat nyata** (smartphone dan laptop) melalui jaringan internet publik (seluler/WiFi nyata), bukan hanya localhost.
- [ ] **Observabilitas**: Log terstruktur/span metrik ditambahkan; jalur penanganan error (*error path*) telah teruji.
- [ ] **Dokumentasi**: Dokumen terkait, ADR (jika ada keputusan arsitektur baru), dan `CHANGELOG.md` telah diperbarui; instruksi flag lingkungan dan rollback jelas.
- [ ] **Security & Privacy Guard**: Tidak ada rahasia/API key yang ter-commit (`.env.example` only), audio pengguna tidak disimpan, dan folder `private/` tidak terlacak oleh git.
