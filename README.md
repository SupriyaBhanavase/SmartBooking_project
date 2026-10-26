# SmartBooking — group competition project

A mobile-friendly booking demo with separate frontend and backend processes, SQLite booking history, printable digital receipts, fare estimates, demo driver assignment, 10% commission calculation, and an optional Gemma AI assistant served by Ollama.

## Stack
- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python + Flask REST API
- Database: SQLite (created automatically)
- Local AI: Ollama + a Gemma model
- Collaboration: Git + GitHub

## Requirements
Python 3.10+, Git, Ollama, and a Gemma model downloaded locally.

## Run the backend (Git Bash / terminal 1)
From the project root:
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python backend/app.py
```
Windows Command Prompt activation instead:
```bat
.venv\Scripts\activate
```
Test API: open `http://127.0.0.1:5000/api/health`.

## Run the frontend separately (terminal 2)
Open `frontend/index.html` using VS Code Live Server (if installed), usually `http://127.0.0.1:5500/frontend/`.
If Live Server isn't installed, use Python's static server from the project root:
```bash
python -m http.server 5500
```
Then open `http://127.0.0.1:5500/frontend/`.

## Gemma / Ollama
Check installed models:
```bash
ollama list
```
If Gemma isn't installed, choose one that your computer can run, for example:
```bash
ollama pull gemma3:1b
```
Keep Ollama running. The backend defaults to model `gemma3:1b`. If `ollama list` shows a different exact name, set it before starting Flask in Git Bash:
```bash
export OLLAMA_MODEL=gemma3:1b
python backend/app.py
```
Replace `gemma3:1b` with the exact name shown by `ollama list`. The AI button calls Ollama locally; if Ollama is off or the model is missing, booking features continue to work.

## Features / demo limitations
- Fare = vehicle base rate + distance × rate per km
- Driver commission = 10% of fare
- Booking ID generated automatically
- Bookings stored in local SQLite database
- Printable digital receipt
- Demo payment status only; no actual payment gateway
- User-entered distance; no live maps or route-distance lookup
- Sample driver assignment; no real driver accounts or authentication yet

## Suggested group split
1. **Frontend owner:** `frontend/index.html`, `frontend/style.css`, `frontend/app.js`
2. **Backend owner:** `backend/app.py`, API validation, SQLite
3. **AI owner:** Ollama/Gemma model, test `/api/ai`, document model name
4. **Integration & Git owner:** README, test full flow, review and merge branches

Keep work in separate branches. Avoid editing the same file simultaneously. Don't commit passwords, API keys, or the generated database.
