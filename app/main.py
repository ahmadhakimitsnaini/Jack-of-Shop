from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers

def create_app() -> FastAPI:
    """
    Factory pattern untuk membuat instance FastAPI.
    Berguna untuk setup test dan modularitas.
    """
    app = FastAPI(
        title="Jaknote to Shopee Dropship API",
        description="Core API untuk sistem scraping dan auto-pricing produk",
        version="1.0.0",
        debug=settings.APP_DEBUG
    )

    # 1. Konfigurasi CORS (Cross-Origin Resource Sharing)
    # Mengizinkan request dari frontend dashboard (misal: Next.js)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Ganti dengan URL domain production spesifik saat deploy
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Setup Global Exception Handlers (400, 404, 422, 500)
    setup_exception_handlers(app)

    # 3. Include Router API
    # Prefix /api/v1 untuk versioning
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health_check():
        """Endpoint sederhana untuk mengecek apakah API berjalan dengan baik."""
        return {"status": "ok", "message": "API is running smooth!"}

    return app

app = create_app()
