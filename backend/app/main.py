from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os

from app.core.config import settings
from app.core.logging import logger
from app.api.v1 import auth, projects, tts, images, settings as settings_router, ws


def create_app() -> FastAPI:
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/")
    async def root():
        logger.info("Root endpoint accessed")
        return {"message": "Novel to Video API v2.0", "status": "running", "docs": "/docs"}

    @application.get("/health")
    async def health_check():
        logger.info("Health check endpoint accessed")
        return {"status": "healthy", "version": settings.VERSION}

    # 静态文件服务
    upload_dir_str = str(settings.upload_dir_path)
    output_dir_str = str(settings.output_dir_path)
    
    if os.path.exists(upload_dir_str):
        application.mount("/storage/uploads", StaticFiles(directory=upload_dir_str), name="uploads")
    
    if os.path.exists(output_dir_str):
        application.mount("/storage/output", StaticFiles(directory=output_dir_str), name="output")

    application.include_router(auth.router, prefix=settings.API_PREFIX)
    application.include_router(projects.router, prefix=settings.API_PREFIX)
    application.include_router(tts.router, prefix=settings.API_PREFIX)
    application.include_router(images.router, prefix=settings.API_PREFIX)
    application.include_router(settings_router.router, prefix=settings.API_PREFIX)
    application.include_router(ws.router, prefix=settings.API_PREFIX)

    return application


app = create_app()
