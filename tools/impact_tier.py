"""tools/impact_tier.py

Clinical Impact Tier Engine helper functions.
"""

def classify_impact_tier(score: float) -> str:
    """Classifies a raw risk attribution score into a clinical impact tier.

    Args:
        score: The raw risk attribution score (usually a percentage 0.0 - 100.0).

    Returns:
        A string representation of the clinical impact tier: Very High, High, Moderate, Low, or Minimal.
    """
    if score >= 30.0:
        return "Very High"
    elif score >= 18.0:
        return "High"
    elif score >= 10.0:
        return "Moderate"
    elif score >= 5.0:
        return "Low"
    else:
        return "Minimal"


def generate_visual_bar(score: float) -> str:
    """Generates a visual bar representation based on the impact score.

    Args:
        score: The raw risk attribution score.

    Returns:
        A string of block characters representing the impact.
    """
    # Map score ranges to block lengths (similar to tier thresholds)
    # Very High (>=30%): 10 blocks
    # High (18% - 30%): 8 blocks
    # Moderate (10% - 18%): 6 blocks
    # Low (5% - 10%): 4 blocks
    # Minimal (<5%): 2 blocks
    if score >= 30.0:
        return "██████████"
    elif score >= 18.0:
        return "████████"
    elif score >= 10.0:
        return "██████"
    elif score >= 5.0:
        return "████"
    else:
        return "██"


def get_impact_color(score: float) -> str:
    """Gets a color representing the clinical impact tier, suitable for UI rendering.

    Args:
        score: The raw risk attribution score.

    Returns:
        A color name or string identifier.
    """
    if score >= 30.0:
        return "red"
    elif score >= 18.0:
        return "orange"
    elif score >= 10.0:
        return "yellow"
    elif score >= 5.0:
        return "blue"
    else:
        return "green"
