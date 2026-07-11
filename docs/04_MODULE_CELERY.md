# 04_MODULE_CELERY: Background Task & Message Broker Architecture

## 1. Module Objective

Modul ini mengatur siklus hidup background jobs menggunakan Celery dan Redis. Semua proses I/O berat (scraping menggunakan Playwright) dan panggilan API eksternal (LLM untuk SEO, generasi media) WAJIB dilempar ke modul ini agar event loop FastAPI tidak terblokir. Sistem mendukung eksekusi manual (per-request) dan auto-treatment (berkala).

**AI ASSISTANT INSTRUCTION:** Pastikan inisialisasi Celery app dikonfigurasi untuk bekerja dengan fungsi `async` Python (gunakan `asgiref.sync.async_to_sync` atau pustaka loop eksekusi yang kompatibel) karena fungsi scraper di Modul 3 ditulis secara asynchronous.

## 2. Core Dependencies

- `celery`
- `redis` (Sebagai Message Broker dan Result Backend)
- `celery-beat` (Untuk penjadwalan Treatment Auto)

## 3. Worker Queues & Task Definitions

Beban kerja harus dipisah ke dalam antrean (queues) yang berbeda agar proses sinkronisasi massal tidak memblokir pengguna yang hanya ingin menganalisa satu produk.

**Queue Definitions:**

- `default`: Untuk tugas-tugas ringan atau update status.
- `scrape_queue`: Khusus dialokasikan untuk worker Playwright (I/O & Memory intensive).
- `ai_queue`: Khusus untuk memanggil API LLM (Network IO intensive).

**Core Task Signatures:**

1. `task_scrape_single_product(user_id: str, url: str) -> dict`
   - Dipicu secara manual via API.
   - Mengambil data dari Modul 3, menyimpannya ke PostgreSQL, update status tabel `scraping_tasks` menjadi `COMPLETED`.
2. `task_batch_sync_stock()`
   - Dipicu secara otomatis oleh Celery Beat (Treatment Auto).
   - Menarik semua produk dengan status `UPLOADED` dari DB, mengecek ulang harga dan stok terbaru di Jaknote, dan memperbarui DB jika ada perubahan.
3. `task_generate_seo_content(product_id: str) -> dict`
   - Memproses data mentah menjadi deskripsi Shopee yang SEO-friendly.

## 4. Architectural Guardrails (Strict Rules)

1. **Idempotency:** Semua task Celery harus bersifat _idempotent_. Jika task yang sama dieksekusi dua kali secara tidak sengaja (misalnya pengguna klik tombol "Sync" berkali-kali), sistem tidak boleh menduplikasi data produk di database. Gunakan pengecekan `jaknote_sku` sebelum melakukan operasi `INSERT`.
2. **Database Connection Lifecycle:** Celery worker berjalan di thread/proses yang terpisah dari FastAPI. AI WAJIB memastikan bahwa setiap eksekusi task membuat _database session_ yang baru (menggunakan `sessionmaker`) dan secara eksplisit menutup sesi tersebut (menggunakan blok `try...finally` atau `async with`) untuk mencegah kebocoran koneksi (Connection Pool Exhaustion).
3. **State Mutation:** Jangan mengirim instance object database (SQLAlchemy models) ke dalam argumen Celery task, karena tidak bisa di-serialize oleh Redis. Selalu kirim tipe data primitif seperti `user_id` (String/UUID) atau payload `dict`, lalu lakukan query ulang di dalam fungsi task.
4. **Retry Policy:** Untuk `ai_queue` dan `scrape_queue`, konfigurasikan `autoretry_for=(Exception,)` dengan batas maksimal 3 retries dan backoff dinamis jika terjadi _rate limit_ dari API eksternal.
