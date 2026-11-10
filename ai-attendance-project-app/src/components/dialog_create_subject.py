import streamlit as st
from src.database.db import create_subject, get_subject_by_code



@st.dialog("New subject")
def create_subject_dialog(teacher_id):
    with st.form("create_subject", border=False):
        sub_id = st.text_input("Subject code", placeholder="CS101", help="Students type this code to join.")
        sub_name = st.text_input("Subject name", placeholder="Introduction to Computer Science")
        sub_section = st.text_input("Section", placeholder="A")
        submitted = st.form_submit_button("Create subject", type="primary", width="stretch")

    if submitted:
        if not (sub_id.strip() and sub_name.strip() and sub_section.strip()):
            st.warning("Fill in the code, name and section.")
            return
        # Join links look subjects up by code, so two subjects can't share one
        if get_subject_by_code(sub_id):
            st.error(f"The code {sub_id.strip().upper()} is already in use. Pick another, for example {sub_id.strip().upper()}-{sub_section.strip().upper()}.")
            return
        try:
            create_subject(sub_id, sub_name, sub_section, teacher_id)
        except Exception:
            st.error("Couldn't create the subject. Try again in a moment.")
            return
        st.toast(f"Created {sub_name.strip()}.", icon=":material/check_circle:")
        st.rerun()
