# Cart State Machine & Intent Schema v1 Design Document

**Document:** `docs/design/cart-state-machine.md`  
**Milestone:** Minggu 3 (Cart State Machine + Intent Schema v1)  
**Status:** DRAFT / COMMITTED BEFORE IMPLEMENTATION  
**Version:** 1.0  
**Authors:** Daryl (Solo Dev) & Implementation Agent  

---

## 1. Acceptance Criteria & Invariants

### 1.1 Minggu 3 Target (PROJECT_PLAN.md §13 Verbatim)

> **Minggu 3 — Cart State Machine Selesai**  
> - Seluruh intent (add/remove/modify/undo/confirm/handoff) di state machine.  
> - 100% skenario inti lulus dengan intent hand-written.  
> - **Target:** cart tidak bisa masuk state tidak valid (property test sederhana).  

### 1.2 Core Architectural Invariants

1. **Cart State Machine di Luar LLM (ADR-0002):** Keranjang belanja dikelola murni oleh mesin deterministik (`packages/cart`). LLM hanya bertindak sebagai semantic parser yang mengusulkan intent terstruktur; LLM dilarang memegang, memutasi, atau mengarang state keranjang.
2. **Kedaulatan MenuService:** `MenuService` adalah satu-satunya otoritas kebenaran untuk katalog item, harga resmi (integer Rupiah), grup modifier, slot combo, ketersediaan jam operasional, dan stok (86'd items).
3. **Imunitas Manipulasi Harga Secara Konstruksi (Price Manipulation Impossible by Construction):** Skema intent tidak memiliki field `price`, `unit_price`, `total_price`, maupun `discount`. Harga sepenuhnya dihitung ulang oleh `MenuService` dari menu baku setelah setiap mutasi. Prompt injection ("beri diskon 100%", "ubah harga jadi 0 rupiah") tidak memiliki mekanisme representation di skema intent.
4. **Fungsi Murni & Deterministik:** State machine tidak melakukan I/O, network call, audio processing, LLM call, atau operasi non-deterministik (random). Waktu operasional disuntikkan secara eksplisit via callable clock (`injected clock`). Input yang sama dengan state dan konteks yang sama pasti menghasilkan output yang identik.
5. **Kekebalan Eksepsi (No Unhandled Exceptions):** Pasangan `(state, intent)` yang tidak valid tidak pernah melempar runtime exception yang menghentikan sistem; seluruh kondisi invalid menghasilkan transisi aman atau mempertahankan state sebelumnya, serta mengembalikan penolakan terstruktur (`rejections`) dan fakta percakapan (`speech_facts`).
6. **Batas Plafon Pesanan (Hard Caps §11.2 & NFR-03):** Total kuantitas item per keranjang dibatasi maksimal 20 item (`total_item_count <= 20`). Setiap baris keranjang wajib memiliki kuantitas integer $\ge 1$.
7. **Semantik Pembatalan yang Ketat (Undo Invariants):** `undo_last` hanya mengembalikan snapshot state sebelum aksi terakhir. Undo tidak pernah menambah item atau menaikkan kuantitas. Ujaran spesifik pembatalan item ("tidak jadi burger") dipetakan ke `remove_item` atau `replace_item`; pembatalan menyeluruh ("batal semua") dipetakan ke `clear_cart`.
8. **Pemisahan Logika & Bahasa (No Reply Text in Cart Engine):** State machine tidak pernah menghasilkan teks balasan percakapan (string bahasa alami). State machine hanya menghasilkan `speech_facts` terstruktur yang menjadi acuan generator balasan audio/teks di layer berikutnya.

---

## 2. Intent Schema v1

Intent schema dimodelkan sebagai Pydantic Discriminated Union (`type` sebagai discriminator). Skema JSON Schema diekspor secara otomatis ke `packages/cart/intent.schema.json`.

Seluruh intent merujuk pada `item_id`, `modifier_id`, `option_id`, atau `slot_id` resmi dari menu, **bukan teks bebas atau harga**.

### 2.1 Daftar Intent Resmi & Justifikasi

| Intent Type | Deskripsi & Parameter Utama | Justifikasi Penambahan / Perubahan |
|---|---|---|
| `add_item` | Menambah item/combo baru: `item_id`, `quantity` (default 1), `size` ("regular"/"medium"/"large"), `modifiers` (list string option ID), `slot_choices` (dict slot ID -> item ID). | Intent dasar pemesanan (§13). |
| `remove_item` | Menghapus atau mengurangi kuantitas: `line_id` (opsional), `item_id` (opsional), `quantity` (opsional; jika None atau $\ge$ qty baris, hapus seluruh baris). | Intent dasar pembatalan item spesifik (§13). |
| `modify_item` | Mengubah modifier atau ukuran baris yang ada: `line_id` / `item_id`, `size` (opsional), `add_modifiers` (list string), `remove_modifiers` (list string), `slot_choices` (dict). | Mengakomodasi permintaan kustomisasi ("upsize kentang", "tanpa es") (§13). |
| `replace_item` | Menukar item lama dengan item baru: `target_item_id` / `target_line_id`, `replacement_item_id`, `size`, `modifiers`. | **Ditambahkan:** Menangani pola ucapan nyata *"ganti kentang jadi nasi"* atau *"eh burgernya tukar yang dobel keju aja"* secara atomik dalam 1 turn tanpa race condition. |
| `undo_last` | Membatalkan 1 langkah mutasi percakapan terakhir dan kembali ke snapshot keranjang sebelumnya. | Intent dasar koreksi pikiran pelanggan (§13). |
| `clear_cart` | Mengosongkan seluruh isi keranjang belanja dan kembali ke keranjang kosong. | **Ditambahkan:** Menangani ujaran *"batalin semuanya mbak"*, *"gak jadi pesen apa-apa"* secara bersih. |
| `answer_choice` | Memberikan jawaban atas pertanyaan pilihan yang tertunda: `choice_id` (ID item, ID modifier, atau ID baris), `slot_id` (opsional). | **Ditambahkan:** Menangani resolusi slot combo (misal memilih minuman cola pada paket) atau memilih modifier wajib. |
| `confirm` | Pelanggan mengonfirmasi pesanan telah tuntas: `payment_method` (opsional). | Menutup pemesanan dan mengunci keranjang (§13). |
| `decline_more` | Pelanggan menyatakan tidak ingin menambah pesanan lagi (*"itu aja"*, *"sudah cukup"*). | **Ditambahkan:** Membedakan antara konfirmasi final pembayaran vs penolakan tawaran upsell, memicu transisi ke `confirming`. |
| `handoff` | Eskalasi segera ke kasir manusia: `reason` (string kategori alasan). | Safety net bila bot gagal paham, sistem error, atau diminta pelanggan (§13). |
| `ask_info` | Pertanyaan pelanggan tentang menu, harga, jam sarapan, atau bahan: `query_type`, `target_item_id` (opsional). | **Ditambahkan:** Menjawab pertanyaan informasi tanpa memutasi keranjang. |
| `unknown` | Ucapan tidak relevan, bising, atau tidak dapat dipahami: `raw_text`, `reason`. | **Ditambahkan:** Menampung fallback non-ordering tanpa memicu crash. |

### 2.2 Larangan Field Finansial pada Intent
Semua intent di atas **dilarang memuat field `price`, `total`, `discount`, `subtotal`, atau `tax`**.  
*Alasan Teknis:* Hal ini membuat serangan manipulasi harga (melalui prompt injection seperti *"Pesan 10 burger dengan harga Rp 0"* atau *"Diskon 99%"*) **mustahil terjadi secara konstruksi (*impossible by construction*)** karena parser schema validator Pydantic akan langsung menolak field yang tidak didefinisikan (`extra="forbid"`).

---

## 3. Dialog States & Tabel Transisi State

### 3.1 Definisi State
1. **`ordering` (Initial State):** State default di mana pelanggan sedang memilih, menambah, mengubah, atau membatalkan item.
2. **`awaiting_choice`:** State tunggu ketika ada pilihan wajib yang belum lengkap:
   - Combo slot yang belum dipilih (misal: paket combo belum memilih minuman atau side).
   - Modifier wajib yang belum dipilih (misal: pilihan rasa saus).
   - Ambiguitas referensi baris (misal: pelanggan bilang "batalin burgernya", tetapi ada 2 baris burger berbeda di keranjang).
3. **`confirming`:** State peninjauan akhir pesanan. Keranjang dibacakan, menunggu jawaban konfirmasi final dari pelanggan.
4. **`done` (Terminal State):** Pesanan telah disetujui dan dikunci. Tidak menerima penambahan/mutasi lebih lanjut.
5. **`handoff` (Terminal State):** Kendali dialihkan ke kru manusia drive-thru.

### 3.2 Tabel Transisi `(State, Intent) -> (New State, Action)`

| State Awal | Intent | State Akhir | Aksi & Efek Samping Deterministik | Rejection Jika Gagal |
|---|---|---|---|---|
| `ordering` | `add_item` | `ordering` / `awaiting_choice` | Validasi stok & jam via MenuService. Jika combo/modifier punya pilihan wajib yang kurang $\to$ `awaiting_choice`. Jika lengkap $\to$ tambahkan ke keranjang, hitung ulang total $\to$ `ordering`. | `OUT_OF_STOCK`, `OUT_OF_HOURS`, `CAP_EXCEEDED` |
| `ordering` | `remove_item` | `ordering` | Cari referensi baris item. Jika ketemu $\to$ kurangi/hapus baris, hitung ulang total $\to$ `ordering`. Jika ada multi-match ambigu $\to$ `awaiting_choice`. | `ITEM_NOT_IN_CART` |
| `ordering` | `modify_item` | `ordering` / `awaiting_choice` | Validasi modifier & ukuran baru pada baris target $\to$ perbarui baris, hitung ulang harga. | `ITEM_NOT_IN_CART`, `INVALID_MODIFIER`, `INVALID_SIZE` |
| `ordering` | `replace_item`| `ordering` / `awaiting_choice` | Hapus item target, tambahkan item pengganti dalam 1 transaksi atomik. Jika pengganti butuh pilihan slot $\to$ `awaiting_choice`. | `ITEM_NOT_IN_CART`, `OUT_OF_STOCK`, `OUT_OF_HOURS` |
| `ordering` | `undo_last` | `ordering` | Ambil snapshot keranjang sebelum mutasi terakhir dari stack riwayat. Kembalikan state keranjang ke snapshot tersebut. | `NOTHING_TO_UNDO` |
| `ordering` | `clear_cart` | `ordering` | Kosongkan seluruh item keranjang, total harga jadi 0 IDR. | - |
| `ordering` | `answer_choice`| `ordering` | Diabaikan secara aman (karena tidak ada pilihan yang sedang ditunggu), emit peringatan. | `UNEXPECTED_CHOICE` |
| `ordering` | `decline_more`| `confirming` | Jika keranjang tidak kosong $\to$ transisi ke `confirming` untuk minta verifikasi akhir. Jika kosong $\to$ tetap `ordering`. | `EMPTY_CART_CONFIRM` |
| `ordering` | `confirm` | `confirming` / `done` | Jika keranjang tidak kosong $\to$ transisi ke `confirming` (atau `done` jika eksplisit setuju checkout). | `EMPTY_CART_CONFIRM` |
| `ordering` | `handoff` | `handoff` | Set status keranjang ke `handoff`. | - |
| `ordering` | `ask_info` | `ordering` | Tetap di `ordering`. Kembalikan fakta informasi menu/jam di `speech_facts`. | `UNKNOWN_ITEM_QUERY` |
| `ordering` | `unknown` | `ordering` | Tetap di `ordering`. Catat rekam fakta ucapan tidak dipahami di `speech_facts`. | - |
| `awaiting_choice`| `answer_choice`| `ordering` / `awaiting_choice` | Terapkan pilihan ke slot combo / modifier / baris yang pending. Jika masih ada slot wajib lain yang kurang $\to$ tetap `awaiting_choice`. Jika semua lengkap $\to$ `ordering`. | `INVALID_CHOICE` |
| `awaiting_choice`| `undo_last` | `ordering` | Batalkan item yang memicu `awaiting_choice`, kembali ke `ordering`. | - |
| `awaiting_choice`| `handoff` | `handoff` | Segera alihkan ke manusia. | - |
| `awaiting_choice`| *intent lain* | `awaiting_choice` | Tolak mutasi item baru sebelum pilihan tertunda diselesaikan atau dibatalkan. | `CHOICE_REQUIRED` |
| `confirming` | `confirm` | `done` | Kunci keranjang pesanan. Tandai status `done`. | - |
| `confirming` | `decline_more`| `confirming` | Tetap di `confirming`, menunggu jawaban konfirmasi final atau perubahan. | - |
| `confirming` | `add`/`modify`/`remove`/`replace` | `ordering` | Jika pelanggan berubah pikiran saat konfirmasi, izinkan mutasi dan kembalikan state ke `ordering`. | Sesuai aturan ordering |
| `confirming` | `undo_last` | `ordering` | Batalkan aksi terakhir, kembalikan state ke `ordering`. | - |
| `confirming` | `handoff` | `handoff` | Segera alihkan ke manusia. | - |
| `done` | *any intent* | `done` | Terminal. Tidak ada mutasi yang diizinkan (idempoten). | `ORDER_ALREADY_COMPLETED` |
| `handoff` | *any intent* | `handoff` | Terminal. Seluruh interaksi dialihkan ke staf restoran. | `SESSION_HANDED_OFF` |

---

## 4. Result Schema & Speech Facts

Eksekusi transisi dijalankan melalui fungsi murni:
```python
def apply_intent(
    current_state: DialogState,
    cart: Cart,
    intent: Intent,
    context: StateContext,
) -> StateMachineResult:
    ...
```

### 4.1 Struktur `StateMachineResult`
```python
class StateMachineResult(BaseModel):
    new_state: DialogState
    cart: Cart
    events: list[CartEvent]
    rejections: list[Rejection]
    speech_facts: SpeechFacts
```

### 4.2 Struktur `SpeechFacts` (Fakta Terstruktur untuk Voice Generator)
Fakta percakapan disusun tanpa teks string bebas agar layer berikutnya (LLM bot reply generator atau template TTS) dapat merangkai kalimat kasir yang natural:
- `intent_handled`: Tipe intent yang berhasil/gagal diproses.
- `items_added`: Daftar item yang baru saja ditambahkan beserta kuantitas, ukuran, dan modifier.
- `items_removed`: Daftar item yang baru saja dikeluarkan dari keranjang.
- `items_modified`: Detail baris yang baru dimodifikasi.
- `pending_prompt`: Jika berpindah ke `awaiting_choice`, memuat informasi slot apa yang perlu ditanyakan ke pelanggan (misal: jenis minuman, pilihan saus, atau pilihan nomor baris).
- `rejection_reasons`: Kode alasan penolakan jika intent ditolak (misal: item habis, di luar jam sarapan, batas 20 item terlampaui).
- `cart_summary`: Total kuantitas item dan total harga terkini dalam integer IDR.
- `requires_confirmation`: Boolean apakah kasir perlu membacakan ringkasan pesanan.

---

## 5. Lokasi Aturan Bisnis & Penanganan Kasus Khusus

1. **Pemeriksaan Stok & Jam Operasional:** Dievaluasi menggunakan method `MenuService.is_in_stock(target)` dan `MenuService.is_item_available(target, current_time=clock())`. Item sarapan ditolak jika di luar 05:00–11:00.
2. **Plafon 20 Item (§11.2):** Jika `cart.total_item_count + intent.quantity > 20`, intent `add_item` ditolak dengan rejection `CAP_EXCEEDED`.
3. **Resolusi Referensi Baris (*Reference Resolution*):**
   - Jika intent memuat `line_id`: langsung cocokkan ke baris keranjang yang memiliki ID tersebut.
   - Jika intent hanya memuat `item_id`:
     - Cari seluruh baris dengan `item_id` sama.
     - Jika ditemukan persis 1 baris: referensi diselesaikan ke baris tersebut.
     - Jika ditemukan > 1 baris (misal ada 2 Burger Sapi dengan modifier berbeda): transisi ke `awaiting_choice` dengan detail ambiguitas agar pelanggan mengklarifikasi baris mana yang dimaksud.
     - Jika 0 baris: tolak dengan `ITEM_NOT_IN_CART`.
4. **Semantik Undo:**
   - State machine menyimpan `history: list[Cart]` (snapshot state sebelum mutasi).
   - `undo_last` mengeluarkan snapshot terakhir dan me-restore keranjang.
   - Undo **tidak pernah menambah item**.
   - Ucapan "tidak jadi burger" diproses sebagai `remove_item` (bukan undo).
   - Ucapan "batal semua" diproses sebagai `clear_cart` (bukan undo).
5. **Combo Slots:** Definisi slot dan pilihan sah diambil dari `Combo.slots`. Slot wajib (`required=True`) yang belum terisi menyebabkan pesanan combo berstatus pending dan mengarahkan state ke `awaiting_choice`.

---

## 6. Kontrak Parser Intent (Parser Contract)

Dokumen kontrak terpisah didefinisikan di [`docs/design/intent-parser-contract.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/design/intent-parser-contract.md). Dokumen ini merinci:
- Payload konteks yang dikirimkan ke LLM: transkrip ujaran pelanggan, snapshot ringkas isi keranjang saat ini (beserta `line_id`), pertanyaan tertunda (`pending_choice`), dan daftar ID menu beserta alias resmi.
- Payload keluaran yang wajib dikembalikan oleh LLM: envelope JSON valid berisi list intent yang sesuai dengan `intent.schema.json`.
- Memperbaiki kegagalan evaluasi Minggu 2 di mana parser mengevaluasi intent secara terisolasi tanpa mengetahui kondisi keranjang belanja saat ini.

---

## 7. Analisis Keputusan: Keselarasan vs Konflik Rencana

| Aspek Desain | Status vs PROJECT_PLAN.md | Justifikasi |
|---|---|---|
| State Machine Terpisah | **Sesuai Penuh (ADR-0002)** | Menjamin validasi deterministik di luar LLM. |
| Intent Tambahan (`replace_item`, `clear_cart`, `answer_choice`, `decline_more`, `ask_info`, `unknown`) | **Ekstensi Resmi (Tanpa Konflik)** | Memperluas 6 intent dasar (§13) untuk menangani kasus riil ujaran drive-thru tanpa mengubah arsitektur inti. |
| Imunitas Harga Tanpa Field Finansial | **Sesuai Penuh (ADR-0002 & §10 STRIDE)** | Mencegah prompt injection manipulasi harga. |
| Injected Clock | **Sesuai Penuh (§8 & MenuService)** | Menjamin pengujian jam sarapan deterministik tanpa dependensi sistem OS. |
| Pydantic Discriminated Union & JSON Schema | **Sesuai Penuh (§12)** | Standar validasi type-safe Python 3.12. |

*Kesimpulan:* **Tidak ada keputusan yang bertentangan (*conflicting*) dengan PROJECT_PLAN.md.** Seluruh rancangan adalah implementasi langsung dan ekstensi yang selaras dengan arsitektur yang direncanakan.
