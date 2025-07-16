import re


def extract_words(text: str) -> list[str]:
    """Extract words from text and convert to lowercase."""
    if not text:
        return []

    words = re.findall(r"\b\w+\b", text.lower())
    return words


def has_spelling_corrections(original: str, suggested: str) -> bool:
    """Check if the suggested text contains spelling corrections."""
    if not suggested or not suggested.strip():
        return False

    original_words = extract_words(original)
    suggested_words = extract_words(suggested)

    if len(original_words) != len(suggested_words):
        print(f"Word count mismatch: {len(original_words)} vs {len(suggested_words)}")
        return False

    has_diffs = any(orig != sugg for orig, sugg in zip(original_words, suggested_words))
    return has_diffs


def normalize_line_endings(text: str, preserve_final_newline: bool = True) -> str:
    """Normalize line endings by removing trailing whitespace from each line."""
    corrected_lines = []
    for line in text.splitlines():
        corrected_lines.append(line.rstrip())

    if preserve_final_newline and text.endswith("\n"):
        return "\n".join(corrected_lines) + "\n"
    else:
        return "\n".join(corrected_lines)
