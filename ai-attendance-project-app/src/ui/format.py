import html
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import streamlit as st


def plural(count, word, many=None):
    return f"{count} {word if count == 1 else (many or word + 's')}"


def esc(text):
    return html.escape(str(text))


def md_escape(text):
    # Names go into widget labels, which render markdown
    for char in "\\*_[]`":
        text = text.replace(char, "\\" + char)
    return text


def viewer_timezone():
    try:
        return ZoneInfo(st.context.timezone or "UTC")
    except Exception:
        return timezone.utc


def local_time(ts):
    """Attendance timestamps are stored in UTC; show them in the viewer's timezone."""
    when = datetime.fromisoformat(ts)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(viewer_timezone())


def tally_html(count, of_text, low=False, fresh=False, small=False):
    classes = " ".join(c for c in ["tally", "fresh" if fresh else "", "small" if small else ""] if c)
    count_class = "count low" if low else "count"
    return f'<p class="{classes}"><span class="{count_class}">{esc(count)}</span><span class="of">{esc(of_text)}</span></p>'


def first_name(name):
    parts = str(name).split()
    return parts[0] if parts else str(name)
