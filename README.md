# SmartFlight

A flight search and comparison application with risk analysis using OpenSky Network data.

## Project Structure

```
Smart_Flight/
├── backend/          # Python FastAPI backend
├── frontend/         # React + Vite frontend
└── README.md
```

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Deployment

See `RENDER_FRESH_START.md` for Render deployment instructions.
