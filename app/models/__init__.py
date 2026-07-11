# app/models/__init__.py
# Ekspor semua models agar mudah diakses dan agar Alembic bisa
# auto-detect semua tabel saat autogenerate migrasi.

from app.models.base import Base
from app.models.user import User
from app.models.product import Product
from app.models.scraping import ScrapingTask

__all__ = ["Base", "User", "Product", "ScrapingTask"]
