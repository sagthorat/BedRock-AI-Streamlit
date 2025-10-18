@echo off
echo ========================================
echo Quick Deploy to AWS App Runner via ECR
echo ========================================
echo.

echo This script will:
echo 1. Create IAM roles
echo 2. Build and push Docker image to ECR
echo 3. Provide next steps for App Runner service creation
echo.

set /p confirm="Continue? (y/n): "
if /i "%confirm%" neq "y" (
    echo Deployment cancelled.
    exit /b 0
)

echo.
echo Step 1: Creating IAM roles...
call create-iam-roles.bat
if %errorlevel% neq 0 (
    echo Error creating IAM roles
    exit /b 1
)

echo.
echo Step 2: Building and pushing to ECR...
call build-and-deploy.bat
if %errorlevel% neq 0 (
    echo Error building and pushing to ECR
    exit /b 1
)

echo.
echo ========================================
echo Quick Deploy Completed!
echo ========================================
echo.
echo Next Steps:
echo 1. Go to AWS Console → App Runner
echo 2. Create new service with ECR source
echo 3. Use the ECR URI shown above
echo 4. Configure environment variables as per the guide
echo.
echo For detailed instructions, see: ECR-DEPLOYMENT-GUIDE.md
echo.