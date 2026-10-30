# Panduan Wawancara Mom Test (Pemilik & Staf F&B)

**Dokumen:** `docs/interviews/interview-guide-id.md`  
**Milestone:** Minggu 6 — Validasi Pasar Dimulai  
**Target:** Pemilik (*owner*), pengelola, manajer operasional, atau kasir restoran kecil, kedai kopi (*coffee shop*), gerai cepat saji, dan warung makan dengan volume pesanan tinggi (khususnya yang melayani *takeaway* / *drive-thru* / pesanan jarak jauh).  
**Metodologi:** *The Mom Test* (Rob Fitzpatrick) — Fokus pada perilaku masa lalu nyata (*past behavior*), solusi alternatif saat ini (*current workaround*), waktu dan uang yang dikeluarkan (*money & time spent*).  
**Aturan Emas:** DILARANG melakukan *pitching*, DILARANG menceritakan ide AI/teknologi Lajur, DILARANG bertanya *"apakah Anda suka ide ini"*, dan DILARANG menanyakan opini masa depan yang hipotetis.

---

## 1. Verbatim Target Rencana Proyek (PROJECT_PLAN.md §13 & §16)

- **Target Minggu 6 (PROJECT_PLAN.md §13, baris 421–425):**
  > Mulai wawancara Mom Test (target 8–10 sampai Minggu 10).  
  > **Target:** skenario barge-in dan koreksi lulus; wawancara ≥ 3 selesai.
- **Kriteria Gerbang G3 (PROJECT_PLAN.md §16):**
  > Lanjut hanya jika $\ge 2$ pemilik bersedia pilot dan $\ge 1$ menyatakan kesediaan bayar konkret. Jika tidak: proyek berhenti sebagai portofolio.

---

## 2. Struktur Wawancara (Durasi: 15–20 Menit)

### Bagian 1: Pengantar Santai & Konteks Usaha (2–3 Menit)
*Tujuan: Memahami profil operasional tanpa mengarahkan topik ke AI.*
- "Boleh cerita sedikit kak/pak/bu, di sini jam-jam paling ramainya biasanya kapan saja?"
- "Berapa rata-rata transaksi pesanan yang masuk pas jam sibuk itu?"
- "Siapa yang biasanya pegang bagian penerimaan pesanan dan kasir?"

### Bagian 2: Penggalian Perilaku Nyata & Masalah Terakhir (7–8 Menit)
*Tujuan: Mengetahui insiden konkret terakhir kali terjadi pesanan terlewat, salah input, atau antrean macet.*
- **Pertanyaan Inti 1 (Insiden Terakhir):**  
  *"Bisa diceritakan terakhir kali ada pesanan yang salah catat atau terlewat pas jam ramai? Kapan itu terjadi dan ceritanya bagaimana?"*
  - *Follow-up:* *"Waktu itu dampaknya apa? Makanannya harus diganti, pelanggan komplain, atau bagaimana?"*
  - *Follow-up:* *"Seberapa sering kejadian seperti itu dalam seminggu terakhir?"*
- **Pertanyaan Inti 2 (Bottleneck Operasional):**  
  *"Di alur dari pelanggan datang/pesan sampai makanan disiapkan, bagian mana yang paling sering bikin kasir atau kru dapur kewalahan?"*
- **Pertanyaan Inti 3 (Upsell & Penawaran Tambahan):**  
  *"Apakah kasir diwajibkan menawarkan menu tambahan (misal upsize minum atau tambah side dish)? Dalam praktiknya pas lagi antre panjang, penawaran itu sempat ditawarkan tidak? Kenapa?"*

### Bagian 3: Solusi yang Digunakan Sekarang & Pengeluaran Nyata (5–6 Menit)
*Tujuan: Mengukur apakah masalah cukup menyakitkan hingga mereka sudah mengeluarkan uang atau tenaga untuk menyelesaikannya.*
- **Pertanyaan Inti 4 (Current Workaround):**  
  *"Untuk mengatasi masalah pesanan salah atau antrean menumpuk itu, sekarang langkah apa yang sudah pernah dicoba?"*
  - *Contoh probing:* Tambah kasir paruh waktu? Pakai kertas bon manual? Pakai sistem POS tertentu?
- **Pertanyaan Inti 5 (Pengeluaran Finansial):**  
  *"Alat atau aplikasi apa saja yang sekarang dipakai dan rutin dibayar bulanan untuk kasir atau operasional? (misal Moka, ESB, iSeller, Pawoon, GrabMerchant) Berapa biayanya per bulan?"*
  - *Follow-up:* *"Siapa yang memutuskan untuk beli atau langganan alat itu?"*
- **Pertanyaan Inti 6 (Waktu Terbuang):**  
  *"Berapa banyak waktu staf yang habis hanya untuk input ulang pesanan atau beresin selisih bon setiap harinya?"*

### Bagian 4: Penutup & Tindak Lanjut Alami (2 Menit)
- *"Terima kasih banyak atas waktunya, cerita operasionalnya sangat mencerahkan."*
- *"Ke depannya kami sedang meriset solusi untuk membantu kelancaran pesanan di jam sibuk F&B. Kalau nanti riset kami ada perkembangan atau ingin menguji coba sesuatu di lapangan, bolehkah kami kontak lagi?"*

---

## 3. Jebakan yang Harus Dihindari (*Red Flags*)

| Jebakan / Godaan | Mengapa Berbahaya | Yang Seharusnya Ditanyakan |
| :--- | :--- | :--- |
| *"Apakah bapak suka ide kasir suara otomatis AI?"* | Pelanggan akan bersikap sopan dan berbohong ("Bagus kok idenya"). Opini tidak bernilai validasi. | *"Ceritakan bagaimana staf mencatat pesanan saat jam sibuk kemarin."* |
| *"Berapa bapak mau bayar kalau ada alat ini?"* | Angka hipotetis di masa depan tidak mencerminkan kesediaan bayar nyata. | *"Berapa biaya yang rutin dibayar saat ini untuk sistem kasir/POS yang sedang dipakai?"* |
| Melakukan demo aplikasi atau menjelaskan fitur web Lajur | Mengubah wawancara dari eksplorasi masalah menjadi sesi jualan (*pitching*). | Jangan tunjukkan demo atau jelaskan arsitektur teknis sama sekali. |
