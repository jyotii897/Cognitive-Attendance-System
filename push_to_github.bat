@echo off
git remote remove origin 2>nul
git remote add origin https://github.com/jyotii897/Cognitive-Attendance-System.git
git branch -m main
git add .
git commit -m "Fix Jinja2 UndefinedError, update requirements, switch to port 5001"
git push -u origin main
pause
