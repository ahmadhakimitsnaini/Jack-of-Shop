# 📋 Project Implementation TODO List: Jaknote to Shopee Dropship SaaS

Daftar tugas ini disusun berdasarkan analisa menyeluruh terhadap arsitektur (_Architecture_), spesifikasi produk (_PRD_), dan panduan _setup_ yang telah dibuat. Pengerjaan dibagi menjadi fase-fase sistematis dan bertahap untuk menjaga stabilitas pengembangan (_Vibe Coding Guide_).

Gunakan tanda `[x]` untuk menandai tugas yang sudah selesai.

---

## Phase 1: Environment & Data Layer (Database)

Fokus pada penyiapan pondasi _database_ dan koneksi yang efisien (Asynchronous & Pooler).

- [x] Inisialisasi Python virtual environment dan instal seluruh dependensi _backend_ (FastAPI, Celery, SQLAlchemy, Alembic).
- [x] Konfigurasi file `.env` dengan URL Supabase Transaction Pooler (Port 6543, `pool_timeout=30`) dan URL Redis.
- [x] Buat file konfigurasi _database engine_ asinkron dan `sessionmaker` di `app/core/database.py`.
- [x] Definisikan _SQLAlchemy Models_ (`User`, `Product`, `ScrapingTask`) di `app/models/`.
- [x] Buat _Pydantic V2 schemas_ (untuk validasi API) di `app/schemas/`.
- [x] Inisialisasi Alembic (`alembic init -t async alembic`) dan sesuaikan `env.py`.
- [x] Jalankan migrasi awal ke Supabase (`alembic revision --autogenerate` & `alembic upgrade head`).

---

## Phase 2: Core API (FastAPI Gateway)

Fokus pada pembuatan _entry-point_ _backend_ dan operasi _CRUD_ dasar.

- [x] Setup `app/main.py` FastAPI lengkap dengan penanganan CORS Middleware.
- [x] Buat _endpoint_ REST API untuk manajemen _Settings_ Toko/User (`users`).
- [x] Buat _endpoint_ REST API untuk mengambil daftar produk olahan (`products`).
- [x] Terapkan mekanisme _Error Handling_ global untuk merespons _HTTP Status Code_ yang spesifik (400, 404, 422).

---

## Phase 3: Background Worker Setup (Celery & Redis)

Fokus pada isolasi tugas berat (I/O) agar _Event Loop_ FastAPI tetap bersih.

- [x] Inisialisasi aplikasi Celery di `app/worker/celery_app.py` yang terhubung dengan Redis broker.
- [x] Atur pemisahan antrean (_Queues_): `default`, `scrape_queue`, dan `ai_queue`.
- [x] Terapkan penanganan _Database Session Life-cycle_ (menggunakan blok `try..finally` atau `async with`) di dalam _worker_ untuk menghindari kebocoran koneksi.
- [x] Buat satu API percobaan untuk melempar dan memastikan _dummy task_ berjalan lancar di _worker_.

---

## Phase 4: Scraper Engine (Playwright)

Fokus pada pengambilan data secara senyap (_stealth_) dari Jakarta Notebook.

- [ ] Instal _browser binary_ untuk Playwright (`playwright install chromium`).
- [ ] Tulis logika `extract_product_dom` menggunakan _Playwright_ dan _BeautifulSoup4_.
- [ ] Implementasikan profil _stealth_ dan rotasi _User-Agent_ pada _browser_.
- [ ] Buat `task_scrape_single_product` di Celery yang bertugas menyimpan data mentah `raw_*` ke PostgreSQL.
- [ ] Implementasikan _retry logic_ dengan pustaka Tenacity jika target DOM berubah atau koneksi terputus.

---

## Phase 5: AI Pipeline & Pricing Automation

Fokus pada otomatisasi pengolahan harga, teks SEO, dan manipulasi media visual.

- [ ] Buat fungsi modul `MarginCalculator` (Harga = raw_price + margin + fee admin + packaging).
- [ ] Integrasikan `LangChain`/`LiteLLM` yang memproduksi _Structured Output_ (JSON) khusus untuk `shopee_seo_title` dan `shopee_description`.
- [ ] Implementasikan pipa (_pipeline_) manipulasi gambar komersial sinematik.
- [ ] Tulis skrip untuk mengunggah gambar jadi ke _Public Bucket_ Supabase (`enhanced_images`).
- [ ] Rangkai rantai tugas (_task chain_) di Celery: `Scraping -> AI Processing -> Media Upload -> Update Database status ke COMPLETED`.

---

## Phase 6: Integrasi Ekspor (Shopee Mass Upload) & Penjadwalan

Fokus pada hasil akhir (XLSX) dan sinkronisasi harga/stok berkelanjutan.

- [ ] Buat endpoint API khusus eksportir yang mencetak file format `.xlsx` (Shopee Mass Upload Template) dengan memetakan kolom dari tabel `products`.
- [ ] Tulis _task_ `task_batch_sync_stock` yang mengecek perubahan data produk aktif.
- [ ] Konfigurasikan Celery Beat untuk memicu `task_batch_sync_stock` secara berkala (_cron/interval_).

---

## Phase 7: Frontend Application (Dashboard UI & Realtime)

Fokus pada antarmuka pengguna tanpa _polling_, 100% menggunakan WebSocket.

- [ ] Inisialisasi proyek _Next.js (App Router)_, _TailwindCSS_, dan _Zustand_.
- [ ] Inisialisasi koneksi klien `@supabase/supabase-js` dengan tipe data yang aman (TypeScript).
- [ ] Buat _Layout Dashboard_ dengan tab navigasi: **Mode Auto Treatment** vs **Mode Manual**.
- [ ] Implementasikan Supabase Auth (Login).
- [ ] Bangun _custom hook_ `useTaskSubscription` yang berlangganan pada perubahan tabel `scraping_tasks` di Supabase Realtime.
- [ ] Integrasikan UI (tombol sinkronisasi) untuk memanggil API FastAPI dan melihat progress _live_ di _Dashboard_.

---

## Phase 8: Pengujian & Deployment

Fokus memindahkan sistem ke server _Production/Staging_.

- [ ] Uji coba ujung-ke-ujung (E2E Test): `Input URL -> Scrape -> AI -> DB -> WebSocket Push -> UI Update`.
- [ ] Siapkan `Dockerfile` dan `docker-compose.yml` untuk FastAPI, Celery Worker, Celery Beat, dan Redis.
- [ ] _Deploy_ aplikasi backend (_Docker_) ke server VPS (e.g., DigitalOcean / AWS).
- [ ] _Deploy_ aplikasi _Next.js Frontend_ ke _Edge provider_ (e.g., Vercel / Netlify).
