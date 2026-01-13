from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import auth

app = FastAPI(title="SGT-H API", version="0.1.0")

# Configure CORS
origins = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to SGT-H API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Include routers
app.include_router(auth.router)
