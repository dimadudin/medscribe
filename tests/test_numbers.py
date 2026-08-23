"""Unit tests for the comma-decimal disambiguation and token-gate internals."""

from parser import _is_numeric_token, _select_numbers, _token_variants, _tokens_compatible


class TestTokenVariants:
    def test_plain_integer(self):
        assert _token_variants("50") == [[50.0]]

    def test_leading_zero_forces_merge(self):
        assert _token_variants("0,7") == [[0.7]]

    def test_two_part_single_digit_tail_prefers_decimal(self):
        assert _token_variants("21,2")[0] == [21.2]
        assert _token_variants("108,2")[0] == [108.2]

    def test_multi_digit_tail_prefers_separate_ints(self):
        assert _token_variants("12,13")[0] == [12.0, 13.0]
        assert _token_variants("32,47")[0] == [32.0, 47.0]

    def test_three_parts_enumerate_all_readings(self):
        assert [9.0, 12.0, 8.0] in _token_variants("9,12,8")
        assert [9.12, 8.0] in _token_variants("9,12,8")


class TestSelectNumbers:
    def test_exact_count_from_separate_tokens(self):
        assert _select_numbers(["48", "32"], 2) == [48.0, 32.0]

    def test_group_count_resolves_three_part_token(self):
        assert _select_numbers(["9,12,8"], 3) == [9.0, 12.0, 8.0]

    def test_pair_count_splits_two_part_token(self):
        assert _select_numbers(["32,47"], 2) == [32.0, 47.0]

    def test_decimal_across_adjacent_tokens(self):
        assert _select_numbers(["7,8", "9", "4"], 3) == [7.8, 9.0, 4.0]

    def test_single_field_takes_preferred_reading(self):
        assert _select_numbers(["21,2"], 1)[0] == 21.2
        assert _select_numbers(["0,14"], 1)[0] == 0.14
        assert _select_numbers(["12,13"], 1)[0] == 12.0

    def test_spaced_commas_never_join(self):
        assert _select_numbers(["12", "13"], 2) == [12.0, 13.0]


class TestNumericTokens:
    def test_digits(self):
        assert _is_numeric_token("38")

    def test_trailing_punctuation_still_numeric(self):
        assert _is_numeric_token("39,")
        assert _is_numeric_token("3,3,")

    def test_words_rejected(self):
        assert not _is_numeric_token("ац")
        assert not _is_numeric_token("предсердие")

    def test_gate_blocks_digit_word_confusion(self):
        assert not _tokens_compatible(
            ["эффективное", "отверстие", "мк"],
            ["эффективное", "отверстие", "3,3,"],
        )

    def test_gate_allows_class_consistent_fuzzy_window(self):
        assert _tokens_compatible(
            ["правая", "предсердие", "4", "ац"],
            ["правая", "предсердие", "38", "на"],
        )

    def test_gate_allows_matching_classes(self):
        assert _tokens_compatible(
            ["4", "ац", "правое", "предсердие"],
            ["4", "ац", "правое", "предсердие"],
        )
