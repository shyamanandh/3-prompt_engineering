# app/main.py

from fastapi import FastAPI
# FastAPI is our web framework — same as Component 01

from fastapi.middleware.cors import CORSMiddleware
# CORSMiddleware handles Cross Origin Resource Sharing
# This allows other apps (like a frontend) to call our API
# Without this, browsers block requests from different domains

from app.routes.prompts import router
# We import the router from our routes file
# The router contains all our API endpoints
# We have not written this file yet — we do it next

# Create the FastAPI application instance
# title and description show up in the auto-generated docs at /docs
app = FastAPI(
    title="Prompt Engineering API",
    description="Component 03 — 10 prompt engineering techniques exposed as API endpoints",
    version="1.0.0"
)

# Add CORS middleware to the app
# This runs on every request before it reaches your endpoints
app.add_middleware(
    CORSMiddleware,
    # allow_origins tells which domains can call this API
    # ["*"] means anyone can call it — fine for development
    # In production you would list specific domains
    allow_origins=["*"],
    allow_credentials=True,
    # allow_methods tells which HTTP methods are allowed
    allow_methods=["*"],
    # allow_headers tells which headers are allowed
    allow_headers=["*"],
)

# Register our router with the app
# prefix="/api/v1" means all our routes start with /api/v1
# Example: /api/v1/zero-shot, /api/v1/few-shot etc.
# tags=["Prompt Engineering"] groups them in the /docs page
app.include_router(
    router,
    prefix="/api/v1",
    tags=["Prompt Engineering"]
)


# Root endpoint — the welcome message
# When someone visits http://localhost:8000/ they see this
@app.get("/")
def root():
    return {
        "message": "Component 03 — Prompt Engineering API is running",
        "docs": "Visit /docs to see all available endpoints",
        "version": "1.0.0"
    }


# Health check endpoint
# Used to confirm the server is alive and responding
# Common in production systems for monitoring
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "component": "03",
        "name": "prompt-engineering"
    }