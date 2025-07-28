import streamlit as st
import re

from proofer.agent import build_graph
from proofer.diff import find_word_changes


def display_word_changes_streamlit(changes):
    """Display word-level changes in Streamlit format."""
    if not changes:
        st.success("✓ No spelling errors found!")
        return

    st.warning(f"Found {len(changes)} spelling correction(s):")

    for i, change in enumerate(changes, 1):
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            st.write(f"{i}.")
        with col2:
            st.markdown(f"**:red[{change['original']}]**")
        with col3:
            st.markdown(f"**:green[{change['corrected']}]**")


def highlight_changes_in_text(text, changes):
    """Apply highlighting to text based on changes."""
    highlighted_text = text

    for change in changes:
        original_word = change["original"]
        corrected_word = change["corrected"]

        pattern = re.compile(r"\b" + re.escape(original_word) + r"\b", re.IGNORECASE)
        highlighted_text = pattern.sub(
            lambda m: (
                f"**:red[{m.group()}]**"
                if text == highlighted_text
                else f"**:green[{corrected_word}]**"
            ),
            highlighted_text,
        )

    return highlighted_text


def display_line_diff_streamlit(original_text, corrected_text, changes):
    """Display line-by-line diff in Streamlit format."""
    if not changes:
        return

    st.subheader("Preview:")

    original_lines = original_text.splitlines()
    corrected_lines = corrected_text.splitlines()

    changed_lines = []
    for i, (orig_line, corr_line) in enumerate(zip(original_lines, corrected_lines), 1):
        if orig_line.strip() != corr_line.strip():
            changed_lines.append((i, orig_line, corr_line))

    if not changed_lines:
        st.info("No line changes to display")
        return

    for line_num, orig_line, corr_line in changed_lines:
        st.write(f"**Line {line_num}:**")

        orig_highlighted = orig_line
        corr_highlighted = corr_line

        for change in changes:
            orig_pattern = re.compile(
                r"\b" + re.escape(change["original"]) + r"\b", re.IGNORECASE
            )
            corr_pattern = re.compile(
                r"\b" + re.escape(change["corrected"]) + r"\b", re.IGNORECASE
            )

            orig_highlighted = orig_pattern.sub(
                f"**:red[{change['original']}]**", orig_highlighted
            )
            corr_highlighted = corr_pattern.sub(
                f"**:green[{change['corrected']}]**", corr_highlighted
            )

        col1, col2 = st.columns([1, 20])
        with col1:
            st.write("−")
        with col2:
            st.markdown(orig_highlighted)

        col1, col2 = st.columns([1, 20])
        with col1:
            st.write("+")
        with col2:
            st.markdown(corr_highlighted)

        st.divider()


def process_text_with_agent(text, auto_approve=False):
    """Process text through the proofreader agent and return results."""
    try:
        initial_state = {"input_text": text, "auto_approve": auto_approve}

        graph = build_graph()
        result = graph.invoke(initial_state)

        return result
    except Exception as e:
        st.error(f"Error processing text: {e}")
        return None


def main():
    st.set_page_config(page_title="Proofreader Agent", page_icon="📝", layout="wide")

    st.title("Proofer")

    with st.sidebar:
        st.header("Options")
        input_method = st.radio("Input method:", ["Direct text input", "File upload"])

        auto_approve = st.checkbox(
            "Auto-approve changes",
            help="Automatically apply suggested changes without confirmation",
        )

    text_to_process = ""

    if input_method == "Direct text input":
        st.subheader("Enter text to proofread:")
        text_to_process = st.text_area(
            "Text input", height=200, placeholder="Paste your text here..."
        )
    else:
        st.subheader("Upload a file:")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["txt", "md", "mdx"],
            help="Upload a text, markdown, or mdx file",
        )

        if uploaded_file is not None:
            try:
                text_to_process = uploaded_file.read().decode("utf-8")
                st.text_area(
                    "File content:", text_to_process, height=200, disabled=True
                )
            except Exception as e:
                st.error(f"Error reading file: {e}")

    if st.button(
        "Check",
        type="primary",
        disabled=not text_to_process.strip(),
    ):
        if not text_to_process.strip():
            st.warning("Please enter some text to proofread.")
            return

        with st.spinner("Checking for spelling errors"):
            result = process_text_with_agent(text_to_process, auto_approve)

            if result is None:
                return

            if not result.get("has_corrections", False):
                st.success("✅ No spelling errors found! The document looks good!")
                return

            original_text = result["original_text"]
            corrected_text = result["llm_response"]

            changes = find_word_changes(original_text, corrected_text)

            if changes:
                st.subheader("Corrections Found:")
                display_word_changes_streamlit(changes)

                st.subheader("Detailed Preview:")
                display_line_diff_streamlit(original_text, corrected_text, changes)

                # Show full corrected text
                with st.expander("View Full Corrected Text", expanded=False):
                    st.text_area(
                        "Corrected version:", corrected_text, height=300, disabled=True
                    )

                col1, col2, col3 = st.columns([1, 1, 2])

                with col1:
                    if st.button("✅ Accept Changes", type="primary"):
                        st.session_state["accepted_text"] = corrected_text
                        st.success("Changes accepted! See corrected text below.")
                        st.rerun()

                with col2:
                    if st.button("❌ Reject Changes"):
                        st.info("Changes rejected. Original text preserved.")

                if "accepted_text" in st.session_state:
                    st.subheader("✅ Final Corrected Text:")
                    st.text_area(
                        "Copy the corrected text below:",
                        st.session_state["accepted_text"],
                        height=200,
                    )

                    st.download_button(
                        label="Download Corrected Text",
                        data=st.session_state["accepted_text"],
                        file_name="corrected_text.txt",
                        mime="text/plain",
                    )
            else:
                st.success("No spelling errors found!")


if __name__ == "__main__":
    main()
