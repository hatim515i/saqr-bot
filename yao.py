import logging
import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# 1. إعداد السيرفر الوهمي
app = Flask('')
@app.route('/')
def home():
    return "صقر الحماية يعمل بكفاءة 🦅"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 2. إعدادات البوت
TOKEN = "8958537727:AAHBx4ULFETLfOoQY97RVoEMkjWEhN3tRM8"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("يا هلا! أرسل لي أي رابط وبفحصه لك 🦅")

async def check_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "http" in text:
        await update.message.reply_text("🔍 جاري فحص الرابط...")
        if any(word in text for word in ["phishing", "scam", "fake"]):
            await update.message.reply_text("⚠️ تحذير: هذا الرابط مشبوه!")
        else:
            await update.message.reply_text("✅ الرابط يبدو آمناً.")
    else:
        await update.message.reply_text("🔗 أرسل لي رابطاً يبدأ بـ http")

if__name__ == '__main__':
    # تشغيل السيرفر في الخلفية
    Thread(target=run_server).start()
    
    # تشغيل البوت
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_link))
    
    application.run_polling()
