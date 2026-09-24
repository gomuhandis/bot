import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# LinkedIn profil rasm o'lchamlari
LINKEDIN_SIZE = (800, 800)

# Rasm yaxshilash parametrlari (yuz mimikalari o'zgarmaydi)
ENHANCE_SHARPNESS = 1.3
ENHANCE_CONTRAST = 1.15
ENHANCE_BRIGHTNESS = 1.05
ENHANCE_COLOR = 1.1

# Yuz frameda qancha joy egallashi (0.0 - 1.0)
FACE_RATIO = 0.60

# Professional fon ranglari
BACKGROUNDS = {
    "blue": (0, 102, 178),        # LinkedIn ko'k
    "white": (255, 255, 255),      # Oq
    "light_gray": (240, 240, 240), # Och kulrang
    "dark_blue": (0, 51, 102),     # To'q ko'k
}

# Gradient fon sozlamalari
GRADIENT_PRESETS = {
    "blue_white": {
        "top": (0, 102, 178),
        "bottom": (220, 235, 250),
    },
    "gray": {
        "top": (180, 180, 180),
        "bottom": (240, 240, 240),
    },
}

# 9:16 Story / Status format o'lchamlari
STORY_SIZE = (1080, 1920)

# Foydalanuvchilar rasmlari saqlanadigan asosiy papka
STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_users")

