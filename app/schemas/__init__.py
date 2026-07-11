# app/schemas/__init__.py
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.schemas.scraping import ScrapingTaskCreate, ScrapingTaskRead

__all__ = [
    "UserCreate", "UserRead", "UserUpdate",
    "ProductCreate", "ProductRead", "ProductUpdate",
    "ScrapingTaskCreate", "ScrapingTaskRead",
]
