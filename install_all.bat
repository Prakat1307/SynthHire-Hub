@echo off
echo ==========================================
echo SynthHire Dependency Installer
echo ==========================================

echo.
echo [1/3] upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/3] Installing Backend Dependencies...
pip install -r backend/requirements.txt
:: Also traverse services just in case, though shared should cover it
for /d %%d in (backend\services\*) do (
    if exist "%%d\requirements.txt" (
        echo Installing dependencies for %%d...
        pip install -r "%%d\requirements.txt"
    )
)

echo.
echo [3/3] Installing Frontend Dependencies...
cd frontend
call npm install
cd ..

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================

