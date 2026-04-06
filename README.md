# Yunnan Enterprise Employment Data Collection System

## Backend setup
1. Create and activate a Python virtual environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and adjust `DATABASE_URL` and `JWT_SECRET_KEY`.
4. Run database migrations:
   `alembic upgrade head`
5. Seed demo users if needed:
   `python scripts/seed_demo_data.py`
6. Start the API service:
   `uvicorn app.main:app --reload`

## Frontend setup
1. Open the `frontend` directory.
2. Install dependencies:
   `npm install`
3. Copy `frontend/.env.example` to `frontend/.env` if you need to override the API base URL.
4. Start the Vite dev server:
   `npm run dev`

## One-click start
- Double-click `start_dev.bat` to launch backend and frontend in separate windows.
- Double-click `stop_dev.bat` to close those two development windows.
- You can also use `start_backend.bat` or `start_frontend.bat` separately.

## Demo accounts
- Province: `province_admin` / `Admin12345`
- City: `kunming_city` / `City12345`
- Enterprise: `demo_enterprise` / `Enterprise12345`

## Notes
- Enterprise monthly reporting requires an approved filing and a configured reporting window for the target month.
- Province users can configure reporting windows and inspect system CPU/memory metrics.
- The backend supports both PostgreSQL and MySQL SQLAlchemy URLs. PostgreSQL is the default.
