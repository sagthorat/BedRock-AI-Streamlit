@echo off
echo Creating IAM role for App Runner...

REM Create IAM role
aws iam create-role --role-name BedrockAppRunnerRole --assume-role-policy-document file://trust-policy.json

REM Attach policy to role
aws iam put-role-policy --role-name BedrockAppRunnerRole --policy-name BedrockPolicy --policy-document file://iam-policy.json

echo IAM role created successfully!
echo Role ARN: 
aws iam get-role --role-name BedrockAppRunnerRole --query "Role.Arn" --output text

echo.
echo Next steps:
echo 1. Push your code to GitHub
echo 2. Create App Runner service in AWS Console
echo 3. Use the Role ARN above for the service role
echo.