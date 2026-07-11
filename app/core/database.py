"""
app/core/database.py

Setup koneksi database asinkron menggunakan SQLAlchemy 2.0 dan asyncpg.

Arsitektur koneksi:
- Engine   : create_async_engine (satu instance, dibagikan ke seluruh app)
- Session  : async_sessionmaker (factory pembuat sesi per-request)
- get_db() : FastAPI dependency yang me-yield sesi dan menutupnya otomatis

Catatan Penting untuk Supabase Transaction Pooler (Port 6543):
- `pool_size` dan `max_overflow` dikontrol dari sisi Supabase,
  sehingga kita hanya perlu mengatur `pool_pre_ping=True`
  untuk mendeteksi koneksi yang sudah mati (stale connections).
- `pool_pre_ping=True` memastikan setiap koneksi dari pool
  diuji sebelum digunakan (mencegah "connection closed" error).
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# ==================================================================
# 1. ENGINE — Buat satu kali, bagikan ke seluruh aplikasi
# ==================================================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,      # Log SQL query ke console (hanya di development)
    pool_pre_ping=True,           # Deteksi koneksi mati sebelum digunakan
    pool_recycle=1800,            # Daur ulang koneksi setiap 30 menit
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)

# ==================================================================
# 2. SESSION FACTORY — Factory untuk membuat sesi database
# ==================================================================
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Mencegah lazy-loading error setelah commit
)

# ==================================================================
# 3. DEPENDENCY — FastAPI dependency untuk injeksi sesi per-request
# ==================================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yang menyediakan sesi database untuk setiap request.

    Pola `async with` memastikan sesi SELALU ditutup,
    bahkan jika terjadi exception di dalam endpoint.
    Ini adalah cara yang benar untuk mencegah connection leak.

    Contoh penggunaan di endpoint FastAPI:
        @router.get("/")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
