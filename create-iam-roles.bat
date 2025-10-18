@echo off
echo Creating IAM roles for App Runner...

REM Create App Runner Instance Role
echo.
echo Creating App Runner Instance Role...
aws iam create-role --role-name AppRunnerBedrockInstanceRole --assume-role-policy-document file://trust-policy.json
aws iam put-role-policy --role-name AppRunnerBedrockInstanceRole --policy-name BedrockPolicy --policy-document file://iam-policy.json

REM Create App Runner Access Role (for ECR access)
echo.
echo Creating App Runner Access Role...
aws iam create-role --role-name AppRunnerECRAccessRole --assume-role-policy-document file://apprunner-access-trust-policy.json
aws iam attach-role-policy --role-name AppRunnerECRAccessRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess

echo.
echo Getting Role ARNs...
echo.
echo Instance Role ARN:
aws iam get-role --role-name AppRunnerBedrockInstanceRole --query "Role.Arn" --output text

echo.
echo Access Role ARN:
aws iam get-role --role-name AppRunnerECRAccessRole --query "Role.Arn" --output text

echo.
echo IAM roles created successfully!
echo Save these ARNs for App Runner service creation.