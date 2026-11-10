import streamlit as st
from urllib.parse import urlsplit

import segno
import io

from src.ui.format import esc

APP_DOMAIN = "https://rollcall-ai.streamlit.app"


def app_domain():
    # Use the address the teacher is on, so links work on local and preview deployments too
    try:
        parts = urlsplit(st.context.url)
        if parts.scheme and parts.netloc:
            return f"{parts.scheme}://{parts.netloc}"
    except Exception:
        pass
    return APP_DOMAIN


@st.dialog("Join code")
def share_subject_dialog(subject_name, subject_code):
    join_url = f"{app_domain()}/?join-code={subject_code}"

    st.html(f'<p class="join-code">{esc(subject_code)}</p>'
            f'<p class="join-code-help">Students open RollCall, sign in, choose Join a subject and enter this code for {esc(subject_name)}. '
            'Or they scan the QR code below.</p>')

    qr = segno.make(join_url)

    out = io.BytesIO()

    qr.save(out, kind='png', scale=10, border=2)

    st.image(out.getvalue(), width="stretch", alt=f"QR code to join {subject_name}")

    st.caption("Join link, to share on WhatsApp or email")
    st.code(join_url, language=None)
