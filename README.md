# NOVA AI
Mobile-first AI chat starter powered by FastAPI and g4f.

## Run locally
1. Python 3.10+
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `APP_PASSWORD`
4. `uvicorn app:app --host 0.0.0.0 --port 8000`
5. Open http://localhost:8000

## Deploy to Render
- Push this folder to GitHub.
- Create a Render Web Service from the repository.
- Set `APP_PASSWORD` to a long, unique secret.
- Keep `COOKIE_SECURE=true` for HTTPS deployment.

Provider availability in g4f can change; errors are shown in chat if a provider fails.
This starter uses in-memory sessions, so logging in again after a server restart is expected.
