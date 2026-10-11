import streamlit as st
import pandas as pd
import plotly.express as px


NAVY = "#17324D"
TEAL = "#168B83"
BLUE = "#4C78A8"
ORANGE = "#F2A541"
RED = "#D9534F"


def render_dashboard(
    overview,
    admissions,
    readmissions,
    length_of_stay
):
    st.title("Healthcare Intelligence")
    st.caption(
        "Operational overview | Patient activity "
        "| Admissions | Readmission analytics"
    )

    st.divider()

    # KPI CARDS
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Patients",
        f"{overview['total_patients']:,}"
    )

    c2.metric(
        "Total Encounters",
        f"{overview['total_encounters']:,}"
    )

    c3.metric(
        "Average Stay",
        f"{overview['average_length_of_stay']:.1f} days"
    )

    c4.metric(
        "Readmission Rate",
        f"{overview['readmission_rate_percent']:.2f}%"
    )

    st.divider()

    # PREPARE DATA
    admission_data = admissions["admission_analytics"]
    readmission_data = readmissions["status_breakdown"]
    stay_data = length_of_stay["length_of_stay_analytics"]

    admission_df = pd.DataFrame(admission_data)
    readmission_df = pd.DataFrame(readmission_data)
    stay_df = pd.DataFrame(stay_data)

    # ADMISSION ANALYSIS
    st.subheader("Admission Analysis")

    left, right = st.columns(2)

    with left:
        fig = px.bar(
            admission_df.sort_values(
                "total_encounters",
                ascending=True
            ),
            x="total_encounters",
            y="admission_type",
            orientation="h",
            text="total_encounters",
            color="total_encounters",
            color_continuous_scale=[
                "#D9F0ED",
                TEAL
            ],
            labels={
                "total_encounters": "Encounters",
                "admission_type": "Admission Type"
            },
            title="Encounter Volume by Admission Type"
        )

        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_title=None,
            xaxis_title="Total Encounters",
            margin=dict(l=10, r=10, t=55, b=10),
            height=420
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:
        fig = px.bar(
            admission_df.sort_values(
                "average_length_of_stay",
                ascending=True
            ),
            x="average_length_of_stay",
            y="admission_type",
            orientation="h",
            text="average_length_of_stay",
            color="average_length_of_stay",
            color_continuous_scale=[
                "#D9E8F5",
                BLUE
            ],
            labels={
                "average_length_of_stay": "Average Days",
                "admission_type": "Admission Type"
            },
            title="Average Stay by Admission Type"
        )

        fig.update_traces(
            texttemplate="%{x:.2f} days",
            textposition="outside"
        )

        fig.update_layout(
            coloraxis_showscale=False,
            yaxis_title=None,
            xaxis_title="Average Length of Stay (Days)",
            margin=dict(l=10, r=30, t=55, b=10),
            height=420
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # READMISSION ANALYSIS
    st.subheader("Readmission Analysis")

    left, right = st.columns([1, 1])

    with left:
        fig = px.pie(
            readmission_df,
            names="readmission_status",
            values="total_encounters",
            hole=0.62,
            color="readmission_status",
            color_discrete_map={
                "<30": RED,
                ">30": ORANGE,
                "NO": TEAL
            },
            title="Readmission Status Distribution"
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate=(
                "%{label}<br>"
                "Encounters: %{value:,}<br>"
                "Share: %{percent}"
                "<extra></extra>"
            )
        )

        fig.update_layout(
            margin=dict(l=10, r=10, t=55, b=10),
            height=380,
            showlegend=False
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:
        st.markdown("#### Readmission Summary")

        st.metric(
            "Readmitted Encounters",
            f"{readmissions['readmitted_encounters']:,}"
        )

        st.metric(
            "Known Status Encounters",
            f"{readmissions['known_status_encounters']:,}"
        )

        st.metric(
            "Readmission Rate",
            f"{readmissions['readmission_rate_percent']:.2f}%"
        )

        st.info(
            "The rate combines encounters labelled '<30' "
            "and '>30', divided by encounters with known "
            "readmission status. It is an encounter-level "
            "dataset metric, not a clinically validated "
            "patient-level readmission rate."
        )

    st.divider()

    # LENGTH-OF-STAY ANALYSIS
    st.subheader("Length-of-Stay Analysis")

    fig = px.bar(
        stay_df,
        x="stay_category",
        y="total_encounters",
        text="total_encounters",
        color="total_encounters",
        color_continuous_scale=[
            "#D9F0ED",
            TEAL
        ],
        labels={
            "stay_category": "Length of Stay",
            "total_encounters": "Encounters"
        },
        title="Encounter Distribution by Stay Duration"
    )

    fig.update_traces(
        texttemplate="%{y:,}",
        textposition="outside"
    )

    fig.update_layout(
        coloraxis_showscale=False,
        xaxis_title="Stay Duration",
        yaxis_title="Total Encounters",
        margin=dict(l=10, r=20, t=55, b=10),
        height=400
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # DATA TABLES
    with st.expander("Explore the underlying analytics data"):
        st.markdown("**Admission Analytics**")
        st.dataframe(
            admission_df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("**Readmission Breakdown**")
        st.dataframe(
            readmission_df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("**Length-of-Stay Breakdown**")
        st.dataframe(
            stay_df,
            use_container_width=True,
            hide_index=True
        )