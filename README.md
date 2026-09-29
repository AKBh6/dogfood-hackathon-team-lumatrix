# Dogfood 2026

An offline-first, self-hostable hackathon management platform covering participant registration, teams, project submissions, judging, and results.

## Stack

- FastAPI + Uvicorn
- Jinja2 + HTML/CSS
- SQLAlchemy
- SQLite
- JWT authentication
- bcrypt password hashing
- Docker / Docker Compose

## Current status

Functional hackathon prototype. The participant, judge, organizer, results, gallery, seed, and automated verification flows are implemented.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

For a clean demo database, delete `dogfood.db` first and run the seed command again.

## Demo accounts

- Admin: `admin@raptors.dev` / `admin123`
- Judge: `judge@raptors.dev` / `judge123`
- Participant: `builder@raptors.dev` / `build123`

Public registration creates participant accounts only. Email ownership is not verified because the prototype has no mail service.

## Docker

```bash
docker compose up --build
```

## Verification

The repository includes an end-to-end test covering registration, login, team creation, final submission, judge assignment, rubric scoring, results, CSV export, gallery visibility, and final-submission locking.

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Data Model](DATA-MODEL.md)
- [Judging](JUDGING.md)

## Security note

Passwords are stored as bcrypt hashes. The default local JWT secret is intended only for development. Set a strong `SECRET_KEY` for any shared deployment.

## License

MIT
