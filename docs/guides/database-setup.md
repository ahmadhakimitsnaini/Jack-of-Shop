# Database & Supabase Setup Guide

Sistem **Jaknote to Shopee Dropship SaaS** menggunakan **Supabase** sebagai _Backend-as-a-Service_ (BaaS). Supabase menyediakan instance PostgreSQL terkelola, otentikasi, penyimpanan objek (Storage), dan Realtime WebSockets.

Panduan ini akan memandu Anda melakukan konfigurasi database dari awal hingga sistem siap berinteraksi dengan backend (FastAPI/Celery) dan frontend (Next.js).

---

## 1. Membuat Proyek Supabase

1. Kunjungi [Supabase Dashboard](https://supabase.com/dashboard) dan buat proyek baru (New Project).
2. Pilih organisasi dan tentukan nama proyek (misal: `jack-of-shopee`).
3. Buat **Database Password** yang kuat dan simpan di tempat yang aman.
4. Pilih _Region_ yang paling dekat dengan server backend/VPS Anda (misal: Singapore `ap-southeast-1`).
5. Tunggu beberapa menit hingga proses _provisioning_ selesai.

---

## 2. Mendapatkan Kredensial Koneksi (Transaction Pooler)

Karena aplikasi backend menggunakan arsitektur _asynchronous_ dan *background workers* (Celery) yang berpotensi membuka banyak koneksi simultan, kita **WAJIB** menggunakan **Transaction Pooler** Supabase (PgBouncer).

1. Buka menu **Project Settings -> Database** di dashboard Supabase.
2. Scroll ke bagian **Connection pooler**.
3. Pastikan **Pool Mode** diatur ke **Transaction**.
4. Salin _Connection string_ (Pilih tab URL) yang menggunakan **Port 6543**.

Format yang diharapkan di file `.env` backend:
```env
# Ganti [PROJECT_REF] dan [PASSWORD] dengan data Anda.
# TAMBAHKAN ?pool_timeout=30 di akhir URL!
DATABASE_URL="postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?pool_timeout=30"
```

---

## 3. Konfigurasi Supabase Storage

Kita membutuhkan Storage Bucket untuk menyimpan hasil optimasi gambar (Cinematic Media Enhancement) yang dilakukan oleh worker.

1. Buka menu **Storage** di dashboard Supabase.
2. Buat _bucket_ baru bernama `enhanced_images`.
3. Atur _bucket_ ini sebagai **Public Bucket** agar gambar dapat diakses dan di-render langsung oleh Shopee dan frontend Anda tanpa memerlukan _signed URL_.
4. (Opsional) Atur _Storage Policies_ untuk mengamankan hak unggah hanya dari _service role_ backend.

---

## 4. Persiapan Tabel & Skema (via Alembic)

Berbeda dengan proyek Supabase pada umumnya (yang biasanya membuat tabel via UI/SQL Editor), proyek ini memegang prinsip *Infrastructure as Code*. **Semua tabel dibuat melalui SQLAlchemy dan Alembic Migration** dari sisi backend.

Pastikan Anda sudah mengikuti panduan `backend-setup.md` dan menginstal *environment* Python.

### A. Mendeklarasikan Model (SQLAlchemy)
Pastikan file model di folder `backend/app/models/` sudah mendefinisikan skema dengan tepat sesuai desain pada dokumen `02_DATABASE_SCHEMA.md` (tabel `users`, `products`, `scraping_tasks`).

*Aturan Ketat:* Semua field uang (harga, biaya, margin) harus bertipe `Integer`.

### B. Membuat dan Menjalankan Migrasi
Buka terminal di folder `backend/`, lalu jalankan:

```bash
# Membuat file revisi migrasi berdasarkan model SQLAlchemy
alembic revision --autogenerate -m "Init database schema"

# Mengaplikasikan perubahan (membuat tabel) di database Supabase
alembic upgrade head
```

Jika berhasil, cek kembali Supabase Dashboard (menu **Table Editor**). Anda seharusnya melihat tabel `users`, `products`, dan `scraping_tasks` sudah terbuat.

---

## 5. Mengaktifkan Supabase Realtime

Agar frontend dapat bereaksi secara *real-time* saat worker Celery selesai memproses suatu tugas (tanpa *HTTP Polling*), kita harus mengaktifkan _webhook/replication_ pada tabel tertentu.

1. Buka menu **Database -> Replication** di dashboard Supabase.
2. Pada bagian **Supabase Realtime**, klik tombol untuk mengaktifkan (*Enable*).
3. Pilih tabel `scraping_tasks` (dan `products` jika frontend memerlukan update data inventaris secara seketika).
4. Klik **Save**.

Sekarang, setiap operasi `UPDATE` pada status tabel `scraping_tasks` oleh Celery akan langsung disiarkan (_broadcast_) ke _channel WebSocket_ frontend.

---

## 6. Integrasi Kredensial untuk Frontend

Untuk menyelesaikan tahap otentikasi pengguna dan langganan _Realtime_, *frontend* Next.js membutuhkan *API Keys* publik dari Supabase.

1. Buka menu **Project Settings -> API**.
2. Salin nilai **Project URL** dan **anon / public key**.
3. Masukkan ke dalam file `.env.local` di folder `frontend/`:

```env
NEXT_PUBLIC_SUPABASE_URL="https://[PROJECT_REF].supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJh..."
```

Database Anda kini telah disiapkan secara penuh dan selaras dengan arsitektur _Dropship SaaS_ ini!
