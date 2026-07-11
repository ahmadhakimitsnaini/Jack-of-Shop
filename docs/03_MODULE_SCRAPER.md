# 03_MODULE_SCRAPER: Asynchronous Headless Extraction Engine

## 1. Module Objective

Modul ini bertanggung jawab penuh untuk mengambil data mentah produk dari Jakarta Notebook (Jaknote). Karena halaman target berpotensi dirender menggunakan JavaScript dan dilindungi mekanisme anti-bot dasar, modul ini WAJIB menggunakan `Playwright` (Async API) yang dikombinasikan dengan `BeautifulSoup4` untuk parsing HTML agar lebih ringan memori.

**AI ASSISTANT INSTRUCTION:** Jangan pernah menginisialisasi atau menjalankan fungsi Playwright di dalam routing/endpoint FastAPI. Modul ini HANYA akan dipanggil oleh Celery Worker (Task Queue).

## 2. Core Dependencies

- `playwright` (async API)
- `beautifulsoup4` (lxml parser)
- `fake-useragent` (untuk randomisasi user-agent)
- `tenacity` (library untuk mekanisme retry otomatis)

## 3. The Scraping Pipeline (Input -> Process -> Output)

### A. Input

Fungsi utama (contoh: `async def scrape_jaknote_product(url: str) -> ProductCreate:`) menerima URL produk Jaknote.

### B. Process & Anti-Bot Strategy

1. **Context Isolation:** Setiap task harus membuka `browser.new_context()` yang independen (jangan gunakan state/cookie dari task sebelumnya).
2. **Stealth Mode:** - Inject User-Agent yang terlihat organik (Chrome/Firefox versi terbaru).
   - Disable WebRTC dan otomatisasi flag webdriver.
3. **Navigation & Wait State:** - Arahkan ke URL menggunakan `page.goto(url, wait_until="domcontentloaded")`.
   - Gunakan `page.wait_for_selector()` khusus untuk elemen harga atau tombol stok, memastikan halaman benar-benar selesai di-render sebelum diekstrak.
4. **DOM Handoff:**
   - Setelah halaman dirender, ambil full HTML string menggunakan `await page.content()`.
   - Tutup _context_ Playwright segera untuk menghemat RAM.
   - Lakukan parsing elemen menggunakan `BeautifulSoup(html_content, 'lxml')`.

### C. Output Configuration

Hasil akhir harus divalidasi dan di-return sebagai Pydantic model `ProductCreate` (merujuk ke `02_DATABASE_SCHEMA.md`).

**Data Extraction Rules:**

- **Harga (`raw_price`):** Hapus simbol "Rp", titik, atau spasi. Konversi murni ke integer (misal: "Rp 1.500.000" -> `1500000`).
- **Stok (`raw_stock`):** Jika tombol "Beli" disable atau terdapat teks "Stok Habis", return `0`. Jika ada, return representasi integer.
- **Berat (`raw_weight_gram`):** Konversi otomatis ke satuan Gram (integer). Jika di website tertera "1.2 kg", jadikan `1200`.
- **Gambar (`raw_images`):** Ekstrak atribut `src` atau `data-src`. Pastikan mengambil resolusi paling tinggi (high-res), buang URL yang mengarah ke thumbnail/icon.

## 4. Guardrails & Error Handling (Strict)

Gunakan decorator dari library `tenacity` untuk menangani kegagalan jaringan atau timeout.

1. **Exponential Backoff:** Jika `TimeoutError` terjadi pada Playwright, lakukan retry maksimal 3 kali. Waktu tunggu antar retry harus berlipat ganda (misal: 2 detik, 4 detik, 8 detik).
2. **Missing Selectors:** Jika elemen DOM berubah (misal: Jaknote melakukan update UI) dan tag harga tidak ditemukan, JANGAN buat aplikasi crash. Lemparkan custom exception `DOMSelectorChangedError` dan tangkap di level pemanggil (Celery Task) untuk dicatat ke database sebagai log error.
3. **Resource Leak Prevention:** Bungkus eksekusi Playwright dalam blok `try...finally`. Pastikan `browser_context.close()` dan `browser.close()` selalu dipanggil dalam kondisi apapun (sukses maupun error) agar server tidak kehabisan memori.
