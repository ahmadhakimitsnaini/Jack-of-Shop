"""
app/models/base.py

Mendefinisikan Base class untuk semua SQLAlchemy ORM models.

Menggunakan `DeclarativeBase` dari SQLAlchemy 2.0 (bukan `declarative_base()`
yang sudah deprecated). Semua model di proyek ini harus mewarisi dari `Base`.

Kelas `TimestampMixin` disediakan sebagai mixin opsional untuk menambahkan
kolom `created_at` dan `updated_at` secara otomatis ke model yang membutuhkannya.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class untuk semua SQLAlchemy models.
    Menggunakan API deklaratif terbaru dari SQLAlchemy 2.0.
    """
    pass


class TimestampMixin:
    """
    Mixin yang menambahkan kolom `created_at` dan `updated_at` secara otomatis.
    - `created_at` : diisi otomatis saat record pertama kali dibuat.
    - `updated_at` : diperbarui otomatis setiap kali record diubah.

    Contoh penggunaan:
        class User(Base, TimestampMixin):
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
