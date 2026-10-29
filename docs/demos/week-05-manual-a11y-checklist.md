# Checklist Uji Aksesibilitas Manual — Minggu 5

**Dokumen:** `docs/demos/week-05-manual-a11y-checklist.md`  
**Milestone:** Minggu 5 (Web Simulator Manual Accessibility Verification)  
**Status:** **OPTIONAL CHECKLIST FOR DARYL [HUMAN] — UNVERIFIED**  
**Catatan Penting:** Audit otomatis Playwright + `@axe-core/playwright` hanya menguji subset aturan WCAG secara sintaksis dan **BUKAN bukti aksesibilitas penuh**. Pengujian manual berikut disediakan sebagai checklist verifikasi independen bagi penguji manusia. Asisten AI **TIDAK MENGKLAIM** pengujian manual ini telah selesai.

---

## 1. Navigasi Papan Ketik Penuh (*Keyboard-Only Pass*)
- [ ] Buka simulator tanpa menggunakan mouse atau layar sentuh.
- [ ] Gunakan tombol `Tab` dan `Shift + Tab` untuk berpindah fokus ke seluruh elemen interaktif (tombol Mulai/Selesai, alih bahasa ID/EN, tab kategori menu, kartu item, pemilih replay).
- [ ] Pastikan indikator cincin fokus (*focus ring*) terlihat jelas di setiap elemen yang aktif.
- [ ] Tekan `Enter` atau `Spasi` untuk memicu aksi (memilih tab menu, membuka dropdown, memulai replay).
- [ ] Pastikan tidak ada perangkap fokus (*focus trap*) di modal atau banner handoff kru (tombol tutup dapat diakses via keyboard).

## 2. Pengujian Pembaca Layar (*Screen-Reader Pass*)
- [ ] Aktifkan pembaca layar (NVDA / Narrator di Windows, atau VoiceOver di iOS/macOS).
- [ ] Periksa apakah panel transkrip (`role="log"`, `aria-live="polite"`) dibacakan secara otomatis begitu kalimat baru atau transkrip parsial masuk tanpa mengganggu navigasi pengguna.
- [ ] Periksa apakah tombol kontrol memiliki label teks yang jelas (bukan hanya ikon).
- [ ] Periksa apakah pembaruan total harga dan lencana keranjang diumumkan dengan wajar.

## 3. Pembesaran Tampilan 200% (*Zoom 200% Pass*)
- [ ] Atur perbesaran browser menjadi 200% (`Ctrl + Plus` dua kali di browser desktop).
- [ ] Pastikan tidak ada teks yang terpotong (*text truncation* yang merusak makna), tumpang tindih (*overlapping*), atau overflow horizontal yang tidak wajar.
- [ ] Pastikan layout responsif menyesuaikan diri secara proporsional dan tombol kontrol tetap dapat diklik.

## 4. Kepatuhan Reduksi Gerakan (*Reduced Motion Pass*)
- [ ] Aktifkan preferensi sistem operasi untuk mengurangi gerakan (*prefers-reduced-motion: reduce*).
- [ ] Pastikan animasi visualizer suara bot (gelombang bar melompat) dan animasi badge tidak memicu gerakan cepat yang mengganggu atau berpotensi memicu pusing/disorientasi.
