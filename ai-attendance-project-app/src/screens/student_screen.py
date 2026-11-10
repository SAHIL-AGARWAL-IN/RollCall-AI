import numpy as np
import streamlit as st

from src.components.demo_register import brand_panel
from src.components.dialog_enroll import enroll_dialog
from src.components.header import header_dashboard
from src.components.subject_card import subject_card
from src.database.db import (create_student, get_student, get_student_attendance, get_student_subjects,
                             unenroll_student_to_subject, update_student_voice)
from src.pipelines.face_pipeline import get_face_embeddings, identify_faces, load_image, refresh_face_index
from src.pipelines.voice_pipeline import get_voice_embedding
from src.ui.format import first_name, md_escape, plural, tally_html
from src.ui.navigation import go_home, sign_in, sign_out

# Most Indian colleges require 75% attendance to sit exams
ATTENDANCE_TARGET = 0.75


def student_screen():
    if "student_data" in st.session_state:
        student_dashboard()
    else:
        student_screen_login()


# Dashboard

def leave_subject(student_id, subject_id, subject_name):
    unenroll_student_to_subject(student_id, subject_id)
    st.toast(f"Left {subject_name}.", icon=":material/check_circle:")


def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    header_dashboard("Sign out", sign_out, ":material/logout:")

    st.title(f"Hi, {md_escape(first_name(student_data['name']))}", anchor=False)

    with st.spinner('Loading your subjects…'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}
    for log in logs:
        stats = stats_map.setdefault(log['subject_id'], {"total": 0, "attended": 0})
        stats['total'] += 1
        if log.get('is_present'):
            stats['attended'] += 1

    with st.container(horizontal=True, vertical_alignment="center"):
        st.header("Your subjects", anchor=False, width="content")
        st.space("stretch")
        if st.button("Join a subject", type="primary", icon=":material/add:"):
            enroll_dialog()

    if not subjects:
        st.html('<p class="lead">You haven\'t joined any subjects yet. Ask your teacher for the subject code, '
                'or scan the QR code they show in class.</p>')

    # Two cards a row on laptops; filled row by row so phones keep the same order
    joined = [node['subjects'] for node in subjects if node['subjects']]  # skips subjects a teacher deleted
    for first in range(0, len(joined), 2):
        for column, sub in zip(st.columns(2, gap="medium"), joined[first:first + 2]):
            with column:
                student_subject_card(sub, stats_map.get(sub['subject_id'], {"total": 0, "attended": 0}), student_id)

    st.space("medium")
    voice_sample_section(student_data)


def student_subject_card(sub, stats, student_id):
    sid = sub['subject_id']
    with subject_card(sub['name'], sub['subject_code'], sub['section'], key=f"subject_{sid}"):
        if stats['total']:
            rate = stats['attended'] / stats['total']
            low = rate < ATTENDANCE_TARGET
            st.html(
                tally_html(f"{rate:.0%}", f"present in {stats['attended']} of {plural(stats['total'], 'class', 'classes')}",
                           low=low, small=True)
                + f'<div class="meter{" low" if low else ""}" role="img" aria-label="{rate:.0%} attendance against a {ATTENDANCE_TARGET:.0%} minimum">'
                f'<div class="fill" style="width:{rate:.1%}"></div>'
                f'<div class="target" style="left:{ATTENDANCE_TARGET:.0%}"></div></div>'
            )
            if low:
                st.caption(f":red[Below the {ATTENDANCE_TARGET:.0%} minimum.]")
        else:
            st.caption("No classes taken yet.")

        with st.popover("Leave subject", type="tertiary", icon=":material/logout:"):
            st.markdown(f"Leave **{md_escape(sub['name'])}**? Your attendance stays on record, "
                        "but it won't show here unless you join again.")
            st.button("Leave subject", type="primary", key=f"leave_{sid}", width="stretch",
                      on_click=leave_subject, args=(student_id, sid, sub['name']))


def voice_sample_section(student_data):
    has_voice = bool(student_data.get('voice_embedding'))
    title = "Voice sample: added" if has_voice else "Voice sample: not added"
    with st.expander(title, icon=":material/mic:"):
        st.markdown("Your teacher can take attendance by voice. Record yourself saying "
                    "“I am present, my name is …” in a quiet room.")
        audio = st.audio_input("Voice sample", label_visibility="collapsed", key="voice_sample")
        if st.button("Replace voice sample" if has_voice else "Save voice sample", disabled=audio is None,
                     width="stretch"):
            with st.spinner("Saving your voice sample…"):
                embedding = get_voice_embedding(audio.getvalue())
            if embedding:
                update_student_voice(student_data['student_id'], embedding)
                student_data['voice_embedding'] = embedding
                st.toast("Voice sample saved.", icon=":material/check_circle:")
                st.rerun()


# Sign in

def scan_face(photo):
    # Keep the result for this photo so typing a name doesn't rerun face detection
    cached = st.session_state.get('face_scan')
    if cached and cached['file_id'] == photo.file_id:
        return cached

    with st.spinner('Checking your face…'):
        encodings = get_face_embeddings(np.array(load_image(photo)))
        detected, _ = identify_faces(encodings)

    scan = {
        'file_id': photo.file_id,
        'faces': len(encodings),
        'student_id': next(iter(detected), None),
        'embedding': encodings[0].tolist() if len(encodings) == 1 else None,
    }
    st.session_state.face_scan = scan
    return scan


def student_screen_login():
    header_dashboard("Back", go_home, ":material/arrow_back:")
    form_side, panel_side = st.columns(2, gap="large")
    with panel_side:
        brand_panel("Your teacher takes one photo of the class. Your selfie is how RollCall knows it's you.")
    with form_side:
        student_sign_in()


def student_sign_in():
    st.title("Sign in with your face", anchor=False)

    join_code = st.query_params.get('join-code')
    if join_code:
        st.info(f"Sign in to join **{join_code}**.", icon=":material/qr_code_2:")

    st.html('<p class="lead">Hold your phone at eye level in good light, with only your face in the frame.</p>')
    photo_source = st.camera_input("Take a selfie", label_visibility="collapsed", key="face_login")
    if not photo_source:
        return

    scan = scan_face(photo_source)

    if scan['faces'] == 0:
        st.warning("No face found. Face the camera in better light, then retake the photo.")
        return
    if scan['faces'] > 1:
        st.warning("More than one face is in the photo. Make sure only you are in frame, then retake it.")
        return

    if scan['student_id'] is not None:
        student = get_student(scan['student_id'])
        if student:
            st.session_state.pop('face_scan', None)
            sign_in('student', student)
            st.toast(f"Welcome back, {first_name(student['name'])}.", icon=":material/waving_hand:")
            st.rerun()

    register_profile(scan)


def register_profile(scan):
    with st.container(border=True, key="new_profile"):
        st.subheader("New here? Create your profile", anchor=False)
        st.markdown("We couldn't match this face to a profile. If you've signed in before, retake the photo "
                    "in better light. Otherwise, add your name.")
        new_name = st.text_input("Full name", placeholder="Hamza Rizvi", autocomplete="name")
        audio_data = st.audio_input("Voice sample (optional)",
                                    help="Say “I am present, my name is …”. Your teacher can then take attendance by voice.")

        if st.button('Create profile', type='primary', width='stretch'):
            if not new_name.strip():
                st.warning('Enter your name to create your profile.')
                return

            with st.spinner('Creating your profile…'):
                voice_emb = get_voice_embedding(audio_data.getvalue()) if audio_data else None
                response_data = create_student(new_name.strip(), face_embedding=scan['embedding'],
                                               voice_embedding=voice_emb)

            if response_data:
                refresh_face_index()
                st.session_state.pop('face_scan', None)
                sign_in('student', response_data[0])
                st.toast(f"Profile created. Hi, {first_name(new_name)}!", icon=":material/waving_hand:")
                st.rerun()
            else:
                st.error("Couldn't create your profile. Try again in a moment.")
