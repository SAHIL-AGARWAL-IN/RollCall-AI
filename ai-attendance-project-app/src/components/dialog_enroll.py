import streamlit as st
from src.database.db import enroll_student_to_subject, get_subject_by_code, is_enrolled



@st.dialog("Join a subject")
def enroll_dialog():
    with st.form("join_subject", border=False):
        join_code = st.text_input('Subject code', placeholder='CS101', help="Your teacher shares this code in class.")
        submitted = st.form_submit_button('Join subject', type='primary', width='stretch')

    if not submitted:
        return
    if not join_code.strip():
        st.warning('Enter the subject code from your teacher.')
        return

    subject = get_subject_by_code(join_code)
    if not subject:
        st.error(f"No subject uses the code {join_code.strip().upper()}. Check it with your teacher.")
        return

    student_id = st.session_state.student_data['student_id']
    if is_enrolled(student_id, subject['subject_id']):
        st.info(f"You've already joined {subject['name']}.")
        return

    enroll_student_to_subject(student_id, subject['subject_id'])
    st.toast(f"Joined {subject['name']}.", icon=":material/check_circle:")
    st.rerun()
