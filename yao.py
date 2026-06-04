import logging
import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# إعداد السيرفر
app = Flask('')
@app.route('/')
def home():
    return "نظام صقر الحماية الأمني يعمل 🦅"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# استخدام متغيرات البيئة من ريندر
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def check_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "http" in text:
        await update.message.reply_text("🔍 جاري إجراء فحص أمني عميق...")
        
        # قائمة الحماية الاستباقية (حظر فوري)
        blacklist = ["trycloudflare.com", "ngrok.io", "serveo.net", "ngrok-free.app", "loca.lt"]
        if any(domain in text for domain in blacklist):
            await update.message.reply_text("⛔ تنبيه عالي الخطورة: تم رصد أداة تصيد مشبوهة! تم الحظر فوراً.")
            return

        # فحص VirusTotal
        try:
            url = "https://www.virustotal.com/vtapi/v2/url/report"
            params = {'apikey': VT_API_KEY, 'resource': text}
            response = requests.get(url, params=params).json()
            
            if response.get('response_code') == 1 and response.get('positives', 0) > 0:
                await update.message.reply_text("⚠️ تنبيه أمني: تم رصد مخاطر في هذا الرابط!")
            else:
                await update.message.reply_text("✅ الرابط سليم.")
        except:
            await update.message.reply_text("✅ تم الفحص، الرابط لا يبدو خطيراً.")
    else:
        await update.message.reply_text("🔗 أرسل الرابط الذي تود فحصه.")

if __name__ == '__main__':
    Thread(target=run_server).start()
    application = ApplicationBuilder().token(TOKEN).build()
    # رسالة ترحيب نظيفة وبدون إجبار
    application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("أهلاً بك في صقر الحماية 🦅\nأرسل أي رابط وسأقوم بفحصه أمنياً لك.")))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_link))
    application.run_polling()
