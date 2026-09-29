# Judging

Dogfood uses an event-specific weighted rubric. The seeded Dogfood 2026 event currently defines four criteria:

| Criterion | Weight | Maximum |
|---|---:|---:|
| Tier Completion & Correctness | 40% | 10 |
| Judging Integrity | 25% | 10 |
| Adoptability & Operability | 20% | 10 |
| Code Quality & Innovation | 15% | 10 |

The application stores each criterion as a `RubricCriterion`, so an event can use a different set of criteria and weights.

## Assignment and access control

Judges are assigned to submissions through `JudgeAssignment`. The assignment is unique per judge/submission pair.

When a judge submits an evaluation, the backend verifies:

1. the authenticated user is a judge;
2. the submission exists;
3. the judge is assigned to that submission;
4. each criterion belongs to the submission's event; and
5. every score is within the criterion's configured range.

This keeps judge isolation in the backend rather than relying only on hidden frontend controls.

## Weighted raw score

For each criterion:

```
criterion contribution =
(raw score / maximum score) × weight × 100
```

The organizer results view sums the weighted criterion contributions for each submission.

## Cross-judge normalization

The prototype applies judge-relative z-score normalization to weighted evaluation scores.

For each judge:

```
Z = (score - judge mean) / judge standard deviation
```

If a judge gives identical scores to all represented submissions, the standard deviation is zero and the implementation uses zero z-scores for that judge.

For each submission, the available judge z-scores are averaged and mapped to a display score:

```
normalized score = 50 + mean z-score × 15
```

The resulting value is clamped to the 0-100 range.

This normalization reduces the effect of different judge scoring distributions. It does not prove that all forms of bias have been eliminated and is intentionally presented as a prototype normalization method.

## Community voting

Community voting is separate from judge scoring.

The event controls:

- voting start time;
- voting deadline;
- access mode: open, email-gated, or authenticated.

The ballot order is randomized server-side. A voter receives a stable voter key, and a database uniqueness constraint allows only one vote per voter key for an event. Authenticated users can also be associated with their account.

Voting requests are rate-limited per IP using an in-memory minute bucket. Duplicate attempts and rate-limited requests are recorded in the audit log.

Public results are hidden before the voting period closes. Organizer-facing result and audit views remain available according to their authorization rules.

## Operational judging outputs

The platform can expose normalized results to organizers, generate participation certificates for submissions, export submission data as CSV, and generate signed judge participation records using Ed25519 signatures. These features complement the core judging workflow rather than changing the scoring calculation.
