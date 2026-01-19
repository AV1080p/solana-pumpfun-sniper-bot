# AWS Deployment Guide

This directory contains AWS deployment configurations for the Tourist App.

## Deployment Options

### Option 1: Docker Compose (Recommended for Development)

1. Ensure Docker and Docker Compose are installed
2. Copy environment variables:
   ```bash
   cp ../backend/env.example ../backend/.env
   cp ../frontend/env.example ../frontend/.env.local
   ```
3. Update the `.env` files with your actual credentials
4. Run:
   ```bash
   docker-compose up -d
   ```

### Option 2: EC2 Deployment

1. Launch an EC2 instance (Ubuntu 20.04 or Amazon Linux 2)
2. SSH into the instance
3. Run the deployment script:
   ```bash
   chmod +x ec2-deploy.sh
   ./ec2-deploy.sh
   ```
4. Clone your repository
5. Set up environment variables
6. Run `docker-compose up -d`

### Option 3: AWS ECS/Fargate

1. Build and push Docker images to ECR
2. Create ECS task definitions
3. Deploy using ECS service

### Option 4: AWS Lambda (Serverless)

For serverless deployment, you would need to:
1. Convert FastAPI to use Mangum adapter
2. Package frontend as static files in S3
3. Use API Gateway for backend
4. Use RDS for database

## Environment Variables

Make sure to set all required environment variables in your deployment environment.

## Database Setup

For production, use AWS RDS PostgreSQL:
- Create RDS instance
- Update DATABASE_URL in backend/.env
- Run migrations: `alembic upgrade head`

## Security Groups

Ensure your security groups allow:
- Port 3000 (Frontend)
- Port 8000 (Backend API)
- Port 5432 (PostgreSQL, if not using RDS)

