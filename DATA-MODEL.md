# Data Model

The relational schema is implemented in `app/models.py`. SQLAlchemy is the source of truth.

## Core entities

### User

Stores email, full name, bcrypt password hash, role, and account creation time.

Roles are PARTICIPANT, JUDGE, ORGANIZER, ADMIN, and VISITOR.

### Event

Stores the event slug, title, submission deadline, voting deadline, optional start/end times, tracks, prizes, custom questions, voting access mode, voting start time, and active state.

### Team

Belongs to an event and stores the team name and unique invite code. Current application logic limits a team to four members and allows one submission per team.

### TeamMember

Joins users to teams and records whether each member is the team leader. A user/team pair is unique.

### Submission

Belongs to one team and stores title, description, tagline, thumbnail, image gallery, demo video, live URL, technology tags, track, custom answers, repository URL, demo URL, draft/final state, and submission timestamp.

A team can have one submission. Final submissions are locked against further edits.

## Judging entities

### RubricCriterion

Belongs to an event and stores the criterion name, weight, and maximum score.

### JudgeInvitation

Stores an event-specific judge invitation email, track scope, invitation token, invitation timestamp, and optional acceptance timestamp.

### JudgeTrack

Associates a judge with an event and track. The combination of judge, event, and track is unique.

### JudgeAssignment

Associates a judge with a submission. The judge/submission pair is unique.

### Score

Stores a judge's score for one rubric criterion on one submission, optional feedback, and creation time. The combination of submission, judge, and criterion is unique.

### JudgeParticipationRecord

Stores an event/judge payload and an Ed25519 signature for publicly verifiable participation records.

## Community and audit entities

### Vote

Stores the event, submission, optional authenticated user, voter key, optional hashed IP address, and creation time.

The event/voter-key pair is unique, providing database-backed duplicate-vote protection.

### GalleryComment

Stores a submission comment, optional authenticated user, display author name, body, creation time, and hidden-state flag.

### AuditLog

Stores the event and user context when available, action, target type/id, optional hashed IP, details, and timestamp. It is used for organizer auditability of important actions such as votes, blocked duplicates, rate limits, comments, assignments, invitations, imports, and event operations.

## Relationships

```
User
 ├── TeamMember ──> Team ──> Event
 │                    |
 │                    └──> Submission
 |
 ├── JudgeAssignment ──> Submission
 ├── Score ──> Submission
 └── Vote

Event
 ├── Team
 ├── RubricCriterion
 ├── Vote
 ├── JudgeInvitation
 ├── JudgeTrack
 ├── JudgeParticipationRecord
 └── AuditLog

Submission
 ├── JudgeAssignment
 ├── Score
 ├── Vote
 └── GalleryComment
```

Foreign keys connect the related records, while uniqueness constraints enforce one membership per user/team, one submission per team, one judge/submission assignment, one score per judge/criterion/submission, one judge/event/track association, and one voter key per event.

## Persistence notes

SQLite is the default local database. The application creates tables from the current SQLAlchemy metadata, but there is no migration framework. When the model schema changes, a fresh development/demo database should be created by removing the old SQLite file and running the seed script again.
