import asyncio
from app.worker.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def async_dummy_db_task():
    """Fungsi asinkron yang melakukan tes koneksi ke database."""
    async with AsyncSessionLocal() as db:
        try:
            # Uji query sederhana
            result = await db.execute(text("SELECT 1"))
            value = result.scalar()
            return f"Database connected. Value: {value}"
        finally:
            # Sesi otomatis ditutup oleh blok async with
            pass

@celery_app.task(name="task.dummy_test")
def dummy_test_task(message: str):
    """
    Task Celery synchronous yang menjalankan fungsi asynchronous.
    """
    db_result = asyncio.run(async_dummy_db_task())
    return f"Task Received: {message}. DB Status: {db_result}"
