import streamlit as st

LANDING_URL = "https://roll-call-ai.vercel.app"


def footer_home():
    st.html(f'<p class="home-footer">New to RollCall? <a href="{LANDING_URL}" target="_blank" rel="noopener">See how it works</a>.</p>')
