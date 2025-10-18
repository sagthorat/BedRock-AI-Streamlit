# CloudFormation Deployment Guide for Bedrock AI App

This guide provides step-by-step instructions to deploy your Bedrock AI Streamlit application using AWS CloudFormation for complete infrastructure as code.

## Overview

The CloudFormation template creates:
- **ECR Repository** for Docker images
- **IAM Roles** for App Runner service and Bedrock access
- **App Runner Service** with auto-scaling configuration
- **CloudWatch Log Group** for application logs

## Prerequisites

- **AWS CLI** installed and configured
- **Docker Desktop** installed and running
- **AWS Account** with appropriate permissions
- **Bedrock Agent** already created and deployed

## Quick Start

### Option 1: Interactive Deployment
```cmd
deploy-cloudformation.bat
```

### Option 2: Manual Deployment
```cmd
aws cloudformation deploy \
    --template-file cloudformation-template.yaml \
    --stack-name bedrock-ai-streamlit-stack \
    --parameters file://parameters.json \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1
```

## Detailed Steps

### Step 1: Customize Parameters

Edit `parameters.json` with your values:
```json
[
  {
    "ParameterKey": "BedrockAgentId",
    "ParameterValue": "YOUR_AGENT_ID"
  },
  {
    "ParameterKey": "BedrockAgentAliasId", 
    "ParameterValue": "YOUR_AGENT_ALIAS_ID"
  },
  {
    "ParameterKey": "AppTitle",
    "ParameterValue": "Your Custom Title"
  }
]
```

### Step 2: Deploy Infrastructure

Run the deployment script:
```cmd
deploy-cloudformation.bat
```

This will:
1. Prompt for your Bedrock Agent details
2. Deploy the CloudFormation stack
3. Create all required AWS resources
4. Display the stack outputs

### Step 3: Build and Deploy Application

After infrastructure is ready:
```cmd
build-and-push-to-stack.bat
```

This will:
1. Get ECR repository URI from the stack
2. Build Docker image
3. Push to ECR
4. Trigger App Runner deployment
5. Provide the application URL

## CloudFormation Template Details

### Resources Created

#### ECR Repository
```yaml
ECRRepository:
  Type: AWS::ECR::Repository
  Properties:
    RepositoryName: !Ref AppName
    ImageScanningConfiguration:
      ScanOnPush: true
    LifecyclePolicy: # Keeps last 10 images
```

#### IAM Roles
```yaml
# Instance Role (for Bedrock access)
AppRunnerInstanceRole:
  Type: AWS::IAM::Role
  Properties:
    Policies:
      - PolicyName: BedrockAccess
        # Bedrock and CloudWatch permissions

# Access Role (for ECR access)  
AppRunnerAccessRole:
  Type: AWS::IAM::Role
  Properties:
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess
```

#### App Runner Service
```yaml
AppRunnerService:
  Type: AWS::AppRunner::Service
  Properties:
    SourceConfiguration:
      ImageRepository:
        ImageIdentifier: # ECR Image URI
        ImageConfiguration:
          Port: 8080
          RuntimeEnvironmentVariables: # Your app config
    InstanceConfiguration:
      Cpu: !Ref InstanceCpu
      Memory: !Ref InstanceMemory
    HealthCheckConfiguration: # HTTP health checks
    AutoScalingConfigurationArn: # Auto-scaling config
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `AppName` | Application name | `bedrock-ai-streamlit` |
| `BedrockAgentId` | Your Bedrock Agent ID | `HMASWS7VNA` |
| `BedrockAgentAliasId` | Your Agent Alias ID | `S7KMPCYKQX` |
| `AppTitle` | Application title | `Welcome to BEDROCK Agent` |
| `AppIcon` | Application icon | `🤖` |
| `InstanceCpu` | CPU allocation | `1 vCPU` |
| `InstanceMemory` | Memory allocation | `2 GB` |
| `ECRImageURI` | Pre-built image URI | `""` (optional) |

### Outputs

| Output | Description |
|--------|-------------|
| `ECRRepositoryURI` | ECR repository URI for pushing images |
| `AppRunnerServiceURL` | Your application URL |
| `AppRunnerServiceArn` | Service ARN for management |
| `InstanceRoleArn` | Instance role ARN |
| `AccessRoleArn` | Access role ARN |

## Management Commands

### View Stack Status
```cmd
aws cloudformation describe-stacks --stack-name bedrock-ai-streamlit-stack
```

### Update Stack
```cmd
aws cloudformation deploy \
    --template-file cloudformation-template.yaml \
    --stack-name bedrock-ai-streamlit-stack \
    --parameters file://parameters.json \
    --capabilities CAPABILITY_NAMED_IAM
```

### Delete Stack
```cmd
cleanup-stack.bat
```

## Monitoring and Troubleshooting

### CloudWatch Logs
- **Log Group**: `/aws/apprunner/bedrock-ai-streamlit-service/application`
- **Retention**: 14 days (configurable)

### CloudFormation Events
```cmd
aws cloudformation describe-stack-events --stack-name bedrock-ai-streamlit-stack
```

### App Runner Service Status
```cmd
aws apprunner describe-service --service-arn <SERVICE_ARN>
```

## Cost Optimization

### Resource Sizing
- Start with `1 vCPU` and `2 GB` memory
- Monitor usage and adjust parameters
- Redeploy stack with new parameters

### Auto Scaling
- **Max Concurrency**: 100 requests per instance
- **Max Size**: 10 instances
- **Min Size**: 1 instance

### ECR Lifecycle Policy
- Automatically keeps only last 10 images
- Reduces storage costs

## Security Features

### IAM Roles
- **Least privilege** access
- **Service-specific** roles
- **No hardcoded credentials**

### Container Security
- **Non-root user** in container
- **Image scanning** enabled
- **Private ECR repository**

### Network Security
- **HTTPS only** via App Runner
- **AWS managed** load balancing
- **VPC integration** available

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy CloudFormation
        run: |
          aws cloudformation deploy \
            --template-file cloudformation-template.yaml \
            --stack-name bedrock-ai-streamlit-stack \
            --parameters file://parameters.json \
            --capabilities CAPABILITY_NAMED_IAM
      
      - name: Build and Push
        run: |
          # Get ECR URI from stack outputs
          ECR_URI=$(aws cloudformation describe-stacks \
            --stack-name bedrock-ai-streamlit-stack \
            --query "Stacks[0].Outputs[?OutputKey=='ECRRepositoryURI'].OutputValue" \
            --output text)
          
          # Build and push
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
          docker build -t app .
          docker tag app:latest $ECR_URI:latest
          docker push $ECR_URI:latest
          
          # Trigger deployment
          SERVICE_ARN=$(aws cloudformation describe-stacks \
            --stack-name bedrock-ai-streamlit-stack \
            --query "Stacks[0].Outputs[?OutputKey=='AppRunnerServiceArn'].OutputValue" \
            --output text)
          aws apprunner start-deployment --service-arn $SERVICE_ARN
```

## Advanced Configuration

### Custom Domain
Add to CloudFormation template:
```yaml
CustomDomain:
  Type: AWS::AppRunner::CustomDomainAssociation
  Properties:
    ServiceArn: !Ref AppRunnerService
    DomainName: your-domain.com
```

### VPC Integration
Add to App Runner service:
```yaml
NetworkConfiguration:
  EgressConfiguration:
    EgressType: VPC
    VpcConnectorArn: !Ref VPCConnector
```

### Environment-Specific Deployments
Use different parameter files:
- `parameters-dev.json`
- `parameters-staging.json`
- `parameters-prod.json`

## Troubleshooting

### Common Issues

#### Stack Creation Failed
```cmd
aws cloudformation describe-stack-events --stack-name bedrock-ai-streamlit-stack
```

#### App Runner Service Not Starting
- Check CloudWatch logs
- Verify environment variables
- Ensure Docker image is valid

#### Bedrock Access Denied
- Verify IAM role permissions
- Check Bedrock agent status
- Confirm agent ID and alias ID

### Rollback Strategy
CloudFormation automatically rolls back on failure:
- Failed resources are deleted
- Previous working state is restored
- Stack events show failure details

## Best Practices

### Infrastructure as Code
- **Version control** CloudFormation templates
- **Parameter files** for different environments
- **Stack naming** conventions
- **Resource tagging** for cost allocation

### Security
- **Regular updates** to base images
- **Vulnerability scanning** enabled
- **Secrets management** via Parameter Store
- **Network isolation** when needed

### Monitoring
- **CloudWatch alarms** for key metrics
- **Log aggregation** and analysis
- **Performance monitoring**
- **Cost tracking** and optimization

This CloudFormation approach provides a complete, repeatable, and maintainable deployment solution for your Bedrock AI application.