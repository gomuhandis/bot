"""
PDP University fon rasmiga odam qo'yish — Telegram Bot

Foydalanuvchining ism-familiyasini so'rab, shaxsiy papkasiga saqlaydi.
Yuborilgan rasmdagi odamni ajratib olib, PDP University fonidagi
(pdp.jpg) ikkita bayroq orasiga, markazda joylashtirib beradi.
"""

import asyncio
import io
import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from config import BOT_TOKEN, STORAGE_DIR
from image_processor import process_photo
from storage import get_user_profile, sanitize_name, save_user_profile

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start buyrug'i — botni tanishtirish va ism-familiya so'rash.
    """
    user = update.effective_user
    full_name = get_user_profile(user.id)

    if not full_name:
        context.user_data["awaiting_name"] = True
        welcome_text = (
            "👋 *Assalomu alaykum!*\n\n"
            "Men rasmingizdagi odamni ajratib olib, *PDP University* fonida "
            "ikkita bayroq orasida turgandek qilib tayyorlab beraman.\n\n"
            "📸 Rasm o'ta tinniq (HD) sifatga keltiriladi va shaxsiy "
            "papkangizga avtomatik saqlanadi.\n\n"
            "✍️ Boshlash uchun, iltimos, **ism va familiyangizni** yuboring:\n"
            "_(Masalan: Ali Valiyev)_"
        )
    else:
        safe_name = sanitize_name(full_name)
        welcome_text = (
            f"👋 *Assalomu alaykum, {full_name}!*\n\n"
            "Rasmingizni yuboring (foto yoki hujjat ko'rinishida) 📷\n\n"
            f"📁 Rasmingiz shaxsiy papkangizga saqlanadi: `saved_users/{safe_name}/`\n\n"
            "✏️ Ism-familiyani o'zgartirish: `/ism Yangi Ism-Familiya`"
        )

    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def ism_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /ism yoki /name buyrug'i — ism-familiyani o'zgartirish.
    """
    user = update.effective_user
    args = context.args

    if args:
        new_name = " ".join(args).strip()
        save_user_profile(user.id, new_name)
        context.user_data["awaiting_name"] = False
        await update.message.reply_text(
            f"✅ Ism-familiyangiz saqlandi: *{new_name}*!\n\n"
            "Endi menga rasmingizni yuborishingiz mumkin 📷",
            parse_mode="Markdown",
        )
    else:
        context.user_data["awaiting_name"] = True
        await update.message.reply_text(
            "✍️ Iltimos, yangi **ism va familiyangizni** yuboring:\n_(Masalan: Ali Valiyev)_",
            parse_mode="Markdown",
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /help buyrug'i — yordam.
    """
    help_text = (
        "ℹ️ *Qanday ishlatiladi:*\n\n"
        "1️⃣ Ism va familiyangizni kiriting\n"
        "2️⃣ Rasmingizni yuboring (foto yoki fayl ko'rinishida)\n"
        "3️⃣ Bot sizni *PDP University* fonida, ikkita bayroq orasida "
        "turgandek qilib tayyorlaydi\n"
        "4️⃣ Rasm sizning shaxsiy papkangizga avtomatik saqlanadi\n"
        "5️⃣ Telegramdan to'g'ridan-to'g'ri ko'rasiz va PNG fayl holida yuklab olasiz\n\n"
        "🔧 *Buyruqlar:*\n"
        "/start — Botni boshlash\n"
        "/ism <Ism Familiya> — Ismni o'zgartirish\n"
        "/help — Yordam"
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")


def _save_result(safe_name: str, result: dict) -> str:
    """Tayyor rasmni foydalanuvchining shaxsiy papkasiga saqlaydi."""
    user_folder = os.path.join(STORAGE_DIR, safe_name)
    os.makedirs(user_folder, exist_ok=True)

    with open(os.path.join(user_folder, f"{safe_name}_pdp.png"), "wb") as f:
        f.write(result["png"])
    with open(os.path.join(user_folder, f"{safe_name}_pdp.jpg"), "wb") as f:
        f.write(result["jpeg"])

    return user_folder


async def _process_and_send_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    file_id: str,
    full_name: str,
) -> None:
    """Rasmni yuklab oladi, qayta ishlaydi, saqlaydi va yuboradi."""
    safe_name = sanitize_name(full_name)

    processing_msg = await update.message.reply_text(
        f"⏳ *Rasmingiz qayta ishlanmoqda...*\n\n"
        f"👤 Talaba: *{full_name}*\n"
        "🔍 Yuz aniqlanmoqda...\n"
        "✂️ Fon olib tashlanmoqda...\n"
        "🏛 PDP University foniga joylashtirilmoqda...\n"
        "✨ O'ta tinniq (HD) sifatga keltirilmoqda...\n\n"
        "⏱ Bir necha soniya kuting...",
        parse_mode="Markdown",
    )

    try:
        file = await context.bot.get_file(file_id)
        image_bytes = await file.download_as_bytearray()
        logger.info(f"Rasm yuklandi: {len(image_bytes)} bytes")

        result = await asyncio.to_thread(process_photo, bytes(image_bytes))
        saved_folder = await asyncio.to_thread(_save_result, safe_name, result)

        chat_id = update.effective_chat.id

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=io.BytesIO(result["jpeg"]),
            caption=f"✅ *{full_name}* — PDP University",
            parse_mode="Markdown",
        )
        await context.bot.send_document(
            chat_id=chat_id,
            document=io.BytesIO(result["png"]),
            filename=f"{safe_name}_pdp.png",
            caption=f"📎 {full_name} — asl (lossless) PNG",
        )

        rel_folder = os.path.relpath(saved_folder, os.path.dirname(os.path.abspath(__file__)))
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"🎉 *Tayyor va saqlandi!*\n\n"
                f"👤 *Talaba:* {full_name}\n"
                f"📁 *Shaxsiy papka:* `{rel_folder}/`"
            ),
            parse_mode="Markdown",
        )

        try:
            await processing_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Xatolik: {e}", exc_info=True)
        await processing_msg.edit_text(
            "❌ *Xatolik yuz berdi!*\n\n"
            f"Sabab: `{str(e)[:200]}`\n\n"
            "Iltimos, boshqa rasm yuborib ko'ring.\n"
            "Yuzingiz aniq ko'rinadigan rasm yuboring.",
            parse_mode="Markdown",
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi rasm yuborganda."""
    user = update.effective_user
    full_name = get_user_profile(user.id)
    photo = update.message.photo[-1]

    if not full_name:
        context.user_data["pending_file_id"] = photo.file_id
        context.user_data["awaiting_name"] = True
        await update.message.reply_text(
            "⚠️ Rasmni qayta ishlash va shaxsiy papkangizga saqlash uchun, "
            "iltimos, avval **ism va familiyangizni** yuboring:\n\n"
            "_(Masalan: Ali Valiyev)_",
            parse_mode="Markdown",
        )
        return

    await _process_and_send_image(update, context, photo.file_id, full_name)


async def handle_document_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Document holatida yuborilgan rasmlar uchun."""
    document = update.message.document

    if document.mime_type and document.mime_type.startswith("image/"):
        if document.file_size > 20 * 1024 * 1024:
            await update.message.reply_text(
                "⚠️ Rasm hajmi juda katta (max 20MB). Kichikroq rasm yuboring."
            )
            return

        user = update.effective_user
        full_name = get_user_profile(user.id)

        if not full_name:
            context.user_data["pending_file_id"] = document.file_id
            context.user_data["awaiting_name"] = True
            await update.message.reply_text(
                "⚠️ Rasmni qayta ishlash va shaxsiy papkangizga saqlash uchun, "
                "iltimos, avval **ism va familiyangizni** yuboring:\n\n"
                "_(Masalan: Ali Valiyev)_",
                parse_mode="Markdown",
            )
            return

        await _process_and_send_image(update, context, document.file_id, full_name)
    else:
        await update.message.reply_text(
            "📷 Iltimos, rasm yuboring.\nBoshqa turdagi fayllar qabul qilinmaydi."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Matnli xabarlar va ism-familiya kiritishni qabul qilish."""
    text = update.message.text.strip()
    user = update.effective_user
    full_name = get_user_profile(user.id)

    if context.user_data.get("awaiting_name") or not full_name:
        if len(text) < 2:
            await update.message.reply_text(
                "Iltimos, haqiqiy ism va familiyangizni kiriting."
            )
            return

        save_user_profile(user.id, text)
        context.user_data["awaiting_name"] = False
        full_name = text

        pending_file_id = context.user_data.pop("pending_file_id", None)

        if pending_file_id:
            await update.message.reply_text(
                f"✅ Rahmat, *{full_name}*!\n\nRasmingiz qayta ishlanmoqda...",
                parse_mode="Markdown",
            )
            await _process_and_send_image(update, context, pending_file_id, full_name)
        else:
            safe_name = sanitize_name(full_name)
            await update.message.reply_text(
                f"✅ Rahmat, *{full_name}*!\n\n"
                f"📁 Siz uchun shaxsiy papka ochildi: `saved_users/{safe_name}/`\n\n"
                "Endi menga rasmingizni yuboring (foto yoki fayl ko'rinishida) 📷",
                parse_mode="Markdown",
            )
        return

    await update.message.reply_text(
        f"👋 Salom, *{full_name}*!\n\n"
        "PDP University foniga qo'yish uchun menga rasm yuboring 📷\n\n"
        "Ism-familiyangizni o'zgartirish uchun: `/ism Yangi Ism-Familiya`",
        parse_mode="Markdown",
    )


def main() -> None:
    """Bot ni ishga tushirish."""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN topilmadi!")
        print("📝 .env faylga BOT_TOKEN=<sizning_tokeningiz> yozing.")
        print("💡 Tokenni @BotFather dan olishingiz mumkin.")
        return

    print("🚀 Bot ishga tushmoqda...")

    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30.0,
        read_timeout=60.0,
        write_timeout=60.0,
        media_write_timeout=120.0,
        pool_timeout=10.0,
    )

    application = (
        Application.builder().token(BOT_TOKEN).request(request).build()
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ism", ism_command))
    application.add_handler(CommandHandler("name", ism_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(
        MessageHandler(filters.Document.ALL, handle_document_photo)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    print("✅ Bot tayyor! Ctrl+C bosib to'xtatishingiz mumkin.")
    print("📱 Telegram da botingizga /start yuboring.")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()