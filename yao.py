import os, requests, threading, time
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# إعداد السيرفر
PORT = int(os.environ.get('PORT', 10000))
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MODE = 1

# دالة الفحص العميق (التحليل الصدقي)
def deep_scan_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        if soup.find('input', {'type': 'password'}): return "⚠️ خطر: الموقع يطلب كلمة مرور!"
        return "✅ الفحص العميق: المحتوى يبدو آمناً."
    except: return "❌ تعذر الفحص العميق (الموقع غير متاح)."

async def start(update, context):
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='file')]]
    await update.message.reply_text("🦅 صقر الحماية: اختر نوع الفحص:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MODE

async def button_handler(update, context):
    query = update.callback_query
    context.user_data['mode'] = query.data
    await query.answer()
    await query.edit_message_text(f"✅ تم اختيار {query.data}. أرسل الآن الملف أو الرابط:")
    return MODE

async def handle_content(update, context):
    mode = context.user_data.get('mode')
    if not mode:
        await update.message.reply_text("⚠️ يرجى الضغط على /start أولاً.")
        return ConversationHandler.END
    
    status_msg = await update.message.reply_text("⏳ جاري الفحص الشامل...")
    headers = {"x-apikey": VT_API_KEY}

    try:
        if mode == 'link':
            url = update.message.text
            # 1. فحص VT
            resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url})
            analysis_id = resp.json()['data']['id']
            time.sleep(5)
            res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
            stats = res.json()['data']['attributes']['stats']
            # 2. فحص عميق
            deep = deep_scan_page(url)
            await status_msg.edit_text(f"🛡️ التقرير:\n\n🌐 VT: {stats['malicious']} ضار\n{deep}")

        elif mode == 'file':
            file = await update.message.document.get_file()
            file_data = await file.download_as_bytearray()
            resp = requests.post("https://www.virustotal.com/api/v3/files", headers=headers, files={"file": ("file", file_data)})
            file_id = resp.json()['data']['id']
            time.sleep(5)
            res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{file_id}", headers=headers)
            stats = res.json()['data']['attributes']['stats']
            await status_msg.edit_text(f"🛡️ نتيجة فحص الملف:\n🔴 ضار: {stats['malicious']}\n🟢 آمن: {stats['harmless']}")

    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ تقني: {str(e)}")
    
    context.user_data.clear()
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MODE: [CallbackQueryHandler(button_handler), 
                   MessageHandler(filters.TEXT & (~filters.COMMAND), handle_content),
                   MessageHandler(filters.Document.ALL, handle_content)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    app.add_handler(conv)
    # تشغيل وهمي للسيرفر
    threading.Thread(target=lambda: os.system(f"python3 -m http.server {PORT}"), daemon=True).start()
    app.run_polling()
