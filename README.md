# QA Test Case Generator Agent

See `IMPLEMENTATION_PLAN.md`.

## Setup notes (Windows)
- Python 3.12 (installed via winget, user scope).
- The virtualenv lives **outside** this folder (`%LOCALAPPDATA%\qa-agent-venv`) because the project path is too long for some packages (numpy) and OneDrive would sync it.
- Copy `.env.example` to `.env` and fill in credentials.

## Run
```powershell
& "$env:LOCALAPPDATA\qa-agent-venv\Scripts\python.exe" -m streamlit run agent_app/app.py
```

## Demo without credentials
Runs the real UI on fake Jira/GitHub/Claude services (the test runner is faked too):
```powershell
& "$env:LOCALAPPDATA\qa-agent-venv\Scripts\python.exe" -m streamlit run scripts/demo_app.py
```
The first page load takes about 20 seconds while Python imports warm up.

## Tests
```powershell
& "$env:LOCALAPPDATA\qa-agent-venv\Scripts\python.exe" -m pytest tests
```
