# Dogfood 2026

Dogfood is an offline-first, self-hostable hackathon management platform for running a complete event lifecycle in one application: participant registration, teams, submissions, judging, community voting, results, auditability, certificates, and operational exports.

## What it provides

- Role-based authentication for participants, judges, organizers, and admins.
- Public participant registration with bcrypt password hashing and JWT authentication stored in HTTP-only cookies.
- Event configuration with tracks, prizes, custom questions, submission deadlines, and voting windows.
- Team creation/joining through invite codes, with a four-member limit in the current application logic.
- Draft and final project submissions with deadline enforcement and final-submission locking.
- Public, searchable/filterable project gallery.
- Judge invitations, track assignments, submission assignments, and backend assignment checks.
- Configurable weighted rubrics and judge scoring with feedback.
- Judge-relative z-score normalization and 0-100 normalized results.
- Community voting with configurable access mode, randomized ballot order, one-vote-per-event/voter enforcement, IP-based rate limiting, and audit logging.
- Gallery comments.
- Organizer audit trail.
- Printable participation certificates.
- Signed judge participation records using Ed25519 signatures and public verification.
- Embeddable gallery.
- REST APIs for events, submissions, votes, judges, certificates, and bulk operations.
- CSV submission export and CSV bulk submission import.
- Docker/Docker Compose deployment using local SQLite storage.
- Automated verification covering compilation, tests, Docker build/run, and HTTP startup.

## Technology

- Python 3.11
- FastAPI + Uvicorn
- Jinja2 server-rendered HTML
- SQLAlchemy
- SQLite
- PyJWT
- bcrypt
- cryptography
- Docker / Docker Compose
- pytest + httpx for verification

The application does not require a hosted database, CDN, external API, or frontend framework at runtime.

## Run locally

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create the seeded demo data:

```bash
python -m app.seed
```

Start the application:

```bash
uvicorn app.main:app --reload
```

Open:

```
http://127.0.0.1:8000
```

For a fresh local database, stop the server, remove `dogfood.db`, and run `python -m app.seed` again. The application uses SQLAlchemy `create_all()`; it does not provide schema migrations.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin / Organizer | `admin@raptors.dev` | `admin123` |
| Judge | `judge@raptors.dev` | `judge123` |
| Participant | `builder@raptors.dev` | `build123` |

These credentials are development/demo seed data only. Public registration creates participant accounts; email ownership is not verified because the prototype has no mail service.

## Docker

```bash
docker compose up --build
```

The Compose deployment stores the SQLite database in `./data/dogfood.db` and exposes port 8000.

## Main web routes

- `/` — landing page
- `/register` — participant registration
- `/login` — authentication
- `/gallery` — public project gallery
- `/participant/dashboard` — participant dashboard
- `/participant/team` — team management
- `/participant/submission` — project submission
- `/judge/dashboard` — judge dashboard
- `/judge/assignments` — assigned projects
- `/judge/evaluate/{submission_id}` — rubric evaluation
- `/organizer/dashboard` — organizer dashboard
- `/organizer/event` — event configuration
- `/organizer/assignments` — judge assignment management
- `/organizer/results` — normalized results
- `/organizer/audit` — audit log
- `/organizer/certificate/{submission_id}` — printable certificate
- `/vote` — community voting ballot
- `/public/results` — public results after voting closes
- `/embed/gallery` — embeddable gallery

The voting and public-results routes enforce the configured voting window. A seeded event may therefore return HTTP 403 before voting opens or while results are intentionally hidden.

## API surface

The application exposes REST endpoints for event listing/creation, event submissions, voting, judge invitations and assignments, certificates, and bulk submission import/export. Existing judging and submission APIs are mounted under `/api`.

## Verification

Run the automated test suite with:

```bash
python -m pytest -q
```

Compile the application with:

```bash
python -m compileall app
```

The GitHub Actions verification workflow also builds and starts the Docker deployment and checks HTTP startup.

## Security and prototype limitations

Passwords are hashed with bcrypt and authentication uses signed JWTs. Protected routes enforce roles, judge evaluation verifies assignments, final submissions are locked, duplicate voting is prevented by a database uniqueness constraint, and voting requests are rate-limited per IP.

This is a hackathon prototype rather than a production identity or distributed event platform. It has no email verification, password reset, MFA, CSRF protection, persistent distributed rate limiter, external mail service, or database migration framework. The in-memory rate limiter resets when the process restarts.

## Team

Built by Team Lumatrix for Dogfood 2026.

Arkesh Bhattacharya - Team Lead

Argha Ghosh - Developer

Ritul Sharma - Developer

## License

MIT
