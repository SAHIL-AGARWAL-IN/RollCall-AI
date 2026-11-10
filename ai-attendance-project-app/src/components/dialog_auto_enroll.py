import streamlit as st
from src.database.db import enroll_student_to_subject, get_subject_by_code, is_enrolled


def close_join_link():
    st.query_params.clear()


@st.dialog("Join a subject", on_dismiss=close_join_link)
def auto_enroll_dialog(subject_code):
    student_id = st.session_state.student_data['student_id']

    subject = get_subject_by_code(subject_code)
    if not subject:
        st.error(f"No subject uses the code {subject_code.strip().upper()}. Ask your teacher for a new link.")
        st.button('Close', on_click=close_join_link, width='stretch')
        return

    if is_enrolled(student_id, subject['subject_id']):
        st.info(f"You've already joined {subject['name']}.")
        st.button('Done', on_click=close_join_link, width='stretch')
        return

    st.markdown(f"Join **{subject['name']}**, section {subject['section']}?")

    with st.container(horizontal=True):
        st.button('Not now', on_click=close_join_link, width='stretch')
        if st.button('Join subject', type='primary', width='stretch'):
            enroll_student_to_subject(student_id, subject['subject_id'])
            close_join_link()
            st.toast(f"Joined {subject['name']}.", icon=":material/check_circle:")
            st.rerun()
