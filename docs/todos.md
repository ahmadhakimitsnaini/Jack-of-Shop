# 📋 Project Implementation TODO List: Jaknote to Shopee Dropship SaaS

Daftar tugas ini disusun berdasarkan analisa menyeluruh terhadap arsitektur (_Architecture_), spesifikasi produk (_PRD_), dan panduan _setup_ yang telah dibuat. Pengerjaan dibagi menjadi fase-fase sistematis dan bertahap untuk menjaga stabilitas pengembangan (_Vibe Coding Guide_).

Gunakan tanda `[x]` untuk menandai tugas yang sudah selesai.

---

## Phase 1: Environment & Data Layer (Database)
Fokus pada penyiapan pondasi _database_ dan koneksi yang efisien (Asynchronous & Pooler).

- [ ] Inisialisasi Python virtual environment dan instal seluruh dependensi *backend* (FastAPI, Celery, SQLAlchemy, Alembic).
- [ ] Konfigurasi file `.env` dengan URL Supabase Transaction Pooler (Port 6543, `pool_timeout=30`) dan URL Redis.
- [ ] Buat file konfigurasi *database engine* asinkron dan `sessionmaker` di `app/core/database.py`.
- [ ] Definisikan *SQLAlchemy Models* (`User`, `Product`, `ScrapingTask`) di `app/models/`.
- [ ] Buat *Pydantic V2 schemas* (untuk validasi API) di `app/schemas/`.
- [ ] Inisialisasi Alembic (`alembic init -t async alembic`) dan sesuaikan `env.py`.
- [ ] Jalankan migrasi awal ke Supabase (`alembic revision --autogenerate` & `alembic upgrade head`).

---

## Phase 2: Core API (FastAPI Gateway)
Fokus pada pembuatan *entry-point* _backend_ dan operasi *CRUD* dasar.

- [ ] Setup `app/main.py` FastAPI lengkap dengan penanganan CORS Middleware.
- [ ] Buat *endpoint* REST API untuk manajemen _Settings_ Toko/User (`users`).
- [ ] Buat *endpoint* REST API untuk mengambil daftar produk olahan (`products`).
- [ ] Terapkan mekanisme _Error Handling_ global untuk merespons _HTTP Status Code_ yang spesifik (400, 404, 422).

---

## Phase 3: Background Worker Setup (Celery & Redis)
Fokus pada isolasi tugas berat (I/O) agar *Event Loop* FastAPI tetap bersih.

- [ ] Inisialisasi aplikasi Celery di `app/worker/celery_app.py` yang terhubung dengan Redis broker.
- [ ] Atur pemisahan antrean (*Queues*): `default`, `scrape_queue`, dan `ai_queue`.
- [ ] Terapkan penanganan *Database Session Life-cycle* (menggunakan blok `try..finally` atau `async with`) di dalam *worker* untuk menghindari kebocoran koneksi.
- [ ] Buat satu API percobaan untuk melempar dan memastikan *dummy task* berjalan lancar di *worker*.

---

## Phase 4: Scraper Engine (Playwright)
Fokus pada pengambilan data secara senyap (_stealth_) dari Jakarta Notebook.

- [ ] Instal *browser binary* untuk Playwright (`playwright install chromium`).
- [ ] Tulis logika `extract_product_dom` menggunakan *Playwright* dan *BeautifulSoup4*.
- [ ] Implementasikan profil _stealth_ dan rotasi _User-Agent_ pada _browser_.
- [ ] Buat `task_scrape_single_product` di Celery yang bertugas menyimpan data mentah `raw_*` ke PostgreSQL.
- [ ] Implementasikan _retry logic_ dengan pustaka Tenacity jika target DOM berubah atau koneksi terputus.

---

## Phase 5: AI Pipeline & Pricing Automation
Fokus pada otomatisasi pengolahan harga, teks SEO, dan manipulasi media visual.

- [ ] Buat fungsi modul `MarginCalculator` (Harga = raw_price + margin + fee admin + packaging).
- [ ] Integrasikan `LangChain`/`LiteLLM` yang memproduksi _Structured Output_ (JSON) khusus untuk `shopee_seo_title` dan `shopee_description`.
- [ ] Implementasikan pipa (*pipeline*) manipulasi gambar komersial sinematik.
- [ ] Tulis skrip untuk mengunggah gambar jadi ke *Public Bucket* Supabase (`enhanced_images`).
- [ ] Rangkai rantai tugas (*task chain*) di Celery: `Scraping -> AI Processing -> Media Upload -> Update Database status ke COMPLETED`.

---

## Phase 6: Integrasi Ekspor (Shopee Mass Upload) & Penjadwalan
Fokus pada hasil akhir (XLSX) dan sinkronisasi harga/stok berkelanjutan.

- [ ] Buat endpoint API khusus eksportir yang mencetak file format `.xlsx` (Shopee Mass Upload Template) dengan memetakan kolom dari tabel `products`.
- [ ] Tulis *task* `task_batch_sync_stock` yang mengecek perubahan data produk aktif.
- [ ] Konfigurasikan Celery Beat untuk memicu `task_batch_sync_stock` secara berkala (*cron/interval*).

---

## Phase 7: Frontend Application (Dashboard UI & Realtime)
Fokus pada antarmuka pengguna tanpa *polling*, 100% menggunakan WebSocket.

- [ ] Inisialisasi proyek *Next.js (App Router)*, *TailwindCSS*, dan *Zustand*.
- [ ] Inisialisasi koneksi klien `@supabase/supabase-js` dengan tipe data yang aman (TypeScript).
- [ ] Buat _Layout Dashboard_ dengan tab navigasi: **Mode Auto Treatment** vs **Mode Manual**.
- [ ] Implementasikan Supabase Auth (Login).
- [ ] Bangun _custom hook_ `useTaskSubscription` yang berlangganan pada perubahan tabel `scraping_tasks` di Supabase Realtime.
- [ ] Integrasikan UI (tombol sinkronisasi) untuk memanggil API FastAPI dan melihat progress *live* di _Dashboard_.

---

## Phase 8: Pengujian & Deployment
Fokus memindahkan sistem ke server *Production/Staging*.

- [ ] Uji coba ujung-ke-ujung (E2E Test): `Input URL -> Scrape -> AI -> DB -> WebSocket Push -> UI Update`.
- [ ] Siapkan `Dockerfile` dan `docker-compose.yml` untuk FastAPI, Celery Worker, Celery Beat, dan Redis.
- [ ] _Deploy_ aplikasi backend (_Docker_) ke server VPS (e.g., DigitalOcean / AWS).
- [ ] _Deploy_ aplikasi *Next.js Frontend* ke _Edge provider_ (e.g., Vercel / Netlify).
