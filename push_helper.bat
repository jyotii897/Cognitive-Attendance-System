@echo off
echo ===========================================
echo Preparing your code for GitHub...
echo ===========================================

REM Initialize Git if not already done
if not exist .git (
    echo Initializing Git repository...
    git init
)

echo Adding files...
git add .

echo Committing files...
git commit -m "Ready for Render Deployment"

echo.
echo ===========================================
echo STEP 1 COMPLETE: Code is COMMITTED locally.
echo.
echo STEP 2: Create a repository on GitHub here:
echo https://github.com/new
echo.
echo STEP 3: Run the commands GitHub gives you below.
echo Example:
echo git remote add origin https://github.com/YOUR_NAME/REPO.git
echo git branch -M main
echo git push -u origin main
echo ===========================================
echo.
cmd /k
