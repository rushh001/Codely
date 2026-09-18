@echo off
echo ===================================================
echo   CODELY LIVE CODEBASE CONTEXT ENGINE
echo   Sub-Second AST Retrieval for Live Engineering Calls
echo ===================================================
echo.
echo Starting Python FastAPI Backend on http://127.0.0.1:8000 ...
start "Codely Backend" cmd /k "cd backend && .\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting React HUD Frontend on http://localhost:5173 ...
start "Codely Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo [OK] Services started! Open http://localhost:5173 in browser or run "npm run electron" in frontend directory.
