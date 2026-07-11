"""
app/core/config.py

Konfigurasi aplikasi terpusat menggunakan Pydantic BaseSettings.
Variabel diambil secara otomatis dari file .env di root project.

Pola ini memastikan:
1. Tidak ada kredensial yang ter-hardcode di dalam kode.
2. Satu sumber kebenaran (single source of truth) untuk semua konfigurasi.
3. Validasi tipe otomatis (misalnya, DATABASE_URL harus string, APP_DEBUG harus bool).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Kelas konfigurasi utama aplikasi.
    Pydantic akan secara otomatis membaca dari file .env
    dan memvalidasi tipenya.
    """

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/jack_of_shopee"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Aplikasi ---
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "default-insecure-key-please-change"

    # Konfigurasi agar Pydantic membaca file .env
    # `env_file_encoding='utf-8'` untuk kompatibilitas karakter antar OS
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Inisiasi singleton settings — diimpor oleh modul lain
# Contoh: from app.core.config import settings
settings = Settings()
