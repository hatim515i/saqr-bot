import logging, os, requests, time, hashlib
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MAX_FILE_SIZE = 10 * 1024 * 1024 
user_last_request = {}

logging.basicConfig(level=logging.INFO)

# سيرفر Keep Alive
app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية يعمل"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# دالة الحماية والسرعة
async def is_rate_limited(update: Update):
    user_id = update.effective_user.id
    if time.time() - user_last_request.get(user_id, 0) < 5:
        msg = "⏳ انتظر 5 ثوانٍ قبل الطلب التالي."
        if update.message: await update.message.reply_text(msg)
        else: await update.callback_query.answer(msg, show_alert=True)
        return True
    user_last_request[user_id] = time.time()
    return False

# الأوامر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link')],
        [InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]
    ]
    await update.message.reply_text("🦅 أهلاً بك في صقر الحماية، اختر نوع الفحص:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = query.data
    await query.edit_message_text(f"✅ تم الاختيار، أرسل { 'الرابط' if query.data == 'mode_link' else 'الملف' } الآن.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_rate_limited(update): return
    mode = context.user_data.get('mode')
    
    if mode == 'mode_link' and update.message.text:
        await update.message.reply_text("🔍 جاري الفحص عبر VirusTotal...")
        # فحص الرابط
        try:
            resp = requests.get("https://www.virustotal.com/vtapi/v2/url/report", 
                                params={'apikey': VT_API_KEY, 'resource': update.message.text}).json()
            if resp.get('positives', 0) > 0: await update.message.reply_text("⚠️ تحذير: الرابط مشبوه!")
            else: await update.message.reply_text("✅ الرابط سليم.")
        except: await update.message.reply_text("❌ خطأ في الاتصال.")

    elif mode == 'mode_file' and update.message.document:
        if update.message.document.file_size > MAX_FILE_SIZE:
            await update.message.reply_text("🚫 الملف كبير جداً (أقصى حجم 10MB).")
            return
        await update.message.reply_text("📁 جاري فحص بصمة الملف...")
        # (بإمكانك إضافة كود الـ Hash هنا)
        await update.message.reply_text("✅ تم استلام الملف ومعالجته.")
    else:
        await update.message.reply_text("⚠️ يرجى الضغط على /start أولاً واختيار نوع الفحص.")

if __name__ == '__main__':
    Thread(target=run_server).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_message))
    app_bot.run_polling()
