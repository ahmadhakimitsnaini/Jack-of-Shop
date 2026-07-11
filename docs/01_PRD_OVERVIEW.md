# 01_PRD_OVERVIEW: Jaknote to Shopee Dropship SaaS

## 1. Project Context & Vision

SaaS ini adalah mesin otomasi backend dan dashboard operasi untuk model bisnis dropship/arbitrage dari Jakarta Notebook (Jaknote) ke Shopee. Sistem ini bertugas melakukan ekstraksi data (scraping) secara massal dari Jaknote, memproses harga dinamis untuk margin keuntungan, meningkatkan SEO deskripsi produk menggunakan AI, dan menyiapkannya dalam format yang siap diunggah ke Shopee.

Dokumen ini berfungsi sebagai instruksi mutlak (context rule) untuk AI Coding Assistant. Patuhi arsitektur, tech stack, dan guardrails di bawah ini tanpa pengecualian.

## 2. Tech Stack Lock-In (Strict Requirements)

Dilarang menggunakan framework atau library di luar daftar ini tanpa persetujuan eksplisit.

- **Language:** Python 3.11+
- **Core API Framework:** FastAPI (Strictly Async pattern).
- **Database Engine:** Supabase Hosted PostgreSQL (dihubungkan via Connection String standar).
- **ORM & Migrations:** SQLAlchemy 2.0 (Strictly Async Engine) + Alembic. DILARANG menggunakan library `supabase-py` untuk operasi CRUD di backend Python. Semua interaksi database wajib melalui SQLAlchemy.
- **Task Queue / Message Broker:** Celery + Redis.
- **Web Scraper Engine:** Playwright (Python async API) + BeautifulSoup4.
- **Object Storage:** Supabase Storage (diakses via Boto3/S3-compatible API dari worker Python).

## 3. High-Level Architecture Flow

Sistem beroperasi menggunakan pola Asynchronous Task Queue untuk mencegah blocking pada API saat proses scraping berjalan.

1. **Client/UI** mengirim request sinkronisasi produk via `FastAPI endpoint`.
2. **FastAPI** menyimpan status job (`PENDING`) ke `PostgreSQL` dan melempar task ke `Redis Broker`.
3. **FastAPI** langsung mengembalikan response berupa `task_id` (Non-blocking).
4. **Celery Worker** mengambil task dari Redis dan menjalankan `Playwright` secara headless.
5. **Worker** melakukan scraping ke Jaknote, membersihkan data, memproses kalkulasi harga dan SEO LLM.
6. **Worker** memperbarui data produk dan status task (`COMPLETED` / `FAILED`) di `PostgreSQL`.
7. **Client/UI** melakukan polling via `task_id` untuk mendapatkan hasil akhir atau file Excel format Shopee.

## 4. Core Modules Scope (MVP)

Pengembangan akan dibagi menjadi 4 modul independen:

- **Module 1 (Scraper Engine):** Menangani interaksi browser headless dengan Jaknote, bypass proteksi dasar, dan parsing DOM untuk ekstraksi SKU, Harga, Stok, Berat, dan URL Gambar.
- **Module 2 (Task Dispatcher):** Manajemen antrean Redis dan siklus hidup Celery worker (Retry policy, error logging, database status update).
- **Module 3 (Data Processing & AI):** Modul kalkulasi margin dinamis (rumus persentase laba, potongan admin Shopee) dan penulisan ulang deskripsi produk dengan LLM.
- **Module 4 (Export/Integrations):** Mapping data internal SaaS ke dalam format Mass Upload Excel (XLSX) sesuai template resmi Shopee.

## 5. Global Guardrails (The "DO NOT" List)

AI Assistant WAJIB mematuhi aturan penulisan kode berikut:

1. **NEVER Block the Event Loop:** Dilarang menaruh operasi sinkron (seperti `requests.get` atau operasi I/O file berat) di dalam endpoint FastAPI. Gunakan `httpx` untuk HTTP call internal atau offload ke Celery.
2. **Strict Playwright Isolation:** Playwright instance HANYA boleh berjalan di dalam proses Celery Worker. Dilarang menginisialisasi Playwright di dalam routing FastAPI.
3. **Currency Data Types:** Dilarang keras menggunakan tipe data `Float` untuk kalkulasi harga dan margin. Selalu gunakan `Integer` (menyimpan nilai Rupiah penuh tanpa desimal) atau `Decimal` di SQLAlchemy dan Pydantic.
4. **Graceful Degradation:** Jika scraping satu halaman produk gagal (misal selector berubah atau page timeout), worker tidak boleh crash. Tangkap exception, catat error di DB dengan status `SCRAPE_FAILED`, dan lanjutkan iterasi produk berikutnya.
5. **No Hardcoded Credentials:** Semua API Keys, URL Database, dan konfigurasi environment harus dimuat dari file `.env` menggunakan `pydantic-settings`.
