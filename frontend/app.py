"""
Healthcare Patient Management System - Main Streamlit Dashboard
Visual Identity: Deep Navy, White, Teal accents, subtle borders, persistent sidebar.
Data Integrity: All data fetched live from FastAPI backend.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from frontend.services.api_client import APIClient

st.set_page_config(
    page_title="Healthcare Patient Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply CSS
try:
    with open("frontend/assets/style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

api = APIClient()

# Session State for Authentication
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

# Sidebar Authentication & Navigation
with st.sidebar:
    st.markdown("## 🏥 **HealthPulse™**")
    st.caption("Enterprise Healthcare Management")
    st.markdown("---")

    if not st.session_state.token:
        st.subheader("🔐 Staff Sign-In")
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="Admin123!")
        
        if st.button("Sign In", use_container_width=True, type="primary"):
            try:
                auth_res = api.login(username, password)
                st.session_state.token = auth_res["access_token"]
                st.session_state.user = {
                    "username": auth_res["username"],
                    "role": auth_res["role"]
                }
                st.success(f"Welcome, {username} ({auth_res['role']})")
                st.rerun()
            except Exception as e:
                st.error("Authentication failed. Check credentials.")
        
        st.info("**Demo Accounts:**\n- `admin` / `Admin123!` (Admin)\n- `doctor` / `Doctor123!` (Healthcare Staff)\n- `analyst` / `Analyst123!` (Analyst)")
    else:
        st.success(f"👤 **{st.session_state.user['username']}**")
        st.badge(f"Role: {st.session_state.user['role']}")
        
        if st.button("Sign Out", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

    st.markdown("---")
    st.caption("FastAPI Microservice: **Online**")
    st.caption("Relational Core: **Normalized DB**")

# Main Content
st.markdown(
    """
    <div class="main-header">
        <h1>🏥 Clinical Operations & Patient Management Dashboard</h1>
        <p>Live Hospital Admissions, Readmission Risk Indicators, and Length-of-Stay Metrics</p>
    </div>
    """,
    unsafe_allow_html=True
)

if not st.session_state.token:
    st.warning("⚠️ Please sign in through the sidebar to access live operational metrics and records.")
    st.stop()

# Fetch Analytics Overview
try:
    with st.spinner("Fetching real-time hospital analytics from FastAPI..."):
        overview = api.get_analytics_overview(st.session_state.token)
        admissions = api.get_admission_trends(st.session_state.token)
        readmissions = api.get_readmission_insights(st.session_state.token)
        los = api.get_length_of_stay(st.session_state.token)
except Exception as e:
    st.error(f"Failed to communicate with FastAPI backend: {e}")
    st.stop()

# Top KPI Metric Cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Active Patients</div>
            <div class="kpi-value">{overview.get('total_patients', 0):,}</div>
            <div class="kpi-subtitle">Master Patient Registry</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Clinical Encounters</div>
            <div class="kpi-value">{overview.get('total_encounters', 0):,}</div>
            <div class="kpi-subtitle">Logged Inpatient Records</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top-color: #EF4444;">
            <div class="kpi-title">Readmission Rate</div>
            <div class="kpi-value">{overview.get('readmission_rate_percent', 0.0)}%</div>
            <div class="kpi-subtitle" style="color: #EF4444;">{overview.get('total_readmissions', 0):,} Total Readmissions</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-top-color: #3B82F6;">
            <div class="kpi-title">Avg Length of Stay</div>
            <div class="kpi-value">{overview.get('average_length_of_stay', 0.0)} Days</div>
            <div class="kpi-subtitle" style="color: #3B82F6;">Hospital Inpatient Duration</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# Charts Section
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Readmission Status Distribution")
    status_data = readmissions.get("status_breakdown", [])
    if status_data:
        df_readm = pd.DataFrame(status_data)
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        colors = ["#0D9488", "#EF4444", "#F59E0B"]
        ax1.pie(
            df_readm["encounters"],
            labels=df_readm["status"],
            autopct="%1.1f%%",
            startangle=140,
            colors=colors[:len(df_readm)],
            wedgeprops=dict(width=0.4, edgecolor='w')
        )
        ax1.axis("equal")
        st.pyplot(fig1)
        plt.close(fig1)
    else:
        st.info("No readmission records available.")

with col_right:
    st.subheader("⏱️ Length of Stay (LOS) Groups")
    los_data = los.get("length_of_stay_distribution", [])
    if los_data:
        df_los = pd.DataFrame(los_data)
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.barh(df_los["stay_bracket"], df_los["encounter_count"], color="#1E3A8A")
        ax2.set_xlabel("Number of Encounters")
        ax2.set_ylabel("Length of Stay Bracket")
        ax2.grid(axis='x', linestyle='--', alpha=0.5)
        st.pyplot(fig2)
        plt.close(fig2)
    else:
        st.info("No length of stay records available.")

st.markdown("---")

# Admission Types Table
st.subheader("🏥 Admission Source & Encounter Volumes")
adm_data = admissions.get("admission_breakdown", [])
if adm_data:
    df_adm = pd.DataFrame(adm_data)
    st.dataframe(
        df_adm.rename(columns={
            "admission_type": "Admission Category",
            "total_encounters": "Encounters",
            "avg_stay_days": "Avg Stay (Days)"
        }),
        use_container_width=True,
        hide_index=True
    )
