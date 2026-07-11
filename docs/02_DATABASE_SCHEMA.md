# 02_DATABASE_SCHEMA: Entity Relationship & Data Models

## 1. Overview

Dokumen ini mendefinisikan struktur tabel database (SQLAlchemy 2.0) dan skema validasi data (Pydantic V2). Semua entitas dirancang untuk mendukung asynchrony dan strict type checking.

**CRITICAL RULE:** - Semua representasi mata uang (harga, biaya, margin) WAJIB menggunakan `Integer` (rupiah penuh) di database. Jangan gunakan `Float`.

- Semua string panjang (deskripsi, payload JSON) menggunakan `Text` atau `JSONB` (PostgreSQL).

**CRITICAL RULE FOR SUPABASE CONNECTION:**

- Karena database di-host di Supabase, AI wajib memastikan connection string SQLAlchemy menggunakan Transaction Pooler port (biasanya `6543`) dan menambahkan parameter `?pool_timeout=30` jika diperlukan.
- URL Storage untuk `enhanced_images` akan mengarah ke domain public/private bucket Supabase Storage, bukan lagi AWS S3.

## 2. Core Entities & Relationships

Sistem terdiri dari 3 entitas utama:

1. `users` (atau `stores`): Menyimpan kredensial dan konfigurasi margin dinamis.
2. `products`: Menyimpan data produk Jaknote mentah sekaligus data hasil olahan (AI SEO, final pricing) untuk Shopee.
3. `scraping_tasks`: Melacak status background job dari Celery.

---

## 3. SQLAlchemy Models (Source of Truth)

### A. User & Store Settings Table

Menyimpan konfigurasi otomatisasi per pengguna/toko.

- `id`: UUID (Primary Key)
- `email`: String (Unique)
- `shopee_admin_fee_pct`: Integer (Persentase potongan admin, misal: 6 untuk 6%)
- `packaging_cost`: Integer (Biaya tetap per pesanan, misal: 2500)
- `default_margin_pct`: Integer (Target margin keuntungan kotor, misal: 30 untuk 30%)
- `auto_sync_enabled`: Boolean (Default: False)

### B. Products Table

Menyimpan state produk dari hulu (Jaknote) ke hilir (Shopee).

- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> users.id)
- `jaknote_sku`: String (Unique index)
- `jaknote_url`: String
- **Raw Data (Scraped):**
  - `raw_title`: String
  - `raw_price`: Integer (Harga beli/modal)
  - `raw_stock`: Integer
  - `raw_weight_gram`: Integer
  - `raw_images`: JSON (List of URLs)
- **Processed Data (Ready for Shopee):**
  - `shopee_seo_title`: String (Hasil generate LLM)
  - `shopee_description`: Text (Hasil generate LLM)
  - `shopee_sell_price`: Integer (Kalkulasi otomatis dari raw_price + margin + fee)
  - `enhanced_images`: JSON (List of URLs untuk media komersial)
- `sync_status`: Enum (`DRAFT`, `AI_PROCESSED`, `READY_TO_UPLOAD`, `UPLOADED`)
- `updated_at`: DateTime (Timezone aware)

### C. Scraping Tasks Table

Tracking job Celery.

- `id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key -> users.id)
- `celery_task_id`: String (Unique)
- `task_type`: Enum (`SINGLE_SCRAPE`, `CATEGORY_SCRAPE`, `MASS_UPLOAD_GENERATE`)
- `status`: Enum (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`)
- `target_url`: String (URL Jaknote yang di-scrape)
- `result_payload`: JSON (Menyimpan error log atau summary success)
- `created_at`: DateTime

---

## 4. Pydantic V2 Schemas (API Contracts)

Model Pydantic digunakan ketat untuk validasi Input/Output API. Gunakan `ConfigDict(from_attributes=True)` untuk serialisasi dari SQLAlchemy.

```python
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum

class SyncStatus(str, Enum):
    DRAFT = "DRAFT"
    AI_PROCESSED = "AI_PROCESSED"
    READY_TO_UPLOAD = "READY_TO_UPLOAD"

class ProductBase(BaseModel):
    jaknote_sku: str
    jaknote_url: HttpUrl
    raw_title: str
    raw_price: int = Field(ge=0, description="Harga modal dalam Rupiah")
    raw_stock: int = Field(ge=0)
    raw_weight_gram: int
    raw_images: List[HttpUrl]

class ProductCreate(ProductBase):
    pass # Data yang dilempar dari Scraper Engine (Module 1) ke DB

class ProductResponse(ProductBase):
    id: str
    shopee_seo_title: Optional[str]
    shopee_sell_price: Optional[int]
    sync_status: SyncStatus
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MarginCalculationRequest(BaseModel):
    raw_price: int
    shopee_admin_fee_pct: int
    packaging_cost: int
    default_margin_pct: int
```
