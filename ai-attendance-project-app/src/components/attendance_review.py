import time
from datetime import datetime, timezone

import streamlit as st

from src.components.scan_timeline import show_timeline
from src.database.db import create_attendance
from src.ui.format import esc, md_escape, tally_html


def start_review(subject, rows, note=None, flags=None, photos=None, steps=None, strangers=None):
    """Hold a fresh set of marks for the teacher to check before anything is saved.

    flags: sentences about anything that needs a second look. photos: JPEG bytes with the matches drawn on.
    steps: (label, detail) pairs from the scan's timeline.
    strangers: (close-up JPEG, label) pairs for faces that didn't match anyone on the roster.
    """
    st.session_state.attendance_review = {
        "subject_id": subject['subject_id'],
        "subject_name": subject['name'],
        "subject_code": subject['subject_code'],
        "rows": sorted(rows, key=lambda r: r['name'].lower()),
        "note": note,
        "flags": flags or [],
        "photos": photos or [],
        "steps": steps or [],
        "strangers": strangers or [],
        "nonce": time.time_ns(),
        "fresh": True,
    }


def clear_review():
    st.session_state.pop('attendance_review', None)


def _mark_key(review, row):
    return f"mark_{review['nonce']}_{row['student_id']}"


def _is_present(review, row):
    return bool(st.session_state.get(_mark_key(review, row), row['present']))


def _row_label(row, present):
    name = md_escape(row['name'])
    if not present:
        return f"{name} :red[absent]"
    label = f"{name} :gray[{row['source'] or 'marked by you'}]"
    if row.get('check'):
        label += f" :orange[{row['check']}]"
    return label


def _save(review):
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    logs = [
        {
            'student_id': row['student_id'],
            'subject_id': review['subject_id'],
            'timestamp': timestamp,
            'is_present': _is_present(review, row),
        }
        for row in review['rows']
    ]
    create_attendance(logs)
    return sum(log['is_present'] for log in logs), len(logs)


def attendance_review(on_saved=None):
    review = st.session_state.attendance_review
    rows = review['rows']
    present = sum(_is_present(review, row) for row in rows)

    st.title("Check the register", anchor=False)
    st.html(f'<p class="subject-meta"><span class="code">{esc(review["subject_code"])}</span>&ensp;{esc(review["subject_name"])}</p>'
            + tally_html(present, f"of {len(rows)} present", fresh=review.pop('fresh', False)))
    # Laptops: the evidence on the left, the register on the right. Phones stack them in that order.
    evidence, register = st.columns([2, 3], gap="large")
    with evidence:
        review_evidence(review)
    with register:
        review_register(review, present)

    # Pinned to the bottom of the screen so Save is always in reach of a thumb
    with st.container(horizontal=True, key="review_actions"):
        st.button("Discard", on_click=clear_review, width="stretch", icon=":material/close:")
        if st.button("Save attendance", type="primary", width="stretch", icon=":material/check:"):
            try:
                saved, total = _save(review)
            except Exception:
                st.error("Couldn't save the attendance. Check your connection, then press Save again.")
                return
            st.session_state.saved_notice = f"Saved {review['subject_name']}: {saved} of {total} present."
            clear_review()
            if on_saved:
                on_saved()
            st.rerun()


def review_evidence(review):
    if review['flags']:
        st.warning("\n".join(f"- {flag}" for flag in review['flags']), title="Check before saving",
                   icon=":material/flag:")

    if review['strangers']:
        st.caption("Faces to look at")
        with st.container(horizontal=True, gap="small", key="strangers"):
            for face, label in review['strangers']:
                st.image(face, width=72, caption=label, alt=f"Close-up of a face labelled {label}")

    photos = review['photos']
    if len(photos) == 1:
        st.image(photos[0], width="stretch", alt="Class photo with a labelled box around each face found")
    elif photos:
        for number, (tab, photo) in enumerate(zip(st.tabs([f"Photo {i}" for i in range(1, len(photos) + 1)]), photos), start=1):
            tab.image(photo, width="stretch", alt=f"Class photo {number} with a labelled box around each face found")
    if photos:
        st.caption("Blue boxes are matches, amber ones are worth a check, red ones didn't match anyone in this subject.")

    if review['steps']:
        with st.expander("How RollCall worked this out", icon=":material/timeline:", type="compact"):
            show_timeline(review['steps'])
    elif review['note']:
        st.caption(review['note'])


def _initials(name):
    parts = name.split()
    return (parts[0][:1] + (parts[-1][:1] if len(parts) > 1 else "")).upper()


def review_register(review, present):
    rows = review['rows']
    with_faces = any(row.get('face') for row in rows)
    absent = len(rows) - present
    to_check = sum(1 for row in rows if row.get('check'))
    filter_key = f"review_filter_{review['nonce']}"
    st.session_state.setdefault(filter_key, "all")
    st.segmented_control("Show", options=["all", "absent", "check"], key=filter_key, required=True,
                         format_func={"all": f"All {len(rows)}", "absent": f"Absent {absent}",
                                      "check": f"To check {to_check}"}.get,
                         label_visibility="collapsed", width="stretch")
    shown = {
        "all": rows,
        "absent": [row for row in rows if not _is_present(review, row)],
        "check": [row for row in rows if row.get('check')],
    }[st.session_state[filter_key]]

    st.caption("Tap a name to change their mark. Nothing is saved until you press Save.")
    with st.container(key="register"):
        for row in shown:
            with st.container(horizontal=True, vertical_alignment="center", gap="small",
                              key=f"row_{review['nonce']}_{row['student_id']}"):
                if with_faces:
                    # The face each tick came from, so a teacher can confirm it at a glance
                    if row.get('face'):
                        st.image(row['face'], width=44, alt=f"Face matched to {row['name']}")
                    else:
                        st.html(f'<span class="avatar">{esc(_initials(row["name"]))}</span>', width="content")
                # Marks on rows hidden by the filter are kept until Save
                st.checkbox(_row_label(row, _is_present(review, row)), value=row['present'],
                            key=_mark_key(review, row), width="stretch", persist_state="page")
        if not shown:
            st.caption("Nobody is marked absent." if st.session_state[filter_key] == "absent" else "Nothing to check.")
