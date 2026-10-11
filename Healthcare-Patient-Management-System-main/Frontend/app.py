import streamlit as st

from services.api_client import (
    get_analytics_overview,
    get_analytics
)
from components.dashboard import render_dashboard


st.set_page_config(
    page_title="Healthcare Intelligence",
    page_icon="H",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css():
    with open(
        "assets/style.css",
        encoding="utf-8"
    ) as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True
        )


load_css()

with st.sidebar:
    st.title("Healthcare")
    st.caption("PATIENT MANAGEMENT PLATFORM")
    st.divider()

    st.markdown("### Workspace")
    st.radio(
        "Navigation",
        ["Dashboard"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("Data powered by FastAPI + MySQL")


try:
    with st.spinner("Loading healthcare analytics..."):
        overview = get_analytics_overview()
        admissions = get_analytics("admissions")
        readmissions = get_analytics("readmissions")
        length_of_stay = get_analytics("length-of-stay")

    render_dashboard(
        overview,
        admissions,
        readmissions,
        length_of_stay
    )

except Exception:
    st.error(
        "Unable to load healthcare analytics. "
        "Verify that FastAPI is running and all "
        "analytics endpoints are available."
    )