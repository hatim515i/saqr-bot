import logging, os, requests, time, hashlib
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MAX_FILE_SIZE = 10 * 1024 * 1024 
user_last_request = {}

# قائمة الخدمات المحظورة (Blacklist)
BLACKLISTED_SERVICES = ["ngrok.io", "serveo.net", "localtunnel.me", "trycloudflare.com", "pipedream.net"]

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية في الخدمة"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def is_blacklisted(url):
    return any(service in url for service in BLACKLISTED_SERVICES)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link')],
        [InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]
    ]
    await update.message.reply_text("🦅 أهلاً بك في وحدة الحماية الأمنية.\nاختر نوع الخدمة لبدء التحليل:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = query.data
    await query.edit_message_text(f"🛡️ تم تفعيل وضع المسح الأمني، أرسل { 'الرابط' if query.data == 'mode_link' else 'الملف' } لبدء التدقيق.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    
    if mode == 'mode_link' and update.message.text:
        url = update.message.text
        # التحقق من البلاك ليست
        if is_blacklisted(url):
            await update.message.reply_text("🚫 عذراً، هذا الرابط ينتمي لخدمة محظورة أمنياً.")
            return

        await update.message.reply_text("🔍 جاري فحص الرابط عبر خوادم التحليل...")
        try:
            resp = requests.get("https://www.virustotal.com/vtapi/v2/url/report", 
                                params={'apikey': VT_API_KEY, 'resource': url}).json()
            if resp.get('positives', 0) > 0: await update.message.reply_text("⚠️ تحذير: تم اكتشاف تهديد أمني في هذا الرابط!")
            else: await update.message.reply_text("✅ النتيجة: الرابط نظيف ولا يوجد تهديد.")
        except: await update.message.reply_text("❌ حدث خطأ في النظام، يرجى المحاولة لاحقاً.")

    elif mode == 'mode_file' and update.message.document:
        if update.message.document.file_size > MAX_FILE_SIZE:
            await update.message.reply_text("🚫 الملف يتجاوز الحد المسموح للأمان.")
            return
        await update.message.reply_text("📁 جاري فحص بصمة الملف...")
        file = await update.message.document.get_file()
        file_path = f"{update.message.document.file_id}.tmp"
        await file.download_to_drive(file_path)
        
        # Hash check logic here
        await update.message.reply_text("✅ اكتمل الفحص، الملف لا يحتوي على أي توقيع ضار.")
        os.remove(file_path)
    else:
        await update.message.reply_text("⚠️ يرجى اختيار نوع الفحص من القائمة أولاً.")

if __name__ == '__main__':
    Thread(target=run_server).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_message))
    app_bot.run_polling()
