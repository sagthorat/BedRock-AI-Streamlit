@echo off
echo ========================================
echo Setting up AWS Parameter Store
echo ========================================

set /p AGENT_ID="Enter Bedrock Agent ID: "
set /p AGENT_ALIAS_ID="Enter Bedrock Agent Alias ID: "
set /p UI_TITLE="Enter UI Title (default: AI-Powered Assistant): "
set /p UI_ICON="Enter UI Icon (default: 🤖): "
set /p AWS_REGION="Enter AWS Region (default: us-east-1): "

if "%UI_TITLE%"=="" set UI_TITLE=AI-Powered Assistant
if "%UI_ICON%"=="" set UI_ICON=🤖
if "%AWS_REGION%"=="" set AWS_REGION=us-east-1

echo.
echo Creating parameters in Parameter Store...

aws ssm put-parameter --name "/bedrock-ai-app/agent-id" --value "%AGENT_ID%" --type "SecureString" --overwrite
aws ssm put-parameter --name "/bedrock-ai-app/agent-alias-id" --value "%AGENT_ALIAS_ID%" --type "SecureString" --overwrite
aws ssm put-parameter --name "/bedrock-ai-app/ui-title" --value "%UI_TITLE%" --type "String" --overwrite
aws ssm put-parameter --name "/bedrock-ai-app/ui-icon" --value "%UI_ICON%" --type "String" --overwrite
aws ssm put-parameter --name "/bedrock-ai-app/aws-region" --value "%AWS_REGION%" --type "String" --overwrite

echo.
echo ========================================
echo Parameters created successfully!
echo ========================================
echo.
echo Verifying parameters...
aws ssm get-parameters-by-path --path "/bedrock-ai-app" --recursive --with-decryption --query "Parameters[*].[Name,Value]" --output table

echo.
echo Setup complete! You can now run: streamlit run app_parameter_store.py