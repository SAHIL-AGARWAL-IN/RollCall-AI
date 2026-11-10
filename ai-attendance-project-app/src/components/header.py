import base64

import streamlit as st


# A register box: red margin line and an ink tick
MARK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    '<rect x="1.5" y="1.5" width="29" height="29" rx="7" fill="#FFFFFF" stroke="#1F3AA8" stroke-width="2.5"/>'
    '<path d="M9.5 2.75V29.25" stroke="#D7373F" stroke-width="2"/>'
    '<path d="M14 16.5L18 20.5L25 11.5" fill="none" stroke="#1F3AA8" stroke-width="3.2" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
)
# st.html strips inline <svg>, so the mark goes in as an image
MARK_SRC = "data:image/svg+xml;base64," + base64.b64encode(MARK_SVG.encode()).decode()


def wordmark(large=False):
    size = 36 if large else 28
    css_class = "wordmark large" if large else "wordmark"
    return (f'<div class="{css_class}"><img src="{MARK_SRC}" width="{size}" height="{size}" alt="">'
            '<span>RollCall AI</span></div>')


def header_home():
    st.html(wordmark(large=True))


def header_dashboard(action_label, on_action, action_icon):
    # Wordmark on the left, the screen's one way out (back or sign out) on the right
    with st.container(horizontal=True, vertical_alignment="center", key="brand_bar"):
        st.html(wordmark(), width="content")
        st.space("stretch")
        st.button(action_label, type="tertiary", icon=action_icon, on_click=on_action, key="brand_bar_action")
