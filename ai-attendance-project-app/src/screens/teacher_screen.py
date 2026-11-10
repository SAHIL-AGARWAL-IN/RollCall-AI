from time import perf_counter

import pandas as pd
import streamlit as st
from PIL import Image

from src.components.attendance_review import attendance_review, start_review
from src.components.dialog_create_subject import create_subject_dialog
from src.components.demo_register import brand_panel
from src.components.dialog_share_subject import share_subject_dialog
from src.components.header import header_dashboard
from src.components.scan_timeline import ScanTimeline
from src.components.subject_card import subject_card
from src.database.db import (check_teacher_exists, create_teacher, get_attendance_for_teacher, get_student_names,
                             get_subject_students, get_teacher_subjects, teacher_login)
from src.pipelines.face_pipeline import load_image
from src.pipelines.roll_call import review_voice_segments, scan_class_photos
from src.pipelines.voice_pipeline import identify_segments
from src.screens.student_screen import ATTENDANCE_TARGET
from src.ui.format import local_time, md_escape, plural
from src.ui.navigation import go_home, sign_in, sign_out

TABS = {
    "take": ":material/how_to_reg: Roll call",
    "subjects": ":material/menu_book: Subjects",
    "records": ":material/table_view: Records",
}
METHODS = {
    "photo": ":material/photo_camera: Class photo",
    "voice": ":material/mic: Voice",
}
RECENT_SESSIONS = 50


def teacher_screen():
    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif st.session_state.get('teacher_login_type') == "register":
        teacher_screen_register()
    else:
        teacher_screen_login()


def current_teacher_id():
    teacher = st.session_state.teacher_data
    return teacher.get('username') or teacher.get('teacher_id') or teacher.get('id')


def switch_tab(tab):
    st.session_state.teacher_tab = tab


def take_attendance_for(subject_id):
    st.session_state.att_subject = subject_id
    st.session_state.teacher_tab = "take"


def teacher_dashboard():
    header_dashboard("Sign out", sign_out, ":material/logout:")
    teacher_id = current_teacher_id()

    st.session_state.setdefault('teacher_tab', "take")
    # While a register is being checked, Save and Discard are the only ways out
    reviewing = st.session_state.teacher_tab == "take" and st.session_state.get('attendance_review')
    if not reviewing:
        # On phones this becomes a tab bar along the bottom of the screen (see style.css)
        st.segmented_control("Section", options=list(TABS), format_func=TABS.get, key="teacher_tab",
                             required=True, label_visibility="collapsed", width="stretch", persist_state="page")

    match st.session_state.teacher_tab:
        case "take":
            teacher_tab_take_attendance(teacher_id)
        case "subjects":
            teacher_tab_manage_subjects(teacher_id)
        case "records":
            teacher_tab_attendance_records(teacher_id)


# Roll call

def teacher_tab_take_attendance(teacher_id):
    if notice := st.session_state.pop('saved_notice', None):
        st.success(notice, icon=":material/check_circle:")

    if st.session_state.get('attendance_review'):
        attendance_review(on_saved=reset_capture)
        return

    subjects = get_teacher_subjects(teacher_id)
    st.title("Take attendance", anchor=False)

    if not subjects:
        st.html('<p class="lead">Create a subject first. Students join it with a code, then you can take their attendance here.</p>')
        if st.button("Create a subject", type="primary", icon=":material/add:", width="stretch"):
            create_subject_dialog(teacher_id)
        return

    by_id = {s['subject_id']: s for s in subjects}
    if st.session_state.get('att_subject') not in by_id:
        st.session_state.att_subject = subjects[0]['subject_id']

    # Laptops get the subject's recent classes beside the capture controls; phones stack them
    capture, context = st.columns([3, 2], gap="large")
    with capture:
        st.selectbox("Subject", options=list(by_id), key="att_subject",
                     format_func=lambda sid: f"{by_id[sid]['name']} ({by_id[sid]['subject_code']})")
        subject = by_id[st.session_state.att_subject]

        st.session_state.setdefault('att_method', "photo")
        st.segmented_control("Method", options=list(METHODS), format_func=METHODS.get, key="att_method",
                             required=True, width="stretch")

        if st.session_state.att_method == "photo":
            photo_attendance(subject)
        else:
            voice_attendance(subject)

        st.space("small")
        if st.button("Mark the register by hand instead", type="tertiary", icon=":material/edit:"):
            mark_by_hand(subject)

    with context:
        subject_overview(subject, st.session_state.att_method)


def last_class_metric(subject):
    history = subject.get('class_history') or []
    if not history:
        st.caption("No classes taken yet.")
        return
    timestamp, present, total = history[-1]
    when = local_time(timestamp)
    st.metric(f"Last class, {when:%a} {when.day} {when:%b}", f"{present}/{total}",
              chart_data=[round(100 * p / t) for _, p, t in history[-12:]], chart_type="line",
              help="Share of students present in each of the last 12 classes")


PHOTO_TIPS = """- Stand at the front and hold the phone sideways
- Take a second photo if the back rows look small
- Ask everyone to look up for a moment"""
VOICE_TIPS = """- Call names in order, or let students answer down each row
- One voice at a time, with a short pause between
- Record somewhere quiet, away from fans"""


def subject_overview(subject, method):
    with st.container(border=True, key="subject_overview"):
        st.subheader(md_escape(subject['name']), anchor=False)
        st.caption(f"{subject['subject_code']}, section {subject['section']}. "
                   f"{plural(subject['total_students'], 'student')} enrolled.")
        last_class_metric(subject)
    st.markdown(f"**{'For a good class photo' if method == 'photo' else 'For a clear roll call'}**")
    st.markdown(PHOTO_TIPS if method == "photo" else VOICE_TIPS)


def reset_capture():
    st.session_state.capture_nonce = st.session_state.get('capture_nonce', 0) + 1
    st.session_state.camera_photos = []
    st.session_state.thumbnails = {}


def keep_snapshot(key):
    shot = st.session_state.get(key)
    if shot is not None:
        st.session_state.camera_photos.append(load_image(shot))


def thumbnail(photo):
    cache = st.session_state.setdefault('thumbnails', {})
    cache_key = getattr(photo, 'file_id', None) or id(photo)
    if cache_key not in cache:
        img = (photo if isinstance(photo, Image.Image) else load_image(photo)).copy()
        img.thumbnail((240, 240))
        cache[cache_key] = img
    return cache[cache_key]


def enrolled_students(subject):
    return [node['students'] for node in get_subject_students(subject['subject_id'])]


def photo_attendance(subject):
    st.session_state.setdefault('camera_photos', [])
    nonce = st.session_state.get('capture_nonce', 0)

    st.caption("Stand at the front and take one to three photos so every face is visible. "
               "On a phone, choose the camera when the picker opens.")
    uploads = st.file_uploader("Class photos", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True,
                               key=f"class_photos_{nonce}", label_visibility="collapsed")

    shots = st.session_state.camera_photos
    camera = st.expander("Use this device's camera", icon=":material/photo_camera:", key="class_camera",
                         on_change="rerun")
    # Only create the camera once the teacher opens this, or the webcam switches on unasked
    if camera.open:
        with camera:
            cam_key = f"class_cam_{nonce}_{len(shots)}"
            st.camera_input("Snapshot", key=cam_key, on_change=keep_snapshot, args=(cam_key,),
                            label_visibility="collapsed")

    photos = list(uploads or []) + shots
    if photos:
        with st.container(horizontal=True, gap="small"):
            for photo in photos:
                st.image(thumbnail(photo), width=96)
        st.button("Remove all photos", type="tertiary", icon=":material/delete:", on_click=reset_capture)

    label = "Add a photo to start" if not photos else f"Find students in {plural(len(photos), 'photo')}"
    if st.button(label, type="primary", width="stretch", icon=":material/person_search:", disabled=not photos):
        students = enrolled_students(subject)
        if not students:
            st.warning(f"No students have joined {subject['name']} yet. Share its join code from Subjects.")
            return

        timeline = ScanTimeline()
        timeline("start", f"Preparing {plural(len(photos), 'photo')}")
        images = [photo if isinstance(photo, Image.Image) else load_image(photo) for photo in photos]
        timeline("done", f"Prepared {plural(len(photos), 'photo')}", "Turned upright and resized for scanning")
        rows, flags, annotated, note, strangers = scan_class_photos(subject, images, students, report=timeline)
        start_review(subject, rows, note, flags=flags, photos=annotated, steps=timeline.steps, strangers=strangers)
        st.rerun()


def voice_attendance(subject):
    nonce = st.session_state.get('capture_nonce', 0)
    students = enrolled_students(subject)
    with_voice = [s for s in students if s.get('voice_embedding')]

    st.caption("Press record, then call the roll. Each student says “present” in turn, with a short pause between voices.")
    if students and len(with_voice) < len(students):
        missing = len(students) - len(with_voice)
        st.caption(f"{plural(missing, 'student')} in this subject {'has' if missing == 1 else 'have'} no voice sample "
                   "yet and will start as absent.")

    audio = st.audio_input("Classroom recording", key=f"voice_{nonce}", label_visibility="collapsed")

    if st.button("Identify voices", type="primary", width="stretch", icon=":material/graphic_eq:", disabled=audio is None):
        if not students:
            st.warning(f"No students have joined {subject['name']} yet. Share its join code from Subjects.")
            return
        if not with_voice:
            st.error("None of the students in this subject have a voice sample yet. "
                     "They can add one from their own dashboard.")
            return

        timeline = ScanTimeline()
        timeline("start", "Listening to the recording")
        started = perf_counter()
        candidates = {s['student_id']: s['voice_embedding'] for s in with_voice}
        try:
            segments = identify_segments(audio.getvalue(), candidates)
        except Exception:
            timeline.fail("Couldn't read the recording")
            st.error("Couldn't read that recording. Record it again, then press Identify voices.")
            return
        timeline("done", f"Heard {plural(len(segments), 'answer')}",
                 f"Split at the pauses and matched each voice in {perf_counter() - started:.1f} s")

        rows, flags, note = review_voice_segments(subject, segments, students, report=timeline)
        start_review(subject, rows, note, flags=flags, steps=timeline.steps)
        st.rerun()


def mark_by_hand(subject):
    students = enrolled_students(subject)
    if not students:
        st.warning(f"No students have joined {subject['name']} yet. Share its join code from Subjects.")
        return
    rows = [{'student_id': s['student_id'], 'name': s['name'], 'present': False, 'source': "", 'check': ""}
            for s in students]
    start_review(subject, rows, "Everyone starts as absent. Tick each student who is here.")
    st.rerun()


# Subjects

def teacher_tab_manage_subjects(teacher_id):
    with st.container(horizontal=True, vertical_alignment="center"):
        st.title("Subjects", anchor=False, width="content")
        st.space("stretch")
        if st.button("New subject", icon=":material/add:"):
            create_subject_dialog(teacher_id)

    subjects = get_teacher_subjects(teacher_id)
    if not subjects:
        st.html('<p class="lead">No subjects yet. Create one, then share its join code so students can sign up.</p>')
        return

    # Two cards a row on laptops; filled row by row so phones keep the same order
    for first in range(0, len(subjects), 2):
        for column, sub in zip(st.columns(2, gap="medium"), subjects[first:first + 2]):
            with column:
                subject_tile(sub)


def subject_tile(sub):
    with subject_card(sub['name'], sub['subject_code'], sub['section'], key=f"subject_{sub['subject_id']}"):
        st.caption(f"{plural(sub['total_students'], 'student')} enrolled, "
                   f"{plural(sub['total_classes'], 'class', 'classes')} taken")
        last_class_metric(sub)
        with st.container(horizontal=True):
            if st.button("Show join code", icon=":material/qr_code_2:", key=f"share_{sub['subject_id']}",
                         width="stretch"):
                share_subject_dialog(sub['name'], sub['subject_code'])
            st.button("Take attendance", type="primary", icon=":material/how_to_reg:", width="stretch",
                      key=f"take_{sub['subject_id']}", on_click=take_attendance_for, args=(sub['subject_id'],))


# Records

def short_when(when):
    return f"{when:%a} {when.day} {when:%b}, {when.hour % 12 or 12}:{when:%M %p}"


def teacher_tab_attendance_records(teacher_id):
    st.title("Records", anchor=False)

    records = [r for r in get_attendance_for_teacher(teacher_id) if r.get('timestamp')]
    if not records:
        st.html('<p class="lead">No attendance saved yet. Every class you save shows up here, newest first.</p>')
        st.button("Take attendance", type="primary", icon=":material/how_to_reg:", on_click=switch_tab, args=("take",))
        return

    names = get_student_names({r['student_id'] for r in records})
    df = pd.DataFrame([
        {
            "session": r['timestamp'].split(".")[0],
            "when": local_time(r['timestamp']),
            "subject_id": r['subject_id'],
            "subject": r['subjects']['name'],
            "code": r['subjects']['subject_code'],
            "student_id": r['student_id'],
            "student": names.get(r['student_id'], f"Student {r['student_id']}"),
            "present": bool(r.get('is_present', False)),
        }
        for r in records
    ])

    subject_names = dict(zip(df['subject_id'].tolist(), (df['subject'] + " (" + df['code'] + ")").tolist()))
    # Open on a single subject, where the register and the 75% list make sense
    if st.session_state.get('records_subject') not in ["all", *subject_names]:
        st.session_state.records_subject = next(iter(subject_names))
    choice = st.selectbox("Subject", options=[*subject_names, "all"], key="records_subject",
                          format_func=lambda sid: "All subjects" if sid == "all" else subject_names[sid])
    if choice != "all":
        df = df[df['subject_id'] == choice]

    sessions = (
        df.groupby(['session', 'subject_id'])
        .agg(when=('when', 'first'), code=('code', 'first'), present=('present', 'sum'), total=('present', 'count'))
        .reset_index()
        .sort_values('when', ascending=False)
    )

    if choice == "all":
        st.caption(f"{plural(len(sessions), 'class', 'classes')}, {df['present'].mean():.0%} average attendance. "
                   "Pick a subject to see its register and who is below 75%.")
        class_list(df, sessions)
    else:
        subject_summary(df, sessions)
        st.session_state.setdefault('records_view', "register")
        st.segmented_control("View", options=["register", "classes"], key="records_view", required=True,
                             format_func={"register": ":material/grid_on: Register",
                                          "classes": ":material/view_list: Classes"}.get,
                             label_visibility="collapsed", width="stretch")
        if st.session_state.records_view == "register":
            register_grid(df, sessions, subject_names[choice])
        else:
            class_list(df, sessions)

    export = pd.DataFrame({
        "Date": df['when'].map(lambda w: w.strftime("%Y-%m-%d")),
        "Time": df['when'].map(lambda w: w.strftime("%H:%M")),
        "Subject code": df['code'],
        "Subject": df['subject'],
        "Student": df['student'],
        "Status": df['present'].map({True: "Present", False: "Absent"}),
    }).sort_values(["Date", "Time", "Student"], ascending=[False, False, True])
    st.download_button("Download CSV", export.to_csv(index=False), file_name="rollcall-attendance.csv",
                       mime="text/csv", icon=":material/download:", width="stretch")


def student_rates(df):
    rates = (df.groupby('student_id')
             .agg(student=('student', 'first'), attended=('present', 'sum'), total=('present', 'count'))
             .reset_index())
    rates['rate'] = rates['attended'] / rates['total']
    return rates


def subject_summary(df, sessions):
    rates = student_rates(df)
    below = rates[rates['rate'] < ATTENDANCE_TARGET].sort_values('rate')
    by_date = sessions.sort_values('when')
    trend = (by_date['present'] / by_date['total']).tolist()

    numbers, watch = st.columns([3, 2], gap="medium")
    with numbers:
        # Two plain numbers share a row on a phone; the trend takes the full width
        with st.container(horizontal=True, gap="small"):
            st.metric("Classes taken", len(sessions), border=True, width=150)
            st.metric(f"Below {ATTENDANCE_TARGET:.0%}", len(below), border=True, width=150,
                      help="Students whose attendance in this subject is under the minimum")
            st.metric("Average attendance", f"{df['present'].mean():.0%}", border=True, width="stretch",
                      chart_data=trend, chart_type="line", help="Share of students present, class by class")
    with watch:
        with st.container(border=True, key="below_target"):
            st.markdown(f":material/warning: **Below {ATTENDANCE_TARGET:.0%}**")
            if len(below):
                st.markdown("\n".join(f"- {md_escape(r.student)} :red[{r.rate:.0%}]" for r in below.itertuples()))
            else:
                st.caption("Everyone is at or above the minimum.")


def register_grid(df, sessions, subject_label):
    """The paper register: one row per student, one column per class, newest class first."""
    labels = {s.session: short_when(s.when) for s in sessions.itertuples()}
    marks = df.assign(mark=df['present'].map({True: "✓", False: "A"}), column=df['session'].map(labels))
    grid = marks.pivot_table(index='student_id', columns='column', values='mark', aggfunc='first').fillna("")
    grid = grid[[labels[s] for s in sessions['session'] if labels[s] in grid.columns]]

    rates = student_rates(df).set_index('student_id')
    grid.insert(0, "Attendance", (rates['rate'] * 100).round())
    grid.insert(0, "Student", rates['student'])
    grid = grid.sort_values("Student").reset_index(drop=True)

    styled = grid.style.map(
        lambda mark: "color: #C62F37; font-weight: 700" if mark == "A" else "color: #1F3AA8" if mark == "✓" else "",
        subset=[c for c in grid.columns if c not in ("Student", "Attendance")],
    )
    st.dataframe(
        styled,
        hide_index=True,
        height=min(38 + 35 * len(grid), 720),
        column_config={
            "Student": st.column_config.TextColumn(pinned=True),
            "Attendance": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d%%"),
        },
        alt=f"Attendance register for {subject_label}, one row per student and one column per class",
    )
    st.caption("✓ present, A absent. Scroll sideways for older classes.")


def class_list(df, sessions):
    for s in sessions.head(RECENT_SESSIONS).itertuples():
        marks = df[(df['session'] == s.session) & (df['subject_id'] == s.subject_id)]
        absent = sorted(marks.loc[~marks['present'], 'student'])
        present = sorted(marks.loc[marks['present'], 'student'])
        label = f"**{short_when(s.when)}**  {s.code}  :blue[{s.present}/{s.total}]"
        with st.expander(label):
            if absent:
                st.markdown(f"**Absent ({len(absent)}):** " + md_escape(", ".join(absent)))
            if present:
                st.markdown(f"**Present ({len(present)}):** " + md_escape(", ".join(present)))
    if len(sessions) > RECENT_SESSIONS:
        st.caption(f"Showing the latest {RECENT_SESSIONS}. Download the CSV for the full history.")


# Sign in

def set_teacher_view(view):
    st.session_state.teacher_login_type = view


def login_teacher(username, password):
    if not username or not password:
        return False

    teacher = teacher_login(username, password)

    if teacher:
        sign_in('teacher', teacher)
        return True

    return False


def teacher_screen_login():
    header_dashboard("Back", go_home, ":material/arrow_back:")
    form_side, panel_side = st.columns(2, gap="large")
    with panel_side:
        brand_panel("Snap the class, check the register, save. Most classes take under a minute.")
    with form_side:
        teacher_login_form()


def teacher_login_form():
    st.title("Teacher sign in", anchor=False)

    with st.form("teacher_login", border=False):
        username = st.text_input("Username", placeholder="ananyaroy", autocomplete="username")
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", type="primary", icon=":material/login:", width="stretch")

    if submitted:
        if not username.strip() or not password:
            st.error("Enter your username and password.")
        elif login_teacher(username.strip(), password):
            st.rerun()
        else:
            st.error("That username and password don't match. Check both and try again.")

    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.caption("New to RollCall?")
        st.button("Create a teacher account", type="tertiary", on_click=set_teacher_view, args=("register",))


def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    if not teacher_username or not teacher_name or not teacher_pass:
        return None, "Fill in your name, a username and a password."
    if len(teacher_pass) < 6:
        return None, "Use at least 6 characters for your password."
    if teacher_pass != teacher_pass_confirm:
        return None, "The two passwords don't match."
    if check_teacher_exists(teacher_username):
        return None, f"The username {teacher_username} is taken. Try another."

    try:
        created = create_teacher(teacher_username, teacher_pass, teacher_name)
    except Exception:
        return None, "Couldn't create the account. Try again in a moment."
    return created[0] if created else None, "Account created."


def teacher_screen_register():
    header_dashboard("Back", go_home, ":material/arrow_back:")
    form_side, panel_side = st.columns(2, gap="large")
    with panel_side:
        brand_panel("Create a subject, share its code, and take your first register today.")
    with form_side:
        teacher_register_form()


def teacher_register_form():
    st.title("Create a teacher account", anchor=False)

    with st.form("teacher_register", border=False):
        teacher_name = st.text_input("Full name", placeholder="Ananya Roy", autocomplete="name")
        teacher_username = st.text_input("Username", placeholder="ananyaroy", autocomplete="username",
                                         help="You'll use this to sign in.")
        teacher_pass = st.text_input("Password", type="password", autocomplete="new-password",
                                     help="At least 6 characters.")
        teacher_pass_confirm = st.text_input("Confirm password", type="password", autocomplete="new-password")
        submitted = st.form_submit_button("Create account", type="primary", width="stretch")

    if submitted:
        teacher, message = register_teacher(teacher_username.strip(), teacher_name.strip(), teacher_pass,
                                            teacher_pass_confirm)
        if teacher:
            sign_in('teacher', teacher)
            st.session_state.pop('teacher_login_type', None)
            st.rerun()
        else:
            st.error(message)

    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        st.caption("Already have an account?")
        st.button("Sign in", type="tertiary", on_click=set_teacher_view, args=("login",))
