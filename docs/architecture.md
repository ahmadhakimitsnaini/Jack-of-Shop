# ARCHITECTURE.md: Jaknote to Shopee Dropship SaaS

## Purpose

Sistem operasi e-commerce ini dibangun untuk mengotomatisasi rantai pasok (_supply chain_) digital bagi penjual Shopee yang menggunakan model _arbitrage/dropship_ dari Jakarta Notebook (Jaknote). Sistem ini dirancang sebagai _hybrid automated dashboard_ yang memadukan kontrol kurasi manual dengan eksekusi _treatment auto_ di latar belakang.

Sistem memangkas 90% waktu operasional manual melalui _web scraping_ asinkron, kalkulasi margin dinamis, optimasi SEO berbasis LLM, dan manipulasi media (mengubah foto standar menjadi media komersial sinematik), untuk menghasilkan _file mass upload_ yang siap diintegrasikan dengan platform Shopee.

## High-Level Architecture

```mermaid
graph TD
    %% Define Node Styles
    classDef frontend fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef database fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef external fill:#6b7280,stroke:#374151,stroke-width:2px,color:#fff,stroke-dasharray: 5 5;
    classDef supabase fill:#3ecf8e,stroke:#249361,stroke-width:2px,color:#111;

    %% Nodes
    Client[Frontend Dashboard<br/>Next.js]:::frontend
    API[API Gateway<br/>FastAPI]:::backend
    Cache[(Message Broker<br/>Redis)]:::database
    Worker[Background Worker<br/>Celery + Playwright]:::backend

    %% Supabase Ecosystem
    subgraph Supabase BaaS
        S_Auth[Supabase Auth]:::supabase
        S_DB[(Hosted PostgreSQL)]:::supabase
        S_Realtime[Supabase Realtime]:::supabase
        S_Storage[(Supabase Storage)]:::supabase
    end

    %% External Services
    Jaknote[Jakarta Notebook]:::external
    Shopee[Shopee Platform]:::external
    LLM[LLM Provider<br/>OpenAI/Gemini]:::external

    %% Connections
    Client <-->|1. Login/JWT| S_Auth
    Client <-->|2. Trigger Task| API
    API -->|3. Insert Task| S_DB
    API -->|4. Dispatch Task| Cache
    Cache -->|5. Consume Task| Worker
    Worker <-->|6. Extract DOM| Jaknote
    Worker <-->|7. Generate SEO & Image Prompts| LLM
    Worker -->|8. Upload Enhanced Media| S_Storage
    Worker -->|9. Update Status| S_DB
    S_DB -.->|10. Trigger Webhooks| S_Realtime
    S_Realtime -.->|11. WebSocket Push| Client
    Client -.->|12. Download Excel| Shopee
```

### Architectural Goals

- **Asynchronous by Default:** Mencegah bottleneck I/O. API tidak boleh terblokir oleh proses scraping atau request ke AI yang memakan waktu lama.
- **Fault Tolerance (Resiliency):** Jika target URL berubah struktur DOM-nya atau koneksi terputus, sistem harus bisa melakukan retry otomatis atau mencatat error secara spesifik tanpa mematikan seluruh worker.
- **Data Integrity:** Perhitungan finansial (harga modal, biaya layanan, margin) harus memiliki presisi absolut (menggunakan tipe data Integer), menghindari kerugian akibat kesalahan presisi floating point.
- **Modular Isolation:** Eksekusi browser headless (Playwright) diisolasi ketat di dalam worker (Celery), terpisah dari alur web API (FastAPI).

## Tech Stack (Strict Requirements)

- **Frontend Layer:** Next.js (App Router), TailwindCSS, Zustand (State Management), supabase-js (Auth & Realtime).
- **Core API Backend:** Python 3.11+, FastAPI (Strictly Async).
- **Database Engine & BaaS:** Supabase (Hosted PostgreSQL 15+, Supabase Auth, Supabase Storage).
- **ORM & Migrations:** SQLAlchemy 2.0 (Strictly Async Engine) + Alembic. _(Catatan: Backend Python memperlakukan Supabase murni sebagai PostgreSQL biasa via connection string. Dilarang menggunakan supabase-py untuk operasi CRUD database)._
- **Task Queue & Broker:** Celery + Redis.
- **Web Scraper Engine:** Playwright (Python async API) + BeautifulSoup4 + fake-useragent.
- **AI Integration:** LangChain/LiteLLM (untuk LLM SEO Text) & Pipeline AI Media Generation.

## System Boundaries

Sistem **TIDAK** berinteraksi langsung melalui API resmi ke dua platform (karena limitasi akses/regulasi):

- **Jakarta Notebook:** Interaksi dilakukan via Headless Browser (Playwright) dengan teknik ekstraksi DOM (scraping).
- **Shopee:** Interaksi dilakukan secara offline melalui format XLSX (Mass Upload Template). Sistem memetakan data internal ke format yang dipahami Shopee.

Sistem berinteraksi langsung via API dengan penyedia LLM dan layanan Supabase (Database pgbouncer port 6543 & S3-compatible Storage).

## Request Flow (Manual Curated Scenario)

1. Pengguna (telah terautentikasi via Supabase Auth) memasukkan URL Jaknote di Frontend dan menekan tombol sinkronisasi.
2. Frontend Next.js mengirim HTTP POST ke FastAPI.
3. FastAPI memvalidasi payload dengan Pydantic, membuat record di tabel `scraping_tasks` (PostgreSQL), mengirim perintah ke Redis, dan me-return HTTP 202 Accepted.
4. Frontend langsung melakukan subscribe via WebSocket ke baris tugas tersebut menggunakan supabase-js.
5. Celery Worker mengambil antrean dari Redis dan mengeksekusi Playwright secara headless.
6. Worker mengekstrak data DOM, lalu memanggil modul AI untuk menghitung margin harga dinamis dan men-generate SEO konten.
7. Worker memproses gambar mentah, menyiapkan prompt sinematik, dan mengunggah gambar hasil komersial ke Supabase Storage.
8. Worker melakukan operasi UPDATE (via SQLAlchemy) ke PostgreSQL Supabase, mengubah status menjadi COMPLETED.
9. Supabase Realtime mendeteksi mutasi database dan otomatis mengirimkan notifikasi push ke Frontend.
10. UI Frontend langsung menampilkan data produk baru tanpa memuat ulang halaman (no polling).

## Component Details

### Frontend Layer

- Bertindak sebagai dashboard antarmuka dengan mode ganda: Mode Treatment Auto (memantau log sinkronisasi massal yang berjalan di background) dan Mode Manual (analisa produk presisi tinggi).
- Membuang mekanisme polling HTTP tradisional dan sepenuhnya mengandalkan Supabase Realtime Channels.
- Tidak mengandung logika bisnis finansial. Kalkulator margin eksklusif berada di ranah backend.

### Backend Layer

- **API Gateway (FastAPI):** Menjaga Event Loop tetap bersih dari blocking operations. Mengelola validasi endpoint dan penjadwalan antrean.
- **Scraper Engine (Playwright):** Beroperasi dengan profil stealth, merotasi User-Agent, dan menggunakan BeautifulSoup untuk parsing ringan.
- **AI Pipeline:** Memaksa penggunaan Structured Output (JSON mode) dari LLM agar judul dan deskripsi Shopee terpetakan langsung ke Pydantic Schema, serta menyiapkan aset visual resolusi tinggi untuk kebutuhan fotografi produk AI.

## Data & Error Management

### Schema Management

**CRITICAL RULE FOR SUPABASE CONNECTION:**

- Skema database dideklarasikan terpusat menggunakan SQLAlchemy 2.0 (Async) dan dieksekusi via Alembic.
- AI wajib memastikan connection string SQLAlchemy menggunakan Transaction Pooler dari Supabase (Port 6543) dan menambahkan parameter `?pool_timeout=30`.
- Representasi mata uang di database HANYA menggunakan Integer (Rupiah penuh).

### Error Handling

- **API Level:** FastAPI me-return kode HTTP spesifik (400, 401, 404, 422).
- **Worker Level (Resiliency):**
  - Kegagalan jaringan atau timeout ditangani dengan pustaka Tenacity (Maksimal 3 retries dengan Exponential Backoff).
  - Perubahan struktur DOM dari Jaknote akan memicu pelemparan `DOMSelectorChangedError`. Worker akan menangkap exception ini, menandai status tugas menjadi FAILED di database, dan melanjutkan ke tugas berikutnya tanpa crash.
- **AI Level:** Terdapat mekanisme fallback ke teks asli Jaknote jika API LLM mengalami Rate Limit atau putus koneksi.

## Configuration & Deployment

### Environment Variables (.env structure)

Manajemen konfigurasi menggunakan `pydantic-settings`. Tidak ada hardcode credential.

```env
# Backend Environment Variables
DATABASE_URL="postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?pool_timeout=30"
REDIS_URL="redis://..."
OPENAI_API_KEY="..."
SUPABASE_URL="..."
SUPABASE_SERVICE_ROLE_KEY="..." # Digunakan khusus backend untuk akses bypass Storage API
```

### Deployment Shape

Fase MVP dirancang modular:

- **Frontend:** Di-hosting pada Vercel/Netlify untuk performa Edge CDN.
- **Backend Server (VPS - e.g., DigitalOcean):** Menjalankan Docker Compose yang berisi:
  - `api_service` (FastAPI)
  - `worker_service` (Celery + Playwright)
  - `beat_service` (Celery Beat penjadwal cron)
  - `redis` (Cache & Message Broker)
- **Database & Storage:** Dikelola sepenuhnya (managed) oleh Supabase (Cloud).

## Implementation Sequence (Vibe Coding Guide)

- **Tahap 1 (Data Layer):** Setup Supabase PostgreSQL connection, SQLAlchemy models, Pydantic V2 schemas, dan Alembic migrations.
- **Tahap 2 (Core API):** Setup FastAPI dan CRUD API dasar.
- **Tahap 3 (Worker Setup):** Setup integrasi Redis dan Celery (isolasi task queue).
- **Tahap 4 (Scraper Engine):** Penulisan logika ekstraksi Playwright di dalam Celery task.
- **Tahap 5 (AI Pipeline):** Implementasi formula Margin Calculator, Prompt Engineering LLM (Structured Output), dan integrasi unggah media ke Supabase Storage.
- **Tahap 6 (Export & Integrations):** Endpoint generator format XLSX Shopee Mass Upload.
- **Tahap 7 (Frontend):** Pembangunan UI Next.js, integrasi Supabase Auth, dan WebSocket Realtime.

## Non-Goals

Agar MVP tidak mengalami scope creep, sistem ini secara eksplisit **TIDAK AKAN**:

- Melakukan otomatisasi checkout pembelanjaan di website Jakarta Notebook.
- Mengelola pesan obrolan (chat) pengguna Shopee.
- Melakukan injeksi login otomatis ke Seller Center Shopee (unggah file Excel tetap dilakukan manual oleh pengguna untuk menghindari penalti sistem e-commerce).
- Berfungsi sebagai Warehouse Management System (WMS) untuk barang fisik.
