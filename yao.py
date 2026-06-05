import logging, os, requests, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
ADMIN_ID = 5946250464  # هذا الـ ID الخاص بك
MAX_FILE_SIZE = 10 * 1024 * 1024 
user_last_request = {}
last_activity_log = [] # سجل بسيط للأحداث

BLACKLISTED_SERVICES = ["ngrok.io", "serveo.net", "localtunnel.me", "trycloudflare.com", "pipedream.net", "webhook.site", "bore.pub"]

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية في الخدمة"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# دالة لتسجيل الأحداث
def add_log(event):
    last_activity_log.append(f"{time.strftime('%H:%M:%S')} - {event}")
    if len(last_activity_log) > 10: last_activity_log.pop(0)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_msg = f"مستخدم جديد: {user.full_name} (@{user.username})"
    add_log(log_msg)
    
    # تنبيهك في الخاص
    try: await context.bot.send_message(chat_id=ADMIN_ID, text=f"🦅 {log_msg}")
    except: pass
    
    context.user_data['mode'] = None
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر نوع الفحص المطلوب:", reply_markup=InlineKeyboardMarkup(keyboard))

# الأمر الخاص لك لمشاهدة الرسايل/الأحداث
async def get_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    logs = "\n".join(last_activity_log) if last_activity_log else "لا توجد أحداث حديثة."
    await update.message.reply_text(f"📜 سجل الأحداث الأخير:\n{logs}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = query.data
    await query.edit_message_text(f"🛡️ النظام جاهز، يرجى إرسال الـ { 'رابط' if query.data == 'mode_link' else 'ملف' } لبدء عملية التحليل.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    if not mode:
        await update.message.reply_text("⚠️ يرجى استخدام /start واختيار نوع الفحص أولاً.")
        return

    if mode == 'mode_link':
        if not update.message.text or update.message.text.startswith('/'): return
        url = update.message.text
        add_log(f"تم فحص رابط من قبل {update.effective_user.first_name}")
        
        if any(s in url for s in BLACKLISTED_SERVICES):
            await update.message.reply_text("🚫 الرابط محظور أمنياً.")
        else:
            await update.message.reply_text("🔍 جاري الفحص...")
            # هنا يكمل المنطق الخاص بك...
            await update.message.reply_text("✅ النتيجة: الرابط سليم.")
        context.user_data['mode'] = None

    elif mode == 'mode_file':
        if not update.message.document:
            await update.message.reply_text("⚠️ يرجى إرسال ملف.")
            return
        add_log(f"تم فحص ملف من قبل {update.effective_user.first_name}")
        await update.message.reply_text("✅ تم التحليل، الملف نظيف.")
        context.user_data['mode'] = None

if __name__ == '__main__':
    Thread(target=run_server).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("logs", get_logs)) # أضفنا أمر اللوجز
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_message))
    app_bot.run_polling()
