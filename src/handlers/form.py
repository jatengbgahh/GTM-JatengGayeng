import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot, ForceReply
from telegram.ext import ContextTypes, ConversationHandler
from src.mock_data import get_branches, get_woks
from src.services.db import save_to_mysql
from src.services.sheets import save_to_gsheet
from src.config import ADMIN_CHAT_ID, TELEGRAM_BOT_TOKEN
from src.utils.geocoding import get_location_details
import asyncio

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define conversation states
SELECTING_BRANCH, SELECTING_WOK, TYPING_EVENT_NAME, CHOOSING_DEVICE, SENDING_LOCATION, CONFIRMING = range(6)

# =====================================================
# REUSABLE UI BUILDERS (Prinsip DRY)
# =====================================================

def _nav_keyboard(back_data: str) -> InlineKeyboardMarkup:
    """Buat keyboard navigasi standar [⬅️ Kembali, ❌ Batal]."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⬅️ Kembali", callback_data=back_data),
        InlineKeyboardButton("❌ Batal", callback_data="cancel")
    ]])

def _device_keyboard() -> InlineKeyboardMarkup:
    """Buat keyboard pilih perangkat [Desktop, Phone, Kembali, Batal]."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💻 Desktop", callback_data="device_desktop")],
        [InlineKeyboardButton("📱 Phone", callback_data="device_phone")],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_event_name"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel")
        ]
    ])

def _wok_keyboard(branch_id: str) -> InlineKeyboardMarkup:
    """Buat keyboard daftar WOK berdasarkan branch_id."""
    woks = get_woks(branch_id)
    keyboard = [
        [InlineKeyboardButton(wok["name"], callback_data=wok["id"])]
        for wok in woks
    ]
    keyboard.append([
        InlineKeyboardButton("⬅️ Kembali", callback_data="back_start"),
        InlineKeyboardButton("❌ Batal", callback_data="cancel")
    ])
    return InlineKeyboardMarkup(keyboard)

def _phone_location_keyboard() -> ReplyKeyboardMarkup:
    """Buat Reply Keyboard untuk kirim lokasi via Phone."""
    return ReplyKeyboardMarkup([
        [KeyboardButton("📍 Kirim Lokasi Saya", request_location=True)],
        [KeyboardButton("⬅️ Kembali"), KeyboardButton("❌ Batal")]
    ], resize_keyboard=True, one_time_keyboard=True)

# =====================================================
# REUSABLE HELPERS
# =====================================================

async def _try_delete_message(message) -> None:
    """Coba hapus pesan, abaikan error jika gagal."""
    try:
        await message.delete()
    except Exception:
        pass

async def _cleanup_phone_keyboard(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Bersihkan pesan dummy keyboard Phone jika ada."""
    msg_id = context.user_data.pop("phone_keyboard_msg_id", None)
    if msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

async def _remove_reply_keyboard(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Kirim dan hapus pesan dummy untuk menghilangkan ReplyKeyboard."""
    try:
        msg = await context.bot.send_message(chat_id=chat_id, text="⏳", reply_markup=ReplyKeyboardRemove())
        await msg.delete()
    except Exception:
        pass

async def _notify_admin(bot: Bot, error_message: str, user_data: dict):
    """Kirim laporan error ke admin bot via Telegram."""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID tidak diatur. Tidak bisa mengirim laporan error ke admin.")
        return
    
    try:
        report = (
            "🚨 *LAPORAN ERROR - GTM Bot*\n\n"
            f"👤 *User ID:* `{user_data.get('telegram_user_id', '-')}`\n"
            f"👤 *Username:* @{user_data.get('telegram_username', '-')}\n"
            f"🎉 *Event:* {user_data.get('event_name', '-')}\n"
            f"🏢 *Branch:* {user_data.get('branch', '-')}\n"
            f"🔧 *WOK:* {user_data.get('wok', '-')}\n\n"
            f"❌ *Error:*\n`{error_message}`"
        )
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=report,
            parse_mode="Markdown"
        )
        logger.info(f"Error report sent to admin (chat_id: {ADMIN_CHAT_ID})")
    except Exception as e:
        logger.error(f"Gagal mengirim laporan ke admin: {e}")

def get_form_text(user_data: dict, prompt: str) -> str:
    """Helper untuk merender state form saat ini."""
    lines = ["📋 *Form GTM JatengGayeng*\n"]
    
    fields = [
        ("🏢", "Branch", "branch"),
        ("🔧", "WOK", "wok"),
        ("🎉", "Event", "event_name"),
    ]
    for icon, label, key in fields:
        lines.append(f"{icon} *{label}:* {user_data.get(key, '-')}")
        
    if "location" in user_data:
        loc = user_data["location"]
        lines.append(f"📍 *Lokasi:* {loc['latitude']}, {loc['longitude']}")
        if "kabupaten_kota" in loc:
            lines.append(f"   ┣ 🏙 *Kab/Kota:* {loc['kabupaten_kota']}")
            lines.append(f"   ┣ 🏘 *Kecamatan:* {loc['kecamatan']}")
            lines.append(f"   ┗ 🏠 *Kel/Desa:* {loc['kelurahan_desa']}")
    else:
        lines.append("📍 *Lokasi:* -")
        
    lines.append(f"\n{prompt}")
    return "\n".join(lines)

async def _edit_form_message(context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    """Helper untuk mengedit pesan form."""
    form_message_id = context.user_data.get("form_message_id")
    chat_id = context.user_data.get("chat_id")
    if form_message_id and chat_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=form_message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to edit form message: {e}")

async def _send_force_reply(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, placeholder: str):
    """Kirim pesan dummy ForceReply untuk memfokuskan keyboard, dan catat ID-nya agar bisa dihapus."""
    await _cleanup_force_reply(context, chat_id)
    try:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=ForceReply(selective=True, input_field_placeholder=placeholder)
        )
        context.user_data["force_reply_msg_id"] = msg.message_id
    except Exception as e:
        logger.error(f"Failed to send ForceReply: {e}")

async def _cleanup_force_reply(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Hapus pesan ForceReply dummy jika ada."""
    msg_id = context.user_data.pop("force_reply_msg_id", None)
    if msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

async def _show_event_name_step(context: ContextTypes.DEFAULT_TYPE, chat_id: int, prompt: str = None):
    """Helper gabungan: update form ke step Nama Event + kirim ForceReply."""
    if not prompt:
        prompt = "Silakan ketik Nama Event (tidak boleh kosong):"
    text = get_form_text(context.user_data, prompt)
    reply_markup = _nav_keyboard("back_to_woks")
    await _edit_form_message(context, text, reply_markup)
    await _send_force_reply(context, chat_id, "👇 Silakan ketik Nama Event di sini:", "Ketik nama event...")

# =====================================================
# HANDLERS
# =====================================================

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows the main menu of the bot."""
    await _cleanup_force_reply(context, update.effective_chat.id)
    await _cleanup_phone_keyboard(context, update.effective_chat.id)

    context.user_data.clear()
    
    text = (
        "🤖 *Selamat datang di Bot GTM JatengGayeng!*\n\n"
        "Daftar Menu:\n"
        "👉 /input\_event - Memulai form input event baru"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode="Markdown"
    )

    return ConversationHandler.END

async def start_event_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the event form conversation and asks the user to select a Branch."""
    query = update.callback_query
    if query:
        await query.answer()
        
    branches = get_branches()
    keyboard = [
        [InlineKeyboardButton(branch["name"], callback_data=branch["id"])]
        for branch in branches
    ]
    keyboard.append([InlineKeyboardButton("❌ Batal", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = get_form_text(context.user_data, "Silakan pilih Branch:")
    
    if query and context.user_data.get("form_message_id"):
        await _edit_form_message(context, text, reply_markup)
    else:
        context.user_data.clear()
        chat_id = update.effective_chat.id
        
        # Hide the reply keyboard temporarily while form is active if any
        await _remove_reply_keyboard(context, chat_id)
        
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        context.user_data["form_message_id"] = msg.message_id
        context.user_data["chat_id"] = msg.chat_id

    return SELECTING_BRANCH

async def branch_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    selected_branch_id = query.data
    context.user_data["branch_id"] = selected_branch_id
    
    branches = get_branches()
    branch_name = next((b["name"] for b in branches if b["id"] == selected_branch_id), "Unknown Branch")
    context.user_data["branch"] = branch_name
    
    text = get_form_text(context.user_data, "Silakan pilih WOK:")
    await _edit_form_message(context, text, _wok_keyboard(selected_branch_id))
    
    return SELECTING_WOK

async def back_to_woks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    await _cleanup_force_reply(context, query.message.chat_id)
    
    selected_branch_id = context.user_data.get("branch_id")
    # Clean up forward state
    context.user_data.pop("wok", None)
    
    text = get_form_text(context.user_data, "Silakan pilih WOK:")
    await _edit_form_message(context, text, _wok_keyboard(selected_branch_id))
    
    return SELECTING_WOK

async def wok_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    selected_wok_id = query.data
    woks = get_woks()
    wok_name = next((w["name"] for w in woks if w["id"] == selected_wok_id), "Unknown WOK")
    context.user_data["wok"] = wok_name
    
    await _show_event_name_step(context, query.message.chat_id)
    
    return TYPING_EVENT_NAME

async def back_to_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # Clean up forward state
    context.user_data.pop("event_name", None)
    context.user_data.pop("device", None)
    context.user_data.pop("location", None)
    
    await _show_event_name_step(context, query.message.chat_id)
        
    return TYPING_EVENT_NAME

async def event_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    event_name = update.message.text.strip()
    chat_id = update.message.chat_id
    
    # Delete user's message
    await _try_delete_message(update.message)
    await _cleanup_force_reply(context, chat_id)
    
    if not event_name:
        await _show_event_name_step(context, chat_id, "⚠️ Nama Event tidak boleh kosong. Silakan ketik Nama Event:")
        return TYPING_EVENT_NAME
        
    context.user_data["event_name"] = event_name
    
    text = get_form_text(context.user_data, "Anda menggunakan perangkat apa untuk mengirim lokasi?")
    await _edit_form_message(context, text, _device_keyboard())
    
    return CHOOSING_DEVICE

async def invalid_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat_id
    await _try_delete_message(update.message)
    await _show_event_name_step(context, chat_id, "⚠️ Tolong ketik Nama Event dalam bentuk teks.")
    return TYPING_EVENT_NAME

async def back_to_device(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Clean up forward state
    context.user_data.pop("device", None)
    context.user_data.pop("location", None)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
    else:
        chat_id = update.message.chat_id
        await _try_delete_message(update.message)
        # Remove reply keyboard if returning from Phone location request
        await _remove_reply_keyboard(context, chat_id)

    text = get_form_text(context.user_data, "Anda menggunakan perangkat apa untuk mengirim lokasi?")
    await _edit_form_message(context, text, _device_keyboard())
    
    return CHOOSING_DEVICE

async def device_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    device_choice = query.data
    context.user_data["device"] = device_choice
    chat_id = query.message.chat_id
    
    if device_choice == "device_desktop":
        prompt = (
            "💻 *Anda memilih Desktop*\n\n"
            "Silakan kirimkan Tag Lokasi Anda menggunakan fitur *Location/Share Location* di Telegram.\n"
            "_(Pilih attachment 📎 -> Location)_"
        )
        text = get_form_text(context.user_data, prompt)
        await _edit_form_message(context, text, _nav_keyboard("back_to_device"))
    else:
        prompt = (
            "📱 *Anda memilih Phone*\n\n"
            "Tekan tombol di bawah untuk mengirim lokasi Anda."
        )
        text = get_form_text(context.user_data, prompt)
        await _edit_form_message(context, text, None)  # Remove inline keyboard from form
        
        # Send a dummy message with ReplyKeyboardMarkup to trigger it
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="👇 Gunakan tombol di bawah:",
            reply_markup=_phone_location_keyboard()
        )
        context.user_data["phone_keyboard_msg_id"] = msg.message_id
        
    return SENDING_LOCATION

async def location_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    location = update.message.location
    chat_id = update.message.chat_id
    
    await _try_delete_message(update.message)
    await _cleanup_phone_keyboard(context, chat_id)

    # Clear ReplyKeyboardMarkup cleanly
    if context.user_data.get("device") == "device_phone":
        await _remove_reply_keyboard(context, chat_id)
        
    if not location:
        device_choice = context.user_data.get("device", "device_phone")
        if device_choice == "device_desktop":
            text = get_form_text(context.user_data, "⚠️ Tolong kirimkan lokasi (attachment 📎 -> Location).")
            await _edit_form_message(context, text, _nav_keyboard("back_to_device"))
        else:
            text = get_form_text(context.user_data, "⚠️ Tolong kirimkan lokasi menggunakan tombol di bawah.")
            await _edit_form_message(context, text, None)
            
            msg = await context.bot.send_message(chat_id=chat_id, text="👇 Gunakan tombol di bawah:", reply_markup=_phone_location_keyboard())
            context.user_data["phone_keyboard_msg_id"] = msg.message_id
            
        return SENDING_LOCATION
        
    context.user_data["location"] = {
        "latitude": location.latitude,
        "longitude": location.longitude
    }
    
    # Update temporary UI state
    await _edit_form_message(context, get_form_text(context.user_data, "⏳ Memproses detail alamat..."), None)
    
    # Fetch detailed address
    details = await get_location_details(location.latitude, location.longitude)
    context.user_data["location"].update(details)
    
    prompt = "Apakah data di atas sudah benar? Klik *Submit* untuk menyimpan data."
    text = get_form_text(context.user_data, prompt)
    
    keyboard = [
        [InlineKeyboardButton("✅ Submit", callback_data="submit_data")],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_device"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel")
        ]
    ]
    await _edit_form_message(context, text, InlineKeyboardMarkup(keyboard))
    
    return CONFIRMING

async def invalid_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _try_delete_message(update.message)
        
    device_choice = context.user_data.get("device", "device_phone")
    
    if device_choice == "device_desktop":
        text = get_form_text(context.user_data, "⚠️ Tolong kirimkan lokasi (attachment 📎 -> Location).")
        await _edit_form_message(context, text, _nav_keyboard("back_to_device"))
    else:
        text = get_form_text(context.user_data, "⚠️ Tolong kirimkan lokasi menggunakan tombol di bawah.")
        await _edit_form_message(context, text, None)
        
    return SENDING_LOCATION

async def submit_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    chat_id = query.message.chat_id
    
    # Mark form as processing
    await _edit_form_message(context, get_form_text(context.user_data, "⏳ Sedang memproses submit data..."), None)
    
    final_data = {
        "telegram_user_id": user.id,
        "telegram_username": user.username,
        "branch": context.user_data.get("branch"),
        "wok": context.user_data.get("wok"),
        "event_name": context.user_data.get("event_name"),
        "location": context.user_data.get("location")
    }
    
    logger.info("=== DATA SUBMITTED ===")
    logger.info(final_data)
    logger.info("======================")
    
    combined_result = await save_to_mysql(final_data, sheet_callback=save_to_gsheet)
    mysql_result = combined_result.get("mysql", {"success": False, "error": "Unknown error"})
    sheets_result = combined_result.get("sheets", {"success": False, "error": "Unknown error"})
    
    errors = []
    if not mysql_result["success"]:
        errors.append(("MySQL/Database", mysql_result["error"]))
    if not sheets_result["success"]:
        errors.append(("Google Sheets", sheets_result["error"]))
    
    bot = context.bot
    
    # Finalize form message
    if not errors:
        await _edit_form_message(context, get_form_text(context.user_data, "✅ *Data berhasil disubmit!*"), None)
        
        new_text = (
            "🎉 *Data Event Berhasil Disimpan!*\n\n"
            f"Terima kasih telah memasukkan data event *{final_data['event_name']}*.\n\n"
            "Ketik /input\_event untuk menginput data baru."
        )
        await bot.send_message(chat_id=chat_id, text=new_text, parse_mode="Markdown")
        
    elif len(errors) == 2:
        error_details = "\n".join([f"• *{name}:* `{err}`" for name, err in errors])
        await _edit_form_message(context, get_form_text(context.user_data, "❌ *Gagal menyimpan data!*"), None)
        
        new_text = (
            "❌ *Gagal menyimpan data!*\n\n"
            "Data tidak berhasil disimpan ke Database maupun Google Sheets.\n\n"
            f"{error_details}\n\n"
            "Admin telah diberitahu. Silakan coba /input\_event lagi nanti."
        )
        await bot.send_message(chat_id=chat_id, text=new_text, parse_mode="Markdown")
        
        admin_error_msg = "\n".join([f"[{name}] {err}" for name, err in errors])
        await _notify_admin(bot, admin_error_msg, final_data)
    else:
        failed_name, failed_error = errors[0]
        success_name = "Google Sheets" if failed_name == "MySQL/Database" else "MySQL/Database"
        
        await _edit_form_message(context, get_form_text(context.user_data, "⚠️ *Data sebagian berhasil disimpan.*"), None)
        
        new_text = (
            f"⚠️ *Data sebagian berhasil disimpan.*\n\n"
            f"✅ *{success_name}:* Berhasil\n"
            f"❌ *{failed_name}:* Gagal\n"
            f"Error: `{failed_error}`\n\n"
            "Admin telah diberitahu.\n"
            "Ketik /input\_event untuk menambah data baru."
        )
        await bot.send_message(chat_id=chat_id, text=new_text, parse_mode="Markdown")
        
        await _notify_admin(bot, f"[{failed_name}] {failed_error}", final_data)
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    chat_id = context.user_data.get("chat_id", update.effective_chat.id)
    
    await _cleanup_phone_keyboard(context, chat_id)
    await _cleanup_force_reply(context, chat_id)
    await _remove_reply_keyboard(context, chat_id)

    prompt = "❌ *Proses dibatalkan.*\n\nKetik /start untuk melihat menu utama."
    text = get_form_text(context.user_data, prompt)
    
    try:
        if update.callback_query:
            await update.callback_query.answer()
            await _edit_form_message(context, text, None)
        else:
            await _try_delete_message(update.message)
            await _edit_form_message(context, text, None)
    except Exception:
        pass
        
    context.user_data.clear()
    return ConversationHandler.END
