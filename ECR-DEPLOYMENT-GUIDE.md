# AWS App Runner Deployment Guide Using ECR

This guide provides step-by-step instructions to deploy your Bedrock AI Streamlit application to AWS App Runner using Amazon Elastic Container Registry (ECR).

## Prerequisites

- **AWS CLI** installed and configured with appropriate permissions
- **Docker Desktop** installed and running
- **AWS Account** with the following services enabled:
  - Amazon Bedrock
  - Amazon ECR
  - AWS App Runner
  - AWS IAM

## Architecture Overview

```
Local Development → Docker Build → ECR Push → App Runner Deploy
```

## Step 1: Verify Prerequisites

### 1.1 Check AWS CLI Configuration
```cmd
aws sts get-caller-identity
```
This should return your AWS account details.

### 1.2 Check Docker Installation
```cmd
docker --version
```

### 1.3 Verify AWS Permissions
Ensure your AWS user/role has permissions for:
- ECR (create repository, push images)
- App Runner (create service)
- IAM (create roles, attach policies)
- Bedrock (invoke agent)

## Step 2: Prepare Your Application

### 2.1 Update Environment Configuration
Edit your `.env` file with your specific values:
```env
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1

# Bedrock Agent Configuration  
BEDROCK_AGENT_ID=your_agent_id_here
BEDROCK_AGENT_ALIAS_ID=your_agent_alias_id_here

# UI Configuration
BEDROCK_AGENT_TEST_UI_TITLE=Your App Title
BEDROCK_AGENT_TEST_UI_ICON=🤖

# Logging
LOG_LEVEL=INFO
```

### 2.2 Test Application Locally (Optional)
```cmd
pip install -r requirements.txt
streamlit run app.py --server.port=8080 --server.address=localhost
```
Visit `http://localhost:8080` to verify the app works.

## Step 3: Create IAM Roles

### 3.1 Run IAM Role Creation Script
```cmd
create-iam-roles.bat
```

### 3.2 Save the Role ARNs
The script will output two ARNs:
- **Instance Role ARN**: For Bedrock access
- **Access Role ARN**: For ECR access

**Example Output:**
```
Instance Role ARN: arn:aws:iam::123456789012:role/AppRunnerBedrockInstanceRole
Access Role ARN: arn:aws:iam::123456789012:role/AppRunnerECRAccessRole
```

## Step 4: Build and Push Docker Image to ECR

### 4.1 Run Build and Deploy Script
```cmd
build-and-deploy.bat
```

This script will:
1. Create ECR repository
2. Login to ECR
3. Build Docker image
4. Tag image for ECR
5. Push image to ECR

### 4.2 Verify Image in ECR
1. Go to **AWS Console → ECR**
2. Find your repository: `bedrock-ai-streamlit`
3. Verify the image with tag `latest` exists

## Step 5: Create App Runner Service

### 5.1 Navigate to App Runner Console
1. Open **AWS Console**
2. Go to **App Runner** service
3. Click **"Create service"**

### 5.2 Configure Source
1. **Source type**: Container registry
2. **Provider**: Amazon ECR
3. **Container image URI**: Use the URI from Step 4 output
   ```
   123456789012.dkr.ecr.us-east-1.amazonaws.com/bedrock-ai-streamlit:latest
   ```
4. **Deployment trigger**: Manual
5. **ECR access role**: Select `AppRunnerECRAccessRole`

### 5.3 Configure Service Settings
1. **Service name**: `bedrock-ai-streamlit-service`
2. **Virtual CPU**: 1 vCPU
3. **Memory**: 2 GB
4. **Environment variables**:
   ```
   BEDROCK_AGENT_ID=your_agent_id
   BEDROCK_AGENT_ALIAS_ID=your_agent_alias_id
   AWS_DEFAULT_REGION=us-east-1
   BEDROCK_AGENT_TEST_UI_TITLE=Your App Title
   BEDROCK_AGENT_TEST_UI_ICON=🤖
   LOG_LEVEL=INFO
   ```

### 5.4 Configure Security
1. **Instance role**: Select `AppRunnerBedrockInstanceRole`
2. **Network**: Default VPC (or custom if needed)

### 5.5 Configure Health Check
1. **Health check path**: `/`
2. **Health check protocol**: HTTP
3. **Health check interval**: 20 seconds
4. **Health check timeout**: 10 seconds
5. **Healthy threshold**: 3
6. **Unhealthy threshold**: 5

### 5.6 Configure Auto Scaling (Optional)
1. **Auto scaling**: Enabled
2. **Max concurrency**: 100 (requests per instance)
3. **Max size**: 10 instances
4. **Min size**: 1 instance

## Step 6: Deploy and Monitor

### 6.1 Create Service
1. Review all configurations
2. Click **"Create & deploy"**
3. Wait for deployment (typically 5-10 minutes)

### 6.2 Monitor Deployment
1. **Service status**: Should show "Running"
2. **Service URL**: Will be provided once deployment completes
3. **Logs**: Available in CloudWatch Logs

### 6.3 Test Your Application
1. Click on the **Service URL**
2. Test the chat functionality
3. Verify Bedrock agent responses

## Step 7: Configure Custom Domain (Optional)

### 7.1 Add Custom Domain
1. In App Runner service console
2. Go to **"Custom domains"** tab
3. Click **"Link domain"**
4. Enter your domain name
5. Configure DNS records as instructed

### 7.2 SSL Certificate
App Runner automatically provides SSL certificates for custom domains.

## Step 8: Set Up CI/CD (Optional)

### 8.1 Automated Deployments
Create a GitHub Actions workflow:

```yaml
name: Deploy to App Runner
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push to ECR
        run: |
          aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
          docker build -t bedrock-ai-streamlit .
          docker tag bedrock-ai-streamlit:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/bedrock-ai-streamlit:latest
          docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/bedrock-ai-streamlit:latest
```

## Troubleshooting

### Common Issues and Solutions

#### 1. ECR Login Failed
```cmd
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [ACCOUNT-ID].dkr.ecr.us-east-1.amazonaws.com
```

#### 2. Docker Build Failed
- Check Dockerfile syntax
- Ensure all required files are present
- Verify Docker is running

#### 3. App Runner Service Failed to Start
- Check CloudWatch Logs
- Verify environment variables
- Ensure IAM roles have correct permissions

#### 4. Bedrock Agent Not Responding
- Verify agent ID and alias ID
- Check IAM permissions for Bedrock
- Ensure agent is deployed and active

#### 5. Health Check Failing
- Verify port 8080 is exposed
- Check if Streamlit is binding to 0.0.0.0
- Review health check path

### Monitoring and Logging

#### CloudWatch Logs
- **Log Group**: `/aws/apprunner/[service-name]/application`
- **Log Stream**: Contains application logs

#### CloudWatch Metrics
- **CPU Utilization**
- **Memory Utilization**
- **Request Count**
- **Response Time**

## Cost Optimization

### 1. Right-sizing Resources
- Start with 1 vCPU, 2 GB RAM
- Monitor usage and adjust

### 2. Auto Scaling Configuration
- Set appropriate min/max instances
- Configure based on expected traffic

### 3. Pause When Idle
- Enable automatic pausing for development environments
- Production environments should stay active

## Security Best Practices

### 1. IAM Roles
- Use least privilege principle
- Regularly review and audit permissions

### 2. Environment Variables
- Never hardcode secrets in code
- Use AWS Systems Manager Parameter Store for sensitive data

### 3. Network Security
- Use VPC if additional network isolation needed
- Configure security groups appropriately

### 4. Container Security
- Regularly update base images
- Scan images for vulnerabilities

## Maintenance

### 1. Regular Updates
- Update dependencies in requirements.txt
- Rebuild and redeploy images

### 2. Monitoring
- Set up CloudWatch alarms
- Monitor application performance

### 3. Backup
- ECR images are automatically backed up
- Consider backing up configuration

## Conclusion

Your Bedrock AI Streamlit application is now deployed on AWS App Runner using ECR. The service provides:

- **Automatic scaling** based on traffic
- **Load balancing** across instances  
- **Health monitoring** and automatic recovery
- **SSL termination** and custom domains
- **Integration** with AWS services

For support and updates, refer to the AWS App Runner documentation and Bedrock agent guides.