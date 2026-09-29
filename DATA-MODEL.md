# Data Model

The implementation uses SQLAlchemy models in `app/models.py`. The following is the current relational model.

## User

Stores `id`, unique `email`, `full_name`, bcrypt `hashed_password`, `role`, and `created_at`.

Roles are PARTICIPANT, JUDGE, ORGANIZER, and ADMIN.

## Event

Stores the event slug, title, submission deadline, voting deadline, and active state. An event owns its rubric criteria and teams.

## Team

Stores a team name, unique invite code, and event relationship. A team can have up to four members in the current application logic and can have one submission.

## TeamMember

Links users to teams and records whether the member is the team leader.

## Submission

Stores the team, project title, description, repository URL, optional demo URL, draft/final state, and submission timestamp. A team can have one submission. A final submission is locked against editing.

## RubricCriterion

Stores the event-specific criterion name, weight, and maximum score.

## JudgeAssignment

Links a judge to a submission. A unique constraint prevents duplicate judge/submission assignments.

## Score

Stores a judge's score for one criterion of one submission, optional feedback, and creation time. A unique constraint prevents duplicate criterion scores for the same judge and submission.

## Relationships

`User -> TeamMember -> Team`

`Event -> Team -> Submission`

`Event -> RubricCriterion`

`Submission -> JudgeAssignment -> User`

`Submission -> Score -> User`

The source of truth for the schema is `app/models.py`, not this document.
