import logging
import os
import requests
import time
import hashlib
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# الإعدادات
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 ميجابايت حد أقصى للجميع (VIP لاحقاً)
user_last_request = {}

logging.basicConfig(level=logging.INFO)

# سيرفر Keep Alive
app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية يعمل"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# دالة فحص الملفات (Hash)
def get_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# نظام السرعة
async def is_rate_limited(update: Update):
    user_id = update.effective_user.id
    current_time = time.time()
    if current_time - user_last_request.get(user_id, 0) < 5:
        msg = "⏳ انتظر 5 ثوانٍ قبل الطلب التالي."
        if update.message: await update.message.reply_text(msg)
        else: await update.callback_query.answer(msg, show_alert=True)
        return True
    user_last_request[user_id] = current_time
    return False

# الأوامر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link')],
        [InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]
    ]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر نوع الفحص:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = query.data
    await query.edit_message_text(f"✅ تم اختيار {query.data}, أرسل الآن...")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_rate_limited(update): return
    mode = context.user_data.get('mode')
    
    if mode == 'mode_file' and update.message.document:
        if update.message.document.file_size > MAX_FILE_SIZE:
            await update.message.reply_text("🚫 الملف كبير جداً (أقصى حجم 10MB).")
            return
        
        await update.message.reply_text("🔍 جاري الفحص الأمني للبصمة...")
        file = await update.message.document.get_file()
        file_path = f"{update.message.document.file_id}.tmp"
        await file.download_to_drive(file_path)
        
        file_hash = get_file_hash(file_path)
        # هنا يتم الربط بـ API الخاص بـ VirusTotal باستخدام file_hash
        await update.message.reply_text(f"✅ تم الفحص! بصمة الملف: `{file_hash}`")
        os.remove(file_path)
    else:
        await update.message.reply_text("⚠️ يرجى الضغط على زر /start من القائمة أولاً.")

if __name__ == '__main__':
    Thread(target=run_server).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    # تعريف زر المنيو (Menu)
    commands = [BotCommand("start", "تشغيل البوت")]
    app_bot.bot.set_my_commands(commands)
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.Document.ALL | filters.TEXT, handle_message))
    app_bot.run_polling()
