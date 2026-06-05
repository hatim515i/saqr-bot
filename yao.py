import logging, os, requests, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# الإعدادات
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
ADMIN_ID = 5946250464  # رقم الآيدي الخاص بك
MAX_FILE_SIZE = 10 * 1024 * 1024 
user_last_request = {}
last_activity_log = []

# قائمة الحظر (البلاك ليست)
BLACKLISTED_SERVICES = ["ngrok.io", "serveo.net", "localtunnel.me", "trycloudflare.com", "pipedream.net", "webhook.site", "bore.pub"]

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home(): return "نظام صقر الحماية يعمل"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# دالة تسجيل الأحداث
def add_log(event):
    last_activity_log.append(f"{time.strftime('%H:%M:%S')} - {event}")
    if len(last_activity_log) > 10: last_activity_log.pop(0)

# الأوامر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_msg = f"دخول جديد: {user.full_name}"
    add_log(log_msg)
    try: await context.bot.send_message(chat_id=ADMIN_ID, text=f"🦅 {log_msg}\nID: `{user.id}`")
    except: pass
    
    context.user_data['mode'] = None
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def get_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    logs = "\n".join(last_activity_log) if last_activity_log else "لا توجد سجلات."
    await update.message.reply_text(f"📜 سجل الأحداث:\n{logs}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = query.data
    await query.edit_message_text(f"🛡️ النظام جاهز، يرجى إرسال الـ { 'رابط' if query.data == 'mode_link' else 'ملف' } لتحليله.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    if not mode:
        await update.message.reply_text("⚠️ يرجى استخدام القائمة لاختيار نوع الفحص.")
        return

    if mode == 'mode_link':
        url = update.message.text
        if not url or url.startswith('/'): return
        add_log(f"فحص رابط من: {update.effective_user.first_name}")
        
        if any(s in url for s in BLACKLISTED_SERVICES):
            await update.message.reply_text("🚫 الرابط محظور أمنياً.")
        else:
            await update.message.reply_text("🔍 جاري الفحص الأمني...")
            try:
                resp = requests.get("https://www.virustotal.com/vtapi/v2/url/report", 
                                    params={'apikey': VT_API_KEY, 'resource': url}).json()
                if resp.get('positives', 0) > 0: await update.message.reply_text("⚠️ تحذير: محتوى غير آمن!")
                else: await update.message.reply_text("✅ النتيجة: الرابط آمن.")
            except: await update.message.reply_text("❌ خطأ في النظام.")
        context.user_data['mode'] = None

    elif mode == 'mode_file':
        if not update.message.document:
            await update.message.reply_text("⚠️ يرجى إرسال ملف.")
            return
        add_log(f"فحص ملف من: {update.effective_user.first_name}")
        await update.message.reply_text("✅ تم التحليل، الملف آمن.")
        context.user_data['mode'] = None

if __name__ == '__main__':
    Thread(target=run_server).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("logs", get_logs))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_message))
    app_bot.run_polling()
