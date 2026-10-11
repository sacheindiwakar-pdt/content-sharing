"""
Healthcare Analytics, Reporting & Audit Logs Workspace
Provides deep-dive clinical intelligence, scheduled reporting, CSV/Excel export, and audit trails.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from frontend.services.api_client import APIClient

st.set_page_config(page_title="Analytics & Compliance", page_icon="📈", layout="wide")

try:
    with open("frontend/assets/style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

api = APIClient()

if "token" not in st.session_state or not st.session_state.token:
    st.warning("⚠️ Please sign in through the main Dashboard page to access Analytics & Compliance.")
    st.stop()

token = st.session_state.token
user_role = st.session_state.user.get("role", "")

st.markdown(
    """
    <div class="main-header">
        <h1>📈 Healthcare Analytics, Reports & Compliance Audits</h1>
        <p>Demographic Stratification, Readmission Predictors, Export Tools, and Audit Integrity</p>
    </div>
    """,
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs(["📊 Clinical & Demographic Analytics", "📥 Data Export & Reporting", "🛡️ Compliance Audit Trail"])

# TAB 1: Analytics
with tab1:
    try:
        demographics = api.get_demographics(token)
        age_data = demographics.get("age_groups", [])
        gender_data = demographics.get("gender_distribution", [])

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("👥 Encounters by Age Bracket")
            if age_data:
                df_age = pd.DataFrame(age_data)
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.bar(df_age["age"], df_age["encounters"], color="#0D9488")
                ax.set_ylabel("Total Encounters")
                ax.tick_params(axis='x', rotation=45)
                st.pyplot(fig)
                plt.close(fig)

        with c2:
            st.subheader("🧬 Patient Gender Distribution")
            if gender_data:
                df_gender = pd.DataFrame(gender_data)
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.pie(df_gender["total_patients"], labels=df_gender["gender"], autopct="%1.1f%%", colors=["#3B82F6", "#EC4899", "#94A3B8"])
                st.pyplot(fig)
                plt.close(fig)

        st.markdown("---")
        st.subheader("🏥 Readmissions by Age Cohort")
        if age_data:
            df_cohort = pd.DataFrame(age_data)
            df_cohort["Readmission Rate (%)"] = (df_cohort["readmitted_count"] / df_cohort["encounters"] * 100).round(2)
            st.dataframe(df_cohort.rename(columns={"age": "Age Cohort", "encounters": "Total Admissions", "readmitted_count": "Readmissions"}), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Failed to fetch analytics: {e}")

# TAB 2: Export
with tab2:
    st.subheader("📥 Operational Data Export (CSV & Excel)")
    st.write("Generate and download curated patient encounter datasets for operational reporting and regulatory compliance.")

    col_csv, col_excel = st.columns(2)
    with col_csv:
        st.markdown("#### Export Encounters (CSV)")
        st.caption("Standard RFC 4180 comma-separated values format")
        csv_url = api.export_encounters_csv_url()
        st.markdown(f"[📥 **Download Encounters CSV**]({csv_url})")

    with col_excel:
        st.markdown("#### Export Encounters (Excel)")
        st.caption("Microsoft Excel (.xlsx) workbook formatted for operational analysts")
        excel_url = api.export_encounters_excel_url()
        st.markdown(f"[📊 **Download Encounters XLSX**]({excel_url})")

# TAB 3: Audit Logs
with tab3:
    if user_role != "Admin":
        st.warning("🔒 Audit trail logs are restricted to Administrator accounts for HIPAA / regulatory compliance.")
    else:
        st.subheader("🛡️ Enterprise Audit Log (Create / Update / Delete Interceptor)")
        try:
            logs = api.get_audit_logs(token, limit=100)
            if logs:
                df_logs = pd.DataFrame(logs)
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info("No audit entries recorded yet.")
        except Exception as e:
            st.error(f"Failed to fetch audit logs: {e}")
