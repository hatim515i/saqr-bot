import os, requests, threading, time
from flask import Flask
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# إعداد السيرفر
PORT = int(os.environ.get('PORT', 10000))
app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية في الخدمة 🦅"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()

TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MODE = 1

# دالة فك الرابط المختصر
def get_real_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.url
    except: return url

# دالة ذكية لتحليل صفحة الموقع
def scan_page_content(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        # بحث عن خانات إدخال كلمة مرور أو إيميل
        if soup.find('input', {'type': ['password', 'email']}):
            return "⚠️ تحذير: الموقع يحتوي على خانات إدخال بيانات حساسة!"
    except: pass
    return "✅ لم يتم العثور على أنماط تصيد واضحة في المحتوى."

async def start(update, context):
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية: اختر نوع الفحص:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MODE

async def handle_content(update, context):
    mode = context.user_data.get('mode')
    status_msg = await update.message.reply_text("⏳ جاري الفحص الاحترافي...")
    headers = {"x-apikey": VT_API_KEY}

    try:
        if mode == 'link' and update.message.text:
            url = get_real_url(update.message.text) # فك الرابط أولاً
            content_check = scan_page_content(url) # فحص محتوى الصفحة
            
            # فحص VirusTotal
            resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url})
            analysis_id = resp.json()['data']['id']
            time.sleep(5)
            res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
            stats = res.json()['data']['attributes']['stats']
            
            msg = f"🛡️ تقرير الصقر:\n\n🔗 الرابط الأصلي: {url}\n{content_check}\n\n🔴 ضار: {stats['malicious']}\n🟢 آمن: {stats['harmless']}"
            await status_msg.edit_text(msg)

        elif mode == 'file' and update.message.document:
            file = await update.message.document.get_file()
            file_data = await file.download_as_bytearray()
            resp = requests.post("https://www.virustotal.com/api/v3/files", headers=headers, files={"file": ("file", file_data)})
            file_id = resp.json()['data']['id']
            time.sleep(5)
            res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{file_id}", headers=headers)
            stats = res.json()['data']['attributes']['stats']
            await status_msg.edit_text(f"🛡️ نتيجة فحص الملف:\n🔴 ضار: {stats['malicious']}\n🟢 آمن: {stats['harmless']}")

    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ: {str(e)}")
    
    context.user_data.clear()
    return ConversationHandler.END

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={MODE: [CallbackQueryHandler(lambda u, c: (c.user_data.update({'mode': u.callback_query.data.split('_')[1]}), u.callback_query.edit_message_text(f"✅ تم. أرسل الآن:"))[1] or MODE), MessageHandler(filters.ALL, handle_content)]},
        fallbacks=[CommandHandler('start', start)]
    )
    app_bot.add_handler(conv)
    app_bot.run_polling()
