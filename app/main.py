from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config.settings import settings
from app.config.database import engine, Base
from app.routes import auth
# from app.routes import transactions
from app.routes.transaction import router as transactions_router
from app.routes.analytics import router as analytics_router
from app.routes.savings import router as savings_router
from app.routes.investment import router as investment_router

# Setup logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

def seed_default_user():
    from app.config.database import SessionLocal
    from app.models.user import User
    from app.utils.security import get_password_hash

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "executive@capitallens.com").first()
        if not user:
            logger.info("Creating default executive guest user...")
            new_user = User(
                email="executive@capitallens.com",
                name="Executive Officer",
                password_hash=get_password_hash("password")
            )
            db.add(new_user)
            db.commit()
            logger.info("Default executive guest user created successfully.")
    except Exception as e:
        logger.error(f"Failed to seed default user: {e}")
        db.rollback()
    finally:
        db.close()

seed_default_user()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Capitallens API")
    yield
    logger.info("🛑 Shutting down Capitallens API")

app = FastAPI(
    title=settings.API_TITLE,
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(savings_router, prefix="/api/v1")
app.include_router(investment_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Capitallens API",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {
        "message": "Capitallens live ",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )