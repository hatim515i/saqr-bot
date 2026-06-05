import os, requests, time, threading
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# إعدادات النظام
PORT = int(os.environ.get('PORT', 10000))
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MAX_FILE_SIZE = 10 * 1024 * 1024 

# مراحل المحادثة
CHOOSING = 1

# --- الدوال الأمنية (الفحص) ---
def get_final_url(url):
    try:
        res = requests.head(url, allow_redirects=True, timeout=5)
        return res.url
    except: return url

def deep_scan_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        return bool(soup.find('input', {'type': 'password'}))
    except: return False

def vt_check(data, is_file=False):
    try:
        headers = {"x-apikey": VT_API_KEY}
        url = "https://www.virustotal.com/api/v3/files" if is_file else "https://www.virustotal.com/api/v3/urls"
        data_payload = {"url": data} if not is_file else {"file": data}
        
        resp = requests.post(url, headers=headers, files=data_payload if is_file else None, data=data_payload if not is_file else None)
        analysis_id = resp.json()['data']['id']
        time.sleep(5) # انتظار الفحص
        res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
        stats = res.json()['data']['attributes']['stats']
        return stats['malicious'] > 0
    except: return False

# --- معالجات البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 فحص رابط", callback_data='link')],
        [InlineKeyboardButton("📁 فحص ملف", callback_data='file')]
    ]
    await update.message.reply_text("🦅 صقر الحماية: اختر نوع الفحص للبدء:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING

async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['mode'] = query.data
    await query.answer()
    await query.edit_message_text(f"✅ تم اختيار {query.data}. أرسل الآن {query.data} للفحص:")
    return CHOOSING

async def handle_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    if not mode:
        await update.message.reply_text("⚠️ يرجى الضغط على /start أولاً لاختيار وضع الفحص.")
        return CHOOSING

    status_msg = await update.message.reply_text("🦅 جاري تشغيل فحص صقر الحماية...")
    
    is_bad = False
    if mode == 'link' and update.message.text:
        url = get_final_url(update.message.text)
        is_bad = vt_check(url) or deep_scan_url(url)
        report = f"🛡️ **تقرير صقر الحماية**\n🔗 الرابط: {url}\nالنتيجة: {'❌ خطر!' if is_bad else '✅ آمن.'}"
    
    elif mode == 'file' and update.message.document:
        doc = update.message.document
        if doc.file_size > MAX_FILE_SIZE:
            report = "❌ الملف كبير جداً (أكثر من 10MB)."
        else:
            file_bytes = await (await doc.get_file()).download_as_bytearray()
            is_bad = vt_check(file_bytes, is_file=True)
            report = f"🛡️ **تقرير صقر الحماية**\nملف: {doc.file_name}\nالنتيجة: {'❌ خطر!' if is_bad else '✅ آمن.'}"
    else:
        report = "⚠️ أرسل الشيء الصحيح بناءً على اختيارك (رابط أو ملف)."

    await status_msg.edit_text(report)
    context.user_data.clear() # مسح البيانات بعد الفحص
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={CHOOSING: [CallbackQueryHandler(choice_handler), MessageHandler(filters.ALL & (~filters.COMMAND), handle_scan)]},
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv_handler)
    threading.Thread(target=lambda: os.system(f"python3 -m http.server {PORT}"), daemon=True).start()
    app.run_polling()
