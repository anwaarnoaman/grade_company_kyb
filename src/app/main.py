from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.logging import setup_logging,get_logger
from app.core.config import settings
 

setup_logging() 
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")

    yield  # app is now running
    
    # Shutdown
    logger.info("Application shutting down")

# Pass lifespan to FastAPI
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Routers and middleware
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.documents import router as document_router 
from app.api.security import router as security_router 
from app.api.compnay_profile import router as compnay_profile_router 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(compnay_profile_router)
app.include_router(document_router)
app.include_router(security_router)

@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"status": "ok"}
