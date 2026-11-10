import streamlit as st


def go_home():
    st.session_state.login_type = None
    st.session_state.pop('teacher_login_type', None)
    # Otherwise a join link would send the student straight back to sign-in
    st.query_params.pop('join-code', None)


def sign_out():
    # Shared classroom devices: leave nothing from this session behind
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.login_type = None


def sign_in(role, data):
    st.session_state.is_logged_in = True
    st.session_state.user_role = role
    st.session_state[f'{role}_data'] = data
