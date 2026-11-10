import streamlit as st

from src.ui.format import esc, md_escape


def subject_card(name, code, section, key):
    """A bordered card with the subject's name and code. Returns the card so callers can add to it."""
    card = st.container(border=True, key=key)
    with card:
        st.subheader(md_escape(name), anchor=False)
        st.html(f'<p class="subject-meta"><span class="code">{esc(code)}</span>&ensp;Section {esc(section)}</p>')
    return card
