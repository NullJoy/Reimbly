#!/bin/bash

# GCP Deployment Script for Reimbly AI Agent
# This script deploys the application to Google Cloud Run

set -e

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Configuration - prioritize environment variables, then .env, then defaults
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-${PROJECT_ID:-"your-gcp-project-id"}}
REGION=${REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"reimbly-ai-agent"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting GCP deployment for Reimbly AI Agent${NC}"
echo -e "${YELLOW}📋 Using project ID: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}📋 Using region: ${REGION}${NC}"
echo -e "${YELLOW}📋 Using service name: ${SERVICE_NAME}${NC}"

# Check if project ID is set
if [ "$PROJECT_ID" = "your-gcp-project-id" ]; then
    echo -e "${RED}❌ Please set GOOGLE_CLOUD_PROJECT in your .env file or environment variable${NC}"
    echo -e "${YELLOW}💡 Create a .env file with: GOOGLE_CLOUD_PROJECT=your-actual-project-id${NC}"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}📋 Setting GCP project to: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required GCP APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Configure docker to use gcloud as a credential helper
echo -e "${YELLOW}🔐 Configuring Docker authentication...${NC}"
gcloud auth configure-docker

# Build and push the Docker image
echo -e "${YELLOW}🏗️  Building and pushing Docker image...${NC}"
docker build -t ${IMAGE_NAME} .
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars "PORT=8080"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}📊 Health check: ${SERVICE_URL}/health${NC}"
echo -e "${GREEN}💬 Chat endpoint: ${SERVICE_URL}/chat${NC}"

# Optional: Set up custom domain (uncomment and modify as needed)
# echo -e "${YELLOW}🌍 Setting up custom domain...${NC}"
# gcloud run domain-mappings create \
#     --service ${SERVICE_NAME} \
#     --domain your-domain.com \
#     --region ${REGION}

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}" 