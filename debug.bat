@echo off
title MentorPulse - 1-Click Debug ^& Live Demo
color 0B

echo =================================================================
echo        MentorPulse - Skill-Based Mentor Matching Platform
echo            [1-Click Debug Server ^& Live Demo Launcher]
echo =================================================================
echo.

:: 1. Verify Python availability
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not found in your PATH!
    echo Please install Python 3.10+ and ensure "Add python.exe to PATH" is checked.
    pause
    exit /b 1
)

:: 2. Apply database migrations
echo [1/4] Applying database schema migrations...
python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Migration failed. Check your Python environment.
    pause
    exit /b 1
)

:: 3. Seed demo data
echo.
echo [2/4] Verifying and seeding turnkey demo data...
python manage.py seed_demo_data

:: 4. Launch web browser automatically
echo.
echo [3/4] Opening MentorPulse in your default browser...
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:8000/

:: 5. Start local Django development server
echo.
echo [4/4] Starting Django development server at http://127.0.0.1:8000/ ...
echo =================================================================
echo  Demo Accounts Ready (Password: DemoPass123!):
echo    * [ADMIN]   admin (System Administrator)
echo    * [MENTOR]  sarah_backend (Sarah Connor - Python/Django)
echo    * [MENTOR]  marcus_frontend (Marcus Vance - React/Design)
echo    * [MENTOR]  dr_elena (Dr. Elena Rostova - AI/Data Science)
echo    * [LEARNER] alex_learner (Alex Rivera - Active mentorship)
echo    * [LEARNER] priya_learner (Priya Sharma - Completed & cert)
echo    * [LEARNER] jordan_learner (Jordan Lee - Priority request)
echo.
echo  FEATURE: Use the glowing "Demo Switcher" in the top navbar
echo  for instant 1-click swapping between any of these accounts!
echo =================================================================
echo Press Ctrl+C in this console window to stop the server.
echo.

python manage.py runserver 127.0.0.1:8000

pause
