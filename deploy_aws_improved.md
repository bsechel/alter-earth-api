# Secure AWS FastAPI Deployment Guide

This guide provides a production-ready deployment approach that addresses security and reliability concerns.

## Option 1: EC2 with Production Setup (Recommended for learning)

### 1. Launch EC2 Instance
```bash
# Launch Ubuntu 22.04 LTS
# Instance type: t3.micro (better than t2.micro)
# Key pair: Create new key pair
# Security groups: Custom (see below)
```

### 2. Security Group Configuration
```
SSH (22): Your IP only (not 0.0.0.0/0)
HTTP (80): 0.0.0.0/0
HTTPS (443): 0.0.0.0/0
```

### 3. Initial Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git

# Create app user (don't run as root)
sudo adduser --system --group --disabled-password fastapi
sudo mkdir -p /opt/fastapi
sudo chown fastapi:fastapi /opt/fastapi
```

### 4. Deploy Application
```bash
# Clone your repo
sudo -u fastapi git clone https://github.com/yourusername/your-repo.git /opt/fastapi/app

# Set up virtual environment
sudo -u fastapi python3 -m venv /opt/fastapi/venv
sudo -u fastapi /opt/fastapi/venv/bin/pip install -r /opt/fastapi/app/requirements.txt

# Create environment file
sudo -u fastapi tee /opt/fastapi/.env << EOF
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
ENVIRONMENT=production
EOF
```

### 5. Create Systemd Service
```bash
sudo tee /etc/systemd/system/fastapi.service << EOF
[Unit]
Description=FastAPI application
After=network.target

[Service]
Type=simple
User=fastapi
Group=fastapi
WorkingDirectory=/opt/fastapi/app
Environment=PATH=/opt/fastapi/venv/bin
EnvironmentFile=/opt/fastapi/.env
ExecStart=/opt/fastapi/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi
```

### 6. Configure Nginx with SSL
```bash
# Create Nginx config
sudo tee /etc/nginx/sites-available/fastapi << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate (replace your-domain.com)
sudo certbot --nginx -d your-domain.com
```

## Option 2: AWS Application Load Balancer + ECS (Production-ready)

### 1. Create ECS Cluster
```bash
# Use AWS CLI or Console
aws ecs create-cluster --cluster-name fastapi-cluster
```

### 2. Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Push to ECR
```bash
# Create repository
aws ecr create-repository --repository-name fastapi-app

# Build and push
docker build -t fastapi-app .
docker tag fastapi-app:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/fastapi-app:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/fastapi-app:latest
```

### 4. Create ECS Task Definition
```json
{
  "family": "fastapi-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "fastapi-container",
      "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/fastapi-app:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "your_database_url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fastapi",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Option 3: AWS Lambda + API Gateway (Serverless)

### 1. Install Mangum
```bash
pip install mangum
```

### 2. Create Lambda Handler
```python
# lambda_handler.py
from mangum import Mangum
from main import app

handler = Mangum(app)
```

### 3. Deploy with AWS SAM
```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  FastAPIFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: lambda_handler.handler
      Runtime: python3.11
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

## Monitoring and Logging

### CloudWatch Integration
```python
# Add to your FastAPI app
import logging
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.3f}s")
    return response
```

## Security Checklist

- [ ] SSH access restricted to your IP
- [ ] SSL certificate installed
- [ ] Application runs as non-root user
- [ ] Environment variables for secrets
- [ ] Database credentials in AWS Secrets Manager
- [ ] WAF enabled (for production)
- [ ] Backup strategy implemented
- [ ] Monitoring and alerting configured

## Cost Considerations

- **EC2**: ~$8-15/month for t3.micro
- **ECS Fargate**: ~$15-30/month depending on usage
- **Lambda**: Pay per request (often cheapest for low traffic)

## Recommendation

For your use case, I recommend **Option 1 (EC2)** to start with, as it's educational and gives you full control. Once comfortable, consider moving to **Option 2 (ECS)** for better scalability and management.