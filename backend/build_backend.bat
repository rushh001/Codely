@echo off
echo ===================================================
echo   Compiling Codely Python Backend with PyInstaller
echo ===================================================

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

pip install pyinstaller --upgrade

echo Building codely-backend.exe...
pyinstaller main.py ^
    --onefile ^
    --name codely-backend ^
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

if exist dist\codely-backend.exe (
    copy /y dist\codely-backend.exe dist\cluely-backend.exe
)

echo.
echo Build complete. Output located at backend\dist\codely-backend.exe
pause
