# Reimbly AI Agent - Deployment Guide

This guide covers how to deploy the Reimbly AI Agent using FastAPI, Docker, and Google Cloud Platform.

## 🚀 Quick Start

### Environment Setup

1. **Create a `.env` file in the project root:**
   ```bash
   # Google Cloud Platform Configuration
   GOOGLE_CLOUD_PROJECT=your-actual-gcp-project-id
   
   # Application Configuration
   PORT=8080
   REGION=us-central1
   SERVICE_NAME=reimbly-ai-agent
   
   # Optional: Environment-specific settings
   ENVIRONMENT=development
   LOG_LEVEL=info
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run locally:**
   ```bash
   python main.py
   ```

4. **Access the API:**
   - Health check: http://localhost:8080/health
   - API docs: http://localhost:8080/docs
   - Chat endpoint: http://localhost:8080/chat

### Docker Local

1. **Build and run with Docker:**
   ```bash
   docker build -t reimbly-ai-agent .
   docker run -p 8080:8080 --env-file .env reimbly-ai-agent
   ```

2. **Or use Docker Compose:**
   ```bash
   docker-compose up --build
   ```

## ☁️ Google Cloud Platform Deployment

### Prerequisites

1. **Install Google Cloud SDK:**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate with GCP:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable required APIs:**
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

### Option 1: Manual Deployment

1. **Set up your `.env` file with your GCP project ID:**
   ```bash
   GOOGLE_CLOUD_PROJECT=your-actual-gcp-project-id
   REGION=us-central1
   SERVICE_NAME=reimbly-ai-agent
   ```

2. **Run the deployment script:**
   ```bash
   ./deploy-gcp.sh
   ```

   The script will automatically:
   - Load environment variables from `.env`
   - Use `GOOGLE_CLOUD_PROJECT` as the project ID
   - Deploy to the specified region
   - Show you the service URL

### Option 2: Cloud Build (CI/CD)

1. **Set up Cloud Build trigger:**
   ```bash
   gcloud builds triggers create github \
     --repo-name=your-repo-name \
     --repo-owner=your-github-username \
     --branch-pattern="^main$" \
     --build-config=cloudbuild.yaml
   ```

2. **Or trigger manually:**
   ```bash
   gcloud builds submit --config cloudbuild.yaml .
   ```

### Option 3: Terraform (Infrastructure as Code)

Create a `terraform` directory with the following files:

```hcl
# main.tf
resource "google_cloud_run_service" "reimbly" {
  name     = "reimbly-ai-agent"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/reimbly-ai-agent:latest"
        ports {
          container_port = 8080
        }
        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }
    }
  }
}

# variables.tf
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "your-gcp-project-id"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID | - | ✅ Yes |
| `PORT` | Server port | `8080` | No |
| `REGION` | GCP Region | `us-central1` | No |
| `SERVICE_NAME` | Cloud Run service name | `reimbly-ai-agent` | No |
| `ENVIRONMENT` | Environment name | `development` | No |

### GCP Service Configuration

- **Memory:** 2Gi
- **CPU:** 2 cores
- **Max Instances:** 10
- **Timeout:** 300 seconds
- **Concurrency:** 80 requests per instance

## 📊 Monitoring & Health Checks

### Health Check Endpoints

- **Basic health:** `GET /`
- **Detailed health:** `GET /health`
- **API documentation:** `GET /docs`

The health endpoints now include:
- Project ID from environment
- Environment name
- Service status

### Monitoring Setup

1. **Enable Cloud Monitoring:**
   ```bash
   gcloud services enable monitoring.googleapis.com
   ```

2. **Set up alerts for:**
   - Response time > 5 seconds
   - Error rate > 5%
   - Memory usage > 80%

## 🔒 Security

### Production Security Checklist

- [ ] Configure CORS properly (update `allow_origins` in `main.py`)
- [ ] Set up authentication/authorization
- [ ] Use HTTPS only
- [ ] Configure proper IAM roles
- [ ] Set up VPC if needed
- [ ] Enable audit logging
- [ ] Secure your `.env` file (add to `.gitignore`)

### IAM Roles Required

```bash
# For deployment
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

## 🚨 Troubleshooting

### Common Issues

1. **Project ID not set:**
   ```bash
   # Check your .env file
   cat .env
   # Make sure GOOGLE_CLOUD_PROJECT is set correctly
   ```

2. **Port already in use:**
   ```bash
   # Check what's using port 8080
   lsof -i :8080
   # Kill the process or change port in .env
   ```

3. **Docker build fails:**
   ```bash
   # Clear Docker cache
   docker system prune -a
   # Rebuild
   docker build --no-cache -t reimbly-ai-agent .
   ```

4. **GCP authentication issues:**
   ```bash
   # Re-authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

5. **Cloud Run deployment fails:**
   ```bash
   # Check logs
   gcloud run services logs read reimbly-ai-agent --region=us-central1
   ```

### Logs and Debugging

```bash
# View Cloud Run logs
gcloud run services logs tail reimbly-ai-agent --region=us-central1

# View build logs
gcloud builds log BUILD_ID

# Test locally with Docker
docker run -p 8080:8080 --env-file .env reimbly-ai-agent
curl http://localhost:8080/health
```

## 📈 Scaling

### Auto-scaling Configuration

Cloud Run automatically scales based on:
- Number of concurrent requests
- CPU utilization
- Memory usage

### Manual Scaling

```bash
# Update service configuration
gcloud run services update reimbly-ai-agent \
  --region=us-central1 \
  --max-instances=20 \
  --concurrency=100
```

## 🔄 Updates and Rollbacks

### Rolling Updates

```bash
# Deploy new version
./deploy-gcp.sh

# Rollback to previous version
gcloud run services update-traffic reimbly-ai-agent \
  --to-revisions=reimbly-ai-agent-00001-abc=100 \
  --region=us-central1
```

### Blue-Green Deployment

1. Deploy new version with different service name
2. Test the new version
3. Switch traffic when ready
4. Clean up old version

## 📞 Support

For deployment issues:
1. Check the logs: `gcloud run services logs read`
2. Verify configuration in `main.py` and `Dockerfile`
3. Ensure your `.env` file is properly configured
4. Test locally first
5. Check GCP quotas and billing

---

**Happy Deploying! 🚀** 