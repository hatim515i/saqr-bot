import logging
import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# 1. إعداد السيرفر لخدعة ريندر
app = Flask('')
@app.route('/')
def home():
    return "صقر الحماية يعمل بكفاءة 🦅"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 2. إعدادات البوت والـ API
TOKEN = "8958537727:AAHBx4ULFETLfOoQY97RVoEMkjWEhN3tRM8"
VT_API_KEY = "5cd48ac6cb3ffbd76a79abe5838f9f9732ee95a1dc673cc20b0db125813c0f8f"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("يا هلا! أرسل لي أي رابط وبفحصه لك بذكاء 🦅")

async def check_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "http" in text:
        await update.message.reply_text("🔍 جاري فحص الرابط عبر VirusTotal...")
        
        url = "https://www.virustotal.com/vtapi/v2/url/report"
        params = {'apikey': VT_API_KEY, 'resource': text}
        
        try:
            response = requests.get(url, params=params)
            result = response.json()
            
            # فحص النتيجة
            if result.get('response_code') == 1:
                positives = result.get('positives', 0)
                if positives > 0:
                    await update.message.reply_text(f"⚠️ تحذير: الرابط مشبوه! تم رصده من قبل {positives} محركات أمنية.")
                else:
                    await update.message.reply_text("✅ الرابط سليم ولم يتم العثور على تهديدات.")
            else:
                await update.message.reply_text("✅ الرابط يبدو آمناً (لم يتم الإبلاغ عنه كخطر).")
        except Exception as e:
            await update.message.reply_text("❌ حدث خطأ أثناء الفحص، حاول مرة أخرى.")
    else:
        await update.message.reply_text("🔗 أرسل لي رابطاً يبدأ بـ http")

if __name__ == '__main__':
    # تشغيل السيرفر في الخلفية
    Thread(target=run_server).start()
    
    # تشغيل البوت
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_link))
    
    application.run_polling()
