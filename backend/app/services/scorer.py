"""Signal scoring algorithm for Ableton projects."""

from typing import List, Optional
from dataclasses import dataclass

from app.config import settings


@dataclass
class ScoringFactors:
    """Factors used in signal score calculation."""
    diamond_keywords: List[str]
    gold_keywords: List[str]
    time_spent_days: Optional[int]
    backup_count: int
    cluster_size: int  # Number of versions in the cluster


def calculate_signal_score(factors: ScoringFactors) -> int:
    """
    Calculate the signal score (0-100) for an Ableton project.
    
    The score is based on multiple factors:
    - Diamond tier keywords: High-value indicators like RENDER, FINAL, BANGER
    - Gold tier keywords: Medium-value indicators like FIRE, GOOD DRUMS
    - Time spent: Days of work based on backup folder analysis
    - Backup count: Number of backup files (more = more work invested)
    - Version count: Number of versions in the cluster
    
    Args:
        factors: ScoringFactors with all relevant metrics
        
    Returns:
        Integer score from 0 to 100
    """
    score = settings.base_score  # Start with base score (20)
    
    # Diamond tier keywords (+30 each, but we take max of one)
    if factors.diamond_keywords:
        score += settings.diamond_weight
    
    # Gold tier keywords (+15 each, but we take max of one)
    if factors.gold_keywords:
        score += settings.gold_weight
    
    # Time spent multiplier (days * 2, capped at 40)
    if factors.time_spent_days is not None and factors.time_spent_days > 0:
        time_bonus = min(
            factors.time_spent_days * settings.time_spent_multiplier,
            settings.time_spent_cap
        )
        score += time_bonus
    
    # Backup count bonus (+10 if > threshold)
    if factors.backup_count > settings.backup_threshold:
        score += settings.backup_bonus
    
    # Version count bonus (cluster size * 5, capped at 20)
    if factors.cluster_size > 1:
        version_bonus = min(
            factors.cluster_size * settings.version_weight,
            settings.version_cap
        )
        score += version_bonus
    
    # Clamp to 0-100 range
    return max(0, min(100, score))


def extract_keywords_from_filename(filename: str) -> tuple[List[str], List[str]]:
    """
    Extract diamond and gold tier keywords from a filename.
    
    Args:
        filename: The project filename (without path)
        
    Returns:
        Tuple of (diamond_keywords, gold_keywords) found in the filename
    """
    filename_upper = filename.upper()
    
    diamond_found = []
    gold_found = []
    
    for keyword in settings.diamond_keywords:
        if keyword.upper() in filename_upper:
            diamond_found.append(keyword)
    
    for keyword in settings.gold_keywords:
        if keyword.upper() in filename_upper:
            gold_found.append(keyword)
    
    return diamond_found, gold_found


def estimate_tier_from_score(score: int) -> str:
    """
    Get a human-readable tier label based on score.
    
    Args:
        score: The signal score (0-100)
        
    Returns:
        Tier label string
    """
    if score >= 80:
        return "S-Tier (Must Finish)"
    elif score >= 60:
        return "A-Tier (High Potential)"
    elif score >= 40:
        return "B-Tier (Review)"
    elif score >= 20:
        return "C-Tier (Low Priority)"
    else:
        return "D-Tier (Archive)"

