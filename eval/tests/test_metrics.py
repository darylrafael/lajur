"""Unit tests for speech evaluation metrics (Normalization, WER, KER)."""

from eval.metrics.ker import calculate_ker
from eval.metrics.normalization import normalize_text
from eval.metrics.wer import calculate_wer


def test_normalization_basic_and_punctuation():
    raw = "Halo! Saya Mau Pesan Burger Sapi, Tolong Ya?"
    expected = "halo saya mau pesan burger sapi tolong ya"
    assert normalize_text(raw, canonicalize=False) == expected


def test_normalization_numbers_indonesian():
    raw = "pesan burger sapi satu kentang dua cola tiga sepuluh"
    expected = "pesan burger sapi 1 kentang 2 cola 3 10"
    assert normalize_text(raw, canonicalize=False) == expected


def test_normalization_numbers_compounds():
    raw = "nugget dua puluh satu dan sayap lima belas"
    expected = "nugget 21 dan sayap 15"
    assert normalize_text(raw, canonicalize=False) == expected


def test_normalization_numbers_english():
    raw = "one cheeseburger and two large fries please"
    expected = "1 cheeseburger and 2 large fries please"
    assert normalize_text(raw, canonicalize=False) == expected


def test_normalization_alias_canonicalization():
    raw = "saya mau french fries satu dan double cheeseburger dua"
    # french fries -> kentang goreng, double cheeseburger -> burger sapi keju ganda
    norm = normalize_text(raw, canonicalize=True)
    assert "kentang goreng" in norm
    assert "burger sapi keju ganda" in norm
    assert "1" in norm
    assert "2" in norm


def test_wer_exact_match():
    ref = "saya mau pesan burger sapi tunggal satu"
    hyp = "saya mau pesan burger sapi tunggal satu"
    res = calculate_wer(ref, hyp)
    assert res.wer == 0.0
    assert res.substitutions == 0
    assert res.deletions == 0
    assert res.insertions == 0
    # "saya", "mau", "pesan", "burger", "sapi", "tunggal", "1" -> 7 words
    assert res.hits == 7
    assert res.ref_length == 7


def test_wer_substitution():
    ref = "saya mau burger sapi"
    hyp = "saya mau ayam krispi"  # burger sapi -> ayam krispi (2 substitutions)
    res = calculate_wer(ref, hyp, normalize=False)
    assert res.substitutions == 2
    assert res.hits == 2
    assert res.wer == 0.5


def test_wer_deletion_and_insertion():
    # Test distinct words for unambiguous alignment
    ref = "pesan burger sekarang"
    hyp = "pesan kentang sekarang cepat"  # sub: burger -> kentang, ins: cepat
    res = calculate_wer(ref, hyp, normalize=False)
    assert res.hits == 2  # pesan, sekarang
    assert res.substitutions == 1  # burger -> kentang
    assert res.insertions == 1  # cepat
    assert res.deletions == 0
    assert res.wer == 2 / 3


def test_wer_pure_deletion():
    ref = "pesan burger sapi sekarang"
    hyp = "pesan burger sekarang"  # deleted "sapi"
    res = calculate_wer(ref, hyp, normalize=False)
    assert res.deletions == 1
    assert res.hits == 3
    assert res.insertions == 0
    assert res.substitutions == 0
    assert res.wer == 1 / 4


def test_wer_empty_cases():
    assert calculate_wer("", "").wer == 0.0
    assert calculate_wer("halo", "").wer == 1.0
    assert calculate_wer("", "halo").wer == 1.0


def test_ker_exact_match():
    ref = "saya mau pesan burger sapi tunggal satu"
    hyp = "saya mau pesan burger sapi tunggal satu"
    res = calculate_ker(ref, hyp)
    assert res.ker == 0.0
    assert res.hits == 2  # ITEM:burger_sapi_tunggal, QTY:1
    assert res.substitutions == 0
    assert res.deletions == 0
    assert res.insertions == 0


def test_ker_alias_matching():
    # User said English alias "french fries" in hyp, ref is Indonesian "kentang goreng"
    ref = "kentang goreng satu"
    hyp = "french fries satu"
    res = calculate_ker(ref, hyp)
    assert res.ker == 0.0
    assert res.hits == 2  # Both extract ITEM:kentang_goreng and QTY:1


def test_ker_item_substitution():
    # Ordered single beef burger, transcribed as cheese burger
    ref = "burger sapi tunggal satu"  # ITEM:burger_sapi_tunggal, QTY:1
    hyp = "burger sapi keju satu"  # ITEM:burger_sapi_keju, QTY:1
    res = calculate_ker(ref, hyp)
    assert res.substitutions == 1
    assert res.hits == 1  # QTY:1 hits
    assert res.ker == 0.5


def test_ker_quantity_substitution():
    ref = "burger sapi tunggal dua"  # ITEM:burger_sapi_tunggal, QTY:2
    hyp = "burger sapi tunggal satu"  # ITEM:burger_sapi_tunggal, QTY:1
    res = calculate_ker(ref, hyp)
    assert res.substitutions == 1  # QTY:2 -> QTY:1
    assert res.hits == 1
    assert res.ker == 0.5


def test_ker_missed_size_modifier():
    ref = "es teh manis ukuran large satu"  # ITEM:es_teh_manis, SIZE:size_large, QTY:1
    hyp = "es teh manis satu"  # ITEM:es_teh_manis, QTY:1 (size missed)
    res = calculate_ker(ref, hyp)
    assert res.deletions == 1  # Missed size
    assert res.hits == 2
    assert res.ref_count == 3
    assert res.ker == 1 / 3


def test_ker_inserted_item():
    ref = "burger sapi tunggal satu"  # ITEM:burger_sapi_tunggal, QTY:1
    hyp = "burger sapi tunggal satu dan air mineral satu"  # + ITEM:air_mineral, QTY:1
    res = calculate_ker(ref, hyp)
    assert res.insertions == 2
    assert res.hits == 2
    assert res.ref_count == 2
    assert res.ker == 1.0  # (0 S + 0 D + 2 I) / 2 = 1.0


def test_ker_empty():
    res = calculate_ker("hallo selamat siang", "halo selamat siang")
    # Neither has menu keywords
    assert res.ref_count == 0
    assert res.ker == 0.0
