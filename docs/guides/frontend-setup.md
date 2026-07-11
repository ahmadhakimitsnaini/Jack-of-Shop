# Frontend Setup Guide: Jaknote to Shopee Dropship SaaS

Panduan ini mendeskripsikan langkah-langkah pengaturan lingkungan antarmuka pengguna (_frontend environment_). Frontend dirancang sebagai _dashboard_ yang ringan dan responsif, dibangun dengan Next.js (App Router), dan berinteraksi secara _real-time_ menggunakan Supabase.

## 1. Prerequisites (Persyaratan Sistem)

Pastikan sistem Anda memiliki:

- **Node.js** (Versi 18.17 atau yang lebih baru direkomendasikan).
- **Package Manager**: npm, yarn, atau pnpm.
- **Akun Supabase** (untuk mendapatkan URL proyek dan anon key).

---

## 2. Struktur Direktori Frontend

Kode frontend sebaiknya diletakkan di dalam folder `frontend/` pada root proyek, menggunakan struktur standar Next.js App Router:

```text
frontend/
├── src/
│   ├── app/                # Next.js App Router (Halaman dan Layout)
│   ├── components/         # Komponen UI Reusable (TailwindCSS)
│   ├── lib/                # Konfigurasi utilitas (Supabase client, axios/fetch)
│   ├── store/              # State Management (Zustand)
│   └── hooks/              # Custom React Hooks (khususnya untuk Supabase Realtime)
├── public/                 # Aset statis (gambar, favicon)
├── next.config.mjs         # Konfigurasi Next.js
├── tailwind.config.ts      # Konfigurasi TailwindCSS
└── .env.local              # File variabel lingkungan lokal
```

---

## 3. Konfigurasi Environment Variables (.env.local)

Buat file `.env.local` di root folder `frontend/`. Variabel yang diekspos ke browser harus diawali dengan `NEXT_PUBLIC_`.

```env
# Koneksi ke API Gateway (FastAPI) backend lokal
NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"

# Kredensial Supabase (URL dan Anon Key)
NEXT_PUBLIC_SUPABASE_URL="https://[PROJECT_REF].supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-supabase-anon-key"
```

---

## 4. Instalasi dan Setup Proyek

Buka terminal, dan jalankan perintah berikut untuk menginisialisasi proyek dan memasang _dependency_:

### A. Inisialisasi Proyek Next.js

Jika Anda belum membuat folder frontend, gunakan `create-next-app`:

```bash
npx create-next-app@latest frontend
```

_(Saat diminta konfigurasi, pilih TypeScript, ESLint, Tailwind CSS, `src/` directory, dan App Router)._

Masuk ke dalam folder yang baru dibuat:

```bash
cd frontend
```

### B. Menginstal Library Tambahan

Instal pustaka esensial sesuai dengan _Tech Stack_ proyek:

```bash
# Supabase Client (untuk Auth dan Realtime)
npm install @supabase/supabase-js

# State Management
npm install zustand

# Ikon dan Komponen (Opsional, sesuai kebutuhan UI)
npm install lucide-react clsx tailwind-merge
```

---

## 5. Setup Klien Supabase & Realtime

Sistem ini bergantung pada Supabase Realtime Channels untuk menerima notifikasi saat _worker_ selesai melakukan _scraping_.

Buat klien Supabase di `src/lib/supabase.ts`:

```typescript
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseKey);
```

Untuk berlangganan pembaruan tabel (_Realtime_), Anda bisa membuat _custom hook_ di `src/hooks/useTaskSubscription.ts` yang memantau tabel `scraping_tasks`.

---

## 6. Menjalankan Server Development

Setelah semua konfigurasi selesai, jalankan _development server_:

```bash
npm run dev
```

Buka peramban (browser) dan navigasikan ke [http://localhost:3000](http://localhost:3000).

---

## 7. Catatan Penting untuk Developer (Guardrails)

- **Tidak Ada HTTP Polling:** DILARANG menggunakan metode `setInterval` atau SWR polling untuk mengecek status pemrosesan. Frontend sepenuhnya harus menggunakan _WebSocket push_ melalui event Supabase Realtime saat mendeteksi mutasi database di backend.
- **Pemisahan Logika Keuangan:** Frontend murni bertindak sebagai antarmuka tampilan. **Jangan** pernah meletakkan algoritma kalkulasi _margin_, biaya layanan, atau pajak di frontend. Semua logika kalkulasi harga Shopee dieksekusi secara eksklusif di backend.
- **Edge Deployment:** Arsitektur frontend disiapkan untuk dapat di-_deploy_ dengan optimal menggunakan platform Edge CDN seperti Vercel atau Netlify. Pastikan tidak ada _backend heavy processing_ (seperti scraping) yang bocor ke fungsi _Server Actions_ Next.js.
