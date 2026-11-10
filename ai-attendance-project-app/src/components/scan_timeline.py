import streamlit as st


class ScanTimeline:
    """Draws each stage of a scan as a timeline step while it runs, and keeps them for the review.

    Pass an instance as the `report` callback of the roll-call scans.
    """

    def __init__(self):
        self.steps = []
        self._current = None

    def __call__(self, event, label, detail=None):
        if event == "start":
            self._current = st.status(f"{label}…", state="running", type="step")
            return
        self._current.update(label=label, state="complete")
        if detail:
            self._current.caption(detail)
        self.steps.append((label, detail))

    def fail(self, label):
        if self._current is not None:
            self._current.update(label=label, state="error")


def show_timeline(steps):
    for label, detail in steps:
        with st.status(label, state="complete", type="step"):
            if detail:
                st.caption(detail)
