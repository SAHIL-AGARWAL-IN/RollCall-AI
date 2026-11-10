from src.database.config import supabase
import bcrypt



def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


def check_teacher_exists(username):
    # Check for unique username, returns false when username is already taken
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0



def create_teacher(username, password, name):

    data = { "username" : username, "password": hash_pass(password), "name": name}
    response = supabase.table("teachers").insert(data).execute()
    return response.data


def get_teacher(username):
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    return response.data[0] if response.data else None


def teacher_login(username, password):
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher['password']):
            return teacher
    return None


def get_all_students():
    response = supabase.table('students').select("*").execute()
    return response.data

def get_student(student_id):
    response = supabase.table('students').select("*").eq('student_id', student_id).execute()
    return response.data[0] if response.data else None

def get_student_names(student_ids):
    # Maps student_id -> name without pulling face and voice embeddings
    if not student_ids:
        return {}
    response = supabase.table('students').select("student_id, name").in_('student_id', list(student_ids)).execute()
    return {s['student_id']: s['name'] for s in response.data}

def create_student(new_name, face_embedding=None, voice_embedding=None):
    data = {'name': new_name, 'face_embedding':face_embedding, "voice_embedding": voice_embedding}
    response = supabase.table('students').insert(data).execute()
    return response.data

def update_student_voice(student_id, voice_embedding):
    response = supabase.table('students').update({"voice_embedding": voice_embedding}).eq('student_id', student_id).execute()
    return response.data


def normalize_subject_code(code):
    return code.strip().upper()

def get_subject_by_code(code):
    # Codes are saved in upper case, older subjects may not be, so try both spellings
    code = code.strip()
    spellings = list({code, code.upper()})
    response = supabase.table('subjects').select("subject_id, name, subject_code, section").in_('subject_code', spellings).execute()
    return response.data[0] if response.data else None

def create_subject(subject_code, name, section, teacher_id):
    data = {"subject_code": normalize_subject_code(subject_code), "name": name.strip(), "section": section.strip(), "teacher_id": teacher_id}
    response = supabase.table("subjects").insert(data).execute()
    return response.data

def get_teacher_subjects(teacher_id):
    response = supabase.table('subjects').select("*, subject_students(count), attendance_logs(timestamp, is_present)").eq("teacher_id", teacher_id).execute()
    subjects = response.data


    for sub in subjects:
        sub['total_students'] = sub.get("subject_students", [{}])[0].get('count', 0) if sub.get('subject_students') else 0
        # One entry per class taken, oldest first: (timestamp, present, total)
        sessions = {}
        for log in sub.get('attendance_logs', []):
            counts = sessions.setdefault(log['timestamp'], [0, 0])
            counts[0] += bool(log.get('is_present'))
            counts[1] += 1
        sub['class_history'] = [(ts, present, total) for ts, (present, total) in sorted(sessions.items())]
        sub['total_classes'] = len(sessions)


        sub.pop('subject_students', None)
        sub.pop('attendance_logs', None)

    return subjects

def get_subject_students(subject_id):
    response = supabase.table('subject_students').select("*, students(*)").eq('subject_id', subject_id).execute()
    return response.data


def is_enrolled(student_id, subject_id):
    response = supabase.table('subject_students').select('student_id').eq('subject_id', subject_id).eq('student_id', student_id).execute()
    return len(response.data) > 0

def  enroll_student_to_subject(student_id, subject_id):
    data = {'student_id': student_id, "subject_id": subject_id}
    response= supabase.table('subject_students').insert(data).execute()
    return response.data


def  unenroll_student_to_subject(student_id, subject_id):
    response= supabase.table('subject_students').delete().eq('student_id', student_id).eq('subject_id', subject_id).execute()
    return response.data



def get_student_subjects(student_id):
    response = supabase.table('subject_students').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def get_student_attendance(student_id):
    response = supabase.table('attendance_logs').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def create_attendance(logs):
    response = supabase.table('attendance_logs').insert(logs).execute()
    return response.data

def get_attendance_for_teacher(teacher_id):
    response = supabase.table('attendance_logs').select("*, subjects!inner(*)").eq('subjects.teacher_id', teacher_id).execute()
    return response.data
