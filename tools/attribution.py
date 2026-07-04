from typing import List, Optional
from schemas.contracts import PatientProfile, EvidencePackage, Contributor


def calculate_attribution(profile: PatientProfile, evidence: EvidencePackage) -> List[Contributor]:
    """Estimates relative attribution percentage and classification for each contributor.

    Args:
        profile: The PatientProfile containing patient demographics, lifestyle, and history.
        evidence: The EvidencePackage containing identified risk factors and active interactions.

    Returns:
        A list of Contributor objects sorted by attribution percentage in descending order.
    """
    raw_scores = {}
    
    # 1. Base scores for each factor
    for rf in evidence.risk_factors:
        raw_scores[rf.factor] = rf.evidence_score
        
    # Apply hereditary/lifestyle weighting
    for factor in raw_scores:
        is_hereditary = any(x in factor.lower() for x in ["genetic", "mutation", "brca", "family"])
        is_lifestyle = any(x in factor.lower() for x in ["tobacco", "smoke", "alcohol", "obesity", "bmi", "diet", "activity", "inactivity"])
        
        weight = 1.0
        if is_hereditary:
            weight = 1.25
        elif is_lifestyle:
            weight = 1.0
        else:
            weight = 0.75
            
        raw_scores[factor] *= weight

    # 2. Interaction allocation
    interactions = getattr(evidence, "interactions", [])
    allocated_interactions = {}
    
    for inter in interactions:
        if "asbestos" in inter.name.lower():
            name = "Tobacco Smoke × Asbestos Interaction"
        elif "alcohol" in inter.name.lower():
            name = "Alcohol × Tobacco Interaction"
        elif "brca" in inter.name.lower():
            name = "BRCA Mutation × Family History Interaction"
        elif "inactivity" in inter.name.lower():
            name = "Obesity × Physical Inactivity Interaction"
        elif "diet" in inter.name.lower():
            name = "Poor Diet × Obesity Interaction"
        else:
            name = f"{inter.name} Interaction"
            
        part_factors = [f for f in raw_scores if any(pf.lower() in f.lower() for pf in inter.participating_factors)]
        if part_factors:
            combined_part_score = sum(raw_scores[f] for f in part_factors)
            inter_raw = combined_part_score * 0.35
            allocated_interactions[name] = inter_raw
            
            # Subtract overlap from participating factors
            for f in part_factors:
                raw_scores[f] = max(raw_scores[f] - (raw_scores[f] * 0.15), 0.10)
                
    # Combine factors and interactions
    all_raw = {}
    for f, val in raw_scores.items():
        all_raw[f] = val
    for name, val in allocated_interactions.items():
        all_raw[name] = val
        
    # Normalize to sum to approximately 100%
    total_raw = sum(all_raw.values())
    if total_raw == 0:
        total_raw = 1.0
        
    normalized = {}
    for f, val in all_raw.items():
        normalized[f] = (val / total_raw) * 100.0
        
    # Build Contributor objects
    contributors = []
    sorted_items = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    
    for i, (name, pct) in enumerate(sorted_items):
        rank = i + 1
        
        # Classification
        if "baseline" in name.lower() or "general environmental" in name.lower():
            classification = "Background Risk"
        elif pct >= 30.0:
            classification = "Primary Driver"
        elif pct >= 18.0:
            classification = "Major Contributor"
        elif pct >= 10.0:
            classification = "Moderate Contributor"
        else:
            classification = "Minor Contributor"
            
        factor_words = [w.lower() for w in name.split() if len(w) > 3]
        matched_quals = []
        for c in evidence.citations:
            cit_text = f"{c.title} {c.source}".lower()
            if any(w in cit_text for w in factor_words) or (("tobacco" in factor_words or "smoke" in factor_words) and "tobacco" in cit_text):
                if c.evidence_quality:
                    matched_quals.append(c.evidence_quality)
        
        quality_str = ""
        if matched_quals:
            unique_quals = sorted(list(set(matched_quals)))
            quality_str = f" Supported by {', '.join(unique_quals)}."

        reason = f"Contributes {pct:.1f}% to overall risk profile. Classified as {classification}.{quality_str}"
        if "interaction" in name.lower():
            reason += " Represents synergistic co-exposure magnification effect."
            
        rf_match = next((rf for rf in evidence.risk_factors if rf.factor == name), None)
        if rf_match and profile:
            factor_lower = name.lower()
            if "smoke" in factor_lower or "tobacco" in factor_lower:
                reason += f" Matches patient history of smoking {profile.smoking_years} years."
            elif "age" in factor_lower:
                reason += f" Matches patient age of {profile.age} years (increases susceptibility)."
            elif "genetic" in factor_lower or "familial" in factor_lower:
                mutations_str = ", ".join(profile.known_mutations) if profile.known_mutations else "none detected"
                reason += f" Matches family history of cancer with mutations: {mutations_str}."
            elif "sun" in factor_lower or "uv" in factor_lower:
                reason += f" Matches history of high sun exposure ({profile.sun_exposure})."
            elif "alcohol" in factor_lower:
                reason += f" Matches alcohol consumption level of {profile.alcohol_use}."
                
        from tools.impact_tier import classify_impact_tier, generate_visual_bar
        contributors.append(
            Contributor(
                factor=name,
                rank=rank,
                reason=reason,
                attribution_percentage=pct,
                classification=classification,
                impact_tier=classify_impact_tier(pct),
                impact_bar=generate_visual_bar(pct)
            )
        )
        
    return contributors
