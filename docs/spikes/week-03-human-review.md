# Week 03 Human Review: Sample 20 Scenarios

> **Label:** unverified: agent-authored for human review
>
> Dokumen ini memuat 20 sampel skenario pesanan untuk verifikasi manusia.
> Mencakup seluruh 11 skenario koreksi/pembatalan (correction/undo) plus 9 skenario acak terdistribusi (random seed: 42).

---

## Skenario `scen_071`
**Tags:** `['correction', 'undo', 'side', 'nasi', 'minuman']`

### Transkrip Percakapan (Utterances)
1. *"Mbak mau kentang goreng satu sama es teh manis."*
2. *"Eh bentar mas, kentangnya tidak jadi deh, ganti nasi putih aja."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "kentang_goreng", "quantity": 1, "size": "regular"}`<br>• **`add_item`** `{"item_id": "es_teh_manis", "quantity": 1, "size": "regular"}`<br>• **`replace_item`** `{"target_item_id": "kentang_goreng", "replacement_item_id": "nasi_putih", "quantity": 1, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 17,000<br>**Items:**<br>• `es_teh_manis` x1 (regular) Rp 9,000<br>• `nasi_putih` x1 (regular) Rp 8,000 |

---

## Skenario `scen_072`
**Tags:** `['correction', 'undo', 'burger']`

### Transkrip Percakapan (Utterances)
1. *"Pesan burger sapi keju dua."*
2. *"Eh batalin satu deh, jadi cuma satu burger sapi keju."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "burger_sapi_keju", "quantity": 2, "size": "regular"}`<br>• **`remove_item`** `{"item_id": "burger_sapi_keju", "quantity": 1}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 28,000<br>**Items:**<br>• `burger_sapi_keju` x1 (regular) Rp 28,000 |

---

## Skenario `scen_073`
**Tags:** `['correction', 'undo', 'minuman']`

### Transkrip Percakapan (Utterances)
1. *"Mau es teh manis satu."*
2. *"Eh gak jadi manis, maunya es teh tawar."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "es_teh_manis", "quantity": 1, "size": "regular"}`<br>• **`replace_item`** `{"target_item_id": "es_teh_manis", "replacement_item_id": "es_teh_original", "quantity": 1, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 8,000<br>**Items:**<br>• `es_teh_original` x1 (regular) Rp 8,000 |

---

## Skenario `scen_074`
**Tags:** `['correction', 'undo', 'burger']`

### Transkrip Percakapan (Utterances)
1. *"Can I get two cheeseburgers please?"*
2. *"Wait, scratch that, make it one double cheeseburger instead."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "burger_sapi_keju", "quantity": 2, "size": "regular"}`<br>• **`replace_item`** `{"target_item_id": "burger_sapi_keju", "replacement_item_id": "burger_sapi_keju_ganda", "quantity": 1, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 39,000<br>**Items:**<br>• `burger_sapi_keju_ganda` x1 (regular) Rp 39,000 |

---

## Skenario `scen_075`
**Tags:** `['correction', 'undo', 'ayam', 'nasi']`

### Transkrip Percakapan (Utterances)
1. *"Ayam goreng crispy satu sama nasi uduk satu."*
2. *"Eh ayamnya ganti ayam pedas ya, nasinya tetap nasi uduk."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "ayam_goreng_crispy", "quantity": 1, "size": "regular"}`<br>• **`add_item`** `{"item_id": "nasi_uduk", "quantity": 1, "size": "regular"}`<br>• **`replace_item`** `{"target_item_id": "ayam_goreng_crispy", "replacement_item_id": "ayam_goreng_pedas", "quantity": 1, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 32,000<br>**Items:**<br>• `ayam_goreng_pedas` x1 (regular) Rp 22,000<br>• `nasi_uduk` x1 (regular) Rp 10,000 |

---

## Skenario `scen_076`
**Tags:** `['correction', 'modifier', 'side']`

### Transkrip Percakapan (Utterances)
1. *"Mau kentang goreng regular satu."*
2. *"Bentar mas, tolong di-upsize ke large ya kentangnya."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "kentang_goreng", "quantity": 1, "size": "regular"}`<br>• **`modify_item`** `{"item_id": "kentang_goreng", "size": "large"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 25,000<br>**Items:**<br>• `kentang_goreng` x1 (large) Rp 25,000 |

---

## Skenario `scen_077`
**Tags:** `['correction', 'combo']`

### Transkrip Percakapan (Utterances)
1. *"Pesan paket hemat ayam satu potong."*
2. *"Minumnya ganti jadi soda lemon ya, jangan es teh."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "paket_hemat_ayam_1", "quantity": 1, "size": "regular", "slot_choices": {"main": "ayam_goreng_crispy", "side": "nasi_putih", "drink": "es_teh_manis"}}`<br>• **`modify_item`** `{"item_id": "paket_hemat_ayam_1", "slot_choices": {"drink": "soda_lemon"}}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 34,000<br>**Items:**<br>• `paket_hemat_ayam_1` x1 (regular) Rp 34,000<br>&nbsp;&nbsp;*slots:* `{'main': 'ayam_goreng_crispy', 'side': 'nasi_putih', 'drink': 'soda_lemon'}` |

---

## Skenario `scen_078`
**Tags:** `['correction', 'undo', 'dessert']`

### Transkrip Percakapan (Utterances)
1. *"Order nugget ayam 6 pcs sama pai apel."*
2. *"Pai apelnya gak jadi deh, ganti pai cokelat."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "nugget_ayam_6", "quantity": 1, "size": "regular"}`<br>• **`add_item`** `{"item_id": "pai_apel", "quantity": 1, "size": "regular"}`<br>• **`replace_item`** `{"target_item_id": "pai_apel", "replacement_item_id": "pai_cokelat", "quantity": 1, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 44,000<br>**Items:**<br>• `nugget_ayam_6` x1 (regular) Rp 28,000<br>• `pai_cokelat` x1 (regular) Rp 16,000 |

---

## Skenario `scen_079`
**Tags:** `['correction', 'undo', 'minuman']`

### Transkrip Percakapan (Utterances)
1. *"Burger sapi tunggal dua sama es teh manis dua."*
2. *"Gak jadi es teh manisnya, semuanya batalin minumnya."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "burger_sapi_tunggal", "quantity": 2, "size": "regular"}`<br>• **`add_item`** `{"item_id": "es_teh_manis", "quantity": 2, "size": "regular"}`<br>• **`remove_item`** `{"item_id": "es_teh_manis"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 44,000<br>**Items:**<br>• `burger_sapi_tunggal` x2 (regular) Rp 44,000 |

---

## Skenario `scen_080`
**Tags:** `['correction', 'undo']`

### Transkrip Percakapan (Utterances)
1. *"Mau pesan burger sapi keju satu."*
2. *"Eh batalin semuanya mas, gak jadi beli."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "burger_sapi_keju", "quantity": 1, "size": "regular"}`<br>• **`clear_cart`** | **Status:** `empty`<br>**Total:** Rp 0<br>**Items:**<br>*[Keranjang Kosong]* |

---

## Skenario `scen_134`
**Tags:** `['correction', 'undo', 'burger', 'minuman', 'code_switching']`

### Transkrip Percakapan (Utterances)
1. *"Mas, mau order double cheeseburger satu sama mineral water."*
2. *"Eh sorry mas, double cheeseburger-nya ganti crispy chicken burger aja deh, minumnya tetap."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "burger_sapi_keju_ganda", "quantity": 1, "size": "regular"}`<br>• **`add_item`** `{"item_id": "air_mineral", "quantity": 1, "size": "regular"}`<br>• **`replace_item`** `{"target_item_id": "burger_sapi_keju_ganda", "replacement_item_id": "burger_ayam_crispy", "quantity": 1, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 34,000<br>**Items:**<br>• `burger_ayam_crispy` x1 (regular) Rp 26,000<br>• `air_mineral` x1 (regular) Rp 8,000 |

---

## Skenario `scen_004`
**Tags:** `['simple', 'burger']`

### Transkrip Percakapan (Utterances)
1. *"Pesan burger sapi spesial satu."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "burger_sapi_spesial", "quantity": 1, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 45,000<br>**Items:**<br>• `burger_sapi_spesial` x1 (regular) Rp 45,000 |

---

## Skenario `scen_014`
**Tags:** `['simple', 'code_switching', 'dessert']`

### Transkrip Percakapan (Utterances)
1. *"Apple pie satu hangat ya."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "pai_apel", "quantity": 1, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 15,000<br>**Items:**<br>• `pai_apel` x1 (regular) Rp 15,000 |

---

## Skenario `scen_015`
**Tags:** `['simple', 'dessert']`

### Transkrip Percakapan (Utterances)
1. *"Es krim cone vanila satu."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "es_krim_vanila", "quantity": 1, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 9,000<br>**Items:**<br>• `es_krim_vanila` x1 (regular) Rp 9,000 |

---

## Skenario `scen_018`
**Tags:** `['quantity', 'ayam']`

### Transkrip Percakapan (Utterances)
1. *"Pesan ayam goreng crispy dua potong."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "ayam_goreng_crispy", "quantity": 2, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 42,000<br>**Items:**<br>• `ayam_goreng_crispy` x2 (regular) Rp 42,000 |

---

## Skenario `scen_029`
**Tags:** `['modifier', 'minuman']`

### Transkrip Percakapan (Utterances)
1. *"Soda kola ukuran medium satu."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "soda_kola", "quantity": 1, "size": "medium"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 16,000<br>**Items:**<br>• `soda_kola` x1 (medium) Rp 16,000 |

---

## Skenario `scen_032`
**Tags:** `['modifier', 'burger']`

### Transkrip Percakapan (Utterances)
1. *"Burger sapi keju ganda satu, jangan pakai acar."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "burger_sapi_keju_ganda", "quantity": 1, "size": "regular", "modifiers": ["no_pickles"]}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 39,000<br>**Items:**<br>• `burger_sapi_keju_ganda` x1 (regular) Rp 39,000<br>&nbsp;&nbsp;*modifiers:* `['no_pickles']` |

---

## Skenario `scen_036`
**Tags:** `['modifier', 'minuman']`

### Transkrip Percakapan (Utterances)
1. *"Es teh manis satu jangan pakai es."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "es_teh_manis", "quantity": 1, "size": "regular", "modifiers": ["ice_none"]}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 9,000<br>**Items:**<br>• `es_teh_manis` x1 (regular) Rp 9,000<br>&nbsp;&nbsp;*modifiers:* `['ice_none']` |

---

## Skenario `scen_092`
**Tags:** `['breakfast', 'sarapan']`

### Transkrip Percakapan (Utterances)
1. *"Muffin daging telur satu sama hash brown satu."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`add_item`** `{"item_id": "muffin_daging_telur", "quantity": 1, "size": "regular"}`<br>• **`add_item`** `{"item_id": "hash_brown", "quantity": 1, "size": "regular"}`<br>• **`confirm`** | **Status:** `confirmed`<br>**Total:** Rp 44,000<br>**Items:**<br>• `muffin_daging_telur` x1 (regular) Rp 32,000<br>• `hash_brown` x1 (regular) Rp 12,000 |

---

## Skenario `scen_105`
**Tags:** `['handoff']`

### Transkrip Percakapan (Utterances)
1. *"Woy mas, panggil orang aslinya dong, saya buru-buru nih."*

### Side-by-Side: Gold Intents vs Expected Cart

| Turn / Hand-Written Intents (`gold_intents_v2.jsonl`) | Expected Cart State (`scenarios.jsonl`) |
| :--- | :--- |
| • **`handoff`** `{"reason": "customer_requested_human_crew"}` | **Status:** `handoff`<br>**Total:** Rp 0<br>**Items:**<br>*[Keranjang Kosong]* |

---
