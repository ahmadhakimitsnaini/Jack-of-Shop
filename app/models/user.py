"""
app/models/user.py

Model SQLAlchemy untuk tabel `users`.

Tabel ini menyimpan data akun pengguna beserta konfigurasi toko mereka,
termasuk pengaturan margin harga, fee admin Shopee, dan biaya packaging
yang akan digunakan oleh `MarginCalculator` di Phase 5.

Relasi:
- User (1) ——< Product (many)   : Satu user bisa punya banyak produk
- User (1) ——< ScrapingTask (many) : Satu user bisa punya banyak task
"""

import uuid

from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    Representasi tabel `users` di database.
    """
    __tablename__ = "users"

    # --- Primary Key ---
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="ID unik pengguna (UUID v4)",
    )

    # --- Identitas ---
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Email pengguna, digunakan sebagai identifier login",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Password yang telah di-hash (bcrypt)",
    )
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Nama lengkap pengguna",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Status aktif akun",
    )

    # --- Pengaturan Toko (untuk MarginCalculator di Phase 5) ---
    shopee_shop_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Nama toko di Shopee",
    )
    default_margin_percent: Mapped[float] = mapped_column(
        Float,
        default=20.0,
        nullable=False,
        comment="Margin keuntungan default dalam persen (contoh: 20.0 = 20%)",
    )
    shopee_admin_fee_percent: Mapped[float] = mapped_column(
        Float,
        default=2.0,
        nullable=False,
        comment="Persentase biaya admin Shopee (contoh: 2.0 = 2%)",
    )
    packaging_cost_rp: Mapped[float] = mapped_column(
        Float,
        default=2000.0,
        nullable=False,
        comment="Biaya packaging dalam Rupiah per item",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Catatan tambahan dari pengguna",
    )

    # --- Relasi ---
    products: Mapped[list["Product"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Product",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select",
    )
    scraping_tasks: Mapped[list["ScrapingTask"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "ScrapingTask",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
