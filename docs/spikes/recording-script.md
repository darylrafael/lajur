# Human Voice Recording Guide & Script (Spike 01 STT Benchmark)

**Document:** `docs/spikes/recording-script.md`  
**Purpose:** Provides the 40 sampled evaluation utterances and instructions for recording audio to benchmark STT providers at Gate G1.  
**Author:** Lajur Engineering  
**Version:** 1.0 (Minggu 2)

---

## 1. Recording Specifications & Requirements

All recordings must meet the following technical specifications to ensure compatibility with LiveKit and streaming STT models:
- **Audio Format:** WAV (PCM 16-bit, uncompressed).
- **Channels:** Mono (1 channel). *Stereo recordings will be rejected by the validation script.*
- **Sample Rate:** 16,000 Hz (16 kHz) or higher (48,000 Hz recommended).
- **Target Folder:** `eval/audio/real/` *(This folder is gitignored; audio files must never be committed to git per ADR-0005).*
- **Manifest File:** `eval/audio/real/manifest.csv` *(Pre-populated with expected file names and reference texts).*

---

## 2. Acoustic Conditions

Recordings are grouped into three acoustic conditions to evaluate noise robustness:
1. **`quiet` (Mandatory, 40 files):**
   - Recorded in a quiet indoor room (bedroom or office).
   - Normal conversational speaking distance (15–30 cm from laptop/phone microphone).
   - Filename format: `real_<001-040>_quiet.wav`
2. **`noise` (Recommended, 40 files):**
   - Recorded with continuous background ambient noise (e.g. an electric fan running nearby, TV playing news in the background, or open window with street traffic).
   - Filename format: `real_<001-040>_noise.wav`
3. **`helmet` (Optional, 40 files):**
   - Recorded while wearing a motorcycle helmet (full-face or half-face with visor down), OR speaking through a piece of folded cloth held over your mouth.
   - Simulates the acoustic muffling and high-frequency roll-off typical of two-wheeler drive-thru customers.
   - Filename format: `real_<001-040>_helmet.wav`

> [!TIP]
> You do **NOT** need to record all 120 files at once. You can start by recording only the 40 `quiet` files (`real_001_quiet.wav` through `real_040_quiet.wav`). The validation script and benchmark runner allow partial batches per condition.

---

## 3. The 40 Utterances Recording Script

Read each sentence clearly and naturally at your normal speaking pace. Do not over-enunciate.

| No | Scenario ID | Category | Spoken Reference Text | Target Filenames |
|:---:|:---:|---|---|---|
| 01 | `scen_001` | **Simple Indonesian** | Saya mau pesan burger sapi tunggal satu. | `real_001_quiet.wav`<br>`real_001_noise.wav`<br>`real_001_helmet.wav` |
| 02 | `scen_002` | **Simple Indonesian** | Mau burger sapi keju satu ya. | `real_002_quiet.wav`<br>`real_002_noise.wav`<br>`real_002_helmet.wav` |
| 03 | `scen_004` | **Simple Indonesian** | Pesan burger sapi spesial satu. | `real_003_quiet.wav`<br>`real_003_noise.wav`<br>`real_003_helmet.wav` |
| 04 | `scen_006` | **Simple Indonesian** | Ayam goreng crispy satu mas. | `real_004_quiet.wav`<br>`real_004_noise.wav`<br>`real_004_helmet.wav` |
| 05 | `scen_008` | **Simple Indonesian** | Nasi uduk satu bungkus. | `real_005_quiet.wav`<br>`real_005_noise.wav`<br>`real_005_helmet.wav` |
| 06 | `scen_009` | **Simple Indonesian** | Kentang goreng satu ya. | `real_006_quiet.wav`<br>`real_006_noise.wav`<br>`real_006_helmet.wav` |
| 07 | `scen_011` | **Simple Indonesian** | Es teh manis satu. | `real_007_quiet.wav`<br>`real_007_noise.wav`<br>`real_007_helmet.wav` |
| 08 | `scen_012` | **Simple Indonesian** | Minta air mineral botol satu. | `real_008_quiet.wav`<br>`real_008_noise.wav`<br>`real_008_helmet.wav` |
| 09 | `scen_013` | **Simple Indonesian** | Kopi susu gula aren satu. | `real_009_quiet.wav`<br>`real_009_noise.wav`<br>`real_009_helmet.wav` |
| 10 | `scen_015` | **Simple Indonesian** | Es krim cone vanila satu. | `real_010_quiet.wav`<br>`real_010_noise.wav`<br>`real_010_helmet.wav` |
| 11 | `scen_003` | **Mixed ID-EN** | Can I get one Double Cheeseburger, please. | `real_011_quiet.wav`<br>`real_011_noise.wav`<br>`real_011_helmet.wav` |
| 12 | `scen_005` | **Mixed ID-EN** | Mau crispy chicken burger satu. | `real_012_quiet.wav`<br>`real_012_noise.wav`<br>`real_012_helmet.wav` |
| 13 | `scen_007` | **Mixed ID-EN** | Spicy chicken wings satu porsi. | `real_013_quiet.wav`<br>`real_013_noise.wav`<br>`real_013_helmet.wav` |
| 14 | `scen_010` | **Mixed ID-EN** | I want one sweet corn cup. | `real_014_quiet.wav`<br>`real_014_noise.wav`<br>`real_014_helmet.wav` |
| 15 | `scen_014` | **Mixed ID-EN** | Apple pie satu hangat ya. | `real_015_quiet.wav`<br>`real_015_noise.wav`<br>`real_015_helmet.wav` |
| 16 | `scen_017` | **Mixed ID-EN** | Give me three single beef burgers please. | `real_016_quiet.wav`<br>`real_016_noise.wav`<br>`real_016_helmet.wav` |
| 17 | `scen_023` | **Mixed ID-EN** | Two bottles of mineral water and two colas. | `real_017_quiet.wav`<br>`real_017_noise.wav`<br>`real_017_helmet.wav` |
| 18 | `scen_026` | **Mixed ID-EN** | Kentang goreng satu yang ukuran large ya. | `real_018_quiet.wav`<br>`real_018_noise.wav`<br>`real_018_helmet.wav` |
| 19 | `scen_027` | **Mixed ID-EN** | Kentang goreng medium satu. | `real_019_quiet.wav`<br>`real_019_noise.wav`<br>`real_019_helmet.wav` |
| 20 | `scen_028` | **Mixed ID-EN** | Es teh manis satu yang large. | `real_020_quiet.wav`<br>`real_020_noise.wav`<br>`real_020_helmet.wav` |
| 21 | `scen_030` | **Mixed ID-EN** | Large cola soda, please. | `real_021_quiet.wav`<br>`real_021_noise.wav`<br>`real_021_helmet.wav` |
| 22 | `scen_031` | **Mixed ID-EN** | Burger sapi keju satu, tambah extra cheese ya. | `real_022_quiet.wav`<br>`real_022_noise.wav`<br>`real_022_helmet.wav` |
| 23 | `scen_033` | **Mixed ID-EN** | Double cheeseburger no onions, please. | `real_023_quiet.wav`<br>`real_023_noise.wav`<br>`real_023_helmet.wav` |
| 24 | `scen_035` | **Mixed ID-EN** | Es kopi susu gula aren yang medium, less sugar ya. | `real_024_quiet.wav`<br>`real_024_noise.wav`<br>`real_024_helmet.wav` |
| 25 | `scen_037` | **Mixed ID-EN** | Nugget ayam 6 pcs pakai dipping sauce cheddar cheese dip. | `real_025_quiet.wav`<br>`real_025_noise.wav`<br>`real_025_helmet.wav` |
| 26 | `scen_071` | **Correction / Undo** | Mbak mau kentang goreng satu sama es teh manis. Eh bentar mas, kentangnya tidak jadi deh, ganti nasi putih aja. | `real_026_quiet.wav`<br>`real_026_noise.wav`<br>`real_026_helmet.wav` |
| 27 | `scen_072` | **Correction / Undo** | Pesan burger sapi keju dua. Eh batalin satu deh, jadi cuma satu burger sapi keju. | `real_027_quiet.wav`<br>`real_027_noise.wav`<br>`real_027_helmet.wav` |
| 28 | `scen_073` | **Correction / Undo** | Mau es teh manis satu. Eh gak jadi manis, maunya es teh tawar. | `real_028_quiet.wav`<br>`real_028_noise.wav`<br>`real_028_helmet.wav` |
| 29 | `scen_074` | **Correction / Undo** | Can I get two cheeseburgers please? Wait, scratch that, make it one double cheeseburger instead. | `real_029_quiet.wav`<br>`real_029_noise.wav`<br>`real_029_helmet.wav` |
| 30 | `scen_075` | **Correction / Undo** | Ayam goreng crispy satu sama nasi uduk satu. Eh ayamnya ganti ayam pedas ya, nasinya tetap nasi uduk. | `real_030_quiet.wav`<br>`real_030_noise.wav`<br>`real_030_helmet.wav` |
| 31 | `scen_016` | **Quantities & Combos** | Mau dua burger sapi keju ya. | `real_031_quiet.wav`<br>`real_031_noise.wav`<br>`real_031_helmet.wav` |
| 32 | `scen_017` | **Quantities & Combos** | Give me three single beef burgers please. | `real_032_quiet.wav`<br>`real_032_noise.wav`<br>`real_032_helmet.wav` |
| 33 | `scen_018` | **Quantities & Combos** | Pesan ayam goreng crispy dua potong. | `real_033_quiet.wav`<br>`real_033_noise.wav`<br>`real_033_helmet.wav` |
| 34 | `scen_019` | **Quantities & Combos** | Beli nugget ayam yang isi 6 dua kotak. | `real_034_quiet.wav`<br>`real_034_noise.wav`<br>`real_034_helmet.wav` |
| 35 | `scen_020` | **Quantities & Combos** | Nasi putihnya tiga porsi. | `real_035_quiet.wav`<br>`real_035_noise.wav`<br>`real_035_helmet.wav` |
| 36 | `scen_081` | **Hesitations & Pauses** | Emmm... apa ya sebentar... mau... burger sapi keju satu deh. | `real_036_quiet.wav`<br>`real_036_noise.wav`<br>`real_036_helmet.wav` |
| 37 | `scen_082` | **Hesitations & Pauses** | Wait a minute... umm... let me think... okay, one french fries large. | `real_037_quiet.wav`<br>`real_037_noise.wav`<br>`real_037_helmet.wav` |
| 38 | `scen_083` | **Hesitations & Pauses** | Aduh mau makan apa ya... anu mas... ayam goreng crispy satu sama... es teh manis. | `real_038_quiet.wav`<br>`real_038_noise.wav`<br>`real_038_helmet.wav` |
| 39 | `scen_084` | **Hesitations & Pauses** | Hmm sebentar... kopinya... kopi susu gula aren satu ya. | `real_039_quiet.wav`<br>`real_039_noise.wav`<br>`real_039_helmet.wav` |
| 40 | `scen_085` | **Hesitations & Pauses** | Uhhh... give me... two chicken wings please. | `real_040_quiet.wav`<br>`real_040_noise.wav`<br>`real_040_helmet.wav` |

---

## 4. How to Validate Recordings

After placing your `.wav` files into `eval/audio/real/`, run the automated validation script:

```powershell
uv run python eval/scripts/check_recordings.py
```

The script will automatically check:
- File existence against `eval/audio/real/manifest.csv`.
- Valid WAV PCM format.
- Channels (must be Mono / 1 channel).
- Sample rate (must be $\ge$ 16,000 Hz).
- Audio duration (must be between 0.5s and 30.0s).

It prints a clear checklist and highlights any file that needs re-recording or reformatting.
