import difflib
import re


def find_word_changes(original: str, corrected: str) -> list[dict[str, str]]:
    """Find word-level changes between original and corrected text."""
    original_words = re.findall(r"\b\w+\b", original.lower())
    corrected_words = re.findall(r"\b\w+\b", corrected.lower())

    changes = []
    matcher = difflib.SequenceMatcher(None, original_words, corrected_words)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            for k in range(i2 - i1):
                if i1 + k < len(original_words) and j1 + k < len(corrected_words):
                    orig_word = original_words[i1 + k]
                    corr_word = corrected_words[j1 + k]
                    if orig_word != corr_word:
                        changes.append({"original": orig_word, "corrected": corr_word})

    return changes
