# Speech Recognition & Keyword Metrics Specification

**Document:** `docs/eval/metrics.md`  
**Applies To:** Spike 01 (STT), Eval Harness (Minggu 7), Gate G1 Review  
**Author:** Lajur Engineering  
**Version:** 1.0 (Minggu 2 Baseline)

---

## 1. Overview and Engineering Rationale

In voice-ordering drive-thru systems handling Indonesian-English code-switched speech, traditional general-purpose speech metrics (like generic Word Error Rate) fail to measure domain viability:
1. **Conversational Variance:** A customer saying *"Saya mau pesan satu burger sapi"* vs *"Pesan 1 burger sapi dong"* has a high standard WER due to conversational particles (*dong, ya, tolong*), yet the actual ordering payload is 100% identical and successful.
2. **Code-Switching Discrepancies:** English loan words (e.g., *"french fries"* vs *"kentang goreng"*, *"cheeseburger"* vs *"burger sapi keju"*) must not penalize an STT engine if the menu alias maps directly to the same underlying item.
3. **Domain Criticality:** Misrecognizing *"burger sapi tunggal"* as *"burger sapi keju"* or confusing quantity *"1"* with *"2"* directly causes wrong food preparation, customer dissatisfaction, and revenue discrepancies.

To address this, Lajur implements two complementary metrics:
- **Normalized WER (Word Error Rate):** Measures acoustic and textual transcription fidelity across all spoken words.
- **KER (Keyword Error Rate):** Measures semantic extraction accuracy strictly across domain-critical entities (items, modifiers, sizes, quantities). Gate G1 enforces $\text{KER} \le 15\%$ on clean Indonesian-English utterances.

---

## 2. Text Normalization Pipeline

Before computing WER or KER, raw transcripts are processed through a deterministic normalization pipeline:

### 2.1 Lowercasing and Punctuation Stripping
- All characters are lowercased.
- Hyphens (`-`) and slashes (`/`) are transformed to whitespace (e.g., *"di-upsize"* &rarr; *"di upsize"*, *"besar/large"* &rarr; *"besar large"*).
- All remaining punctuation marks (`. , ! ? ; : " '`) are removed.
- Consecutive whitespace is collapsed into single spaces.

### 2.2 Number Word to Numeric Digit Conversion
Both Indonesian and English spoken number words are deterministically converted into Arabic numeral digits to ensure fair acoustic comparison:
- **Indonesian:** *"satu"* &rarr; `"1"`, *"dua"* &rarr; `"2"`, *"sepuluh"* &rarr; `"10"`, *"sebelas"* &rarr; `"11"`, *"dua puluh satu"* &rarr; `"21"`, etc.
- **English:** *"one"* &rarr; `"1"`, *"two"* &rarr; `"2"`, *"ten"* &rarr; `"10"`, *"twenty one"* &rarr; `"21"`, etc.
- Compound numbers (e.g., *"dua puluh lima"*, *"twenty five"*) are matched greedily before single-digit words to prevent partial substitutions.

### 2.3 Menu Alias Canonicalization
Aliases defined in `eval/menu/menu.json` are mapped to their canonical item or modifier names. For instance:
- *"french fries"* &rarr; `"kentang goreng renyah"`
- *"double cheeseburger"* &rarr; `"burger sapi keju ganda"`
- *"mcspicy kw"* &rarr; `"burger ayam pedas"`
- *"no ice"* / *"less ice"* &rarr; canonical modifier option forms

Longer phrases are canonicalized first to avoid subphrase collisions.

---

## 3. Word Error Rate (WER)

### 3.1 Mathematical Definition
$$\text{WER} = \frac{S + D + I}{N}$$

Where:
- $N$: Total number of words in the normalized reference transcript.
- $S$: Number of substituted words.
- $D$: Number of deleted (missed) words.
- $I$: Number of inserted (hallucinated) words.

### 3.2 Sequence Alignment
$S, D,$ and $I$ are calculated via the standard dynamic programming Levenshtein algorithm (Wagner-Fischer) at the whitespace-delimited word level.

**Edge Cases:**
- If $N = 0$ and hypothesis is empty ($M = 0$): $\text{WER} = 0.0$.
- If $N = 0$ and hypothesis is non-empty ($M > 0$): $\text{WER} = 1.0$.

---

## 4. Keyword Error Rate (KER)

### 4.1 Keyword Definition
A keyword $k$ is any critical entity extracted from the transcript that falls into one of four domain categories:
1. **`ITEM`:** Canonical menu item ID or combo ID (e.g. `ITEM:burger_sapi_tunggal`, `ITEM:combo_ayam_1`).
2. **`MODIFIER`:** Modifier group and option identifier (e.g. `MODIFIER:mod_ice:ice_no`, `MODIFIER:mod_sauce_dip:dip_bbq`).
3. **`SIZE`:** Size variant identifier (e.g. `SIZE:size_regular`, `SIZE:size_large`).
4. **`QUANTITY`:** Arabic numeral digit indicating quantity (e.g. `QUANTITY:1`, `QUANTITY:2`, `QUANTITY:10`).

### 4.2 Keyword Extraction
Keywords are extracted using greedy longest-match regex patterns constructed dynamically from `eval/menu/menu.json`. Non-keyword conversational filler words (*"saya"*, *"mau"*, *"pesan"*, *"tolong"*, *"ya"*) are discarded during extraction.

### 4.3 Error Counting & Sequence Alignment
Let $K_{\text{ref}} = [k_1, k_2, \dots, k_{N_k}]$ be the sequential list of keyword tokens in the reference transcript.  
Let $K_{\text{hyp}} = [h_1, h_2, \dots, h_{M_k}]$ be the sequential list of keyword tokens in the hypothesis transcript.

We perform optimal sequence alignment between $K_{\text{ref}}$ and $K_{\text{hyp}}$ minimizing total edit distance:
- **Hit ($H_k$):** $k_i == h_j$ (Reference and hypothesis agree on the canonical keyword at the corresponding position). Cost = 0.
- **Missed Keyword / Deletion ($D_k$):** A keyword in $K_{\text{ref}}$ that was omitted in $K_{\text{hyp}}$ (e.g., customer ordered a large size, but STT missed the size token). Cost = 1.
- **Inserted Keyword ($I_k$):** A keyword in $K_{\text{hyp}}$ that does not exist in $K_{\text{ref}}$ (e.g., STT hallucinated an extra drink). Cost = 1.
- **Substituted Keyword ($S_k$):** A keyword in $K_{\text{ref}}$ aligned to a differing keyword in $K_{\text{hyp}}$ (e.g., customer ordered `burger_sapi_tunggal`, but STT returned `burger_sapi_keju`; or customer ordered quantity `2`, but STT returned quantity `1`). Cost = 1.

$$\text{KER} = \frac{S_k + D_k + I_k}{N_k}$$

Where $N_k = |K_{\text{ref}}|$ is the total number of keywords in the reference transcript.

### 4.4 Why Sequence Alignment over Set Difference?
A naive set symmetric difference ($\frac{|K_{\text{ref}} \Delta K_{\text{hyp}}|}{|K_{\text{ref}}|}$) fails on multi-item orders:
- Example: *"2 burger sapi tunggal dan 1 kentang goreng"*.
- If the model transcribes: *"1 burger sapi tunggal dan 2 kentang goreng"*, the multiset of entities (`{1, 2, burger, kentang}`) would appear identical in an unordered set, masking a critical order quantity reversal!
- Sequence alignment preserves the ordering context between numbers and food items, accurately penalizing quantity mismatches as substitutions.

---

## 5. Gate G1 Criteria Verification

In accordance with `docs/PROJECT_PLAN.md` §3.2:
> **Gate G1 Condition:** *"Tidak ada vendor STT dengan KER ≤ 15% pada set ucapan ID–EN bersih dan latensi turn estimasi ≤ 1,2s"*

Spike 01 benchmarks four candidate STT engines against clean real recordings and synthetic audio. Any candidate exceeding 15% KER on clean speech is disqualified from serving as the primary STT provider.
