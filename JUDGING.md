# Judging

The event rubric currently has four criteria:

| Criterion | Weight | Maximum |
|---|---:|---:|
| Tier Completion & Correctness | 40% | 10 |
| Judging Integrity | 25% | 10 |
| Adoptability & Operability | 20% | 10 |
| Code Quality & Innovation | 15% | 10 |

Judges score only submissions assigned to them. The API checks the assignment, verifies that the criterion belongs to the submission's event, and rejects scores outside the criterion's allowed range.

## Raw score

Each criterion contributes:

`raw_score / max_score * weight * 100`

The organizer results page sums these weighted contributions for each submission.

## Normalization

The implementation applies judge-relative z-score normalization to weighted evaluations. For each judge, it calculates that judge's mean and standard deviation across the submissions represented in the evaluation data:

`Z = (score - mean) / standard_deviation`

A judge with identical scores across their evaluations receives zero z-scores because the standard deviation is zero.

For each submission, the mean z-score across available judge evaluations is mapped to a 0-100 display range using:

`50 + mean_z * 15`

The result is clamped to 0-100.

This is a normalization mechanism for the prototype, not a claim that all forms of judge bias are eliminated.