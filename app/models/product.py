"""
app/models/product.py

Model SQLAlchemy untuk tabel `products`.

Tabel ini menyimpan data produk dalam dua tahap:
1. Data mentah (raw_*) : hasil scraping langsung dari Jakarta Notebook
2. Data olahan         : hasil pemrosesan AI dan kalkulasi margin

Status produk mengikuti lifecycle:
PENDING → SCRAPING → AI_PROCESSING → COMPLETED / FAILED

Relasi:
- Product (many) >—— User (1)         : Setiap produk milik satu user
- Product (1) ——< ScrapingTask (many) : Satu produk bisa punya beberapa task history
"""

import uuid
from enum import Enum

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ProductStatus(str, Enum):
    """
    Status lifecycle sebuah produk di dalam sistem pipeline.
    Menggunakan `str, Enum` agar mudah diserialisasi ke JSON.
    """
    PENDING = "PENDING"
    SCRAPING = "SCRAPING"
    AI_PROCESSING = "AI_PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Product(Base, TimestampMixin):
    """
    Representasi tabel `products` di database.

    Kolom dibagi menjadi dua kelompok besar:
    - `raw_*`    : Data mentah hasil scraping (belum diolah)
    - (tanpa raw): Data siap pakai hasil AI + margin calculator
    """
    __tablename__ = "products"

    # --- Primary Key ---
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="ID unik produk (UUID v4)",
    )

    # --- Foreign Key ---
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID user pemilik produk ini",
    )

    # --- Metadata Produk ---
    source_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="URL produk di Jakarta Notebook (sumber scraping)",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=ProductStatus.PENDING,
        nullable=False,
        index=True,
        comment="Status produk dalam pipeline: PENDING/SCRAPING/AI_PROCESSING/COMPLETED/FAILED",
    )

    # --- Data Mentah (dari Scraping) ---
    raw_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Nama produk asli dari halaman Jakarta Notebook",
    )
    raw_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Harga asli produk dalam Rupiah",
    )
    raw_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Deskripsi produk asli dari halaman Jakarta Notebook",
    )
    raw_image_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        comment="URL gambar produk asli dari Jakarta Notebook",
    )
    raw_stock: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Jumlah stok asli yang tersedia",
    )
    raw_sku: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="SKU / kode produk asli",
    )

    # --- Data Olahan (dari AI + MarginCalculator) ---
    shopee_title: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        comment="Judul produk SEO-optimized untuk Shopee (maks 120 karakter)",
    )
    shopee_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Deskripsi produk marketing-oriented hasil AI untuk listing Shopee",
    )
    selling_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Harga jual final (raw_price + margin + fee + packaging)",
    )
    enhanced_image_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        comment="URL gambar produk yang sudah diproses/enhanced di Supabase Storage",
    )

    # --- Relasi ---
    owner: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="products",
    )
    scraping_tasks: Mapped[list["ScrapingTask"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "ScrapingTask",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} status={self.status!r} url={self.source_url!r}>"
