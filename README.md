# Recursive Image Compress

Skrip Python untuk mengompres dan mengubah ukuran gambar secara rekursif dalam sebuah folder, sambil mempertahankan nama file dan format aslinya. Mendukung kompresi agresif hingga ukuran target (KB), penghapusan metadata EXIF, dan output ringkas satu baris per file.

## Prasyarat
- Python 3.8 atau lebih baru
- Pip untuk menginstal dependensi

## Instalasi
Disarankan menggunakan virtual environment, namun opsional.

```bash
# (Opsional) membuat dan mengaktifkan virtualenv
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Instal dependensi
pip install -r requirements.txt
```

## Menjalankan
Jalankan skrip dengan menentukan folder berisi gambar menggunakan `--path`.

```bash
python compress.py --path /path/ke/folder --size 720 --maxsize 30 --quality 60 --target 30 --summary
```

Contoh dengan target ukuran dan output ringkas satu baris per file:
```bash
python compress.py \
  --path /Users/iyan/Documents/CODE/python/recursive-image-compress/kompres \
  --size 720 --maxsize 30 --quality 60 --target 30 --summary
```

Contoh output satu baris:
```
✓ 1010300000080.jpg | 4080x2296 -> 720x405 | target 60KB ✓ | 153.6KB -> 37.6KB (-75.5%)
```

## Opsi CLI
- `--path <str>`: Path folder berisi gambar (wajib diisi jika tidak ingin input manual).
- `--size <int>`: Dimensi maksimum (px) untuk lebar/tinggi. Default: `720`.
- `--quality <int>`: Kualitas kompresi JPEG/WebP (0–100). Default: `85`.
- `--maxsize <int>`: Ukuran file maksimum (KB) untuk memicu kompresi. Default: `200`.
- `--target <int>`: Ukuran file target (KB). Jika disetel, kompresi dilakukan secara agresif untuk mendekati nilai ini.
- `--keep-exif`: Pertahankan metadata EXIF (default: EXIF dihapus untuk mengurangi ukuran).
- `--summary`: Tampilkan output ringkas satu baris per file dan kurangi log verbose.

## Perilaku Skrip
- Resize dilakukan jika salah satu dimensi gambar melebihi `--size`.
- Kompresi dilakukan jika ukuran file melebihi `--maxsize`.
- Jika `--target` disetel dan ukuran awal melebihi target, skrip akan melakukan beberapa percobaan dengan menurunkan kualitas JPEG hingga mendekati target (batas penurunan kualitas tidak di bawah 40).
- Untuk gambar dengan transparansi (RGBA/LA/P), transparansi dihapus dengan latar belakang putih untuk kompresi yang lebih baik.
- JPEG disimpan dengan opsi `optimize`, `progressive`, dan `subsampling 4:2:0`.
- PNG disimpan dengan `compress_level=9`. WebP menggunakan `method=6` (upaya maksimal) dengan `quality` yang ditentukan.
- Nama file dan format asli dipertahankan sebisa mungkin.

## Tips
- Sebaiknya backup folder terlebih dahulu sebelum menjalankan, karena skrip menimpa file asli.
- Jika menemukan error hak akses, pastikan folder/file dapat dibaca dan ditulis.
- Dukungan format bergantung pada `Pillow`. Beberapa format (mis. HEIC/AVIF) memerlukan dukungan tambahan di sistem.

## Lisensi
Tidak ditentukan. Gunakan sesuai kebutuhan Anda.