import numpy as np
from typing import Dict, List

def compute_z_score_normalization(
    raw_evaluations: List[dict]
) -> Dict[int, float]:
    """
    raw_evaluations format:
    [
        {"submission_id": 1, "judge_id": 10, "weighted_score": 8.5},
        {"submission_id": 2, "judge_id": 10, "weighted_score": 6.0},
        ...
    ]
    Returns mapping of {submission_id: normalized_final_score (0-100)}
    """
    if not raw_evaluations:
        return {}

    judge_scores: Dict[int, List[float]] = {}
    for entry in raw_evaluations:
        j_id = entry["judge_id"]
        judge_scores.setdefault(j_id, []).append(entry["weighted_score"])

    # Compute mean and standard deviation per judge
    judge_stats = {}
    for j_id, scores in judge_scores.items():
        arr = np.array(scores)
        mean = float(np.mean(arr))
        std = float(np.std(arr))
        # Zero-variance protection (if a judge gave identical marks to everyone)
        judge_stats[j_id] = (mean, std if std > 1e-6 else 1.0)

    # Normalize each evaluation to a z-score
    sub_z_scores: Dict[int, List[float]] = {}
    for entry in raw_evaluations:
        j_id = entry["judge_id"]
        sub_id = entry["submission_id"]
        mean, std = judge_stats[j_id]
        
        z = (entry["weighted_score"] - mean) / std
        sub_z_scores.setdefault(sub_id, []).append(z)

    # Convert average z-score back to an organizer-friendly 0-100 distribution:
    # Formula: 50 + (avg_z * 15), clamped between 0 and 100
    final_rankings = {}
    for sub_id, z_list in sub_z_scores.items():
        mean_z = float(np.mean(z_list))
        scaled_score = round(max(0.0, min(100.0, 50.0 + (mean_z * 15.0))), 2)
        final_rankings[sub_id] = scaled_score

    return final_rankings
