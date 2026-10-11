"""
Patient Management Workspace
Provides Search, Patient Profiles, Full Encounter History, and CRUD updates.
"""

import streamlit as st
import pandas as pd
from frontend.services.api_client import APIClient

st.set_page_config(page_title="Patient Management", page_icon="👤", layout="wide")

try:
    with open("frontend/assets/style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

api = APIClient()

if "token" not in st.session_state or not st.session_state.token:
    st.warning("⚠️ Please sign in through the main Dashboard page to access Patient Management.")
    st.stop()

token = st.session_state.token
user_role = st.session_state.user.get("role", "")

st.markdown(
    """
    <div class="main-header">
        <h1>👤 Patient Registry & Clinical History</h1>
        <p>Search Master Patient Records, Review Inpatient Admissions, and Manage Demographics</p>
    </div>
    """,
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs(["🔍 Patient Directory & Search", "➕ Register New Patient", "📝 Edit Patient Record"])

# TAB 1: Search & History
with tab1:
    col_search, col_gender, col_race = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("Search Patient ID", placeholder="e.g. 8222157")
    with col_gender:
        gender_filter = st.selectbox("Filter Gender", ["All", "Male", "Female"])
    with col_race:
        race_filter = st.selectbox("Filter Race", ["All", "Caucasian", "AfricanAmerican", "Hispanic", "Asian", "Other"])

    gender_param = None if gender_filter == "All" else gender_filter
    race_param = None if race_filter == "All" else race_filter
    search_param = search_query.strip() if search_query.strip() else None

    try:
        patients = api.list_patients(token, limit=50, gender=gender_param, race=race_param, search=search_param)
        if patients:
            df = pd.DataFrame(patients)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("### 📋 View Patient Encounter History")
            selected_patient_id = st.number_input("Enter Patient ID to view clinical timeline", min_value=1, step=1, value=int(df.iloc[0]["patient_nbr"]))
            if st.button("Fetch Clinical Timeline", type="primary"):
                try:
                    history = api.get_patient_encounters(token, selected_patient_id)
                    if history:
                        st.success(f"Found {len(history)} hospital encounter(s) for Patient #{selected_patient_id}:")
                        for enc in history:
                            with st.expander(f"Encounter #{enc['encounter_id']} — Stay: {enc['time_in_hospital']} days | Readmission: {enc['readmitted']}"):
                                c1, c2, c3 = st.columns(3)
                                c1.write(f"**Age Group:** {enc.get('age')}")
                                c1.write(f"**Admission Type:** {enc.get('admission_type', 'N/A')}")
                                c2.write(f"**Lab Procedures:** {enc.get('num_lab_procedures')}")
                                c2.write(f"**Medications Administered:** {enc.get('num_medications')}")
                                c3.write(f"**Payer Code:** {enc.get('payer_code')}")
                                c3.write(f"**Medical Specialty:** {enc.get('medical_specialty')}")

                                # Show Diagnoses & Meds
                                diags = enc.get("diagnoses", [])
                                if diags:
                                    st.write("**Primary Diagnoses (ICD-9 Codes):** " + ", ".join([f"Pos {d['diagnosis_position']}: {d['diagnosis_code']}" for d in diags]))
                                meds = enc.get("medications", [])
                                if meds:
                                    st.write("**Medications:** " + ", ".join([f"{m['medication']} ({m['medication_status']})" for m in meds]))
                    else:
                        st.info("No prior encounter records found for this patient.")
                except Exception as e:
                    st.error(f"Error retrieving timeline: {e}")
        else:
            st.info("No patients matching your search criteria.")
    except Exception as e:
        st.error(f"Failed to fetch patient records: {e}")

# TAB 2: Register Patient
with tab2:
    if user_role not in ["Admin", "Healthcare Staff"]:
        st.warning("🔒 You have Analyst view-only permissions. Patient creation requires Healthcare Staff or Admin role.")
    else:
        st.subheader("Register New Patient in Master Index")
        with st.form("create_patient_form"):
            new_id = st.number_input("Patient Master ID", min_value=100000, max_value=999999999, value=88812345)
            new_race = st.selectbox("Race", ["Caucasian", "AfricanAmerican", "Hispanic", "Asian", "Other"])
            new_gender = st.selectbox("Gender", ["Male", "Female"])
            
            submitted = st.form_submit_button("Save Patient Record", type="primary")
            if submitted:
                try:
                    payload = {"patient_nbr": new_id, "race": new_race, "gender": new_gender}
                    res = api.create_patient(token, payload)
                    st.success(f"Successfully registered Patient #{res['patient_nbr']}!")
                except Exception as e:
                    st.error(f"Failed to create patient: {e}")

# TAB 3: Edit / Delete Patient
with tab3:
    if user_role not in ["Admin", "Healthcare Staff"]:
        st.warning("🔒 You have Analyst view-only permissions. Modifications require Healthcare Staff or Admin role.")
    else:
        st.subheader("Modify Demographics or Remove Record")
        update_id = st.number_input("Target Patient ID", min_value=1, step=1, value=88812345)
        edit_race = st.selectbox("Updated Race", ["Caucasian", "AfricanAmerican", "Hispanic", "Asian", "Other"], key="edit_race")
        edit_gender = st.selectbox("Updated Gender", ["Male", "Female"], key="edit_gender")

        col_up, col_del = st.columns(2)
        with col_up:
            if st.button("Update Demographics", type="primary", use_container_width=True):
                try:
                    res = api.update_patient(token, update_id, {"race": edit_race, "gender": edit_gender})
                    st.success(f"Updated Patient #{update_id} successfully.")
                except Exception as e:
                    st.error(f"Update failed: {e}")

        with col_del:
            if user_role == "Admin":
                if st.button("Delete Patient Record", type="secondary", use_container_width=True):
                    try:
                        res = api.delete_patient(token, update_id)
                        st.success(res.get("message", "Deleted successfully"))
                    except Exception as e:
                        st.error(f"Deletion failed: {e}")
            else:
                st.caption("*(Deletion requires Administrator role)*")
