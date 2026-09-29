# Architecture

Dogfood 2026 is an offline-first FastAPI application using server-rendered Jinja2 templates, SQLAlchemy, and SQLite by default.

## Runtime

- FastAPI + Uvicorn provide the web application.
- Jinja2 renders the participant, judge, organizer, and public gallery pages.
- SQLAlchemy maps users, events, teams, submissions, rubric criteria, assignments, and scores.
- SQLite is the default local database. Docker Compose stores it under `./data`.
- JWT access tokens are stored in HTTP-only cookies.
- Passwords are stored as bcrypt hashes, never as plaintext.
- No external database or frontend service is required.

## Roles

Public registration creates participant accounts only. Judge and organizer/admin accounts are provisioned by the organizer through the seed data or database administration.

Participants can create/join teams, save drafts, submit a final project, and view the public gallery.

Judges can see only submissions assigned to them and submit rubric scores through the judging API.

Organizers/admins can edit the event title, assign submissions to judges, view normalized results, and export CSV results.

## Data flow

1. A participant registers and logs in.
2. The participant creates or joins a team.
3. The team saves a project draft and submits a final version before the deadline.
4. An organizer assigns final submissions to judges.
5. Judges score assigned submissions against the event rubric.
6. The results service calculates weighted raw scores and judge-relative normalized scores.
7. Organizers/admins can inspect the results and export them as CSV.
8. Final submissions are locked against further edits.

## Offline operation

The application has no runtime dependency on external APIs, hosted databases, or frontend frameworks. It can run with Python directly or through Docker.

## Security model

Role checks are enforced on protected routes and APIs. Judge evaluation endpoints verify that the judge is assigned to the submission. Final submissions cannot be edited after submission. Password verification uses bcrypt and authentication uses signed JWTs.

This is a hackathon prototype, not a production identity-management system. Email ownership is not verified and there is no email delivery, password reset, MFA, CSRF protection, or database migration system.
