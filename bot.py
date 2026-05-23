import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

# ==================== SOZLAMALAR ====================
BOT_TOKEN = "7738925861:AAFdq3j8RcE6J-3JYfGbkL6_nvgOGV65h8M"
ADMIN_IDS = [5416327548]
CHANNEL_ID = -1002184105473
CHANNEL_USERNAME = "@tarjima_kinouzbe"

logging.basicConfig(level=logging.INFO)

bot = Bot("7738925861:AAFdq3j8RcE6J-3JYfGbkL6_nvgOGV65h8M")
dp = Dispatcher(storage=MemoryStorage())

# ==================== KINOLAR BAZASI ====================
movies_db = {}

# ==================== OBUNA TEKSHIRISH ====================

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except Exception:
        return False

def subscription_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_sub")]
    ])

# ==================== FOYDALANUVCHI QISMI ====================

@dp.message(Command("start"))
async def start(message: Message):
    if not await check_subscription(message.from_user.id):
        await message.answer(
            "🎬 <b>Kino Botga Xush Kelibsiz!</b>\n\n"
            "⚠️ Botdan foydalanish uchun avval kanalimizga obuna bo'ling!\n\n"
            "📢 Kanalga obuna bo'ling va <b>✅ Obuna bo'ldim</b> tugmasini bosing!",
            parse_mode="HTML",
            reply_markup=subscription_keyboard()
        )
        return

    await message.answer(
        f"🎬 <b>Kino Botga Xush Kelibsiz!</b>\n\n"
        f"📌 <b>Qanday foydalanish:</b>\n"
        f"1️⃣ Instagramdagi postdan <b>kino kodini</b> oling\n"
        f"2️⃣ Kodni bu yerga yuboring\n"
        f"3️⃣ Kinoni yuklab oling! 🍿\n\n"
        f"📢 Kanal: {CHANNEL_USERNAME}",
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text(
            "✅ <b>Tabriklaymiz! Obuna tasdiqlandi!</b>\n\n"
            "🎬 Endi kino kodini yuboring va kinoni oling!\n\n"
            "📌 <b>Misol:</b> <code>KN001</code>",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Siz hali obuna bo'lmadingiz!", show_alert=True)

@dp.message(F.text & ~F.text.startswith("/"))
async def find_movie(message: Message):
    user_id = message.from_user.id

    # Admin emas — obuna tekshir
    if user_id not in ADMIN_IDS:
        if not await check_subscription(user_id):
            await message.answer(
                "⚠️ <b>Avval kanalga obuna bo'ling!</b>",
                parse_mode="HTML",
                reply_markup=subscription_keyboard()
            )
            return

    code = message.text.strip().upper()

    # Admin buyruqlari
    if user_id in ADMIN_IDS and code.startswith("ADD "):
        parts = code.split(" ", 1)
        if len(parts) == 2:
            dp["pending_code"] = {user_id: parts[1].strip()}
            await message.answer(
                f"✅ Kod: <b>{parts[1].strip()}</b>\n\nEndi kino faylini yuboring! 🎬",
                parse_mode="HTML"
            )
        return

    if code in movies_db:
        file_id, title = movies_db[code]
        await message.answer(f"🎬 Topildi! Yuborilmoqda...", parse_mode="HTML")
        try:
            await bot.send_video(
                chat_id=message.chat.id,
                video=file_id,
                caption=(
                    f"🎬 <b>{title}</b>\n"
                    f"📌 Kod: <code>{code}</code>\n\n"
                    f"🍿 Yaxshi tomosha!\n"
                    f"📢 Kanal: {CHANNEL_USERNAME}"
                ),
                parse_mode="HTML"
            )
        except Exception:
            await bot.send_document(
                chat_id=message.chat.id,
                document=file_id,
                caption=(
                    f"🎬 <b>{title}</b>\n"
                    f"📌 Kod: <code>{code}</code>\n\n"
                    f"🍿 Yaxshi tomosha!\n"
                    f"📢 Kanal: {CHANNEL_USERNAME}"
                ),
                parse_mode="HTML"
            )
    else:
        await message.answer(
            f"❌ <b>{code}</b> — kino topilmadi!\n\n"
            f"✅ Kodni to'g'ri yozdingizmi?\n"
            f"📢 Kanaldan tekshiring: {CHANNEL_USERNAME}",
            parse_mode="HTML"
        )

@dp.message(F.video | F.document)
async def receive_movie(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Siz admin emassiz!")
        return

    pending = dp.get("pending_code", {})
    code = pending.get(message.from_user.id)

    if not code:
        await message.answer(
            "⚠️ Avval kod bering:\n<code>/add KOD</code>",
            parse_mode="HTML"
        )
        return

    file_id = message.video.file_id if message.video else message.document.file_id
    title = message.caption or code

    movies_db[code] = (file_id, title)

    if message.from_user.id in pending:
        del pending[message.from_user.id]

    await message.answer(
        f"✅ <b>Kino qo'shildi!</b>\n\n"
        f"📌 Kod: <code>{code}</code>\n"
        f"🎬 Nomi: {title}\n\n"
        f"📸 Instagramga post qo'ying va kodni yozing!",
        parse_mode="HTML"
    )

# ==================== ADMIN BUYRUQLARI ====================

@dp.message(Command("add"))
async def add_movie(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("📝 Ishlatilishi: <code>/add KOD</code>\nKeyin fayl yuboring!", parse_mode="HTML")
        return
    code = parts[1].upper()
    dp["pending_code"] = {message.from_user.id: code}
    await message.answer(f"✅ Kod: <b>{code}</b>\n\nKino faylini yuboring! 🎬", parse_mode="HTML")

@dp.message(Command("list"))
async def list_movies(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if not movies_db:
        await message.answer("📭 Hali kino yo'q!")
        return
    text = "🎬 <b>Barcha kinolar:</b>\n\n"
    for i, (code, (_, title)) in enumerate(movies_db.items(), 1):
        text += f"{i}. <code>{code}</code> — {title}\n"
    text += f"\n📊 Jami: {len(movies_db)} ta"
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("delete"))
async def delete_movie(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("<code>/delete KOD</code>", parse_mode="HTML")
        return
    code = parts[1].upper()
    if code in movies_db:
        del movies_db[code]
        await message.answer(f"✅ <code>{code}</code> o'chirildi!", parse_mode="HTML")
    else:
        await message.answer(f"❌ <code>{code}</code> topilmadi!", parse_mode="HTML")

@dp.message(Command("stats"))
async def stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(
        f"📊 <b>Statistika:</b>\n\n"
        f"🎬 Kinolar: {len(movies_db)} ta\n"
        f"👑 Admin ID: {ADMIN_IDS[0]}",
        parse_mode="HTML"
    )

# ==================== ISHGA TUSHIRISH ====================

async def main():
    print("🤖 Kino Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
