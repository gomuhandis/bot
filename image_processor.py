"""
PDP University fon rasmiga odamni joylashtirish moduli.

Foydalanuvchi yuborgan rasmdan odamni ajratib oladi (background removal),
uni PDP University fonidagi (pdp.jpg) ikkita bayroq orasidagi bo'sh joyga,
markazda va tabiiy o'lchamda joylashtiradi.

Yuz mimikalari va odamning o'zi 100% asl holicha qoladi — faqat fon
almashtiriladi va rasm sifat jihatidan tinniqlashtiriladi.
"""

import io
import logging
import os
from typing import Optional

# Modellar papkasini sozlash
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)
os.environ.setdefault("U2NET_HOME", MODELS_DIR)
os.environ.setdefault("REMBG_HOME", MODELS_DIR)

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from rembg import new_session, remove

# PDP fon rasmi yo'li. config.py da PDP_BACKGROUND_PATH bo'lsa o'shani oladi,
# aks holda shu modul yonidagi assets/pdp.jpg ni ishlatadi.
try:
    from config import PDP_BACKGROUND_PATH
except ImportError:
    PDP_BACKGROUND_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "pdp.jpg"
    )

# Yakuniy rasm o'lchami. config.py da OUTPUT_SIZE bo'lsa o'shani oladi.
try:
    from config import OUTPUT_SIZE
except ImportError:
    OUTPUT_SIZE = (1080, 1080)

logger = logging.getLogger(__name__)

YUNET_MODEL_PATH = os.path.join(MODELS_DIR, "face_detection_yunet.onnx")

# Odam pdp.jpg fonida qaysi (nisbiy, 0.0-1.0) hududni egallashi kerak —
# ikkita bayroq orasidagi bo'sh joy. Fon o'zgarsa shu qiymatlarni sozlang.
PERSON_REGION = {
    "left": 0.20,    # chapdan — O'zbekiston bayrog'idan keyingi bo'sh joy
    "right": 0.80,   # o'ngdan — Buyuk Britaniya bayrog'igacha bo'sh joy
    "top": 0.30,     # yuqoridan — logo/yozuvdan pastroq
    "bottom": 0.98,  # pastgacha
}

_rembg_session = None


def get_rembg_session():
    """Rembg sessiyasini qaytaradi (bir marta yuklanadi va qayta ishlatiladi)."""
    global _rembg_session
    if _rembg_session is None:
        try:
            logger.info("rembg u2net sessiyasi yuklanmoqda...")
            _rembg_session = new_session("u2net")
            logger.info("rembg u2net sessiyasi muvaffaqiyatli yuklandi")
        except Exception as e:
            logger.warning(f"u2net yuklashda ogohlantirish: {e}, default session ishlatiladi")
            _rembg_session = new_session()
    return _rembg_session


def detect_face(image: Image.Image) -> Optional[tuple[int, int, int, int]]:
    """
    Rasmdagi yuzni aniqlaydi (OpenCV FaceDetectorYN).

    Bu funksiya faqat diagnostika/log uchun ishlatiladi — asosiy crop
    va joylashtirish logikasi fondan ajratilgan odamning shaffof
    bo'lmagan (alpha) hududiga asoslanadi. Shuning uchun ONNX model
    fayli topilmasa yoki biror sababdan ishlamasa, bot yiqilib
    qolmaydi — shunchaki None qaytadi.

    Returns:
        (x, y, w, h) tuple yoki None agar yuz topilmasa/model mavjud bo'lmasa
    """
    if not os.path.exists(YUNET_MODEL_PATH):
        logger.warning(
            f"Yuz aniqlash modeli topilmadi: {YUNET_MODEL_PATH}. "
            "Yuz aniqlash o'tkazib yuboriladi (natijaga ta'sir qilmaydi)."
        )
        return None

    try:
        img_array = np.array(image.convert("RGB"))
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        h, w = img_bgr.shape[:2]

        detector = cv2.FaceDetectorYN_create(
            YUNET_MODEL_PATH,
            "",
            (w, h),
            score_threshold=0.5,
            nms_threshold=0.3,
            top_k=5,
        )

        _, faces = detector.detect(img_bgr)

        if faces is None or len(faces) == 0:
            logger.warning("Yuz topilmadi")
            return None

        if len(faces) > 1:
            faces_sorted = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            best = faces_sorted[0]
        else:
            best = faces[0]

        x, y, fw, fh = int(best[0]), int(best[1]), int(best[2]), int(best[3])
        logger.info(f"Yuz topildi: x={x}, y={y}, w={fw}, h={fh}")
        return (x, y, fw, fh)
    except cv2.error as e:
        logger.warning(f"Yuz aniqlashda xatolik (e'tiborsiz qoldiriladi): {e}")
        return None


def remove_background(image: Image.Image) -> Image.Image:
    """
    Rasm fonini olib tashlaydi (rembg yordamida).
    Natija RGBA formatda — shaffof fon bilan.
    """
    logger.info("Fon olib tashlanmoqda...")

    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    session = get_rembg_session()
    result_bytes = remove(img_bytes, session=session)

    result = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
    logger.info("Fon olib tashlandi")
    return result


def crop_subject(
    fg_rgba: Image.Image, face_box: Optional[tuple[int, int, int, int]]
) -> Image.Image:
    """
    Ajratib olingan odamni (RGBA, shaffof fon) alpha-kanal bo'yicha
    tor qilib crop qiladi — atrofidagi ortiqcha shaffof joy olib tashlanadi.
    face_box hozircha faqat bo'sh (hech narsa topilmagan) holatlarni
    diagnostika qilish uchun qabul qilinadi.
    """
    alpha = np.array(fg_rgba.split()[-1])
    ys, xs = np.where(alpha > 10)

    if len(xs) == 0 or len(ys) == 0:
        logger.warning("Shaffof bo'lmagan piksel topilmadi, crop qilinmadi")
        return fg_rgba

    left, right = int(xs.min()), int(xs.max())
    top, bottom = int(ys.min()), int(ys.max())

    # Yengil "padding" — chekka joylar (soch uchi, yelka) kesib qolmasin
    pad_x = int((right - left) * 0.03)
    pad_y = int((bottom - top) * 0.03)
    left = max(0, left - pad_x)
    top = max(0, top - pad_y)
    right = min(fg_rgba.width, right + pad_x)
    bottom = min(fg_rgba.height, bottom + pad_y)

    return fg_rgba.crop((left, top, right, bottom))


def enhance_clarity(image: Image.Image) -> Image.Image:
    """
    Rasmni professional darajada tinniqlashtiradi:
    1. LAB rang makonida CLAHE — yorug'lik va soyalarni tabiiy ochadi.
    2. Unsharp Masking — mayda detallarni tinniq qiladi.
    3. Edge-preserving denoise — shovqinni tozalaydi, chiziqlarni saqlaydi.
    4. Yengil rang va o'tkirlik balansi.

    Yuz mimikalari va geometriyasi 100% asl holicha qoladi.
    """
    img_rgb = np.array(image.convert("RGB"))

    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    l_blended = cv2.addWeighted(l, 0.4, cl, 0.6, 0)
    lab_enhanced = cv2.merge((l_blended, a, b))
    enhanced_rgb = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)

    blurred = cv2.GaussianBlur(enhanced_rgb, (0, 0), sigmaX=2.0)
    sharpened = cv2.addWeighted(enhanced_rgb, 1.45, blurred, -0.45, 0)

    try:
        denoised = cv2.edgePreservingFilter(
            sharpened, flags=1, sigma_s=40, sigma_r=0.25
        )
    except Exception:
        denoised = sharpened

    pil_img = Image.fromarray(denoised)
    pil_img = ImageEnhance.Sharpness(pil_img).enhance(1.25)
    pil_img = ImageEnhance.Color(pil_img).enhance(1.08)
    return pil_img


def enhance_clarity_rgba(image_rgba: Image.Image) -> Image.Image:
    """
    Shaffof fonli subjectni (RGBA) tinniqlashtiradi.
    Alpha maskasi o'zgarmaydi, faqat odam qismi tinniq qilinadi.
    """
    r, g, b, a = image_rgba.split()
    rgb_img = Image.merge("RGB", (r, g, b))
    enhanced_rgb = enhance_clarity(rgb_img)
    er, eg, eb = enhanced_rgb.split()
    return Image.merge("RGBA", (er, eg, eb, a))


def composite_on_pdp_background(subject_rgba: Image.Image) -> Image.Image:
    """
    Ajratib olingan odamni PDP University foniga (pdp.jpg), ikkita bayroq
    orasidagi hududga (PERSON_REGION) joylashtiradi:
    - balandligi hudud balandligiga moslanadi (yoki kenglik yetmasa kenglikka),
    - gorizontal markazlashtiriladi,
    - pastki qismi hudud tagiga tekislanadi (odam "tik turgandek" ko'rinadi).
    """
    if not os.path.exists(PDP_BACKGROUND_PATH):
        raise FileNotFoundError(
            f"PDP fon rasmi topilmadi: {PDP_BACKGROUND_PATH}. "
            "Iltimos, pdp.jpg faylini shu manzilga joylashtiring."
        )

    bg = Image.open(PDP_BACKGROUND_PATH).convert("RGBA")
    bg_w, bg_h = bg.size

    region_left = int(bg_w * PERSON_REGION["left"])
    region_right = int(bg_w * PERSON_REGION["right"])
    region_top = int(bg_h * PERSON_REGION["top"])
    region_bottom = int(bg_h * PERSON_REGION["bottom"])
    region_w = region_right - region_left
    region_h = region_bottom - region_top

    subj_w, subj_h = subject_rgba.size

    # Avval balandlikka moslab masshtablash
    scale = region_h / subj_h
    new_w = int(subj_w * scale)

    # Kenglik hududdan oshib ketsa — kenglikka moslab qayta hisoblash
    if new_w > region_w:
        scale = region_w / subj_w
        new_w = region_w
    new_h = int(subj_h * scale)

    resized = subject_rgba.resize((new_w, new_h), Image.Resampling.LANCZOS)

    paste_x = region_left + (region_w - new_w) // 2
    paste_y = region_bottom - new_h

    result = bg.copy()
    result.paste(resized, (paste_x, paste_y), resized)
    return result.convert("RGB")


def resize_output(image: Image.Image) -> Image.Image:
    """Yakuniy rasmni OUTPUT_SIZE ga keltiradi (LANCZOS — sifatli masshtablash)."""
    return image.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)


def process_photo(image_bytes: bytes) -> dict[str, bytes]:
    """
    Asosiy qayta ishlash pipeline.

    1. Yuzni aniqlaydi.
    2. Fonni olib tashlaydi va odamni tor crop qiladi.
    3. Odamni tinniqlashtiradi.
    4. PDP University foniga, ikkita bayroq orasiga joylashtiradi.

    Returns:
        {"png": png_bytes, "jpeg": jpeg_bytes}
    """
    logger.info("Rasm qayta ishlash boshlandi...")

    original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    logger.info(f"Original o'lcham: {original.size}")

    face_box = detect_face(original)

    no_bg = remove_background(original)
    subject = crop_subject(no_bg, face_box)
    subject = enhance_clarity_rgba(subject)

    composed = composite_on_pdp_background(subject)
    composed = resize_output(composed)
    composed = ImageEnhance.Sharpness(composed).enhance(1.1)

    logger.info("Qayta ishlash tugadi.")
    return {
        "png": _to_png_bytes(composed),
        "jpeg": _to_jpeg_bytes(composed, quality=95),
    }


def _to_png_bytes(image: Image.Image) -> bytes:
    """PIL Image ni siqilgan PNG bytes ga o'giradi."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _to_jpeg_bytes(image: Image.Image, quality: int = 95) -> bytes:
    """PIL Image ni JPEG bytes ga o'giradi."""
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()