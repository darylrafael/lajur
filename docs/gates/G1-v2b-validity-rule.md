# Gate G1-v2b Benchmark Turn Validity Rule (Minggu 4d)

**Document:** `docs/gates/G1-v2b-validity-rule.md`  
**Milestone:** Minggu 4d — Aturan Validitas Data dan Penanganan Anomali Stempel Waktu v2b  
**Date:** 2026-10-26  
**Author:** Daryl (Solo Dev)  
**Status:** PRE-REGISTERED VALIDITY RULE — COMMITTED BEFORE RECOMPUTING  

---

## 1. Latar Belakang Masalah (*Problem Statement*)

Pada laporan awal [`docs/gates/G1-v2b-results.md`](file:///c:/Users/Lenovo/Downloads/drivethru/docs/gates/G1-v2b-results.md), metrik persentil ke-95 ($P95$) tercatat sebesar **$172.143.222,3\text{ ms}$** ($\approx 47,8\text{ jam}$). Angka ini mustahil secara fisik untuk sebuah giliran percakapan drive-thru.

Audit stempel waktu mentah pada basis data SQLite (`data/turn_events.sqlite3`) mengungkap bahwa beberapa giliran menghitung latensi dari nilai mutlak *system boot clock* karena titik referensi akhir ucapan (`t_speech_end`) tidak pernah tercatat (`t_speech_end == 0.0`).

### Penyebab dalam Kode (*Root Cause in Code*)
Pada [`eval/scripts/spikes/benchmark_week04_g1_v2.py:516-521`](file:///c:/Users/Lenovo/Downloads/drivethru/eval/scripts/spikes/benchmark_week04_g1_v2.py#L516-L521):
```python
samples_sent = 0
for c_idx in range(num_chunks):
    # ...
    if t_speech_end == 0.0 and samples_sent >= active_samples:
        t_speech_end = time.perf_counter()

    if stt_done_event.is_set():
        break
```
Ketika giliran sebelumnya (misal Turn 12) mengalami timeout dan memanggil `dg_stream.finalize()`, respons pesan `speech_final` dari Deepgram kadang baru tiba beberapa milidetik setelah giliran berikutnya (Turn 13) dimulai. Pesan terlambat tersebut memicu `stt_done_event.set()`. Akibatnya, pada *chunk* ke-0 (`c_idx == 0`, `samples_sent == 320`), pernyataan `if stt_done_event.is_set(): break` langsung memutus loop sebelum `samples_sent >= active_samples` tercapai. Variabel `t_speech_end` tetap bernilai `0.0`.

Pada penghitungan latensi:
```python
turn_latency_ms = max(0.0, (t_first_audio_received - t_speech_end) * 1000.0)
```
Karena `t_speech_end == 0.0`, latensi menjadi $(T_{\text{first\_audio}} - 0.0) \times 1.000$, yang merefleksikan nilai mutlak `time.perf_counter()` komputer sejak Windows dinyalakan (~172.140 detik).

---

## 2. Aturan Validitas Objektif (*The Validity Rule*)

Untuk menjamin integritas ilmiah tanpa memanipulasi data historis, diberlakukan aturan validitas berikut:

1. **Definisi Giliran Valid (*Valid Turn*):**
   Sebuah giliran dalam data mentah dinyatakan **VALID** jika dan hanya jika:
   - Stempel waktu referensi akhir ucapan tercatat secara riil ($t_{\text{speech\_end}} > 0,0$).
   - Total latensi turn terukur berada dalam batas percakapan manusiawi yang masuk akal:
     $$0\text{ ms} < \text{turn\_latency\_ms} \le 60.000\text{ ms}\quad (\le 60\text{ detik})$$
2. **Definisi Giliran Tidak Valid (*Invalid Turn*):**
   Setiap giliran yang memiliki $t_{\text{speech\_end}} == 0,0$ atau $\text{turn\_latency\_ms} > 60.000\text{ ms}$ diklasifikasikan sebagai **INVALID (cacat pencatatan jam referensi / anomali harness)**.
3. **Aturan Pelaporan Ganda Wajib (*Mandatory Dual Reporting Rule*):**
   - Dilarang keras membuang (*drop*) giliran secara diam-diam.
   - Setiap laporan publikasi **WAJIB** menyajikan dua kelompok data secara berdampingan:
     1. **Semua Giliran Sebagaimana Tercatat (*All Turns as Recorded*, $n=20$)**
     2. **Giliran Valid Saja (*Valid Turns Only*, $n_{\text{valid}}$)** lengkap dengan nilai $n_{\text{valid}}$, P50, P95, dan Bootstrap 95% Confidence Interval.

---

## 3. Identifikasi Giliran Tidak Valid pada Dataset G1-v2b

Berdasarkan aturan di atas, dari 20 giliran yang dieksekusi pada [`eval/results/g1_week04_v2b_benchmark.json`](file:///c:/Users/Lenovo/Downloads/drivethru/eval/results/g1_week04_v2b_benchmark.json):

| Turn ID | Skenario ID | Total Latensi Tercatat | Nilai $t_{\text{speech\_end}}$ | Penyebab Kode | Klasifikasi |
| :---: | :---: | :---: | :---: | :--- | :---: |
| **Turn 13** | `scen_028` | $172.114.890,8\text{ ms}$ | $0,0\text{ ms}$ | `stt_done_event` terpicu prematur pada chunk 0 dari sisa finalize turn 12 | **INVALID** |
| **Turn 15** | `scen_031` | $172.142.418,9\text{ ms}$ | $0,0\text{ ms}$ | `stt_done_event` terpicu prematur pada chunk 0 dari sisa finalize turn 14 | **INVALID** |
| **Turn 16** | `scen_071` | $172.158.487,1\text{ ms}$ | $0,0\text{ ms}$ | `stt_done_event` terpicu prematur pada chunk 0 dari sisa finalize turn 15 | **INVALID** |

Sebanyak **17 giliran lainnya** (Turn 01–12, 14, 17–20) memiliki $t_{\text{speech\_end}} > 0$ dan total latensi di rentang $1.881,9\text{ ms}$ hingga $8.206,0\text{ ms}$, sehingga berstatus **VALID ($n_{\text{valid}} = 17$)**.
