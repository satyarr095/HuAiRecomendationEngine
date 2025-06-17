#!/usr/bin/env python3
"""
AWS Lambda deployment script for AI Recommendation Engine
"""
import json
import boto3
import zipfile
import os
import shutil
from pathlib import Path

def create_lambda_package():
    """Create a deployment package for Lambda"""
    print("📦 Creating Lambda deployment package...")
    
    # Create a temporary directory for the package
    package_dir = "lambda_package"
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Copy essential files from AI_Engine
    files_to_copy = [
        "app.py",
        "ai_recommendation_engine.py", 
        "intelligent_search_engine.py",
        "performance_optimized_engine.py"
    ]
    
    for file in files_to_copy:
        if os.path.exists(f"AI_Engine/{file}"):
            shutil.copy(f"AI_Engine/{file}", package_dir)
    
    # Create a simple Lambda handler
    lambda_handler = '''
import json
import asyncio
from app import app
from fastapi import Request
from mangum import Mangum

# Create the Mangum adapter for AWS Lambda
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """AWS Lambda handler function"""
    try:
        return handler(event, context)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
'''
    
    with open(f"{package_dir}/lambda_function.py", "w") as f:
        f.write(lambda_handler)
    
    # Create a simplified requirements for Lambda
    lambda_requirements = '''
fastapi
mangum
pydantic
requests
beautifulsoup4
aiohttp
'''
    
    with open(f"{package_dir}/requirements.txt", "w") as f:
        f.write(lambda_requirements)
    
    print("✅ Lambda package created")
    return package_dir

def deploy_lambda():
    """Deploy to AWS Lambda"""
    print("🚀 Deploying to AWS Lambda...")
    
    # Create the package
    package_dir = create_lambda_package()
    
    # Create ZIP file
    zip_filename = "ai-recommendation-lambda.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    # Create Lambda function
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    function_name = "ai-recommendation-engine"
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=open(zip_filename, 'rb').read()
        )
        print(f"✅ Updated Lambda function: {function_name}")
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        iam = boto3.client('iam')
        
        # Create execution role if it doesn't exist
        role_name = "lambda-execution-role"
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            role = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy)
            )
            role_arn = role['Role']['Arn']
            
            # Attach basic execution policy
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
        except iam.exceptions.EntityAlreadyExistsException:
            role_arn = f"arn:aws:iam::890742594683:role/{role_name}"
        
        # Create Lambda function
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': open(zip_filename, 'rb').read()},
            Timeout=30,
            MemorySize=512,
            Environment={
                'Variables': {
                    'PYTHONPATH': '/var/task'
                }
            }
        )
        print(f"✅ Created Lambda function: {function_name}")
    
    # Create API Gateway
    apigateway = boto3.client('apigateway', region_name='us-east-1')
    
    try:
        # Create REST API
        api_response = apigateway.create_rest_api(
            name='ai-recommendation-api',
            description='AI Recommendation Engine API'
        )
        api_id = api_response['id']
        
        # Get the root resource
        resources = apigateway.get_resources(restApiId=api_id)
        root_resource_id = resources['items'][0]['id']
        
        # Create proxy resource
        proxy_resource = apigateway.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart='{proxy+}'
        )
        
        # Create ANY method
        apigateway.put_method(
            restApiId=api_id,
            resourceId=proxy_resource['id'],
            httpMethod='ANY',
            authorizationType='NONE'
        )
        
        # Set up Lambda integration
        lambda_arn = response['FunctionArn']
        integration_uri = f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=proxy_resource['id'],
            httpMethod='ANY',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=integration_uri
        )
        
        # Deploy API
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='prod'
        )
        
        # Add Lambda permission
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId='api-gateway-invoke',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f"arn:aws:execute-api:us-east-1:890742594683:{api_id}/*/*"
        )
        
        api_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod"
        print(f"🎉 API deployed successfully!")
        print(f"🌐 Your API URL: {api_url}")
        
    except Exception as e:
        print(f"⚠️ API Gateway setup failed: {e}")
        # Still provide Lambda function ARN
        print(f"📋 Lambda function ARN: {response['FunctionArn']}")
    
    # Cleanup
    shutil.rmtree(package_dir)
    os.remove(zip_filename)
    
    return api_url if 'api_url' in locals() else None

if __name__ == "__main__":
    deploy_lambda() 