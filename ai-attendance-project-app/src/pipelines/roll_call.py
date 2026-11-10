"""Turn face and voice matches into a register to review, plus anything the teacher should check."""
from collections import Counter
from time import perf_counter

import numpy as np

from src.pipelines.annotate import crop_face, draw_matches
from src.pipelines.face_pipeline import WEAK_MATCH, detect_faces, match_faces
from src.ui.format import first_name, plural

# Voice similarities between the 0.65 match threshold and this are real but worth a second look
WEAK_VOICE = 0.75


def _silent(event, label, detail=None):
    pass


def _check_step(report, flags):
    report("start", "Looking for anything odd")
    if flags:
        report("done", f"{plural(len(flags), 'thing')} to check", "Listed above the register")
    else:
        report("done", "Nothing looks off", "No unknown faces, doubles or weak matches")


def _join(names):
    names = list(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def scan_class_photos(subject, images, roster, report=_silent):
    """Find every face in the class photos and match it to the subject's roster.

    images: upright RGB PIL images. roster: enrolled student dicts.
    report(event, label, detail) is called with "start" before each stage and "done" after it,
    so the screen can show the scan as it happens.
    Returns (rows, flags, annotated JPEG bytes per photo, note, strangers). Each matched row carries
    'face', a close-up of the face it was matched to; strangers are (close-up, label) pairs for the
    faces the teacher should look at.
    """
    on_roster = {s['student_id']: s for s in roster}
    seen = {}        # student_id -> photo numbers they were matched in
    closest = {}     # student_id -> smallest distance across photos
    best_face = {}   # student_id -> (photo index, face index) of that closest match
    outsiders = {}   # matched students who aren't enrolled in this subject -> photo numbers
    doubles = []     # (student_id, photo number) when one student matched two faces in a photo
    unknown = 0
    total_faces = 0
    scans = []

    for photo_no, img in enumerate(images, start=1):
        report("start", f"Looking for faces in photo {photo_no}")
        started = perf_counter()
        faces = detect_faces(np.array(img))
        matches = match_faces([face['embedding'] for face in faces])
        total_faces += len(faces)
        report("done", f"Photo {photo_no}: found {plural(len(faces), 'face')}",
               f"Found and compared to every enrolled face in {perf_counter() - started:.1f} s")

        # One person can only be in a photo once: the closest face keeps the match
        nearest = {}
        for i, (sid, distance) in enumerate(matches):
            if sid is not None and (sid not in nearest or distance < matches[nearest[sid]][1]):
                nearest[sid] = i

        verdicts = []
        for i, (sid, distance) in enumerate(matches):
            if sid is None:
                unknown += 1
                verdicts.append(('unknown', None, distance))
            elif nearest[sid] != i:
                doubles.append((sid, photo_no))
                verdicts.append(('double', sid, distance))
            elif sid not in on_roster:
                outsiders.setdefault(sid, []).append(photo_no)
                verdicts.append(('outsider', sid, distance))
            else:
                seen.setdefault(sid, []).append(photo_no)
                if sid not in closest or distance < closest[sid]:
                    closest[sid] = distance
                    best_face[sid] = (photo_no - 1, i)
                verdicts.append(('match', sid, distance))
        scans.append((img, faces, verdicts))

    report("start", f"Marking the {subject['subject_code']} register")
    # Only students on this subject's roster are named. Anyone else stays anonymous, so a photo
    # can't be used to identify students from other teachers' classes.
    name_of = lambda sid: on_roster[sid]['name'] if sid in on_roster else "someone not enrolled"

    annotated, strangers = [], []
    for img, faces, verdicts in scans:
        boxes = []
        for face, (verdict, sid, distance) in zip(faces, verdicts):
            if verdict == 'match' and distance > WEAK_MATCH:
                boxes.append({'box': face['box'], 'label': first_name(name_of(sid)) + '?', 'kind': 'weak'})
            elif verdict == 'match':
                boxes.append({'box': face['box'], 'label': first_name(name_of(sid)), 'kind': 'match'})
            elif verdict == 'double' and sid in on_roster:
                boxes.append({'box': face['box'], 'label': f"{first_name(name_of(sid))} again?", 'kind': 'weak'})
            elif verdict == 'double':
                boxes.append({'box': face['box'], 'label': "Not enrolled", 'kind': 'unknown'})
            elif verdict == 'outsider':
                boxes.append({'box': face['box'], 'label': "Not enrolled", 'kind': 'unknown'})
            else:
                boxes.append({'box': face['box'], 'label': '?', 'kind': 'unknown'})
            if verdict != 'match':
                strangers.append((crop_face(img, face['box']), boxes[-1]['label']))
        annotated.append(draw_matches(img, boxes))

    rows = []
    for student in roster:
        sid = student['student_id']
        photos = seen.get(sid, [])
        source = ("photo " if len(photos) == 1 else "photos ") + ", ".join(map(str, photos)) if photos else ""
        weak = bool(photos) and closest[sid] > WEAK_MATCH
        face = None
        if photos:
            photo_idx, face_idx = best_face[sid]
            face = crop_face(scans[photo_idx][0], scans[photo_idx][1][face_idx]['box'])
        rows.append({'student_id': sid, 'name': student['name'], 'present': bool(photos), 'source': source,
                     'check': "weak match" if weak else "", 'face': face})

    flags = []
    if unknown:
        flags.append(f"{plural(unknown, 'face')} didn't match any student. "
                     f"{'It has' if unknown == 1 else 'They have'} a red box on the photo.")
    for sid, photo_no in doubles:
        if sid in on_roster:
            flags.append(f"Two faces in photo {photo_no} look like {name_of(sid)}. The closer one counts; check the other.")
    if outsiders:
        photos = sorted({n for photo_nos in outsiders.values() for n in photo_nos})
        flags.append(f"{plural(len(outsiders), 'person', 'people')} in photo {', '.join(map(str, photos))} "
                     f"{'is' if len(outsiders) == 1 else 'are'} a RollCall student but not enrolled in {subject['subject_code']}.")
    weak_names = [r['name'] for r in rows if r['check']]
    if weak_names:
        flags.append(f"Weak {'match' if len(weak_names) == 1 else 'matches'} for {_join(weak_names)}. "
                     f"{'It is' if len(weak_names) == 1 else 'They are'} ticked, but check before saving.")

    present = sum(row['present'] for row in rows)
    report("done", f"Matched {present} of {plural(len(roster), 'student')}",
           f"{len(roster) - present} not seen in any photo")
    _check_step(report, flags)

    if total_faces == 0:
        note = "No faces were found. Retake the photo in better light, or mark the register by hand."
    else:
        note = f"Found {plural(total_faces, 'face')} in {plural(len(images), 'photo')}."
    return rows, flags, annotated, note, strangers


def review_voice_segments(subject, segments, roster, report=_silent):
    """Turn identified roll-call segments into a register. Returns (rows, flags, note)."""
    report("start", f"Marking the {subject['subject_code']} register")
    answers = Counter(seg['student_id'] for seg in segments if seg['student_id'] is not None)
    best = {}
    for seg in segments:
        sid = seg['student_id']
        if sid is not None:
            best[sid] = max(seg['score'], best.get(sid, seg['score']))
    unknown = sum(1 for seg in segments if seg['student_id'] is None)

    rows, flags = [], []
    for student in roster:
        sid = student['student_id']
        heard = sid in answers
        check = ""
        if answers[sid] > 1:
            check = f"answered {answers[sid]} times"
            flags.append(f"{student['name']}'s voice answered {answers[sid]} times. "
                         "One of those may have been for someone else.")
        elif heard and best[sid] < WEAK_VOICE:
            check = "weak match"
        rows.append({'student_id': sid, 'name': student['name'], 'present': heard,
                     'source': f"voice match {best[sid]:.0%}" if heard else "", 'check': check})

    if unknown:
        flags.append(f"{plural(unknown, 'answer')} didn't match any voice in {subject['subject_code']}. "
                     "Someone without a voice sample may have answered.")
    weak_names = [r['name'] for r in rows if r['check'] == "weak match"]
    if weak_names:
        flags.append(f"Weak voice {'match' if len(weak_names) == 1 else 'matches'} for {_join(weak_names)}. Check before saving.")

    report("done", f"Matched {len(answers)} of {plural(len(roster), 'student')}",
           f"{len(roster) - len(answers)} not heard")
    _check_step(report, flags)

    note = f"Heard {plural(len(segments), 'answer')} and matched {plural(len(answers), 'student')}."
    return rows, flags, note
