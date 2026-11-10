from pathlib import Path

import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen
from src.ui.base_layout import style_base_layout

from src.components.dialog_auto_enroll import auto_enroll_dialog

FAVICON = Path(__file__).parent / "assets" / "favicon.png"


def main():
    st.set_page_config(
        page_title='RollCall AI: attendance from one class photo',
        page_icon=str(FAVICON),
        layout='wide',
    )
    style_base_layout()

    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None

    # A join link sends students straight to sign-in, then offers to enroll them
    join_code = st.query_params.get('join-code')
    if join_code and st.session_state.login_type != 'student':
        st.session_state.login_type = 'student'

    match st.session_state['login_type']:
        case 'teacher':
            teacher_screen()

        case 'student':
            student_screen()

        case None:
            home_screen()


    if join_code and st.session_state.get('is_logged_in') and st.session_state.get('user_role') == 'student':
        auto_enroll_dialog(join_code)
main()
