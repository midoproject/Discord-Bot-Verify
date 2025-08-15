# Discord Verify Bot (✅) — Termux Android + GitHub (Pemula Friendly)

Template bot Discord **siap pakai**: verifikasi emoji ✅ untuk kasih role, plus **autorole on join (opsional)**.
Didesain untuk **HP Android via Termux**, **upload ke GitHub**, dan **jalan 24/7** pakai `tmux` / Termux:Boot.

---

## 0) Buat Bot di Discord Developer Portal (wajib, sekali saja)
1. Buka https://discord.com/developers/applications → **New Application** → beri nama (misal: *VerifyBot*).
2. Tab **Bot** → **Add Bot** → **Yes, do it!** → **Reset Token** → **Copy** token (simpan rahasia).
3. Masih di tab **Bot** → **Privileged Gateway Intents**:
   - Aktifkan **MESSAGE CONTENT INTENT** (opsional).
   - Aktifkan **SERVER MEMBERS INTENT** (**wajib** untuk add/remove role).
   - **Save Changes** kalau ada.
4. Tab **OAuth2 → URL Generator**:
   - **Scopes**: centang `bot` dan `applications.commands`.
   - **Bot Permissions** minimal: `Read Messages/View Channels`, `Send Messages`, `Manage Roles`, `Add Reactions`, `Read Message History`.
   - Copy **Generated URL** → buka di browser → pilih server kamu → **Authorize**.
5. Di server Discord kamu, buka **Server Settings → Roles** → **pastikan role bot** berada **di atas** role yang akan diberikan oleh verifikasi / autorole.

> **Penting:** Token = rahasia. Jangan pernah commit ke GitHub. Simpan di `.env` saja.

---

## 1) Siapkan Termux di Android
```bash
pkg update && pkg upgrade -y
pkg install -y python git tmux nano
pip install --upgrade pip
termux-setup-storage   # izinkan storage (opsional)
```

---

## 2) Download template (dari ChatGPT) & jalankan
1. Extract folder **discord-verify-bot** ke direktori kerja di Termux (misal `~/discord-verify-bot`).
2. Masuk folder & buat virtual env + install dependency:
```bash
cd discord-verify-bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Salin & isi file **.env**:
```bash
cp .env.example .env
nano .env
# isi DISCORD_TOKEN=TOKEN_BOT_KAMU
```
4. Jalankan bot untuk test:
```bash
python src/bot.py
```
5. Di server kamu:
   - Jalankan `/setup_verify` → pilih **channel** tempat pesan verifikasi, **role** yang diberikan, opsional **pesan** & **emoji** (default ✅).
   - Bot akan kirim **pesan verifikasi** + auto-react ✅.
   - Member react ✅ → **role otomatis ditambahkan**. Jika unreact, role dicabut (bisa diubah lewat kode).

Cek status: `/verify_status` • Nyalakan/Matikan: `/verify_on`, `/verify_off` • Reset: `/reset_verify`.

**Autorole on join (opsional):**
- Set role: `/set_autorole` → pilih role.
- ON/OFF: `/autorole_on`, `/autorole_off` • Cek: `/autorole_status`.

---

## 3) Upload project ke GitHub (HTTPS + Personal Access Token)
> GitHub **tidak pakai password** untuk push. Pakai **PAT (classic)** sebagai *password* saat `git push`.

1. Buat repo kosong di GitHub (misal `discord-verify-bot`).
2. Buat **Personal Access Token (classic)**: Settings → Developer settings → Personal access tokens → **Tokens (classic)** → **Generate new token** → centang `repo` → **Generate** → **copy** token (simpan).
3. Inisialisasi & push:
```bash
git init
git config user.name "Nama Kamu"
git config user.email "emailmu@example.com"
git remote add origin https://github.com/<username>/<repo>.git
git add .
git commit -m "feat: initial verify bot"
git branch -M main
git push -u origin main
```
Saat diminta:
- **Username** = username GitHub kamu
- **Password** = **PAT** (token) yang tadi dibuat

Opsional (biar ga ketik token terus):
```bash
git config credential.helper store
# lalu git push sekali, token tersimpan di ~/.git-credentials
```

> **Catatan:** File `.env` & `.venv` sudah di-ignore oleh `.gitignore` (aman dari kebocoran token).

---

## 4) Jalanin 24/7 di Termux
Pakai `tmux` supaya bot tetap jalan meski Termux ditutup:
```bash
source .venv/bin/activate
tmux new -s bot
python src/bot.py
# detach: Ctrl+b lalu d
# balik:  tmux attach -t bot
```

### (Opsional) Auto start saat HP reboot – Termux:Boot
1. Install **Termux:Boot** dari F-Droid.
2. Buat file start:
```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/start.sh
```
Isi:
```bash
#!/data/data/com.termux/files/usr/bin/bash
cd ~/discord-verify-bot
source .venv/bin/activate
tmux new -d -s bot "python src/bot.py"
```
Simpan & beri izin:
```bash
chmod +x ~/.termux/boot/start.sh
```

---

## 5) Struktur Project
```
discord-verify-bot/
├─ .env.example
├─ .gitignore
├─ LICENSE
├─ README.md
├─ requirements.txt
├─ src/
│  └─ bot.py
└─ (config.json)  # dibuat otomatis saat bot jalan
```

---

## 6) Troubleshooting
- **`ModuleNotFoundError: No module named 'discord'`**
  - Aktifkan venv & install deps: `source .venv/bin/activate && pip install -r requirements.txt`
- **Slash command tidak muncul**
  - Tunggu 1–5 menit (cache Discord). Pastikan invite pakai scope `applications.commands`. Kalau perlu, kick bot & invite ulang.
- **Role tidak nempel saat react**
  - Pastikan bot punya **Manage Roles** dan **role bot** di atas role target di Server Settings → Roles.
- **`Invalid username or token` saat git push**
  - Password = **PAT**, bukan password akun GitHub.
- **Termux auto-matikan proses**
  - Pastikan pakai `tmux` dan kecualikan Termux dari battery optimization di Android Settings.

---

## 7) Keamanan
- Token **jangan** dipublish. Simpan hanya di `.env` (sudah di `.gitignore`).
- Kalau token bocor, reset dari tab **Bot** di Developer Portal.

Selamat mencoba! 🎉
