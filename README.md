# ⚡ Raflux Solana Daily Bot & Referral Multiplier

> [!WARNING]
> ### ⚠️ DISCLAIMER (PERNYATAAN PENYANGKALAN)
> **Proyek ini dibuat HANYA UNTUK TUJUAN EDUKASI DAN RISET (Educational & Research Purposes Only).**
> - Proyek ini bertujuan untuk mengedukasi dan mendemonstrasikan implementasi protokol kriptografi **Sign-In With Solana (SIWS - RFC 8032 / Ed25519)**, arsitektur otomatisasi client-side, dan penanganan rate-limiting.
> - **DILARANG KERAS** menyalahgunakan perangkat lunak ini untuk aktivitas yang melanggar hukum, merugikan pihak lain, atau melanggar *Terms of Service* (ToS) platform terkait.
> - Penulis/kontributor **TIDAK BERTANGGUNG JAWAB** atas segala kerugian finansial, sanksi, pemblokiran akun (banned), atau dampak apa pun akibat penggunaan repositori ini.
> - **Gunakan sepenuhnya dengan risiko dan tanggung jawab Anda sendiri (*Use at your own risk*).**

---

Sistem otomatisasi untuk bot **Raflux** (`https://raflux.io`) pada jaringan **Solana** yang dioptimalkan khusus untuk **skala besar (multi-wallet 30+ hingga 100+ akun)**.

Fitur & kapabilitas:
- 🔑 **Koneksi Wallet Solana** dengan SIWS (*Sign-in With Solana* via Ed25519 signature).
- 🎁 **Input Kode Referral** otomatis (bonus +20 Flux Points per akun).
- 💎 **Klaim Welcome Bonus Points** otomatis.
- 📅 **Daily Check-In Otomatis** (merawat streak harian & kumpulkan FP).
- 🎯 **Klaim Quest & Milestones** otomatis.
- 🚀 **Referral Multiplier Engine**: Generator referral otomatis untuk memperbanyak referral akun utama.
- 📊 **Tabel Ringkasan Terminal & Export Laporan CSV** (`reports/`).
- 🛡️ **Anti-Sybil & Anti-Rate Limit**: Jeda dinamis acak antar akun, auto-retry HTTP 429 backoff, dan dukungan proxy.
- ⏰ **Loop Mode 24 Jam**: Berjalan otomatis setiap hari tanpa perlu dibuka manual.

---

## 🛠️ Instalasi & Persiapan

1. **Clone repositori**:
   ```bash
   git clone https://github.com/bitsmith826/raflux-daily.git
   cd raflux-daily
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Salin file konfigurasi & template**:
   ```bash
   # Di Linux / Mac:
   cp config/config.example.json config/config.json
   cp data/wallets.example.txt data/wallets.txt
   cp data/proxies.example.txt data/proxies.txt
   cp data/referral_targets.example.txt data/referral_targets.txt

   # Di Windows (PowerShell):
   copy config/config.example.json config/config.json
   copy data/wallets.example.txt data/wallets.txt
   copy data/proxies.example.txt data/proxies.txt
   copy data/referral_targets.example.txt data/referral_targets.txt
   ```

---

## 🚀 3 Cara Memasukkan Akun

Pilih salah satu metode yang paling sesuai:

### 1. Masukkan Private Key Manual
Buka file `data/wallets.txt` lalu paste private key (format Base58 string atau array byte), satu baris per akun:
```text
5Mii... (private key akun 1)
4p6H... (private key akun 2)
7kxE... (private key akun 3)
```

### 2. Auto-Derivasi dari 1 Seed Phrase (Mnemonic)
Jika puluhan akun Anda dibuat dari 1 seed phrase (12 atau 24 kata) yang sama di Phantom/Solflare:
```bash
python import_mnemonic.py
```
Masukkan 12/24 kata seed phrase dan jumlah akun (misal `30`). Script akan menderivasi jalur standar `m/44'/501'/x'/0'` dan menyimpannya langsung ke `data/wallets.txt`.

### 3. Generate Akun Baru dari Nol (Fresh Keypairs)
Jika ingin membuat akun baru secara instan:
```bash
python generate_wallets.py 30
```

---

## ⚙️ Konfigurasi (`config/config.json`)

```json
{
  "referral_code": "KODE_REFERRAL_ANDA",
  "fallback_referral_code": "",
  "auto_claim_referral": true,
  "auto_collect_welcome_points": true,
  "auto_daily_checkin": true,
  "auto_claim_quests": true,
  "delay_between_wallets_sec": [2, 4],
  "enable_proxy": false,
  "loop_mode": false,
  "loop_interval_hours": 24,
  "api_base_url": "https://api.raflux.io/solana/v1"
}
```

---

## 🏃 Cara Penggunaan

### 1. Daily Check-In & Farm Saldo (Main Bot)
Jalankan bot untuk memproses seluruh akun yang terdaftar di `data/wallets.txt`:
```bash
python main.py
```

### 2. Mode Loop Otomatis 24 Jam
Jalankan tanpa henti setiap hari secara otomatis:
```bash
python main.py --loop
```

### 3. Memperbanyak Referral (Referral Booster)
Untuk membuat akun referral baru secara otomatis ke link referral Anda:
1. Isi file `data/referral_targets.txt` dengan link referral Anda (atau masukkan langsung saat diminta di terminal).
2. Jalankan perintah:
   ```bash
   python referral_booster.py
   # atau
   python main.py --boost-ref
   ```
Setiap target akan diisi akun fresh yang otomatis mengklaim kode referral, welcome bonus (+20 FP), dan check-in (+1 FP). Hasil disimpan terpisah di `data/referrals_generated.txt` dan `reports/`.

---

## 🛡️ Penggunaan Proxy (Opsional)

Jika ingin menggunakan proxy:
1. Masukkan daftar proxy di `data/proxies.txt`:
   ```text
   http://username:password@ip:port
   http://ip:port
   socks5://ip:port
   ```
2. Ubah `"enable_proxy": true` di `config/config.json`.
3. Anda juga bisa menjalankan mode paralel multi-threading jika memakai proxy:
   ```bash
   python main.py --threads=3
   ```

---

## 📈 Laporan Hasil (CSV / Excel)

Setiap sesi eksekusi menghasilkan file CSV rapi di folder `reports/`:
- Format: `reports/raflux_report_YYYYMMDD_HHMMSS.csv`
- Berisi rekapitulasi: Alamat Wallet, Username, Status Referral, Status Check-In, Streak Harian, dan Saldo Flux Points.

---

## 📜 Lisensi & Etika Penggunaan

Proyek ini dirilis di bawah lisensi terbuka untuk tujuan edukasi. Harap gunakan perangkat lunak ini secara bertanggung jawab dan selalu patuhi hukum serta regulasi setempat yang berlaku.
