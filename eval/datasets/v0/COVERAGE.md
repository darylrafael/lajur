# Laporan Cakupan Dataset Evaluasi (Dataset v0.1)

**File:** `eval/datasets/v0/scenarios.jsonl`  
**Versi Dataset:** v0.1 (Diperbarui pada Minggu 1)  
**Total Skenario:** 135 skenario (seluruhnya bertag `split: "dev"`)  
**Lisensi Data:** CDLA-Permissive-2.0 (`eval/LICENSE-DATA.md`)

---

## 1. Ringkasan Distribusi & Sumber Skenario

| Sumber Skenario | Jumlah | Persentase | Catatan Kualitas |
|---|---:|---:|---|
| **Generated (Template)** | 100 | 74,1% | Dihasilkan dari template kombinasi menu baku (`scen_001` s/d `scen_100`). Frasa cenderung berulang dan mekanis. Berguna untuk *regression coverage* katalog menu dasar. |
| **Handwritten (Natural)** | 35 | 25,9% | Ditulis tangan secara manual (`scen_101` s/d `scen_135`) mencakup bahasa gaul/slang, variasi urutan kata, jeda/keraguan (*hesitation*), serta percampuran bahasa lisan kasual Indonesia–Inggris. |
| **Total** | **135** | **100,0%** | |

---

## 2. Cakupan Perbaikan Titik Lemah (*Thin Spots Fixed*)

Berdasarkan tinjauan awal v0.0, ditemukan 4 titik lemah (*thin spots*) yang telah diperbaiki pada versi v0.1 ini:

| Dimensi Pengujian | Target Minimum | Jumlah Aktual v0.1 | Status |
|---|:---:|:---:|:---:|
| **Percampuran Bahasa (Mixed ID-EN)** | &ge; 40,0% | **54 skenario (40,0%)** | **PASS** |
| **Akustik Helm Motor (`helmet`)** | &ge; 10 skenario | **11 skenario (8,1%)** | **PASS** |
| **Permintaan Kru Manusia (`handoff`)** | &ge; 8 skenario | **8 skenario (5,9%)** | **PASS** |
| **Prank & Prompt Injection (`prank`)** | &ge; 8 skenario | **8 skenario (5,9%)** | **PASS** |
| **Skenario Tulisan Tangan (`handwritten`)** | &ge; 30 skenario | **35 skenario (25,9%)** | **PASS** |

---

## 3. Rincian Distribusi Metrik

### 3.1 Berdasarkan Bahasa (`lang_mix`)
- **Indonesian (`id`):** 66 skenario (48,9%) — Bahasa Indonesia baku dan informal.
- **Mixed ID–EN (`mixed`):** 54 skenario (40,0%) — Percampuran istilah menu Inggris dalam tata bahasa Indonesia (*code-switching*).
- **English (`en`):** 15 skenario (11,1%) — Bahasa Inggris penuh (turis/ekspatriat).

### 3.2 Berdasarkan Profil Derau Akustik (`noise_profile`)
- **Clean (`clean`):** 84 skenario (62,2%) — Audio bersih / dalam mobil tanpa gangguan.
- **Motorcycle Idle (`motor_idle`):** 25 skenario (18,5%) — Suara mesin motor bebek/matic menyala stasioner di antrean drive-thru.
- **Traffic & Rain (`traffic_rain`):** 15 skenario (11,1%) — Derau lalu lintas jalan raya dan hujan rintik.
- **Closed Helmet Acoustic (`helmet`):** 11 skenario (8,1%) — Redaman busa helm *full-face* dengan pemotongan frekuensi tinggi (~3 kHz).

### 3.3 Berdasarkan Tag Kategori Pesanan
```text
code_switching: 52
burger:         33
minuman:        33
combo:          24
ayam:           22
modifier:       21
side:           19
simple:         15
quantity:       14
dessert:        13
correction:     11
undo:            9
handoff:         8
prank:           8
sarapan:         7
hesitation:      7
breakfast:       7
nasi:            5
out_of_stock:    5
injection:       5
upsize:          3
upsell:          3
ambiguous:       3
abuse:           3
```

---

## 4. Rencana Pengembangan Dataset Berikutnya (Minggu 7 / Gerbang G2)
- Saat ini seluruh skenario berada di partisi `split: "dev"`.
- Dataset `held-out` (uji buta tanpa tuning) sengaja **belum dibuat** pada Minggu 1 untuk mencegah *data leakage* dan *overfitting* dini (Hard Rule 3 & ADR-0007).
- Pada Minggu 7, korpus akan diperluas ke 150+ skenario dengan kunci pemisahan *held-out split* resmi untuk penetapan baseline akurasi OAR.
