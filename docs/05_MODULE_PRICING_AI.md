# 05_MODULE_PRICING_AI: Dynamic Margin Calculator & AI Rewriter

## 1. Module Objective

Modul ini menangani dua logika bisnis paling krusial:

1. **Dynamic Margin Calculator:** Algoritma untuk menghitung harga jual ideal (Shopee Selling Price) berdasarkan harga modal Jaknote, dengan mempertimbangkan persentase biaya layanan Shopee dan target laba bersih pengguna.
2. **AI Content Generator:** Menggunakan LLM (OpenAI/Gemini via LangChain) untuk menulis ulang judul dan deskripsi produk agar sesuai dengan algoritma SEO Shopee, serta menyusun parameter _prompt_ untuk peningkatan kualitas foto produk komersial.

**AI ASSISTANT INSTRUCTION:** Semua output dari LLM WAJIB dipaksa menggunakan `Structured Output` (Function Calling / JSON Mode) yang dipetakan langsung ke Pydantic Schema. Jangan terima respon dalam format raw text.

## 2. Dynamic Pricing Logic (Strict Math Rules)

Karena Shopee mengenakan potongan persentase dari **Harga Jual Akhir**, perhitungan harga jual tidak bisa hanya dengan `Modal + (Modal * Margin)`. Gunakan formula aljabar berikut.

**Variables:**

- `P_raw` = Harga beli dari Jaknote (Integer)
- `C_pack` = Biaya kardus/bubble wrap (Integer)
- `F_admin` = Total persentase potongan Shopee (Admin + Gratis Ongkir) (Integer, misal: 10 untuk 10%)
- `M_target` = Persentase margin laba bersih yang diinginkan dari modal (Integer, misal: 25 untuk 25%)

**Formula Target Laba (Net Profit):**
Target Laba (Rupiah) = `P_raw` \* (`M_target` / 100)

**Formula Harga Jual (Shopee Selling Price - S):**
Persamaan: `S` = `P_raw` + `C_pack` + Target Laba + (`S` \* (`F_admin` / 100))
Solusi Algoritma:
`S` = (`P_raw` + `C_pack` + Target Laba) / (1 - (`F_admin` / 100))

**Guardrail:** Hasil dari formula ini WAJIB dibulatkan ke atas ke ratusan terdekat (misal: Rp 45.321 menjadi Rp 45.400) dan disimpan sebagai `Integer`.

## 3. AI SEO Rewriter (LLM Integration)

### A. Pydantic Schema for LLM Output

```python
from pydantic import BaseModel, Field

class ShopeeOptimizedContent(BaseModel):
    seo_title: str = Field(..., max_length=255, description="Judul maksimal 255 karakter, masukkan keyword utama di depan.")
    shopee_description: str = Field(..., description="Deskripsi lengkap dengan format bullet points untuk fitur dan spesifikasi.")
    search_keywords: list[str] = Field(..., max_length=5, description="5 tag pencarian utama.")
```
