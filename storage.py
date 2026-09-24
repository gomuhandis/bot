"""
Foydalanuvchi profillarini saqlash moduli.

Har bir Telegram foydalanuvchisining ism-familiyasini oddiy JSON faylda
saqlaydi (users.json), shuningdek ismni papka/fayl nomi sifatida
ishlatish uchun xavfsiz shaklga keltiradi.
"""

import json
import logging
import os
import re
import threading

from config import STORAGE_DIR

logger = logging.getLogger(__name__)

os.makedirs(STORAGE_DIR, exist_ok=True)
PROFILES_FILE = os.path.join(STORAGE_DIR, "users.json")

_lock = threading.Lock()


def _load_profiles() -> dict:
    if not os.path.exists(PROFILES_FILE):
        return {}
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"users.json o'qishda xatolik: {e}, bo'sh profil ishlatiladi")
        return {}


def _save_profiles(profiles: dict) -> None:
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def get_user_profile(user_id: int) -> str | None:
    """Foydalanuvchining saqlangan ism-familiyasini qaytaradi, yo'q bo'lsa None."""
    with _lock:
        profiles = _load_profiles()
    return profiles.get(str(user_id))


def save_user_profile(user_id: int, full_name: str) -> None:
    """Foydalanuvchining ism-familiyasini saqlaydi."""
    with _lock:
        profiles = _load_profiles()
        profiles[str(user_id)] = full_name.strip()
        _save_profiles(profiles)
    logger.info(f"Profil saqlandi: user_id={user_id}, ism={full_name}")


def sanitize_name(full_name: str) -> str:
    """
    Ism-familiyani papka/fayl nomi sifatida xavfsiz ishlatish uchun
    tozalaydi: bo'shliqlarni pastki chiziqqa almashtiradi, ruxsat
    etilmagan belgilarni olib tashlaydi.
    """
    name = full_name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_\-]", "", name)
    name = name.strip("_")
    return name or "foydalanuvchi"