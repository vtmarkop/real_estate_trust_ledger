# backend/main.py
from app.core.db import engine
from sqlmodel import SQLModel
from app.models.user import User 
from app.models.property import Property
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
from fastapi.staticfiles import StaticFiles
import os

from app.api.routes import auth, properties, tickets, payments, dashboard, upload

app = FastAPI(
    title="Mesitis Trust API",
    description="Secure, resilient backend for Real Estate Dispute Resolution",
    version="2.0.0" # Version bump λόγω refactoring
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# --- SECURITY: Strict CORS Policy ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["set-cookie"], # Επιτρέπουμε στο React να "δει" ότι ήρθε cookie
)

# --- SECURITY: HTTP Security Headers ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# --- RESILIENCE: Redis Connection ---
redis_client = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_client = redis.from_url(redis_url, encoding="utf8", decode_responses=True)

    SQLModel.metadata.create_all(engine)
    print("Η βάση δεδομένων ελέγχθηκε και οι πίνακες δημιουργήθηκαν (αν έλειπαν).")

@app.on_event("shutdown")
async def shutdown_event():
    global redis_client
    if redis_client:
        await redis_client.close()

# --- ROUTES ΕΝΣΩΜΑΤΩΣΗ ---
app.include_router(auth.router, prefix="/api")
app.include_router(properties.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(upload.router, prefix="/api")


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "Mesitis API is secured and running!"}