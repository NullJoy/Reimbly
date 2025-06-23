from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google.adk.adapters.fastapi_adapter import ADKFastAPIAdapter
from reimbly.root_agent import root_agent
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

app = FastAPI(
    title="Reimbly AI Agent",
    description="AI-powered reimbursement workflow system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ADK adapter with the root agent
adapter = ADKFastAPIAdapter(agent=root_agent)
adapter.attach_routes(app)

@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "message": "Reimbly AI Agent is running",
        "status": "healthy",
        "version": "1.0.0",
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "not-set")
    }

@app.get("/health")
def detailed_health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "service": "Reimbly AI Agent",
        "version": "1.0.0",
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "not-set"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "health": "/health",
            "root": "/",
            "chat": "/chat"
        }
    }

if __name__ == "__main__":
    # Get port from environment variable or default to 8080
    port = int(os.getenv("PORT", 8080))
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Set to True for development
        log_level="info"
    ) 