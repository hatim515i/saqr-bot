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

# سيرفر للتشغيل
app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية يعمل"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def get_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

async def is_rate_limited(update: Update):
    user_id = update.effective_user.id
    if time.time() - user_last_request.get(user_id, 0) < 5:
        return True
    user_last_request[user_id] = time.time()
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link')],
        [InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]
    ]
    await update.message.reply_text("🦅 أهلاً بك في نظام صقر الحماية، اختر الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = query.data
    await query.edit_message_text(f"✅ تم تفعيل الوضع، أرسل { 'الرابط' if query.data == 'mode_link' else 'الملف' } وسأقوم بتحليله فوراً.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_rate_limited(update): 
        await update.message.reply_text("⏳ يرجى التريث قليلاً.")
        return
        
    mode = context.user_data.get('mode')
    
    if mode == 'mode_link' and update.message.text:
        await update.message.reply_text("🔍 جاري تحليل الرابط...")
        try:
            resp = requests.get("https://www.virustotal.com/vtapi/v2/url/report", 
                                params={'apikey': VT_API_KEY, 'resource': update.message.text}).json()
            if resp.get('positives', 0) > 0: await update.message.reply_text("⚠️ تحذير: تم اكتشاف محتوى غير آمن في هذا الرابط!")
            else: await update.message.reply_text("✅ النتيجة: الرابط آمن للاستخدام.")
        except: await update.message.reply_text("❌ حدث خطأ أثناء التحليل، يرجى المحاولة لاحقاً.")

    elif mode == 'mode_file' and update.message.document:
        if update.message.document.file_size > MAX_FILE_SIZE:
            await update.message.reply_text("🚫 الملف يتجاوز الحجم المسموح به.")
            return
        await update.message.reply_text("📁 جاري فحص الملف...")
        file = await update.message.document.get_file()
        file_path = f"{update.message.document.file_id}.tmp"
        await file.download_to_drive(file_path)
        
        file_hash = get_file_hash(file_path)
        headers = {"x-apikey": VT_API_KEY}
        resp = requests.get(f"https://www.virustotal.com/api/v3/files/{file_hash}", headers=headers).json()
        
        if 'data' in resp and resp['data']['attributes']['last_analysis_stats']['malicious'] > 0:
            await update.message.reply_text("⚠️ تحذير: تم اكتشاف برمجيات خبيثة في هذا الملف!")
        else:
            await update.message.reply_text("✅ النتيجة: الملف آمن.")
        os.remove(file_path)
    else:
        await update.message.reply_text("⚠️ يرجى الضغط على زر /start واختيار نوع الفحص أولاً.")

if __name__ == '__main__':
    Thread(target=run_server).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_message))
    app_bot.run_polling()
