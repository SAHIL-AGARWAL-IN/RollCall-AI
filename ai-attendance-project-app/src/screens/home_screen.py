import streamlit as st
from src.components.header import header_home
from src.components.demo_register import demo_register_html
from src.components.footer import footer_home
from src.database.db import get_teacher
from src.ui.navigation import sign_in


def choose_role(role):
    st.session_state.login_type = role


def demo_teacher_username():
    # Set DEMO_TEACHER in secrets (and run scripts/seed_demo.py) to offer the demo class
    try:
        return st.secrets.get("DEMO_TEACHER")
    except Exception:
        return None


def start_demo(username):
    teacher = get_teacher(username)
    if not teacher:
        st.toast("The demo class isn't set up yet.", icon=":material/error:")
        return
    sign_in('teacher', teacher)
    st.session_state.login_type = 'teacher'


def home_screen():
    header_home()
    st.space("small")

    intro, demo = st.columns([1.15, 0.85], gap="large")
    with intro:
        st.title("Attendance from one photo of your class", anchor=False)
        st.html('<p class="lead">Take a photo of the room or record a quick roll call. RollCall marks the register, '
                'you check it, and it\'s saved.</p>')
        st.space("small")

        with st.container(border=True, key="role_teacher"):
            st.subheader("I'm a teacher", anchor=False)
            st.caption("Take attendance, manage subjects and see past classes.")
            st.button('Teacher sign in', type='primary', width='stretch', icon=':material/school:',
                      on_click=choose_role, args=('teacher',))

        with st.container(border=True, key="role_student"):
            st.subheader("I'm a student", anchor=False)
            st.caption("Sign in with a selfie, join subjects and check your attendance.")
            st.button('Student sign in', width='stretch', icon=':material/face:',
                      on_click=choose_role, args=('student',))

        if demo_user := demo_teacher_username():
            with st.container(horizontal=True, vertical_alignment="center", gap="small"):
                st.caption("Just looking?")
                st.button("Try a demo class", type="tertiary", icon=":material/play_circle:",
                          on_click=start_demo, args=(demo_user,))

    with demo:
        st.html(demo_register_html())

    st.space("small")
    footer_home()
