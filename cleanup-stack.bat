@echo off
setlocal enabledelayedexpansion

REM Configuration
set STACK_NAME=bedrock-ai-streamlit-stack
set AWS_REGION=us-east-1

echo ========================================
echo CloudFormation Stack Cleanup
echo ========================================

echo WARNING: This will delete all resources created by the CloudFormation stack!
echo This includes:
echo - ECR Repository and all images
echo - App Runner Service
echo - IAM Roles
echo - CloudWatch Log Groups
echo.

set /p confirm="Are you sure you want to delete the stack? (yes/no): "
if /i "%confirm%" neq "yes" (
    echo Cleanup cancelled.
    exit /b 0
)

echo.
echo Step 1: Getting ECR Repository name...
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %STACK_NAME% --region %AWS_REGION% --query "Stacks[0].Outputs[?OutputKey=='ECRRepositoryURI'].OutputValue" --output text 2^>nul') do set ECR_URI=%%i

if not "%ECR_URI%"=="" (
    REM Extract repository name from URI
    for /f "tokens=2 delims=/" %%i in ("%ECR_URI%") do set ECR_REPO=%%i
    
    echo Step 2: Deleting all images from ECR repository...
    aws ecr list-images --repository-name %ECR_REPO% --region %AWS_REGION% --query "imageIds[*]" --output json > temp_images.json
    aws ecr batch-delete-image --repository-name %ECR_REPO% --region %AWS_REGION% --image-ids file://temp_images.json 2>nul
    del temp_images.json 2>nul
    echo ECR images deleted.
)

echo.
echo Step 3: Deleting CloudFormation stack...
aws cloudformation delete-stack --stack-name %STACK_NAME% --region %AWS_REGION%

if %errorlevel% neq 0 (
    echo Error: Failed to initiate stack deletion
    exit /b 1
)

echo.
echo Stack deletion initiated. This may take several minutes...
echo.
echo Monitoring stack deletion status...
aws cloudformation wait stack-delete-complete --stack-name %STACK_NAME% --region %AWS_REGION%

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Stack Deleted Successfully!
    echo ========================================
) else (
    echo.
    echo Stack deletion may have failed or is still in progress.
    echo Check AWS Console for details.
)