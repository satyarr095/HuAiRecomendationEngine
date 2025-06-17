#!/bin/bash

# AWS Deployment Script for AI Recommendation Engine
set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
CLUSTER_NAME="ai-recommendation-cluster"
SERVICE_NAME="ai-recommendation-service"
TASK_FAMILY="ai-recommendation-engine"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting AWS deployment for AI Recommendation Engine${NC}"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not configured. Please run 'aws configure'${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Using AWS Account: ${AWS_ACCOUNT_ID}${NC}"
echo -e "${YELLOW}🌍 Using AWS Region: ${AWS_REGION}${NC}"

# Step 1: Create ECR repositories if they don't exist
echo -e "${GREEN}📦 Creating ECR repositories...${NC}"

for repo in ai-backend ai-frontend; do
    if ! aws ecr describe-repositories --repository-names $repo --region $AWS_REGION &> /dev/null; then
        echo "Creating ECR repository: $repo"
        aws ecr create-repository --repository-name $repo --region $AWS_REGION
    else
        echo "ECR repository $repo already exists"
    fi
done

# Step 2: Login to ECR
echo -e "${GREEN}🔐 Logging into ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Step 3: Build and push Docker images
echo -e "${GREEN}🏗️ Building and pushing Docker images...${NC}"

# Build and push backend
echo "Building backend image..."
docker build -t ai-backend ./AI_Engine
docker tag ai-backend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ai-backend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ai-backend:latest

# Build and push frontend
echo "Building frontend image..."
docker build -t ai-frontend ./client
docker tag ai-frontend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ai-frontend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ai-frontend:latest

# Step 4: Create CloudWatch Log Group
echo -e "${GREEN}📝 Creating CloudWatch Log Group...${NC}"
if ! aws logs describe-log-groups --log-group-name-prefix "/ecs/ai-recommendation-engine" --region $AWS_REGION | grep -q "/ecs/ai-recommendation-engine"; then
    aws logs create-log-group --log-group-name "/ecs/ai-recommendation-engine" --region $AWS_REGION
    echo "Created CloudWatch log group"
else
    echo "CloudWatch log group already exists"
fi

# Step 5: Create ECS Cluster
echo -e "${GREEN}🎯 Creating ECS Cluster...${NC}"
if ! aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION | grep -q "ACTIVE"; then
    aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION
    echo "Created ECS cluster: $CLUSTER_NAME"
else
    echo "ECS cluster $CLUSTER_NAME already exists"
fi

# Step 6: Register Task Definition
echo -e "${GREEN}📋 Registering ECS Task Definition...${NC}"
# Replace placeholders in task definition
sed "s/{ACCOUNT_ID}/$AWS_ACCOUNT_ID/g; s/{REGION}/$AWS_REGION/g" aws/ecs-task-definition.json > /tmp/task-definition.json

aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-definition.json \
    --region $AWS_REGION

# Step 7: Create or Update ECS Service
echo -e "${GREEN}🚀 Creating/Updating ECS Service...${NC}"

# Check if service exists
if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION | grep -q "ACTIVE"; then
    echo "Updating existing service..."
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --region $AWS_REGION
else
    echo "Creating new service..."
    # Get default VPC and subnets
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $AWS_REGION)
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text --region $AWS_REGION)
    
    # Create security group if it doesn't exist
    SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=ai-recommendation-sg" --query "SecurityGroups[0].GroupId" --output text --region $AWS_REGION 2>/dev/null || echo "None")
    
    if [ "$SG_ID" = "None" ]; then
        echo "Creating security group..."
        SG_ID=$(aws ec2 create-security-group \
            --group-name ai-recommendation-sg \
            --description "Security group for AI Recommendation Engine" \
            --vpc-id $VPC_ID \
            --region $AWS_REGION \
            --query "GroupId" --output text)
        
        # Add rules
        aws ec2 authorize-security-group-ingress \
            --group-id $SG_ID \
            --protocol tcp \
            --port 80 \
            --cidr 0.0.0.0/0 \
            --region $AWS_REGION
        
        aws ec2 authorize-security-group-ingress \
            --group-id $SG_ID \
            --protocol tcp \
            --port 8000 \
            --cidr 0.0.0.0/0 \
            --region $AWS_REGION
    fi
    
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
        --region $AWS_REGION
fi

# Step 8: Wait for service to be stable
echo -e "${GREEN}⏳ Waiting for service to stabilize...${NC}"
aws ecs wait services-stable --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION

# Step 9: Get service endpoint
echo -e "${GREEN}🎉 Deployment completed!${NC}"
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --query "taskArns[0]" --output text --region $AWS_REGION)
PUBLIC_IP=$(aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks $TASK_ARN --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text --region $AWS_REGION | xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} --query "NetworkInterfaces[0].Association.PublicIp" --output text --region $AWS_REGION)

echo -e "${GREEN}✅ Your AI Recommendation Engine is now live!${NC}"
echo -e "${YELLOW}🌐 Frontend URL: http://$PUBLIC_IP${NC}"
echo -e "${YELLOW}🔗 Backend API: http://$PUBLIC_IP:8000${NC}"
echo -e "${YELLOW}📚 API Docs: http://$PUBLIC_IP:8000/docs${NC}"

# Cleanup
rm -f /tmp/task-definition.json

echo -e "${GREEN}🎯 Deployment script completed successfully!${NC}" 