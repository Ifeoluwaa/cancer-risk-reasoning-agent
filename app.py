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

    # Use tabs for a clean, non-linear clinical dashboard layout
    tab_overview, tab_drivers, tab_scenarios, tab_audit, tab_trace = st.tabs([
        "📋 Patient Overview", 
        "⚡ Clinical Risk & Drivers", 
        "🔄 Scenario & Recommendations", 
        "🔬 Skeptic & Audit Review",
        "🔍 Reasoning Trace"
    ])

    with tab_overview:
        st.subheader("📋 Patient Baseline Metrics")
        p = state.patient_profile
        if p:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Age:** {p.age}")
                st.markdown(f"**Sex:** {p.sex.capitalize()}")
                st.markdown(f"**BMI:** {p.bmi}")
            with c2:
                st.markdown(f"**Smoking Status:** {p.smoking_status.capitalize()} ({p.smoking_years} years)")
                st.markdown(f"**Alcohol Use:** {p.alcohol_use.capitalize()}")
                st.markdown(f"**Physical Activity:** {p.physical_activity.capitalize()}")
            with c3:
                st.markdown(f"**Diet Quality:** {p.diet_quality.capitalize()}")
                st.markdown(f"**Sun/UV Exposure:** {p.sun_exposure.capitalize()}")
                st.markdown(f"**Occupation:** {p.occupation}")
            
            st.divider()
            c4, c5 = st.columns(2)
            with c4:
                st.markdown(f"**Family History of Cancer:** {'Yes' if p.family_history else 'No'}")
                st.markdown(f"**Genetic Mutations:** {', '.join(p.known_mutations) if p.known_mutations else 'None'}")
            with c5:
                st.markdown(f"**Previous Cancer History:** {'Yes' if p.previous_cancer_history else 'No'}")
                st.markdown(f"**Environmental Exposures:** {', '.join(p.environmental_exposure) if p.environmental_exposure else 'None'}")
        else:
            st.info("No patient profile associated with this execution.")

    with tab_drivers:
        col_main, col_side = st.columns([2, 1])

        with col_main:
            st.subheader("🏆 Risk Drivers & Contributors")
            if state.causality_package and state.causality_package.ranked_contributors:
                for c in state.causality_package.ranked_contributors:
                    rf_match = None
                    if state.evidence_package:
                        rf_match = next((rf for rf in state.evidence_package.risk_factors if rf.factor == c.factor), None)
                    
                    f_lower = c.factor.lower()
                    is_modifiable = any(x in f_lower for x in ["tobacco", "smoke", "smoking", "alcohol", "obesity", "bmi", "diet", "activity", "inactivity", "physical", "sun", "uv", "lifestyle"])
                    mod_status = "Modifiable" if is_modifiable else "Non-Modifiable"
                    mod_color = "green" if is_modifiable else "gray"
                    
                    is_interaction = "interaction" in f_lower
                    if state.evidence_package and getattr(state.evidence_package, "interactions", None):
                        for inter in state.evidence_package.interactions:
                            if any(pf.lower() in f_lower for pf in inter.participating_factors):
                                is_interaction = True
                    
                    strength = rf_match.evidence_strength.capitalize() if rf_match else "Unknown"
                    
                    from tools.impact_tier import get_impact_color
                    tier = c.impact_tier or "Minimal"
                    bar = c.impact_bar or "██"
                    score = c.attribution_percentage or 0.0
                    color = get_impact_color(score)
                    
                    badge_mod = f":{mod_color}[{mod_status}]"
                    badge_inter = " | 🔗 :violet[Synergistic Interaction]" if is_interaction else ""
                    
                    header = f"{c.factor} — :{color}[{tier}] {bar} ({badge_mod}{badge_inter})"
                    
                    with st.expander(header):
                        st.markdown(f"**Clinical Rationale:** {c.reason}")
                        st.markdown(f"**Evidence Strength:** {strength}")
                        
                        # Group citations for this contributor
                        if report.citations:
                            factor_words = [w.lower() for w in c.factor.split() if len(w) > 3]
                            matched_cits = []
                            for cit in report.citations:
                                cit_text = f"{cit.title} {cit.source}".lower()
                                if any(w in cit_text for w in factor_words) or (("tobacco" in factor_words or "smoke" in factor_words) and "tobacco" in cit_text):
                                    matched_cits.append(cit)
                            if matched_cits:
                                st.markdown("**Supporting Literature:**")
                                for cit in matched_cits:
                                    qual_badge = f" :orange[[{cit.evidence_quality}]]" if cit.evidence_quality else ""
                                    st.markdown(f"- *{cit.title}* ({cit.source}, {cit.year}){qual_badge}")
                        
                        # Counterfactual relevance
                        if state.counterfactual_package:
                            rel_scenarios = []
                            for s in state.counterfactual_package.scenarios:
                                if any(w in s.change.lower() or w in s.reasoning.lower() for w in [w for w in c.factor.lower().split() if len(w) > 3]):
                                    rel_scenarios.append(s)
                            if rel_scenarios:
                                st.markdown("**Relevant Intervention Scenarios:**")
                                for s in rel_scenarios:
                                    st.markdown(f"- *{s.change}* (Expected Impact: {s.expected_effect.upper()})")
            else:
                st.write("No major risk factors flagged.")

            st.subheader("📄 Synthesized Evidence Narrative")
            st.write(report.evidence_summary)

        with col_side:
            st.subheader("🔬 Clinical Confidence")
            confidence_level = report.confidence
            confidence_colors = {"high": "violet", "medium": "gray", "low": "gray"}
            color = confidence_colors.get(confidence_level, "gray")
            meter = "🟣🟣🟣" if confidence_level == "high" else ("🟣🟣⚪" if confidence_level == "medium" else "🟣⚪⚪")
            st.markdown(f"### Confidence: :{color}[{confidence_level.upper()}]  \n`{meter}`")
            
            if confidence_level == "high":
                st.markdown("- ✓ Multiple independent studies retrieved  \n- ✓ Strong support in clinical guidelines  \n- ✓ Grounded patient-specific drivers  \n- ✓ No critical confounding factors")
            elif confidence_level == "medium":
                st.markdown("- ✓ Moderate evidence base  \n- ✓ Adequate grounding of lifestyle/clinical exposures  \n- ⚠ Potential self-reporting biases or incomplete parameters")
            else:
                st.markdown("- ⚠ Limited evidence scoring on primary drivers  \n- ⚠ Relies heavily on generic baseline risks  \n- ⚠ Multiple critical missing data points or unresolved confounding factors")

            st.subheader("📚 Citations & References")
            if report.citations:
                for i, cit in enumerate(report.citations, 1):
                    qual_badge = f" :orange[[{cit.evidence_quality}]]" if cit.evidence_quality else ""
                    st.markdown(f"{i}. *{cit.title}* ({cit.source}, {cit.year}){qual_badge}")
            else:
                st.write("*No academic citations included.*")

    with tab_scenarios:
        st.subheader("🔄 Counterfactual Recommendation Cards")
        if state.counterfactual_package and state.counterfactual_package.scenarios:
            for s in state.counterfactual_package.scenarios:
                f_lower = s.change.lower()
                non_modifiable_keywords = ["age", "genetics", "mutation", "brca", "family history", "previous cancer", "malignancy"]
                is_modifiable = not any(kw in f_lower for kw in non_modifiable_keywords)
                
                impact = s.expected_effect.upper()
                impact_color = "red" if impact == "HIGH" else ("orange" if impact == "MEDIUM" else "blue")
                
                priority = "High" if impact in ["HIGH", "MEDIUM"] else "Routine"
                priority_color = "red" if priority == "High" else "gray"
                
                header = f"{s.change} — Impact: :{impact_color}[{impact}]"
                with st.expander(header):
                    st.markdown(f"**Clinical Rationale:** {s.reasoning}")
                    st.markdown(f"**Intervention Priority:** :{priority_color}[{priority}]")
                    st.markdown(f"**Modifiability Status:** {'Modifiable' if is_modifiable else 'Non-modifiable'}")
        else:
            st.info("No counterfactual recommendations generated.")
            
        st.subheader("📄 Synthesized Counterfactual Narrative")
        st.write(report.counterfactual_summary)

    with tab_audit:
        st.subheader("🔬 Clinical Critique & Audit")
        
        alts = [u for u in state.skeptic_package.uncertainties if "Alternative Explanation:" in u] if state.skeptic_package else []
        confounders = [u for u in state.skeptic_package.uncertainties if "Potential Confounder:" in u] if state.skeptic_package else []
        assumptions = [u for u in state.skeptic_package.uncertainties if "Causal link assumes" in u or "assumes" in u.lower()] if state.skeptic_package else []
        limitations = state.skeptic_package.limitations if state.skeptic_package else []
        
        c1, c2 = st.columns(2)
        with c1:
            with st.expander("🔍 Alternative Explanations & Confounders", expanded=True):
                if alts:
                    st.markdown("**Alternative Explanations:**")
                    for a in alts:
                        st.markdown(f"- {a}")
                if confounders:
                    st.markdown("**Potential Confounding Factors:**")
                    for c in confounders:
                        st.markdown(f"- {c}")
                if not alts and not confounders:
                    st.write("*No alternative explanations or confounders identified.*")
                    
            with st.expander("📋 Causal Assumptions", expanded=True):
                if assumptions:
                    for a in assumptions:
                        st.markdown(f"- {a}")
                else:
                    st.write("*No explicit causal assumptions documented.*")
                    
        with c2:
            with st.expander("⚠️ Evidence Limitations", expanded=True):
                if limitations:
                    for l in limitations:
                        st.markdown(f"- {l}")
                else:
                    st.write("*No critical evidence limitations flagged.*")
                    
            with st.expander("❓ Missing Profile Parameters", expanded=True):
                if state.skeptic_package and state.skeptic_package.missing_information:
                    for mi in state.skeptic_package.missing_information:
                        st.markdown(f"- {mi}")
                else:
                    st.write("*No critical missing profile parameters.*")
                    
        st.divider()
        st.subheader("❓ Recommended Clinical Follow-up Questions")
        recommended_questions = getattr(state.skeptic_package, "recommended_questions", []) if state.skeptic_package else []
        if recommended_questions:
            for i, q in enumerate(recommended_questions, 1):
                with st.expander(f"Question {i}: {q.question}"):
                    st.markdown(f"**Why it matters (Rationale):** {q.rationale}")
                    st.markdown(f"**Expected Impact on Reasoning Confidence:** {q.impact}")
        else:
            st.write("*No recommended follow-up questions.*")

    with tab_trace:
        st.subheader("🔍 Interactive Reasoning Trace & Explainability Viewer")
        
        st.markdown("### 🚦 Workflow Execution Status")
        status_emoji = "☑" if state.status == "COMPLETED" else ("❌" if state.status == "FAILED" else "⏳")
        st.markdown(f"**Execution Status:** {status_emoji} {state.status}")
        
        stages_info = [
            ("Security & Sanitization Check", state.security_package is not None),
            ("Evidence Retrieval", state.evidence_package is not None),
            ("Evidence Ranking", state.evidence_package is not None and len(state.evidence_package.risk_factors) > 0),
            ("Interaction Detection", state.evidence_package is not None and getattr(state.evidence_package, "interactions", None) is not None),
            ("Risk Attribution", state.causality_package is not None and len(state.causality_package.ranked_contributors) > 0),
            ("Counterfactual Analysis", state.counterfactual_package is not None),
            ("Skeptic Critique & Audit", state.skeptic_package is not None),
            ("Confidence Assessment", state.final_report is not None and state.final_report.confidence is not None),
            ("Clinical Synthesis", state.final_report is not None)
        ]
        
        status_symbols = []
        for name, completed in stages_info:
            symbol = "✅" if completed else "⬜"
            status_symbols.append(f"{symbol} {name}")
        st.markdown("  \n".join(status_symbols))
        
        st.markdown("---")
        
        with st.expander("1. Security & Sanitization Check"):
            st.markdown("""
            **What this stage does:** Performs safety checks, detects prompt injections, redacts personally identifiable information (PII), and routes the request to educational or refusal pipelines.
            
            **Why it matters:** Ensures clinician/patient data safety, protects application integrity, and enforces clinical routing policies.
            """)
            if state.security_package:
                st.markdown("**Inputs Received:** Raw patient profile form inputs.")
                st.markdown("**Outputs Generated:**")
                st.json(state.security_package.model_dump())
                st.markdown(f"**Key Reasoning Decisions:** Safety status set to `{state.security_package.safety_status}`. Redacted fields: `{state.security_package.redacted_fields}`. Requests categorized as `{state.security_package.medical_request_type}`.")
            else:
                st.info("Stage was bypassed or failed.")

        with st.expander("2. Evidence Retrieval"):
            st.markdown("""
            **What this stage does:** Queries academic databases and guidelines for documents corresponding to the patient's demographics, lifestyle risk factors, and medical history.
            
            **Why it matters:** Grounding reasoning in actual clinical consensus and peer-reviewed studies prevents LLM hallucination.
            """)
            if state.evidence_package:
                st.markdown("**Inputs Received:** Sanitized patient profile.")
                st.markdown("**Outputs Generated:**")
                st.markdown(f"- **Retrieved Documents:** `{state.evidence_package.retrieved_documents}`")
                st.markdown(f"- **Academic Citations:**")
                for c in state.evidence_package.citations:
                    st.markdown(f"  * *{c.title}* ({c.source}, {c.year})")
            else:
                st.info("Stage was bypassed or failed.")

        with st.expander("3. Evidence Ranking"):
            st.markdown("""
            **What this stage does:** Scores and prioritizes retrieved risk factors based on evidence strength and occurrence count in citations.
            
            **Why it matters:** Helps separate background/incidental observations from primary, robustly backed health drivers.
            """)
            if state.evidence_package and state.evidence_package.risk_factors:
                st.markdown("**Inputs Received:** Identified risk factors.")
                st.markdown("**Outputs Generated:**")
                for rf in state.evidence_package.risk_factors:
                    st.markdown(f"- **{rf.factor}** — Strength: `{rf.evidence_strength.upper()}` (Score: `{rf.evidence_score:.2f}`, Count: `{rf.source_count}`)")
            else:
                st.info("Stage was bypassed or failed.")

        with st.expander("4. Interaction Detection"):
            st.markdown("""
            **What this stage does:** Evaluates whether there are synergistic, overlapping exposures that multiply risk non-linearly (e.g. Asbestos exposure combined with smoking).
            
            **Why it matters:** Captures complex clinical reality rather than assuming all risk factors act fully independently.
            """)
            if state.evidence_package and getattr(state.evidence_package, "interactions", None):
                st.markdown("**Inputs Received:** Patient profile and ranked risk factors.")
                st.markdown("**Outputs Generated:**")
                for inter in state.evidence_package.interactions:
                    st.markdown(f"- **{inter.name}**")
                    st.markdown(f"  * Participating factors: `{inter.participating_factors}`")
                    st.markdown(f"  * Strength: `{inter.strength}`")
                    st.markdown(f"  * Clinical Rationale: {inter.rationale}")
            else:
                st.info("No active risk interactions detected for this profile.")

        with st.expander("5. Risk Attribution"):
            st.markdown("""
            **What this stage does:** Allocates relative risk percentages and maps them to clinical impact tiers and visual block representations.
            
            **Why it matters:** Translates mathematical equations into understandable visual categories for communication.
            """)
            if state.causality_package:
                st.markdown("**Inputs Received:** Risk scores and interactions.")
                st.markdown("**Outputs Generated:**")
                for c in state.causality_package.ranked_contributors:
                    st.markdown(f"- **{c.factor}** (Rank {c.rank})")
                    st.markdown(f"  * Raw Attribution Score: `{c.attribution_percentage:.1f}%` (internal only)")
                    st.markdown(f"  * Mapped Clinical Impact: `{c.impact_tier}` (`{c.impact_bar}`)")
                    st.markdown(f"  * Classification: `{c.classification}`")
            else:
                st.info("Stage was bypassed or failed.")

        with st.expander("6. Counterfactual Scenario Analysis"):
            st.markdown("""
            **What this stage does:** Computes risk changes under hypothetical scenarios (e.g. lifestyle modifications) to identify modifiable risk targets.
            
            **Why it matters:** Clinicians need to see not just what the current risk is, but which interventions offer the greatest potential benefit.
            """)
            if state.counterfactual_package:
                st.markdown("**Inputs Received:** Top risk drivers.")
                st.markdown("**Outputs Generated:**")
                for s in state.counterfactual_package.scenarios:
                    st.markdown(f"- **{s.change}**")
                    st.markdown(f"  * Expected Impact: `{s.expected_effect.upper()}`")
                    st.markdown(f"  * Reasoning: {s.reasoning}")
            else:
                st.info("Stage was bypassed or failed.")

        with st.expander("7. Skeptic Critique & Audit"):
            st.markdown("""
            **What this stage does:** Runs a critical review on assumptions, potential confounders, alternative explanations, and evidence limitations.
            
            **Why it matters:** Prevents confirmation bias, highlights diagnostic limitations, and lists what crucial data might be missing.
            """)
            if state.skeptic_package:
                st.markdown("**Inputs Received:** Evidence, causality, and counterfactual packages.")
                st.markdown("**Outputs Generated:**")
                st.markdown("**Uncertainties & Alternative Explanations:**")
                for u in state.skeptic_package.uncertainties:
                    st.markdown(f"- {u}")
                st.markdown("**Limitations:**")
                for l in state.skeptic_package.limitations:
                    st.markdown(f"- {l}")
                st.markdown("**Missing Information:**")
                for m in state.skeptic_package.missing_information:
                    st.markdown(f"- {m}")
            else:
                st.info("Stage was bypassed or failed.")

        with st.expander("8. Confidence Assessment"):
            st.markdown("""
            **What this stage does:** Rates overall certainty in the findings based on evidence grading (RCTs, reviews, guidelines) and unresolved skeptic audits.
            
            **Why it matters:** Clinicians must know how solid the underlying literature is before acting on advice.
            """)
            if state.final_report:
                st.markdown("**Inputs Received:** Citation grading levels and skeptic report.")
                st.markdown(f"**Outputs Generated:** Confidence rating: `{state.final_report.confidence.upper()}`")
            else:
                st.info("Stage was bypassed or failed.")

        with st.expander("9. Clinical Synthesis"):
            st.markdown("""
            **What this stage does:** Translates all packages into patient-centered narratives, structuring information for readability.
            
            **Why it matters:** Converts multi-agent logs into clear clinical summaries for direct presentation.
            """)
            if state.final_report:
                st.markdown("**Inputs Received:** Aggregated agent packages.")
                st.markdown("**Outputs Generated:** Final Synthesized Report (visible on main tabs).")
            else:
                st.info("Stage was bypassed or failed.")

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
