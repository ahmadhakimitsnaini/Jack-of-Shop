from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.exceptions import APIException
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate, ProductListResponse
import uuid

router = APIRouter()

# Dummy dependency untuk mendapatkan current user (sebelum ada fitur Auth).
async def get_dummy_user(db: AsyncSession = Depends(get_db)) -> User:
    stmt = select(User).limit(1)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise APIException(status_code=400, detail="No users found in database, create a user first.")
    return user

@router.post("/", response_model=ProductRead, status_code=201)
async def create_product(
    product_in: ProductCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_dummy_user)
):
    """
    Menambahkan URL produk baru untuk diproses ke dalam pipeline.
    Status default akan menjadi PENDING.
    """
    new_product = Product(
        owner_id=current_user.id,
        source_url=product_in.source_url,
        # status="PENDING" sudah diset default oleh model
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    # TODO di Phase selanjutnya:
    # trigger background task Celery (task_scrape_single_product.delay(new_product.id))
    
    return new_product

@router.get("/", response_model=ProductListResponse)
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_dummy_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Mengambil daftar produk milik user dengan paginasi sederhana.
    """
    # Hitung total
    count_stmt = select(func.count(Product.id)).where(Product.owner_id == current_user.id)
    total = await db.scalar(count_stmt)

    # Ambil items
    stmt = select(Product).where(Product.owner_id == current_user.id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {"total": total, "items": list(items)}

@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_dummy_user)
):
    """
    Mengambil detail produk spesifik.
    """
    product = await db.get(Product, product_id)
    if not product or product.owner_id != current_user.id:
        raise APIException(status_code=404, detail="Product not found")
    
    return product

@router.patch("/{product_id}", response_model=ProductRead)
async def update_product_manual(
    product_id: uuid.UUID,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_dummy_user)
):
    """
    Melakukan update (override) manual pada data produk olahan (contoh: harga, judul).
    """
    product = await db.get(Product, product_id)
    if not product or product.owner_id != current_user.id:
        raise APIException(status_code=404, detail="Product not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
        
    await db.commit()
    await db.refresh(product)
    
    return product
