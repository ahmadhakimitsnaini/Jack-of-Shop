# Jaknote to Shopee Dropship SaaS

Sebuah sistem operasi e-commerce terotomatisasi (_hybrid automated dashboard_) yang dirancang khusus untuk memangkas hingga 90% waktu operasional rantai pasok digital model _arbitrage/dropship_ dari **Jakarta Notebook (Jaknote)** ke platform **Shopee**.

Proyek ini menggabungkan kontrol kurasi manual dengan eksekusi _auto treatment_ di latar belakang menggunakan antrean (task queue) asynchronous yang efisien.

---

## Fitur Utama

- **Asynchronous Web Scraping:** Mengekstrak detail produk dari Jaknote menggunakan _headless browser_ (Playwright) di dalam antrean Celery tanpa memblokir sistem.
- **Dynamic Margin Calculator:** Engine backend yang menghitung harga jual Shopee secara absolut, disesuaikan dengan biaya admin, _packaging cost_, dan target _margin_ persentase secara cerdas.
- **LLM SEO Optimization:** Mengubah judul dan deskripsi mentah Jaknote menjadi format teks komersial yang SEO-friendly khusus untuk algoritma Shopee menggunakan Generative AI (LangChain/LiteLLM).
- **Cinematic Media Enhancement:** Memanipulasi foto standar produk menjadi aset pemasaran/media komersial visual (high-resolution) yang otomatis tersimpan di Supabase Storage.
- **Shopee Mass Upload Exporter:** Menghasilkan _file_ `.xlsx` yang siap diunggah menggunakan template resmi "Shopee Mass Upload", menghindari risiko pemblokiran karena injeksi API ilegal.
- **Real-time Push Notification:** _Dashboard_ bebas-polling. Seluruh notifikasi _update_ kemajuan tugas ditarik seketika menggunakan Supabase Realtime Channels (WebSocket).

---

## Technology Stack

Sistem ini dirancang mematuhi standar asinkron untuk menjaga skalabilitas tinggi pada proses _Input/Output_ (I/O) yang berat (web scraping & pemanggilan LLM).

- **Frontend Layer:** Next.js (App Router), TailwindCSS, Zustand, `@supabase/supabase-js`.
- **Backend / API Gateway:** Python 3.11+, FastAPI (Strictly Async).
- **Background Worker:** Celery, Redis (Broker & Cache).
- **Scraper Engine:** Playwright (Python async API), BeautifulSoup4, fake-useragent.
- **Database & Storage:** Supabase (Hosted PostgreSQL 15+, Supabase Auth, Storage).
- **ORM:** SQLAlchemy 2.0 (Async Engine) + Alembic.

---

## Dokumentasi Proyek

Untuk memahami dan mengembangkan sistem ini lebih lanjut, Anda sangat disarankan membaca file dokumentasi lengkap di direktori `docs/`:

1.  [Architecture & System Boundaries](docs/architecture.md)
2.  [Product Requirements Document (PRD)](docs/01_PRD_OVERVIEW.md)
3.  [Database Schema & Entities](docs/02_DATABASE_SCHEMA.md)
4.  [Scraper Module (Playwright)](docs/03_MODULE_SCRAPER.md)
5.  [Background Task Architecture (Celery)](docs/04_MODULE_CELERY.md)
6.  [Pricing & LLM SEO AI Module](docs/05_MODULE_PRICING_AI.md)

---

## Panduan Menjalankan Sistem (Getting Started)

Proyek ini dipisahkan menjadi dua bagian utama (_Frontend_ dan _Backend_). Lihat panduan detail setup pada file berikut:

- **[Setup Backend (FastAPI, Celery, Alembic)](docs/guides/backend-setup.md)**
- **[Setup Frontend (Next.js & Supabase Realtime)](docs/guides/frontend-setup.md)**

---

## Non-Goals (Batasan Sistem)

Untuk menjaga lingkup _MVP (Minimum Viable Product)_, sistem ini secara eksplisit **TIDAK AKAN**:

1.  Melakukan transaksi otomatis (_auto checkout_) barang di website Jakarta Notebook.
2.  Membaca atau membalas _chat_ pembeli di Seller Center Shopee.
3.  Mengunggah produk langsung ke Shopee via _bot login_ (Unggah massal via excel harus dilakukan oleh _seller_ secara manual untuk mengamankan akun).
4.  Bertindak sebagai _Warehouse Management System_ (WMS) barang fisik.

---

> **Note:** Proyek ini dikembangkan secara spesifik untuk mematuhi _system boundaries_ dalam regulasi scraping dan keterbatasan konektivitas API platform _e-commerce_ lokal.
