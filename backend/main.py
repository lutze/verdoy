import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from database import init_db, check_db_connection
from routers import auth, devices

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up LMS Core API...")
    try:
        # Initialize database
        init_db()
        print("Database initialized successfully")
        
        # Check database connection
        if check_db_connection():
            print("Database connection verified")
        else:
            print("Warning: Database connection failed")
    except Exception as e:
        print(f"Startup error: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down LMS Core API...")

# Create FastAPI app
app = FastAPI(
    title="LMS Core API",
    description="IoT SaaS API for ESP32 device management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(devices.router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if app.debug else "An unexpected error occurred"
        }
    )

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint."""
    db_status = "healthy" if check_db_connection() else "unhealthy"
    return {
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "LMS Core API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Database check endpoint (legacy)
@app.get("/db-check")
async def check_db():
    try:
        from database import engine
        with engine.connect() as connection:
            result = connection.execute("SELECT version();")
            version = result.fetchone()[0]
        return {"status": "success", "postgres_version": version}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Ollama check endpoint (legacy)
@app.post("/ollama-check")
async def ollama_check():
    # Define the payload for the external API
    payload = {
        "model": "llama3.1",
        "prompt": "What's a single word for a thing that holds a chemical solution? Respond with the answer in a single JSON object like {answer:''}",
        "stream": False
    }

    # Define the headers
    headers = {
        "Content-Type": "application/json"
    }

    # Make the POST request
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://localhost:11434/api/generate", json=payload, headers=headers)

        # Return the response from the external API
        return {"status": "success", "data": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}
