@echo off
echo ===================================================
echo   Compiling Cluely Python Backend with PyInstaller
echo ===================================================

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

pip install pyinstaller --upgrade

echo Building cluely-backend.exe...
pyinstaller main.py ^
    --onefile ^
    --name cluely-backend ^
    --hidden-import=sounddevice ^
    --hidden-import=scipy ^
    --hidden-import=scipy.io.wavfile ^
    --hidden-import=groq ^
    --hidden-import=httpx ^
    --hidden-import=fastapi ^
    --hidden-import=uvicorn ^
    --hidden-import=pydantic ^
    --hidden-import=dotenv ^
    --hidden-import=numpy ^
    --clean

echo.
echo Build complete. Output located at backend\dist\cluely-backend.exe
pause
