"""Streamlit Web Interface for the Cancer Risk Reasoning Agent (CRRA).

Presents patient demographics and lifestyle risk forms, routes requests
through the multi-agent reasoning chain, and displays clinical summaries,
evidence citations, and safety warnings.
"""

import streamlit as st
import uuid
from typing import Dict, Any

from schemas.contracts import PatientProfile, WorkflowState
from agents.orchestrator_agent import OrchestratorAgent
from evaluation.observability import setup_observability

# Initialize observability logs/traces automatically
setup_observability()


def map_form_to_profile(inputs: Dict[str, Any]) -> PatientProfile:
    """Helper function to map web UI form inputs to a PatientProfile contract.

    Args:
        inputs: Dictionary of raw inputs from Streamlit form controls.

    Returns:
        A validated PatientProfile schema instance.
    """
    # Parse environmental exposure
    env_str = inputs.get("environmental_exposure", "")
    env_list = [
        item.strip() for item in env_str.split(",") if item.strip()
    ]

    # Parse genetic mutations
    mut_str = inputs.get("known_mutations", "")
    mut_list = [
        item.strip() for item in mut_str.split(",") if item.strip()
    ]

    # Generate session ID if blank
    sess_id = inputs.get("session_id")
    if not sess_id or not sess_id.strip():
        sess_id = f"ui_{uuid.uuid4().hex[:8]}"

    return PatientProfile(
        session_id=sess_id.strip(),
        age=int(inputs.get("age", 45)),
        sex=inputs.get("sex", "male"),
        bmi=float(inputs.get("bmi", 24.5)),
        smoking_status=inputs.get("smoking_status", "never"),
        smoking_years=int(inputs.get("smoking_years", 0)),
        alcohol_use=inputs.get("alcohol_use", "none"),
        physical_activity=inputs.get("physical_activity", "medium"),
        diet_quality=inputs.get("diet_quality", "medium"),
        sun_exposure=inputs.get("sun_exposure", "low"),
        occupation=inputs.get("occupation", "Office worker"),
        environmental_exposure=env_list,
        family_history=bool(inputs.get("family_history", False)),
        known_mutations=mut_list,
        previous_cancer_history=bool(inputs.get("previous_cancer_history", False)),
    )


def execute_pipeline(profile: PatientProfile) -> WorkflowState:
    """Executes the orchestrator multi-agent graph with the patient profile.

    Args:
        profile: The PatientProfile input.

    Returns:
        The resulting WorkflowState containing execution details and reports.
    """
    orchestrator = OrchestratorAgent()
    return orchestrator.run(profile)


def render_report(state: WorkflowState) -> None:
    """Renders the synthesis agent's FinalReport using Streamlit widgets.

    Args:
        state: The completed WorkflowState.
    """
    report = state.final_report
    if not report:
        st.warning("No synthesis report found in the completed workflow state.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🏆 Top Risk Contributors")
        if report.top_contributors:
            for factor in report.top_contributors:
                st.markdown(f"- **{factor}**")
        else:
            st.write("No major risk factors flagged.")

        st.subheader("📄 Evidence Summary")
        st.write(report.evidence_summary)

        st.subheader("🔄 Counterfactual Scenario Analysis")
        st.write(report.counterfactual_summary)

    with col2:
        confidence_colors = {
            "high": "green",
            "medium": "orange",
            "low": "red"
        }
        color = confidence_colors.get(report.confidence, "blue")
        st.markdown(f"**Confidence Level:** :{color}[{report.confidence.upper()}]")

        st.subheader("📚 Citations & References")
        if report.citations:
            for i, cit in enumerate(report.citations, 1):
                st.markdown(f"{i}. *{cit.title}* ({cit.source}, {cit.year})")
        else:
            st.write("*No academic citations included.*")

        st.subheader("🔬 Clinical Limitations")
        if report.limitations:
            for lim in report.limitations:
                st.markdown(f"- {lim}")
        else:
            st.write("*No limitations documented.*")

    st.divider()
    st.info(f"**Safety Disclaimer:** {report.safety_disclaimer}")


def main() -> None:
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title="Cancer Risk Reasoning Agent",
        page_icon="🧬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🧬 Cancer Risk Reasoning Agent (CRRA)")
    st.markdown(
        "This interactive clinical assistant evaluates patient cancer risk factors "
        "using a multi-agent reasoning graph. All execution runs are traced and logged "
        "automatically for audit."
    )

    st.sidebar.header("📋 Patient Demographics & Profile")

    # Patient Inputs Form
    session_id = st.sidebar.text_input("Session ID (blank for auto-gen)", "")
    age = st.sidebar.slider("Age", min_value=0, max_value=120, value=45)
    sex = st.sidebar.selectbox("Sex", options=["male", "female", "other"])
    bmi = st.sidebar.number_input("BMI", min_value=10.0, max_value=60.0, value=24.5, step=0.1)

    st.sidebar.subheader("🚬 Lifestyle Risks")
    smoking_status = st.sidebar.selectbox(
        "Smoking Status", options=["never", "former", "active"]
    )
    smoking_years = st.sidebar.slider("Smoking Years", min_value=0, max_value=100, value=0)
    alcohol_use = st.sidebar.selectbox(
        "Alcohol Use", options=["none", "light", "moderate", "heavy"]
    )
    physical_activity = st.sidebar.selectbox(
        "Physical Activity", options=["low", "medium", "high"]
    )
    diet_quality = st.sidebar.selectbox(
        "Diet Quality", options=["low", "medium", "high"]
    )
    sun_exposure = st.sidebar.selectbox(
        "Sun/UV Exposure", options=["low", "medium", "high"]
    )

    st.sidebar.subheader("🏥 History & Environment")
    occupation = st.sidebar.text_input("Occupation", "Office worker")
    environmental_exposure = st.sidebar.text_input(
        "Environmental Carcinogens (comma-separated, e.g., asbestos, radon)", ""
    )
    known_mutations = st.sidebar.text_input(
        "Known Genetic Mutations (comma-separated, e.g., BRCA1, BRCA2)", ""
    )

    family_history = st.sidebar.checkbox("Family History of Cancer")
    previous_cancer_history = st.sidebar.checkbox("Personal History of Cancer")

    # Run button
    if st.sidebar.button("Run Reasoning Pipeline", type="primary"):
        inputs = {
            "session_id": session_id,
            "age": age,
            "sex": sex,
            "bmi": bmi,
            "smoking_status": smoking_status,
            "smoking_years": smoking_years,
            "alcohol_use": alcohol_use,
            "physical_activity": physical_activity,
            "diet_quality": diet_quality,
            "sun_exposure": sun_exposure,
            "occupation": occupation,
            "environmental_exposure": environmental_exposure,
            "known_mutations": known_mutations,
            "family_history": family_history,
            "previous_cancer_history": previous_cancer_history,
        }

        # 1. Map UI fields to contract schema
        profile = map_form_to_profile(inputs)

        st.info(f"Initiating pipeline for session `{profile.session_id}`...")

        # 2. Run multi-agent orchestrator
        with st.spinner("Processing clinical reasoning layers..."):
            state = execute_pipeline(profile)

        # 3. Handle errors
        if state.status == "FAILED" or state.errors:
            # Check if it was a yellow route warning or a hard error
            safety_status = state.security_package.safety_status if state.security_package else "unknown"
            if safety_status != "yellow":
                st.error(f"Reasoning workflow aborted: {', '.join(state.errors)}")
                return

        # 4. Check Safety Status
        safety_status = "green"
        if state.security_package:
            safety_status = state.security_package.safety_status

        if safety_status == "red":
            st.error("🚨 **RED Warning: Clinical Safety Route Triggered**")
            st.warning(
                "This request has been blocked because it violates system guidelines or contains potential prompt injections. "
                "The synthesis and counterfactual modules have been bypassed."
            )
            # Render refusal report
            if state.final_report:
                st.info(state.final_report.safety_disclaimer)
        elif safety_status == "yellow":
            st.warning("⚠️ **YELLOW Alert: Educational Context Warning**")
            for err in state.errors:
                if "WARNING:" in err:
                    st.caption(err)
            render_report(state)
        else:
            st.success("🟢 **GREEN: Request Safe and Cleared**")
            render_report(state)


if __name__ == "__main__":
    main()
