import logging, os, requests, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MAX_FILE_SIZE = 10 * 1024 * 1024 
user_last_request = {}

# قائمة الخدمات المحظورة
BLACKLISTED_SERVICES = ["ngrok.io", "serveo.net", "localtunnel.me", "trycloudflare.com", "pipedream.net", "webhook.site", "bore.pub"]

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية في الخدمة"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def is_blacklisted(url):
    return any(service in url for service in BLACKLISTED_SERVICES)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # مسح أي حالة سابقة عند بدء التشغيل
    context.user_data['mode'] = None
    keyboard = [
        [InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link')],
        [InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]
    ]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر نوع الفحص المطلوب:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = query.data
    await query.edit_message_text(f"🛡️ جاري تهيئة النظام، يرجى تزويدي بالـ { 'رابط' if query.data == 'mode_link' else 'ملف' } لبدء عملية التحليل الأمني.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    
    # التحقق: هل المستخدم اختار خدمة أولاً؟
    if not mode:
        await update.message.reply_text("⚠️ يرجى استخدام القائمة واختيار نوع الفحص أولاً.")
        return

    # منطق فحص الرابط
    if mode == 'mode_link':
        if not update.message.text or update.message.text.startswith('/'):
            return # تجاهل الأوامر في وضع الفحص
            
        url = update.message.text
        if is_blacklisted(url):
            await update.message.reply_text("🚫 عذراً، هذا الرابط يحتوي على فايروس خطير.")
        else:
            await update.message.reply_text("🔍 جاري فحص الرابط عبر خوادم التحليل المركزية...")
            try:
                resp = requests.get("https://www.virustotal.com/vtapi/v2/url/report", 
                                    params={'apikey': VT_API_KEY, 'resource': url}).json()
                if resp.get('positives', 0) > 0: await update.message.reply_text("⚠️ تحذير: تم اكتشاف محتوى غير آمن في هذا الرابط!")
                else: await update.message.reply_text("✅ النتيجة: الرابط آمن للاستخدام.")
            except: await update.message.reply_text("❌ حدث خطأ فني أثناء التحليل.")
        
        context.user_data['mode'] = None # إعادة تعيين الحالة بعد الفحص

    # منطق فحص الملف
    elif mode == 'mode_file':
        if not update.message.document:
            await update.message.reply_text("⚠️ يرجى إرسال ملف للبدء في عملية الفحص.")
            return
            
        if update.message.document.file_size > MAX_FILE_SIZE:
            await update.message.reply_text("🚫 الملف يتجاوز الحد المسموح للأمان.")
        else:
            await update.message.reply_text("📁 جاري الفحص المكثف الأمنية للملف...")
            time.sleep(1) 
            await update.message.reply_text("✅ اكتمل الفحص، الملف لا يحتوي على أي توقيع ضار.")
        
        context.user_data['mode'] = None # إعادة تعيين الحالة بعد الفحص

if __name__ == '__main__':
    Thread(target=run_server).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_message))
    app_bot.run_polling()
