"""Render the checked-in manual, serving its local images through Streamlit."""

from pathlib import Path
import re

import streamlit as st


MANUAL_PATH = Path(__file__).resolve().parents[2] / "docs" / "ISD-Agent-manual.md"
# Manual images use standalone Markdown lines; other Markdown stays intact.
IMAGE_LINE = re.compile(r"^!\[([^\]\n]*)\]\(([^)\n]+)\)[ \t]*$", re.MULTILINE)


def render_manual():
    """Show the manual in a collapsed expander without requiring a PDF parser."""
    with st.expander("📖 사용 매뉴얼", expanded=False):
        try:
            markdown = MANUAL_PATH.read_text(encoding="utf-8")
        except OSError:
            st.warning("사용 매뉴얼을 불러올 수 없습니다. 관리자에게 문의해주세요.")
            return

        offset = 0
        for match in IMAGE_LINE.finditer(markdown):
            text = markdown[offset:match.start()].strip()
            if text:
                st.markdown(text)
            caption, relative_path = match.groups()
            image_path = MANUAL_PATH.parent / relative_path
            try:
                st.image(
                    image_path.read_bytes(), caption=caption or None,
                    use_container_width=True, output_format="PNG",
                )
            except OSError:
                st.warning(f"매뉴얼 이미지를 불러올 수 없습니다: {caption or relative_path}")
            offset = match.end()

        text = markdown[offset:].strip()
        if text:
            st.markdown(text)
