import pytest
from proofer.text_utils import (
    extract_words,
    has_spelling_corrections,
    normalize_line_endings,
)


class TestExtractWords:
    def test_extract_words_basic(self):
        text = "Hello world test"
        result = extract_words(text)
        assert result == ["hello", "world", "test"]

    @pytest.mark.parametrize("text", ["", "   ", "\n\t"])
    def test_extract_words_empty_or_whitespace(self, text):
        assert extract_words(text) == []

    def test_extract_words_with_punctuation(self):
        text = "Hello, world! How are you?"
        result = extract_words(text)
        assert result == ["hello", "world", "how", "are", "you"]

    def test_extract_words_mixed_case(self):
        text = "Hello WORLD Test"
        result = extract_words(text)
        assert result == ["hello", "world", "test"]

    def test_extract_words_numbers_and_underscores(self):
        text = "test_var 123 hello_world"
        result = extract_words(text)
        assert result == ["test_var", "123", "hello_world"]


class TestHasSpellingCorrections:
    @pytest.mark.parametrize(
        "original,suggested,expected",
        [
            ("Hello world", "Hello world", False),
            ("HELLO WORLD", "hello world", False),
            ("Hello wrold", "Hello world", True),
            ("Helo wrold tset", "Hello world test", True),
            ("Hello, wrold!", "Hello, world!", True),
        ],
    )
    def test_has_corrections_spelling_scenarios(self, original, suggested, expected):
        assert has_spelling_corrections(original, suggested) is expected

    @pytest.mark.parametrize("suggested", ["", None, "   "])
    def test_has_corrections_invalid_suggested(self, suggested):
        original = "Hello world"
        assert has_spelling_corrections(original, suggested) is False

    def test_has_corrections_word_count_mismatch(self, capsys):
        original = "Hello world"
        suggested = "Hello beautiful world"
        result = has_spelling_corrections(original, suggested)
        captured = capsys.readouterr()
        assert result is False
        assert "Word count mismatch: 2 vs 3" in captured.out


class TestNormalizeLineEndings:
    def test_normalize_basic_text(self):
        text = "Hello world\nSecond line"
        result = normalize_line_endings(text)
        assert result == "Hello world\nSecond line"

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Hello world   \nSecond line  ", "Hello world\nSecond line"),
            ("Hello world   ", "Hello world"),
            ("Hello\t  \nWorld   \t", "Hello\nWorld"),
        ],
    )
    def test_normalize_trailing_spaces(self, text, expected):
        result = normalize_line_endings(text)
        assert result == expected

    @pytest.mark.parametrize(
        "text,preserve_final_newline,expected",
        [
            ("Hello world\nSecond line\n", True, "Hello world\nSecond line\n"),
            ("Hello world\nSecond line\n", False, "Hello world\nSecond line"),
            ("Hello world\nSecond line", True, "Hello world\nSecond line"),
            ("Hello world\nSecond line", False, "Hello world\nSecond line"),
        ],
    )
    def test_normalize_final_newline_handling(
        self, text, preserve_final_newline, expected
    ):
        result = normalize_line_endings(
            text, preserve_final_newline=preserve_final_newline
        )
        assert result == expected

    def test_normalize_empty_string(self):
        text = ""
        result = normalize_line_endings(text)
        assert result == ""

    def test_normalize_multiple_trailing_spaces_per_line(self):
        text = "Line one   \nLine two    \nLine three  \n"
        result = normalize_line_endings(text, preserve_final_newline=True)
        assert result == "Line one\nLine two\nLine three\n"

    def test_normalize_preserve_internal_whitespace(self):
        text = "Hello   world\nSecond    line  "
        result = normalize_line_endings(text)
        assert result == "Hello   world\nSecond    line"
