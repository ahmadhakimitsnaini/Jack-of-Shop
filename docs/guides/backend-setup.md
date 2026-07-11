# Backend Setup Guide: Jaknote to Shopee Dropship SaaS

Panduan ini berisi langkah-langkah komprehensif untuk mengatur lingkungan backend (_backend environment_) dari proyek ini. Backend dibangun menggunakan Python (FastAPI, Celery) dan terhubung ke Supabase (PostgreSQL).

## 1. Prerequisites (Persyaratan Sistem)

Pastikan sistem operasi Anda telah memasang:

- **Python 3.11** atau yang lebih baru.
- **Redis Server** (Bisa diinstal via Docker, Homebrew untuk Mac, atau menggunakan layanan Redis cloud). Redis berfungsi sebagai _message broker_ untuk Celery.
- **Akun Supabase** dengan proyek yang sudah berjalan (untuk PostgreSQL Database & Storage).

---

## 2. Struktur Direktori Backend

Direkomendasikan untuk menempatkan seluruh kode backend di dalam folder `backend/` pada root proyek, dengan struktur modular sebagai berikut:

```text
backend/
├── alembic/                # Konfigurasi dan file migrasi database
├── app/
│   ├── main.py             # Entry point FastAPI
│   ├── core/               # Konfigurasi utama (.env settings, setup koneksi database)
│   ├── api/                # Definisi router/endpoint (FastAPI)
│   ├── models/             # SQLAlchemy 2.0 ORM models (Representasi tabel DB)
│   ├── schemas/            # Pydantic V2 schemas (Validasi input/output API)
│   ├── services/           # Logika bisnis (kalkulasi margin, ekstraksi LLM)
│   └── worker/             # Task Celery dan script Playwright scraper
├── requirements.txt        # Daftar dependency Python
├── alembic.ini             # Konfigurasi Alembic
└── .env                    # File variabel lingkungan (JANGAN di-commit!)
```

---

## 3. Konfigurasi Environment Variables (.env)

Buat file `.env` di dalam folder `backend/`. Gunakan konfigurasi berikut sebagai referensi:

```env
# Supabase PostgreSQL Database (Transaction Pooler - Port 6543)
# CRITICAL: Pastikan menambahkan ?pool_timeout=30 pada ujung URL
DATABASE_URL="postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?pool_timeout=30"

# Redis Config untuk Celery Broker & Result Backend
REDIS_URL="redis://localhost:6379/0"

# Kredensial Supabase (Untuk otentikasi & akses Storage API)
SUPABASE_URL="https://[PROJECT_REF].supabase.co"
SUPABASE_SERVICE_ROLE_KEY="your-supabase-service-role-key"

# Kredensial AI (LLM Provider)
OPENAI_API_KEY="sk-your-openai-api-key"
```

_Catatan: Pastikan menggunakan koneksi dengan Transaction Pooler (Port 6543) Supabase untuk menghindari masalah kehabisan koneksi (Connection Pool Exhaustion) dari worker._

---

## 4. Instalasi Dependency & Lingkungan Python

Buka terminal, masuk ke folder `backend/`, lalu jalankan langkah-langkah berikut:

### A. Membuat dan Mengaktifkan Virtual Environment (vEnv)

```bash
python3 -m venv venv
source venv/bin/activate  # Untuk Mac/Linux
# venv\Scripts\activate   # Untuk Windows
```

### B. Menginstal Library Inti

Instal seluruh _library_ yang dibutuhkan oleh infrastruktur (sesuai spesifikasi di `ARCHITECTURE.md` dan modul terkait):

```bash
pip install fastapi uvicorn pydantic pydantic-settings
pip install sqlalchemy asyncpg alembic
pip install celery redis celery-beat
pip install playwright beautifulsoup4 fake-useragent
pip install langchain litellm
```

_Tip: Simpan dependensi ke dalam file `requirements.txt` menggunakan perintah `pip freeze > requirements.txt`._

### C. Instalasi Playwright (Headless Browser)

Playwright membutuhkan _binary browser_ untuk dapat melakukan _scraping_ DOM. Instal browser engine (Chromium direkomendasikan):

```bash
playwright install chromium
```

---

## 5. Setup Database dengan Alembic

Sistem backend bergantung pada Alembic untuk menjalankan migrasi skema tabel (seperti `users`, `products`, `scraping_tasks`) ke Supabase.

1. **Inisialisasi Alembic (Asynchronous Mode):**
   ```bash
   alembic init -t async alembic
   ```
2. **Konfigurasi `alembic/env.py`:**
   Sesuaikan `alembic/env.py` untuk mengimpor dan membaca metadata dari _Base model_ SQLAlchemy Anda, serta memuat URL database dari file `.env`.
3. **Membuat File Migrasi Pertama:**
   Pastikan model telah didefinisikan (lihat `docs/02_DATABASE_SCHEMA.md`).
   ```bash
   alembic revision --autogenerate -m "Initial schema setup"
   ```
4. **Menerapkan Migrasi ke Supabase:**
   ```bash
   alembic upgrade head
   ```

---

## 6. Menjalankan Sistem Secara Lokal

Ada beberapa komponen yang perlu dijalankan secara bersamaan agar sistem berfungsi utuh:

### A. Pastikan Redis Berjalan

Jika menjalankan Redis secara lokal via Docker:

```bash
docker run -d -p 6379:6379 redis
```

### B. Menjalankan FastAPI (API Gateway)

Buka tab terminal baru, aktifkan venv, dan jalankan server web:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### C. Menjalankan Celery Worker (Task Executor)

Buka tab terminal baru, aktifkan venv, dan jalankan _worker_ untuk memproses _scraping_ dan AI. (Ganti `app.worker.celery_app` dengan jalur instans Celery Anda):

```bash
celery -A app.worker.celery_app worker --loglevel=info
```

### D. Menjalankan Celery Beat (Penjadwal Otomatis)

Jika Anda mengaktifkan fitur _auto treatment_ yang berjalan berkala, buka tab terminal baru dan jalankan:

```bash
celery -A app.worker.celery_app beat --loglevel=info
```

---

## 7. Catatan Penting untuk Developer (Guardrails)

- **Session Handling Celery:** Fungsi task Celery berjalan di luar _event loop_ FastAPI. Pastikan di dalam setiap task _worker_, Anda membuat sesi database (_database session_) baru menggunakan blok `async with` atau `try...finally` untuk menutup sesi secara eksplisit.
- **Serialization:** Jangan pernah mengoper objek model SQLAlchemy (_instance_) ke dalam argumen fungsi Celery. Selalu lempar tipe primitif seperti ID berformat String/UUID, lalu lakukan kueri ulang objek tersebut di dalam task Celery.
- **Idempotency:** Semua logic _worker_ harus memvalidasi data (misalnya `jaknote_sku`) agar tidak terjadi duplikasi entri saat URL yang sama dieksekusi berulang kali.
