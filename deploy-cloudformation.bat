@echo off
setlocal enabledelayedexpansion

REM Configuration
set STACK_NAME=bedrock-ai-streamlit-stack
set TEMPLATE_FILE=cloudformation-template.yaml
set AWS_REGION=us-east-1

echo ========================================
echo CloudFormation Deployment Script
echo ========================================

REM Get parameters from user
set /p BEDROCK_AGENT_ID="Enter Bedrock Agent ID (default: HMASWS7VNA): "
if "%BEDROCK_AGENT_ID%"=="" set BEDROCK_AGENT_ID=HMASWS7VNA

set /p BEDROCK_AGENT_ALIAS_ID="Enter Bedrock Agent Alias ID (default: S7KMPCYKQX): "
if "%BEDROCK_AGENT_ALIAS_ID%"=="" set BEDROCK_AGENT_ALIAS_ID=S7KMPCYKQX

set /p APP_TITLE="Enter App Title (default: Welcome to BEDROCK Agent): "
if "%APP_TITLE%"=="" set APP_TITLE=Welcome to BEDROCK Agent

echo.
echo Deploying CloudFormation stack...
echo Stack Name: %STACK_NAME%
echo Region: %AWS_REGION%
echo Agent ID: %BEDROCK_AGENT_ID%
echo Agent Alias ID: %BEDROCK_AGENT_ALIAS_ID%
echo.

REM Deploy CloudFormation stack
aws cloudformation deploy ^
    --template-file %TEMPLATE_FILE% ^
    --stack-name %STACK_NAME% ^
    --parameter-overrides ^
        BedrockAgentId=%BEDROCK_AGENT_ID% ^
        BedrockAgentAliasId=%BEDROCK_AGENT_ALIAS_ID% ^
        AppTitle="%APP_TITLE%" ^
    --capabilities CAPABILITY_NAMED_IAM ^
    --region %AWS_REGION%

if %errorlevel% neq 0 (
    echo Error: CloudFormation deployment failed
    exit /b 1
)

echo.
echo ========================================
echo CloudFormation Stack Deployed Successfully!
echo ========================================

REM Get stack outputs
echo.
echo Getting stack outputs...
aws cloudformation describe-stacks ^
    --stack-name %STACK_NAME% ^
    --region %AWS_REGION% ^
    --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" ^
    --output table

echo.
echo Next Steps:
echo 1. Build and push your Docker image to the ECR repository
echo 2. Update the App Runner service with the new image
echo 3. Access your application using the Service URL above
echo.
echo To build and push image, run: build-and-push-to-stack.bat