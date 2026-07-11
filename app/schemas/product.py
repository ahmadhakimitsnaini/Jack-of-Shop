"""
app/schemas/product.py

Pydantic V2 Schemas untuk endpoint Product.

Schemas:
- ProductCreate : Request saat user menambahkan URL produk baru untuk diproses
- ProductUpdate : Request untuk update data produk secara manual
- ProductRead   : Response berisi data produk lengkap (raw + processed)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.product import ProductStatus


# ==================================================================
# CREATE — Request body untuk POST /products
# ==================================================================
class ProductCreate(BaseModel):
    """Schema untuk menambahkan produk baru dari URL Jakarta Notebook."""
    source_url: str = Field(
        ...,
        description="URL produk di Jakarta Notebook yang akan di-scrape",
        examples=["https://jakartanotebook.com/product/contoh-produk"],
    )


# ==================================================================
# UPDATE — Request untuk PATCH /products/{id} (manual override)
# ==================================================================
class ProductUpdate(BaseModel):
    """Schema untuk mengubah data produk secara manual (semua field opsional)."""
    shopee_title: str | None = Field(
        default=None,
        max_length=120,
        description="Override judul SEO untuk Shopee (maks 120 karakter)",
    )
    shopee_description: str | None = Field(
        default=None,
        description="Override deskripsi produk untuk Shopee",
    )
    selling_price: float | None = Field(
        default=None,
        gt=0,
        description="Override harga jual manual dalam Rupiah",
    )


# ==================================================================
# READ — Response body untuk GET /products dan GET /products/{id}
# ==================================================================
class ProductRawData(BaseModel):
    """Sub-schema yang berisi data mentah hasil scraping."""
    raw_name: str | None = None
    raw_price: float | None = None
    raw_description: str | None = None
    raw_image_url: str | None = None
    raw_stock: int | None = None
    raw_sku: str | None = None


class ProductRead(BaseModel):
    """
    Schema response lengkap untuk produk.
    Menggabungkan data mentah, data olahan, dan metadata.
    """
    id: uuid.UUID
    owner_id: uuid.UUID
    source_url: str
    status: ProductStatus

    # Data mentah
    raw_name: str | None
    raw_price: float | None
    raw_image_url: str | None
    raw_stock: int | None
    raw_sku: str | None

    # Data olahan
    shopee_title: str | None
    shopee_description: str | None
    selling_price: float | None
    enhanced_image_url: str | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Schema response untuk GET /products (dengan paginasi sederhana)."""
    total: int
    items: list[ProductRead]
