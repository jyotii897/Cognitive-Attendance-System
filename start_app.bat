@echo off
echo Stopping old python processes...
taskkill /F /IM python.exe >nul 2>&1

echo Renaming env to .env (if needed)...
if exist env (
    copy env .env
)

echo Installing requirements...
pip install Flask python-dotenv opencv-python dlib face_recognition cvzone firebase-admin

echo Starting Server...
start "" "http://127.0.0.1:5001/signup.html"
python app.py
pause
