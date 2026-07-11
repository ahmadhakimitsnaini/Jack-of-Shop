"""
app/models/scraping.py

Model SQLAlchemy untuk tabel `scraping_tasks`.

Tabel ini berfungsi sebagai log dan mekanisme tracking real-time
untuk setiap task Celery yang sedang dijalankan.

Setiap kali user meminta proses produk, sebuah record `ScrapingTask` dibuat.
Frontend dapat berlangganan (Supabase Realtime) ke tabel ini untuk
mendapatkan update status live tanpa polling.

Status Task mengikuti alur:
QUEUED → RUNNING → SUCCESS / FAILED → RETRYING (opsional)
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TaskStatus(str):
    """Konstanta status untuk ScrapingTask."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class ScrapingTask(Base, TimestampMixin):
    """
    Representasi tabel `scraping_tasks` di database.

    Ini adalah "jantung" dari sistem monitoring real-time.
    Kolom `celery_task_id` menghubungkan record ini ke task Celery yang sesungguhnya.
    Frontend menggunakan Supabase Realtime untuk mendengarkan perubahan tabel ini.
    """
    __tablename__ = "scraping_tasks"

    # --- Primary Key ---
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="ID unik task (UUID v4)",
    )

    # --- Foreign Keys ---
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID user yang memiliki/memicu task ini",
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID produk yang diproses oleh task ini (nullable jika task gagal sebelum produk dibuat)",
    )

    # --- Identitas Celery ---
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="ID task Celery yang dihasilkan saat task dikirim ke worker",
    )

    # --- Status & Progress ---
    status: Mapped[str] = mapped_column(
        String(50),
        default=TaskStatus.QUEUED,
        nullable=False,
        index=True,
        comment="Status task: QUEUED/RUNNING/SUCCESS/FAILED/RETRYING",
    )
    current_step: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Deskripsi langkah yang sedang dijalankan (untuk progress UI)",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Jumlah percobaan ulang yang sudah dilakukan",
    )

    # --- Logging ---
    source_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="URL produk yang diproses oleh task ini",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Pesan error jika task gagal",
    )
    error_traceback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Full traceback Python untuk debugging (hanya tersedia di FAILED)",
    )

    # --- Relasi ---
    owner: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="scraping_tasks",
    )
    product: Mapped["Product | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Product",
        back_populates="scraping_tasks",
    )

    def __repr__(self) -> str:
        return (
            f"<ScrapingTask id={self.id} "
            f"status={self.status!r} "
            f"celery_id={self.celery_task_id!r}>"
        )
