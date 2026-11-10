"""Create the demo class behind the home screen's "Try a demo class" button.

Run from the app folder, after setting DEMO_TEACHER in .streamlit/secrets.toml:

    .venv\\Scripts\\python scripts\\seed_demo.py

It adds a teacher account (no usable password; the button signs straight in), one subject,
30 sample students and four weeks of attendance. Sample students have no face or voice data,
so they never match a real photo. Running it again reuses what's already there.
"""
import random
import secrets
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from src.database.db import (create_attendance, create_student, create_subject, create_teacher,  # noqa: E402
                             enroll_student_to_subject, get_subject_by_code, get_subject_students, get_teacher)
from src.database.config import supabase  # noqa: E402

SUBJECT_CODE = "DEMO-CS101"
SUBJECT_NAME = "Introduction to Computer Science"
CLASSES = 12
STUDENTS = [
    "Aarav Sharma", "Ananya Iyer", "Arjun Mehta", "Diya Kapoor", "Hamza Rizvi", "Ishaan Verma", "Kavya Nair",
    "Rohan Gupta", "Saanvi Reddy", "Vihaan Joshi", "Aditi Rao", "Kabir Malhotra", "Meera Pillai", "Neel Banerjee",
    "Priya Menon", "Rahul Desai", "Sara Khan", "Tanvi Kulkarni", "Vivaan Chopra", "Zoya Siddiqui", "Aryan Bhat",
    "Bhavya Shah", "Dev Patel", "Esha Chatterjee", "Farhan Ali", "Gauri Deshpande", "Harsh Agarwal", "Isha Saxena",
    "Jay Thakur", "Kiara D'Souza",
]
# A few students below the 75% minimum, so the records have someone to flag
LOW_ATTENDANCE = {"Hamza Rizvi": 0.6, "Rohan Gupta": 0.55, "Isha Saxena": 0.68, "Vivaan Chopra": 0.7}


def class_times(count):
    """The last `count` Monday, Wednesday and Friday classes at 9:30 in India (04:00 UTC)."""
    day = datetime.now(timezone.utc).date() - timedelta(days=1)
    times = []
    while len(times) < count:
        if day.weekday() in (0, 2, 4):
            times.append(datetime.combine(day, time(4, 0), tzinfo=timezone.utc))
        day -= timedelta(days=1)
    return sorted(times)


def main():
    username = st.secrets.get("DEMO_TEACHER")
    if not username:
        sys.exit("Set DEMO_TEACHER in .streamlit/secrets.toml first, for example DEMO_TEACHER = \"demo\".")

    if get_teacher(username):
        print(f"Teacher {username} already exists.")
    else:
        create_teacher(username, secrets.token_urlsafe(24), "Demo Teacher")
        print(f"Created teacher {username}.")

    subject = get_subject_by_code(SUBJECT_CODE)
    if subject:
        print(f"Subject {SUBJECT_CODE} already exists.")
    else:
        create_subject(SUBJECT_CODE, SUBJECT_NAME, "A", username)
        subject = get_subject_by_code(SUBJECT_CODE)
        print(f"Created subject {SUBJECT_CODE}.")

    enrolled = {node['students']['name']: node['students'] for node in get_subject_students(subject['subject_id'])}
    for name in STUDENTS:
        if name not in enrolled:
            student = create_student(name)[0]
            enroll_student_to_subject(student['student_id'], subject['subject_id'])
            enrolled[name] = student
    print(f"{len(enrolled)} students enrolled.")

    has_logs = supabase.table('attendance_logs').select('student_id').eq('subject_id', subject['subject_id']).limit(1).execute()
    if has_logs.data:
        print("Attendance history already exists; leaving it as it is.")
        return

    rng = random.Random(2026)
    logs = []
    for when in class_times(CLASSES):
        for name, student in enrolled.items():
            chance = LOW_ATTENDANCE.get(name, rng.uniform(0.86, 0.98))
            logs.append({'student_id': student['student_id'], 'subject_id': subject['subject_id'],
                         'timestamp': when.isoformat(timespec="seconds"), 'is_present': rng.random() < chance})
    create_attendance(logs)
    print(f"Added {CLASSES} classes of attendance.")


if __name__ == "__main__":
    main()
