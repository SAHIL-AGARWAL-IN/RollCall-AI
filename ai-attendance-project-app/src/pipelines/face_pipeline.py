

import dlib
import numpy as np
import face_recognition_models
from PIL import Image, ImageOps
import streamlit as st

from src.database.db import get_all_students


# Phone cameras shoot 12MP+. dlib upsamples once while detecting, so a full-size
# photo is slow and can run the server out of memory. 2048px still leaves
# back-row faces big enough to detect.
MAX_IMAGE_SIDE = 2048

# dlib's face embeddings are trained so that two photos of the same person sit
# less than 0.6 apart. Matches between 0.5 and 0.6 are real but worth a second look.
MATCH_THRESHOLD = 0.6
WEAK_MATCH = 0.5


def load_image(file):
    """Open an uploaded photo upright, in RGB, at a size dlib can scan."""
    img = Image.open(file)
    # Phones save photos sideways and record the rotation in EXIF; dlib only finds upright faces
    img = ImageOps.exif_transpose(img).convert('RGB')
    img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    return img


@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()


    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec

def detect_faces(image_np):
    """Every face in the image: where it is (left, top, right, bottom) and its 128-number embedding."""
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1)

    found = []

    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1) #128 embedding

        found.append({
            'box': (face.left(), face.top(), face.right(), face.bottom()),
            'embedding': np.array(face_descriptor),
        })
    return found

def get_face_embeddings(image_np):
    return [face['embedding'] for face in detect_faces(image_np)]

@st.cache_resource
def get_face_index():
    """Every enrolled face as one matrix, so a lookup is a single distance calculation."""
    ids, embeddings = [], []

    for student in get_all_students():
        embedding = student.get('face_embedding')
        if embedding:
            ids.append(student['student_id'])
            embeddings.append(np.array(embedding))

    if not ids:
        return None
    return {'ids': ids, 'embeddings': np.vstack(embeddings)}


def refresh_face_index():
    # Only drop the index; st.cache_resource.clear() would also reload the dlib and voice models
    get_face_index.clear()
    return get_face_index() is not None

def match_faces(encodings):
    """The nearest enrolled student for each face, with the distance to them (lower is more alike).

    Returns (student_id, distance) per face; student_id is None when nobody is within MATCH_THRESHOLD.
    """
    index = get_face_index()
    if index is None:
        return [(None, None) for _ in encodings]

    matches = []
    for encoding in encodings:
        distances = np.linalg.norm(index['embeddings'] - encoding, axis=1)
        nearest = int(np.argmin(distances))
        distance = float(distances[nearest])
        student_id = index['ids'][nearest] if distance <= MATCH_THRESHOLD else None
        matches.append((student_id, distance))
    return matches

def identify_faces(encodings):
    matches = match_faces(encodings)
    detected_student = {sid: True for sid, _ in matches if sid is not None}
    index = get_face_index()
    return detected_student, (sorted(set(index['ids'])) if index else [])
