# 🔵 LinkedIn & Story Photo Processor — Telegram Bot

Telegram bot orqali rasmlaringizni LinkedIn profil rasmi (1:1) va Story (9:16) formatlarida professional, o'ta tinniq (HD) qilib moslashtiradi hamda talaba ism-familiyasi bilan shaxsiy papkaga saqlab boradi.

## ✨ Imkoniyatlari

- 👤 **Talaba ism-familiyasini so'rash va eslab qolish**
- 📁 **Shaxsiy papkaga avtomatik saqlash**: `saved_users/{Ism_Familiya}/1x1/` va `saved_users/{Ism_Familiya}/9x16/`
- 📐 **Ikkala formatni qo'llab-quvvatlash**:
  - `1:1` (800×800) — LinkedIn profil rasmi
  - `9:16` (1080×1920) — Vertikal Story / Status / Reels formati
- 🔍 **O'ta tinniq (HD) sifat**:
  - LAB rang makonida CLAHE (studiya yorug'ligi)
  - Unsharp Masking (ko'z, qosh, soch, kiyim detallari)
  - Edge-preserving denoising (shovqinni tozalash)
- ✂️ **AI Background Removal**: `u2net` yordamida fonni sifatli olib tashlash
- 🎨 **5 ta professional fon varianti**:
  1. 🔵 LinkedIn ko'k fon
  2. ⚪ Oq fon
  3. 🌊 Ko'k-oq gradient
  4. 🌫️ Kulrang gradient
  5. ✨ Original fon (tinniqlashtirilgan)
- 📱 **Qulay interfeys**:
  - Telegramda foto-albom ko'rinishida tezkor ko'rish
  - Tugma orqali `1:1` va `9:16` formatlarni almashtirish
  - Sifat yo'qolmagan lossless PNG hujjatlarni bir bosishda yuklash

> ⚡ **Yuz mimikalari va tuzilishi 100% asl holicha qoladi!**

## 📁 Papkalar tuzilishi

```
pdp_bot/
├── bot.py              # Telegram bot (handlerlar va interfeys)
├── image_processor.py  # Rasm qayta ishlash (1:1, 9:16, HD Clarity)
├── storage.py          # Foydalanuvchilar va papkalarni boshqarish
├── config.py           # Sozlamalar va o'lchamlar
├── requirements.txt    # Kutubxonalar
├── user_profiles.json  # Talabalar profili keshi
├── models/             # AI modellar (YuNet, u2net)
├── saved_users/        # Talabalarning shaxsiy rasmlar arxivi
│   └── Nurmuhammad_Fayzullayev/
│       ├── 1x1/
│       │   ├── Nurmuhammad_Fayzullayev_1x1_linkedin_blue.png
│       │   └── ...
│       ├── 9x16/
│       │   ├── Nurmuhammad_Fayzullayev_9x16_linkedin_blue.png
│       │   └── ...
│       └── original.jpg
├── .env                # Bot token
└── README.md
```

## 🛠 Ishga tushirish

```bash
cd /home/gomuhandis/Documents/pdp_bot
source venv/bin/activate
python3 bot.py
```

## 📱 Bot buyruqlari

- `/start` — Botni boshlash (ism-familiya so'raydi)
- `/ism <Ism Familiya>` — Ism-familiyani o'zgartirish (masalan: `/ism Ali Valiyev`)
- `/help` — Yordam olish
# bot
# bot
# bot
# bot
# bot
