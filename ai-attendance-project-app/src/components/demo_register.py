import streamlit as st

# A register being marked, name by name: the app's opening moment. Pure CSS (see .demo-register in style.css).
DEMO_ROWS = [
    ("Aarav Sharma", True), ("Ananya Iyer", True), ("Dev Patel", False), ("Diya Kapoor", True),
    ("Hamza Rizvi", True), ("Rohan Gupta", False), ("Zoya Siddiqui", True),
]


def demo_register_html():
    rows = "".join(
        f'<li class="{"present" if here else "absent"}" style="--i:{i}"><span class="box"></span>{name}'
        f'{"" if here else "<em>absent</em>"}</li>'
        for i, (name, here) in enumerate(DEMO_ROWS)
    )
    present = sum(here for _, here in DEMO_ROWS)
    return (
        f'<div class="demo-register" role="img" aria-label="A register for CS101 being marked: {present} of {len(DEMO_ROWS)} present">'
        '<p class="subject-meta"><span class="code">CS101</span>&ensp;Monday, 9:30 AM</p>'
        f'<p class="tally"><span class="count count-up"></span><span class="of">of {len(DEMO_ROWS)} present</span></p>'
        f'<ul>{rows}</ul></div>'
    )


def brand_panel(line):
    """The marking register beside a sign-in form on wide screens; hidden on phones (see style.css)."""
    with st.container(key="brand_panel"):
        st.html(demo_register_html())
        st.caption(line)
