# Architecture

Dogfood 2026 is a self-hostable FastAPI application with server-rendered Jinja2 pages, SQLAlchemy persistence, and SQLite as the default database. The design keeps the runtime self-contained so the platform can operate without a hosted database, CDN, external API, or frontend framework.

## Runtime components

```
Browser
   |
   v
FastAPI + Uvicorn
   |
   +--> Jinja2 templates
   |       |
   |       +--> HTML/CSS
   |
   +--> HTML routes
   |       |
   |       +--> participant workflow
   |       +--> judge workflow
   |       +--> organizer workflow
   |       +--> gallery / voting / results
   |
   +--> REST API
           |
           v
       SQLAlchemy ORM
           |
           v
      SQLite database
```

Docker Compose packages the same application and mounts `./data` into the container so the SQLite database persists outside the container.

## Authentication and roles

Authentication uses bcrypt password hashes and signed JWT access tokens stored in HTTP-only cookies.

The application defines these roles:

- PARTICIPANT: team and submission workflow.
- JUDGE: assigned-project access and rubric evaluation.
- ORGANIZER: event configuration, assignments, results, audit, certificates, and operational tools.
- ADMIN: organizer-level administrative access.
- VISITOR: model-level role value for non-authenticated/public contexts.

Public registration creates participant accounts only. Judge and organizer accounts are provisioned through seed/administrative workflows.

## Event lifecycle

1. A participant registers and authenticates.
2. Participants create or join a team using an invite code.
3. A team prepares a draft submission and finalizes it before the submission deadline.
4. Final submissions appear in the public gallery and become eligible for judging.
5. An organizer configures the rubric and assigns submissions to judges.
6. Judges evaluate only submissions assigned to them.
7. Weighted judging scores are normalized using judge-relative z-scores.
8. Community voting can run in a configured window with access controls, randomized ballots, duplicate-vote protection, rate limiting, and audit logging.
9. Public results are hidden until the configured voting period closes.
10. Organizers can inspect results, audit events, generate certificates, create signed judge participation records, and export/import operational data.

## Application layers

### Presentation layer

Jinja2 templates provide server-rendered pages for participants, judges, organizers, authentication, gallery, voting, results, certificates, and embedded gallery views. The frontend uses ordinary HTML/CSS and does not depend on a third-party frontend framework.

### Application layer

FastAPI routes handle authentication, authorization, event lifecycle operations, team membership, submissions, judging, voting, comments, results, certificates, audit records, signed records, and bulk operations.

### Persistence layer

SQLAlchemy maps the relational domain model to SQLite. The database is created from the SQLAlchemy models through `Base.metadata.create_all()`.

### Algorithm layer

`app/algorithms/normalization.py` contains the judging normalization logic. Weighted raw scores are converted into judge-relative z-scores and then mapped to a bounded 0-100 normalized display score.

## Security controls

- Bcrypt password hashing.
- Signed JWT authentication in HTTP-only cookies.
- Role checks on protected routes.
- Backend judge-assignment verification.
- Database uniqueness constraints for team membership, judge assignments, criterion evaluations, and event voter keys.
- Final-submission edit protection.
- Per-IP in-memory voting rate limiting.
- Audit records for important organizer and community-voting actions.
- Ed25519 signatures for judge participation records.

These controls are appropriate for the hackathon prototype. The system does not implement production-grade email verification, password recovery, MFA, CSRF protection, distributed rate limiting, or database migrations.

## Deployment

Local development:

```bash
python -m app.seed
uvicorn app.main:app --reload
```

Docker:

```bash
docker compose up --build
```

The Docker image uses Python 3.11, installs the pinned dependency set from `requirements.txt`, seeds the application on startup, and serves the application on port 8000.
