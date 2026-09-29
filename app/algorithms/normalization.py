from math import sqrt
from collections import defaultdict

def compute_z_score_normalization(raw_evaluations):
    if not raw_evaluations:
        return {}
    by_judge = defaultdict(list)
    for item in raw_evaluations:
        by_judge[item["judge_id"]].append(item)
    normalized = defaultdict(list)
    for judge_id, items in by_judge.items():
        values = [float(x["weighted_score"]) for x in items]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = sqrt(variance)
        for item in items:
            z = 0.0 if std == 0 else (float(item["weighted_score"]) - mean) / std
            normalized[item["submission_id"]].append(z)
    result = {}
    for submission_id, zs in normalized.items():
        mean_z = sum(zs) / len(zs)
        result[submission_id] = round(max(0.0, min(100.0, 50.0 + mean_z * 15.0)), 2)
    return result
