#!/bin/bash

# AWS EC2 Deployment Script
# This script helps deploy the application to AWS EC2

echo "🚀 Starting deployment to AWS EC2..."

# Update system
sudo yum update -y

# Install Docker
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Node.js
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# Install Python 3.9+
sudo yum install -y python3 python3-pip

echo "✅ Dependencies installed"
echo "📝 Next steps:"
echo "1. Clone your repository"
echo "2. Set up environment variables"
echo "3. Run: docker-compose up -d"

