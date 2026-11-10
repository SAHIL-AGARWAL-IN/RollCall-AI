from pathlib import Path

import streamlit as st

STYLE_PATH = Path(__file__).with_name("style.css")


@st.cache_data
def _load_style(modified_at):
    return STYLE_PATH.read_text(encoding="utf-8")


def style_base_layout():
    st.html(f"<style>{_load_style(STYLE_PATH.stat().st_mtime)}</style>")
