@echo off
setlocal enabledelayedexpansion

REM Configuration
set AWS_REGION=us-east-1
set ECR_REPOSITORY=bedrock-ai-streamlit
set IMAGE_TAG=latest
set APP_RUNNER_SERVICE=bedrock-ai-app

echo ========================================
echo AWS App Runner ECR Deployment Script
echo ========================================

REM Get AWS Account ID
echo Getting AWS Account ID...
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set AWS_ACCOUNT_ID=%%i
if "%AWS_ACCOUNT_ID%"=="" (
    echo Error: Could not get AWS Account ID. Please check AWS CLI configuration.
    exit /b 1
)
echo AWS Account ID: %AWS_ACCOUNT_ID%

REM Set ECR URI
set ECR_URI=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPOSITORY%

echo.
echo Step 1: Creating ECR Repository...
aws ecr create-repository --repository-name %ECR_REPOSITORY% --region %AWS_REGION% 2>nul
if %errorlevel% neq 0 (
    echo Repository might already exist, continuing...
)

echo.
echo Step 2: Getting ECR Login Token...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
if %errorlevel% neq 0 (
    echo Error: ECR login failed
    exit /b 1
)

echo.
echo Step 3: Building Docker Image...
docker build -t %ECR_REPOSITORY%:%IMAGE_TAG% .
if %errorlevel% neq 0 (
    echo Error: Docker build failed
    exit /b 1
)

echo.
echo Step 4: Tagging Image for ECR...
docker tag %ECR_REPOSITORY%:%IMAGE_TAG% %ECR_URI%:%IMAGE_TAG%

echo.
echo Step 5: Pushing Image to ECR...
docker push %ECR_URI%:%IMAGE_TAG%
if %errorlevel% neq 0 (
    echo Error: Docker push failed
    exit /b 1
)

echo.
echo ========================================
echo Build and Push Completed Successfully!
echo ========================================
echo.
echo ECR Image URI: %ECR_URI%:%IMAGE_TAG%
echo.
echo Next Steps:
echo 1. Create IAM roles using: create-iam-roles.bat
echo 2. Create App Runner service in AWS Console
echo 3. Use the ECR Image URI above
echo.