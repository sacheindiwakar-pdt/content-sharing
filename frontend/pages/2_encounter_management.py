"""
Encounter Management Workspace
Filter by Readmission, Age, Admission Type; Record New Admissions; Manage Outcomes.
"""

import streamlit as st
import pandas as pd
from frontend.services.api_client import APIClient

st.set_page_config(page_title="Encounter Management", page_icon="📋", layout="wide")

try:
    with open("frontend/assets/style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

api = APIClient()

if "token" not in st.session_state or not st.session_state.token:
    st.warning("⚠️ Please sign in through the main Dashboard page to access Encounter Management.")
    st.stop()

token = st.session_state.token
user_role = st.session_state.user.get("role", "")

st.markdown(
    """
    <div class="main-header">
        <h1>📋 Clinical Encounter Operations</h1>
        <p>Browse Inpatient Encounters, Monitor Admission Types, and Log New Hospital Admissions</p>
    </div>
    """,
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs(["🔎 Encounter Explorer", "➕ Log New Admission", "⚙️ Update Encounter"])

# TAB 1: Filter Encounters
with tab1:
    c1, c2, c3 = st.columns(3)
    with c1:
        readm_filter = st.selectbox("Readmission Status", ["All", "<30", ">30", "NO"])
    with c2:
        age_filter = st.selectbox("Age Bracket", ["All", "[0-10)", "[10-20)", "[20-30)", "[30-40)", "[40-50)", "[50-60)", "[60-70)", "[70-80)", "[80-90)", "[90-100)"])
    with c3:
        p_filter = st.text_input("Patient ID (Optional)", placeholder="e.g. 8222157")

    r_param = None if readm_filter == "All" else readm_filter
    a_param = None if age_filter == "All" else age_filter
    p_param = int(p_filter.strip()) if p_filter.strip().isdigit() else None

    try:
        encounters = api.list_encounters(token, limit=50, readmitted=r_param, age=a_param, patient_nbr=p_param)
        if encounters:
            df = pd.DataFrame(encounters)
            display_cols = ["encounter_id", "patient_nbr", "age", "time_in_hospital", "num_lab_procedures", "num_medications", "readmitted"]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

            st.markdown("### 🔍 Encounter Full Inspection")
            selected_enc = st.number_input("Enter Encounter ID", min_value=1, step=1, value=int(df.iloc[0]["encounter_id"]))
            if st.button("Inspect Clinical Detail", type="primary"):
                try:
                    detail = api.get_encounter(token, selected_enc)
                    st.json(detail)
                except Exception as e:
                    st.error(f"Failed to fetch detail: {e}")
        else:
            st.info("No encounters match the active filters.")
    except Exception as e:
        st.error(f"Error fetching encounters: {e}")

# TAB 2: Log Admission
with tab2:
    if user_role not in ["Admin", "Healthcare Staff"]:
        st.warning("🔒 You have Analyst view-only permissions. Creating encounters requires Healthcare Staff or Admin role.")
    else:
        st.subheader("Log New Inpatient Hospital Encounter")
        with st.form("new_encounter_form"):
            col1, col2 = st.columns(2)
            with col1:
                enc_id = st.number_input("Encounter ID", min_value=90000000, max_value=999999999, value=99912345)
                pat_id = st.number_input("Associated Patient ID", min_value=1, step=1, value=8222157)
                enc_age = st.selectbox("Patient Age Group", ["[50-60)", "[60-70)", "[70-80)", "[80-90)"])
                adm_type = st.selectbox("Admission Type", [1, 2, 3, 6], format_func=lambda x: f"Type {x}")
                stay_len = st.slider("Time in Hospital (Days)", 1, 14, 3)
            with col2:
                labs = st.number_input("Lab Procedures Count", min_value=0, max_value=150, value=35)
                meds = st.number_input("Medications Count", min_value=0, max_value=100, value=12)
                readm_val = st.selectbox("Readmission Risk / Outcome", ["NO", "<30", ">30"])
                diag_count = st.number_input("Number of Diagnoses", min_value=1, max_value=16, value=5)

            submitted = st.form_submit_button("Record Clinical Encounter", type="primary")
            if submitted:
                payload = {
                    "encounter_id": enc_id,
                    "patient_nbr": pat_id,
                    "age": enc_age,
                    "admission_type_id": adm_type,
                    "time_in_hospital": stay_len,
                    "num_lab_procedures": labs,
                    "num_medications": meds,
                    "number_diagnoses": diag_count,
                    "readmitted": readm_val
                }
                try:
                    res = api.create_encounter(token, payload)
                    st.success(f"Encounter #{res['encounter_id']} logged successfully!")
                except Exception as e:
                    st.error(f"Creation failed: {e}")

# TAB 3: Modify Encounter
with tab3:
    if user_role not in ["Admin", "Healthcare Staff"]:
        st.warning("🔒 You have Analyst view-only permissions.")
    else:
        st.subheader("Update Existing Encounter Details")
        target_eid = st.number_input("Target Encounter ID", min_value=1, step=1, value=99912345)
        new_stay = st.slider("Updated Time in Hospital", 1, 14, 4, key="edit_stay")
        new_readm = st.selectbox("Updated Readmission Status", ["NO", "<30", ">30"], key="edit_readm")

        if st.button("Apply Encounter Updates", type="primary"):
            try:
                res = api.update_encounter(token, target_eid, {"time_in_hospital": new_stay, "readmitted": new_readm})
                st.success(f"Encounter #{target_eid} updated successfully.")
            except Exception as e:
                st.error(f"Failed to update encounter: {e}")
