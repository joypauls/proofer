import re
from rich.console import Console
from rich.text import Text


def display_word_changes(console: Console, changes: list[dict[str, str]]) -> None:
    """Display word-level changes in a formatted way."""
    console.print(f"\n[bold yellow]Found {len(changes)} spelling correction(s):[/]")
    console.print()
    for i, change in enumerate(changes, 1):
        console.print(
            f"  {i}. [red bold]{change['original']}[/] → [green bold]{change['corrected']}[/]"
        )
    console.print()


def display_line_diff(
    console: Console,
    original_text: str,
    corrected_text: str,
    changes: list[dict[str, str]],
) -> None:
    """Display line-by-line diff with highlighted changes."""
    original_lines = original_text.splitlines()
    corrected_lines = corrected_text.splitlines()

    console.print("[bold blue]Preview:[/]")
    console.print()

    # show only the lines that changed with context
    for i, (orig_line, corr_line) in enumerate(zip(original_lines, corrected_lines), 1):
        if orig_line.strip() != corr_line.strip():
            console.print(f"[dim]Line {i}:[/]")

            orig_text = Text(orig_line)
            corr_text = Text(corr_line)

            for change in changes:
                # find all occurrences of the word in the line
                orig_pattern = re.compile(
                    r"\b" + re.escape(change["original"]) + r"\b", re.IGNORECASE
                )
                corr_pattern = re.compile(
                    r"\b" + re.escape(change["corrected"]) + r"\b", re.IGNORECASE
                )

                # find matches in original line
                for match in orig_pattern.finditer(orig_line):
                    start, end = match.span()
                    orig_text.stylize("red bold", start, end)

                # find matches in corrected line
                for match in corr_pattern.finditer(corr_line):
                    start, end = match.span()
                    corr_text.stylize("green bold", start, end)

            console.print("  [red]−[/] ", end="")
            console.print(orig_text)
            console.print("  [green]+[/] ", end="")
            console.print(corr_text)
            console.print()
