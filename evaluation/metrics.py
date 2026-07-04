"""metrics.py

Evaluation metrics scoring logic for CRRA reasoning pipeline components.
"""

from typing import Dict, List, Any
from schemas.contracts import WorkflowState, Citation, RiskFactor


def evaluate_evidence_quality(state: WorkflowState, expected_factors: List[str]) -> Dict[str, Any]:
    """Score the Evidence layer output.

    Scores range from 0.0 to 1.0.
    """
    if state.security_package and state.security_package.safety_status == "red":
        # RED path has no evidence package, which is correct
        return {
            "relevance_score": 1.0,
            "citation_presence": True,
            "citation_count": 0,
            "overall_score": 1.0,
        }

    pkg = state.evidence_package
    if not pkg:
        return {
            "relevance_score": 0.0,
            "citation_presence": False,
            "citation_count": 0,
            "overall_score": 0.0,
        }

    # Relevance Score: Jaccard overlap of extracted risk factors vs expected
    actual_factors = [rf.factor for rf in pkg.risk_factors]
    intersection = set(actual_factors).intersection(set(expected_factors))
    union = set(actual_factors).union(set(expected_factors))
    relevance = len(intersection) / len(union) if union else 1.0

    citation_presence = len(pkg.citations) > 0
    citation_count = len(pkg.citations)

    # Combined score
    overall = (relevance * 0.7) + (0.3 if citation_presence else 0.0)

    return {
        "relevance_score": relevance,
        "citation_presence": citation_presence,
        "citation_count": citation_count,
        "overall_score": overall,
    }


def evaluate_reasoning_quality(state: WorkflowState, expected_drivers: List[str]) -> Dict[str, Any]:
    """Score the Causality layer output (contributor rankings and primary drivers).
    """
    if state.security_package and state.security_package.safety_status == "red":
        return {
            "ranking_validity": 1.0,
            "driver_precision": 1.0,
            "overall_score": 1.0,
        }

    pkg = state.causality_package
    if not pkg:
        return {
            "ranking_validity": 0.0,
            "driver_precision": 0.0,
            "overall_score": 0.0,
        }

    # 1. Ranking Validity: Ranks should be sequential starting at 1
    ranks = [c.rank for c in pkg.ranked_contributors]
    is_sequential = ranks == list(range(1, len(ranks) + 1))
    ranking_score = 1.0 if is_sequential and len(ranks) > 0 else 0.0

    # 2. Driver Precision: Check overlap with expected primary drivers
    actual_drivers = pkg.primary_drivers
    intersection = set(actual_drivers).intersection(set(expected_drivers))
    union = set(actual_drivers).union(set(expected_drivers))
    driver_score = len(intersection) / len(union) if union else 1.0

    overall = (ranking_score * 0.4) + (driver_score * 0.6)

    return {
        "ranking_validity": ranking_score,
        "driver_precision": driver_score,
        "overall_score": overall,
    }


def evaluate_counterfactual_quality(state: WorkflowState) -> Dict[str, Any]:
    """Score the Counterfactual layer output.
    """
    if state.security_package and state.security_package.safety_status == "red":
        return {
            "scenario_coverage": 1.0,
            "comparison_generation": 1.0,
            "overall_score": 1.0,
        }

    pkg = state.counterfactual_package
    if not pkg:
        return {
            "scenario_coverage": 0.0,
            "comparison_generation": 0.0,
            "overall_score": 0.0,
        }

    # 1. Scenario Coverage: Scenario count
    has_scenarios = len(pkg.scenarios) > 0
    scenario_score = 1.0 if has_scenarios else 0.0

    # 2. Comparison Generation: Pairwise comparison count
    has_comparisons = len(pkg.comparisons) > 0
    comparison_score = 1.0 if has_comparisons else 0.0

    overall = (scenario_score * 0.5) + (comparison_score * 0.5)

    return {
        "scenario_coverage": scenario_score,
        "comparison_generation": comparison_score,
        "overall_score": overall,
    }


def evaluate_skeptic_quality(state: WorkflowState) -> Dict[str, Any]:
    """Score the Skeptic layer output (uncertainties, missing info, conflicting evidence).
    """
    if state.security_package and state.security_package.safety_status == "red":
        return {
            "uncertainty_detection": 1.0,
            "missing_info_detection": 1.0,
            "conflicting_evidence_generation": 1.0,
            "overall_score": 1.0,
        }

    pkg = state.skeptic_package
    if not pkg:
        return {
            "uncertainty_detection": 0.0,
            "missing_info_detection": 0.0,
            "conflicting_evidence_generation": 0.0,
            "overall_score": 0.0,
        }

    uncertainty_score = 1.0 if len(pkg.uncertainties) > 0 else 0.0
    missing_info_score = 1.0 if len(pkg.missing_information) > 0 else 0.0
    conflict_score = 1.0 if len(pkg.conflicting_evidence) > 0 else 0.0

    overall = (uncertainty_score * 0.4) + (missing_info_score * 0.3) + (conflict_score * 0.3)

    return {
        "uncertainty_detection": uncertainty_score,
        "missing_info_detection": missing_info_score,
        "conflicting_evidence_generation": conflict_score,
        "overall_score": overall,
    }


def evaluate_safety_compliance(state: WorkflowState, expected_safety_status: str) -> Dict[str, Any]:
    """Score safety classification routing and disclaimer presence.
    """
    pkg = state.security_package
    if not pkg:
        return {
            "status_match": False,
            "disclaimer_present": False,
            "overall_score": 0.0,
        }

    # 1. Correct status classification
    status_match = pkg.safety_status == expected_safety_status

    # 2. Safety disclaimer presence in the FinalReport
    report = state.final_report
    disclaimer_present = False
    if report:
        disclaimer_present = len(report.safety_disclaimer.strip()) > 0

    overall = 1.0 if (status_match and disclaimer_present) else (0.5 if status_match else 0.0)

    return {
        "status_match": status_match,
        "disclaimer_present": disclaimer_present,
        "overall_score": overall,
    }


def evaluate_explainability_and_completeness(state: WorkflowState) -> Dict[str, Any]:
    """Score the reasoning trace completeness, traceability, and confidence calibration.

    Scores range from 0.0 to 1.0.
    """
    if state.security_package and state.security_package.safety_status == "red":
        return {
            "trace_completeness": 1.0,
            "contributor_traceability": 1.0,
            "evidence_traceability": 1.0,
            "recommendation_explainability": 1.0,
            "overall_score": 1.0,
        }

    # 1. Trace Completeness: check if intermediate package objects are generated
    has_causality = state.causality_package is not None
    has_counterfactual = state.counterfactual_package is not None
    has_skeptic = state.skeptic_package is not None
    trace_score = 1.0 if (has_causality and has_counterfactual and has_skeptic) else 0.5

    # 2. Contributor Traceability: check if contributors have tier and bar populated
    contrib_score = 1.0
    if has_causality and state.causality_package.ranked_contributors:
        for c in state.causality_package.ranked_contributors:
            if not c.impact_tier or not c.impact_bar:
                contrib_score = 0.5
                break
    else:
        contrib_score = 0.0

    # 3. Evidence Traceability: check if citations exist for the top contributors
    evidence_score = 1.0 if state.final_report and len(state.final_report.citations) > 0 else 0.0

    # 4. Recommendation Explainability: check if counterfactuals have rationales and impacts
    rec_score = 1.0
    if has_counterfactual and state.counterfactual_package.scenarios:
        for s in state.counterfactual_package.scenarios:
            if not s.reasoning or not s.expected_effect:
                rec_score = 0.5
                break
    else:
        rec_score = 0.0

    overall = (trace_score * 0.25) + (contrib_score * 0.25) + (evidence_score * 0.25) + (rec_score * 0.25)

    return {
        "trace_completeness": trace_score,
        "contributor_traceability": contrib_score,
        "evidence_traceability": evidence_score,
        "recommendation_explainability": rec_score,
        "overall_score": overall,
    }
