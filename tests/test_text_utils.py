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

    def test_extract_words_empty_string(self):
        result = extract_words("")
        assert result == []

    def test_extract_words_none_or_whitespace(self):
        assert extract_words("   ") == []
        assert extract_words("\n\t") == []

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
        assert result == ["test_var", "hello_world"]


class TestHasSpellingCorrections:
    def test_has_corrections_identical_text(self):
        original = "Hello world"
        suggested = "Hello world"
        assert has_spelling_corrections(original, suggested) is False

    def test_has_corrections_spelling_fix(self):
        original = "Hello wrold"
        suggested = "Hello world"
        assert has_spelling_corrections(original, suggested) is True

    def test_has_corrections_empty_suggested(self):
        original = "Hello world"
        suggested = ""
        assert has_spelling_corrections(original, suggested) is False

    def test_has_corrections_none_suggested(self):
        original = "Hello world"
        suggested = None
        assert has_spelling_corrections(original, suggested) is False

    def test_has_corrections_whitespace_only_suggested(self):
        original = "Hello world"
        suggested = "   "
        assert has_spelling_corrections(original, suggested) is False

    def test_has_corrections_word_count_mismatch(self, capsys):
        original = "Hello world"
        suggested = "Hello beautiful world"
        result = has_spelling_corrections(original, suggested)
        captured = capsys.readouterr()
        assert result is False
        assert "Word count mismatch: 2 vs 3" in captured.out

    def test_has_corrections_multiple_spelling_fixes(self):
        original = "Helo wrold tset"
        suggested = "Hello world test"
        assert has_spelling_corrections(original, suggested) is True

    def test_has_corrections_case_insensitive(self):
        original = "HELLO WORLD"
        suggested = "hello world"
        assert has_spelling_corrections(original, suggested) is False

    def test_has_corrections_with_punctuation(self):
        original = "Hello, wrold!"
        suggested = "Hello, world!"
        assert has_spelling_corrections(original, suggested) is True


class TestNormalizeLineEndings:
    def test_normalize_basic_text(self):
        text = "Hello world\nSecond line"
        result = normalize_line_endings(text)
        assert result == "Hello world\nSecond line"

    def test_normalize_trailing_spaces(self):
        text = "Hello world   \nSecond line  "
        result = normalize_line_endings(text)
        assert result == "Hello world\nSecond line"

    def test_normalize_preserve_final_newline_true(self):
        text = "Hello world\nSecond line\n"
        result = normalize_line_endings(text, preserve_final_newline=True)
        assert result == "Hello world\nSecond line\n"

    def test_normalize_preserve_final_newline_false(self):
        text = "Hello world\nSecond line\n"
        result = normalize_line_endings(text, preserve_final_newline=False)
        assert result == "Hello world\nSecond line"

    def test_normalize_no_final_newline(self):
        text = "Hello world\nSecond line"
        result = normalize_line_endings(text, preserve_final_newline=True)
        assert result == "Hello world\nSecond line"

    def test_normalize_empty_string(self):
        text = ""
        result = normalize_line_endings(text)
        assert result == ""

    def test_normalize_single_line_with_trailing_spaces(self):
        text = "Hello world   "
        result = normalize_line_endings(text)
        assert result == "Hello world"

    def test_normalize_multiple_trailing_spaces_per_line(self):
        text = "Line one   \nLine two    \nLine three  \n"
        result = normalize_line_endings(text, preserve_final_newline=True)
        assert result == "Line one\nLine two\nLine three\n"

    def test_normalize_tabs_and_spaces(self):
        text = "Hello\t  \nWorld   \t"
        result = normalize_line_endings(text)
        assert result == "Hello\nWorld"

    def test_normalize_preserve_internal_whitespace(self):
        text = "Hello   world\nSecond    line  "
        result = normalize_line_endings(text)
        assert result == "Hello   world\nSecond    line"
