"""
app/schemas/scraping.py

Pydantic V2 Schemas untuk endpoint ScrapingTask.

ScrapingTask adalah entitas yang digunakan untuk monitoring real-time
melalui Supabase Realtime di frontend (Phase 7).

Schemas:
- ScrapingTaskCreate : Request saat user memulai proses scraping baru
- ScrapingTaskRead   : Response berisi status dan progress task
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ==================================================================
# CREATE — Request body untuk POST /tasks/scrape
# ==================================================================
class ScrapingTaskCreate(BaseModel):
    """Schema untuk memulai task scraping baru."""
    source_url: str = Field(
        ...,
        description="URL produk di Jakarta Notebook yang akan diproses",
        examples=["https://jakartanotebook.com/product/contoh-produk"],
    )


# ==================================================================
# READ — Response body untuk GET /tasks/{id}
# ==================================================================
class ScrapingTaskRead(BaseModel):
    """
    Schema response untuk monitoring status task secara real-time.
    Digunakan oleh frontend untuk menampilkan progress di dashboard.
    """
    id: uuid.UUID
    owner_id: uuid.UUID
    product_id: uuid.UUID | None

    # Celery Integration
    celery_task_id: str | None = Field(
        default=None,
        description="ID task Celery yang dapat digunakan untuk cek status langsung",
    )

    # Status & Progress
    status: str = Field(
        description="Status: QUEUED / RUNNING / SUCCESS / FAILED / RETRYING",
    )
    current_step: str | None = Field(
        default=None,
        description="Langkah saat ini yang sedang dieksekusi worker",
    )
    retry_count: int = Field(
        default=0,
        description="Berapa kali task sudah dicoba ulang",
    )

    # Info
    source_url: str
    error_message: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScrapingTaskListResponse(BaseModel):
    """Schema response untuk GET /tasks (list semua task milik user)."""
    total: int
    items: list[ScrapingTaskRead]
