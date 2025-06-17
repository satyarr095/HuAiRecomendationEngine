# AI Recommendation Engine - Docker & AWS Deployment Guide

This guide covers how to dockerize and deploy the AI Recommendation Engine to AWS using ECS (Elastic Container Service).

## 🐳 Local Docker Development

### Prerequisites
- Docker and Docker Compose installed
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Quick Start

1. **Build and run the entire application:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

3. **Development mode with hot reloading:**
   ```bash
   # Backend only
   docker-compose up backend
   
   # Frontend only  
   docker-compose up frontend
   ```

### Individual Service Commands

**Backend:**
```bash
cd AI_Engine
docker build -t ai-backend .
docker run -p 8000:8000 ai-backend
```

**Frontend:**
```bash
cd client
docker build -t ai-frontend .
docker run -p 80:80 ai-frontend
```

## ☁️ AWS Deployment

### Prerequisites
- AWS CLI configured (`aws configure`)
- Docker installed
- Appropriate AWS permissions (ECS, ECR, EC2, CloudWatch, IAM)

### 1. Quick Deployment
```bash
# Make the script executable
chmod +x aws/deploy.sh

# Deploy to AWS
./aws/deploy.sh
```

### 2. Manual Deployment Steps

#### Step 1: Create ECR Repositories
```bash
aws ecr create-repository --repository-name ai-backend --region us-east-1
aws ecr create-repository --repository-name ai-frontend --region us-east-1
```

#### Step 2: Build and Push Images
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
docker build -t ai-backend ./AI_Engine
docker tag ai-backend:latest {ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/ai-backend:latest
docker push {ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/ai-backend:latest

# Build and push frontend
docker build -t ai-frontend ./client
docker tag ai-frontend:latest {ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/ai-frontend:latest
docker push {ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/ai-frontend:latest
```

#### Step 3: Create ECS Cluster
```bash
aws ecs create-cluster --cluster-name ai-recommendation-cluster
```

#### Step 4: Register Task Definition
```bash
# Update the task definition with your account ID and region
sed "s/{ACCOUNT_ID}/123456789012/g; s/{REGION}/us-east-1/g" aws/ecs-task-definition.json > task-definition.json
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### Step 5: Create ECS Service
```bash
aws ecs create-service \
  --cluster ai-recommendation-cluster \
  --service-name ai-recommendation-service \
  --task-definition ai-recommendation-engine \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

### Environment Variables

Set the following environment variables before deployment:
```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
```

## 🔧 Configuration

### Backend Configuration
- Port: 8000
- Health check: `/health`
- CORS enabled for frontend domains

### Frontend Configuration
- Port: 80 (Nginx)
- API proxy to backend at `/api/*`
- Static file serving with gzip compression

### Resource Requirements
- **CPU**: 1 vCPU (1024 units)
- **Memory**: 2GB (2048 MB)
- **Storage**: Ephemeral (container storage)

## 📊 Monitoring

### CloudWatch Logs
- Log Group: `/ecs/ai-recommendation-engine`
- Backend logs: `backend` stream prefix
- Frontend logs: `frontend` stream prefix

### Health Checks
- Backend: `curl -f http://localhost:8000/health`
- Frontend: `curl -f http://localhost/health`

## 🔒 Security

### Security Groups
The deployment automatically creates a security group with:
- Port 80 (HTTP) - Frontend access
- Port 8000 (HTTP) - Backend API access

### IAM Roles Required
1. **ECS Task Execution Role** (`ecsTaskExecutionRole`)
   - `AmazonECSTaskExecutionRolePolicy`
   
2. **ECS Task Role** (`ecsTaskRole`)
   - Custom policies for your application needs

## 💰 Cost Optimization

### Fargate Pricing (us-east-1)
- CPU: $0.04048 per vCPU per hour
- Memory: $0.004445 per GB per hour
- **Estimated cost**: ~$35/month for 24/7 operation

### Cost Saving Tips
1. Use scheduled scaling to reduce instances during low-traffic periods
2. Consider EC2 launch type for long-running workloads
3. Implement auto-scaling based on CPU/memory utilization

## 🚀 CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to AWS ECS
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
      - name: Deploy to AWS
        run: ./aws/deploy.sh
```

## 🔍 Troubleshooting

### Common Issues

1. **Task fails to start**
   - Check CloudWatch logs
   - Verify ECR image availability
   - Check IAM permissions

2. **Service unreachable**
   - Verify security group rules
   - Check target group health
   - Confirm public IP assignment

3. **High memory usage**
   - Monitor CloudWatch metrics
   - Consider increasing memory allocation
   - Optimize application code

### Debug Commands
```bash
# Check service status
aws ecs describe-services --cluster ai-recommendation-cluster --services ai-recommendation-service

# View task details
aws ecs describe-tasks --cluster ai-recommendation-cluster --tasks {TASK_ARN}

# Check logs
aws logs get-log-events --log-group-name "/ecs/ai-recommendation-engine" --log-stream-name {STREAM_NAME}
```

## 🧹 Cleanup

To remove all AWS resources:
```bash
# Delete ECS service
aws ecs update-service --cluster ai-recommendation-cluster --service ai-recommendation-service --desired-count 0
aws ecs delete-service --cluster ai-recommendation-cluster --service ai-recommendation-service

# Delete ECS cluster
aws ecs delete-cluster --cluster ai-recommendation-cluster

# Delete ECR repositories
aws ecr delete-repository --repository-name ai-backend --force
aws ecr delete-repository --repository-name ai-frontend --force

# Delete CloudWatch log group
aws logs delete-log-group --log-group-name "/ecs/ai-recommendation-engine"
```

## 📞 Support

For issues or questions:
1. Check CloudWatch logs first
2. Review this documentation
3. Create an issue in the project repository

---

**Happy Deploying! 🎉** 