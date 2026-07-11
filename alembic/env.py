"""
alembic/env.py

Konfigurasi Alembic untuk mode Asinkron.

Penyesuaian dari template default:
1. Memuat DATABASE_URL dari file .env (bukan dari alembic.ini)
   agar password tidak ter-hardcode di file konfigurasi.
2. Mengimpor semua Models agar Alembic bisa auto-detect tabel
   saat perintah `alembic revision --autogenerate` dijalankan.
3. Menggunakan `run_async_migrations()` sebagai entry point.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# --- Import semua models agar metadata terisi ---
# WAJIB: Tanpa ini, autogenerate tidak akan mendeteksi tabel apapun
from app.models import Base  # noqa: F401 — import diperlukan untuk side-effect
from app.core.config import settings  # noqa: F401 — untuk DATABASE_URL

# --- Konfigurasi Alembic dari alembic.ini ---
config = context.config

# Override sqlalchemy.url dengan nilai dari .env (lebih aman)
# Untuk Alembic migrations di Supabase, sangat direkomendasikan menggunakan
# Direct Connection (Port 5432) untuk menghindari masalah PgBouncer Transaction Mode.
# Oleh karena itu, kita otomatis ganti port 6543 ke 5432 khusus untuk migrasi.
migration_url = settings.DATABASE_URL.replace(":6543", ":5432")
config.set_main_option("sqlalchemy.url", migration_url)

# Logging dari alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata target untuk autogenerate
target_metadata = Base.metadata


# ==================================================================
# MODE OFFLINE — Menghasilkan SQL script tanpa koneksi ke DB
# ==================================================================
def run_migrations_offline() -> None:
    """
    Jalankan migrasi dalam mode offline.
    Menghasilkan SQL script yang bisa dijalankan manual ke database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ==================================================================
# MODE ONLINE ASYNC — Koneksi langsung ke DB menggunakan asyncpg
# ==================================================================
def do_run_migrations(connection: Connection) -> None:
    """Fungsi helper untuk menjalankan migrasi dalam konteks koneksi."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,       # Deteksi perubahan tipe kolom
        compare_server_default=True,  # Deteksi perubahan server_default
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Jalankan migrasi secara asinkron.
    Membuat engine async sementara khusus untuk migrasi.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Tidak pakai pool untuk migrasi (one-shot)
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        },
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point untuk mode online — memanggil async runner."""
    asyncio.run(run_async_migrations())


# --- Entry point Alembic ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
