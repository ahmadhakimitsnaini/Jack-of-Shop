"""
app/schemas/user.py

Pydantic V2 Schemas untuk endpoint User / Settings Toko.

Schemas dibagi berdasarkan use-case:
- UserCreate  : Data yang diterima saat user mendaftar (POST /users)
- UserUpdate  : Data yang diterima saat user update profil (PATCH /users/{id})
- UserRead    : Data yang dikirimkan sebagai response API (tidak termasuk password)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==================================================================
# Base — Field bersama yang tidak bergantung pada use-case
# ==================================================================
class UserBase(BaseModel):
    """
    Schema dasar yang berisi field yang digunakan di beberapa context.
    Tidak digunakan langsung, hanya diwarisi oleh schema lain.
    """
    email: EmailStr = Field(
        ...,
        description="Alamat email unik pengguna",
        examples=["user@example.com"],
    )
    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="Nama lengkap pengguna",
        examples=["Budi Santoso"],
    )


# ==================================================================
# CREATE — Request body untuk POST /users/register
# ==================================================================
class UserCreate(UserBase):
    """Schema untuk mendaftarkan user baru."""
    password: str = Field(
        ...,
        min_length=8,
        description="Password minimal 8 karakter",
        examples=["password123"],
    )
    shopee_shop_name: str | None = Field(
        default=None,
        max_length=255,
        description="Nama toko di Shopee (opsional saat registrasi)",
    )
    default_margin_percent: float = Field(
        default=20.0,
        ge=0.0,
        le=100.0,
        description="Persentase margin keuntungan default (0-100)",
    )
    shopee_admin_fee_percent: float = Field(
        default=2.0,
        ge=0.0,
        le=100.0,
        description="Persentase biaya admin Shopee (0-100)",
    )
    packaging_cost_rp: float = Field(
        default=2000.0,
        ge=0.0,
        description="Biaya packaging per produk dalam Rupiah",
    )


# ==================================================================
# UPDATE — Request body untuk PATCH /users/{id}/settings
# ==================================================================
class UserUpdate(BaseModel):
    """Schema untuk update settings toko (semua field opsional)."""
    shopee_shop_name: str | None = Field(
        default=None,
        max_length=255,
    )
    default_margin_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    shopee_admin_fee_percent: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    packaging_cost_rp: float | None = Field(
        default=None,
        ge=0.0,
    )
    notes: str | None = None


# ==================================================================
# READ — Response body untuk GET /users/{id}
# ==================================================================
class UserRead(UserBase):
    """
    Schema untuk response API. TIDAK mengekspos password.
    `model_config` dengan `from_attributes=True` memungkinkan
    Pydantic membaca data langsung dari objek SQLAlchemy.
    """
    id: uuid.UUID
    is_active: bool
    shopee_shop_name: str | None
    default_margin_percent: float
    shopee_admin_fee_percent: float
    packaging_cost_rp: float
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
