from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.exceptions import APIException
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
import uuid

router = APIRouter()

# Placeholder sederhana untuk hashing password sebelum Phase Auth penuh
def fake_hash_password(password: str) -> str:
    return f"hashed_{password}"

@router.post("/", response_model=UserRead, status_code=201)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Endpoint untuk mendaftarkan user baru.
    """
    # Cek apakah email sudah terdaftar
    stmt = select(User).where(User.email == user_in.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    if existing_user:
        raise APIException(status_code=400, detail="Email already registered")

    # Buat instance User baru
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=fake_hash_password(user_in.password),
        shopee_shop_name=user_in.shopee_shop_name,
        default_margin_percent=user_in.default_margin_percent,
        shopee_admin_fee_percent=user_in.shopee_admin_fee_percent,
        packaging_cost_rp=user_in.packaging_cost_rp
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.get("/{user_id}", response_model=UserRead)
async def get_user_profile(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Mengambil data profil dan pengaturan toko dari user spesifik.
    """
    user = await db.get(User, user_id)
    if not user:
        raise APIException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}/settings", response_model=UserRead)
async def update_user_settings(user_id: uuid.UUID, user_update: UserUpdate, db: AsyncSession = Depends(get_db)):
    """
    Memperbarui pengaturan toko milik user tertentu.
    Hanya field yang disertakan dalam request body yang akan diperbarui.
    """
    user = await db.get(User, user_id)
    if not user:
        raise APIException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    return user
