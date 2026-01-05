from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat

app = FastAPI(
    title="Visual Intelligence Chatbot API",
    description="12-Layer Conversational Image Recognition System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/")
async def root():
    return {
        "message": "Visual Intelligence Chatbot API",
        "docs": "/docs",
        "health": "/api/health"
    }
