@echo off
setlocal enabledelayedexpansion

REM Configuration
set STACK_NAME=bedrock-ai-streamlit-stack
set AWS_REGION=us-east-1
set IMAGE_TAG=latest

echo ========================================
echo Build and Push to CloudFormation Stack
echo ========================================

REM Get ECR Repository URI from CloudFormation stack
echo Getting ECR Repository URI from stack...
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --region %AWS_REGION% --query "Stacks[0].Outputs[?OutputKey=='ECRRepositoryURI'].OutputValue" --output text') do set ECR_URI=%%i

if "%ECR_URI%"=="" (
    echo Error: Could not get ECR Repository URI from stack
    echo Make sure the CloudFormation stack is deployed successfully
    exit /b 1
)

echo ECR Repository URI: %ECR_URI%

REM Get AWS Account ID
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set AWS_ACCOUNT_ID=%%i

echo.
echo Step 1: Login to ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
if %errorlevel% neq 0 (
    echo Error: ECR login failed
    exit /b 1
)

echo.
echo Step 2: Building Docker image...
docker build -t bedrock-ai-streamlit:%IMAGE_TAG% .
if %errorlevel% neq 0 (
    echo Error: Docker build failed
    exit /b 1
)

echo.
echo Step 3: Tagging image for ECR...
docker tag bedrock-ai-streamlit:%IMAGE_TAG% %ECR_URI%:%IMAGE_TAG%

echo.
echo Step 4: Pushing image to ECR...
docker push %ECR_URI%:%IMAGE_TAG%
if %errorlevel% neq 0 (
    echo Error: Docker push failed
    exit /b 1
)

echo.
echo Step 5: Updating App Runner service...
REM Get App Runner Service ARN
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --region %AWS_REGION% --query "Stacks[0].Outputs[?OutputKey=='AppRunnerServiceArn'].OutputValue" --output text') do set SERVICE_ARN=%%i

REM Start deployment
aws apprunner start-deployment --service-arn "%SERVICE_ARN%" --region %AWS_REGION%
if %errorlevel% neq 0 (
    echo Warning: Could not trigger App Runner deployment automatically
    echo You may need to trigger deployment manually in the AWS Console
)

echo.
echo ========================================
echo Build and Push Completed Successfully!
echo ========================================

REM Get Service URL
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --region %AWS_REGION% --query "Stacks[0].Outputs[?OutputKey=='AppRunnerServiceURL'].OutputValue" --output text') do set SERVICE_URL=%%i

echo.
echo Your application is available at: %SERVICE_URL%
echo.
echo Monitor deployment status in AWS Console → App Runner