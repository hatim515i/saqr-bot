import logging
import os
import requests
import hashlib
import time
from flask import Flask
from threading import Thread
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# 1. الإعدادات
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')

# خريطة لتخزين آخر وقت لكل مستخدم
user_last_request = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 2. السيرفر (Keep Alive)
app = Flask(__name__)
@app.route('/')
def home():
    return "صقر الحماية يعمل بكفاءة 🦅"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 3. نظام الحماية من السرعة (Rate Limiter)
async def is_rate_limited(update: Update):
    user_id = update.message.from_user.id
    current_time = time.time()
    last_time = user_last_request.get(user_id, 0)
    
    if current_time - last_time < 5:
        remaining = int(5 - (current_time - last_time))
        await update.message.reply_text(f"⏳ مهلاً يا بطل! انتظر {remaining} ثوانٍ قبل الطلب التالي.")
        return True
    
    user_last_request[user_id] = current_time
    return False

# 4. وظائف الفحص
async def check_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_rate_limited(update): return
    
    text = update.message.text
    await update.message.reply_text("🔍 جاري الفحص الأمني للرابط...")
    try:
        url = "https://www.virustotal.com/vtapi/v2/url/report"
        params = {'apikey': VT_API_KEY, 'resource': text}
        response = requests.get(url, params=params).json()
        
        if response.get('positives', 0) > 0:
            await update.message.reply_text(f"⚠️ تحذير: تم رصد {response.get('positives')} تهديد!")
        else:
            await update.message.reply_text("✅ الرابط سليم.")
    except Exception:
        await update.message.reply_text("❌ خطأ في الاتصال.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_rate_limited(update): return
    await update.message.reply_text("📁 نظام الفحص العميق قيد التجهيز.. سنربطه بـ Hash قريباً!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦅 أهلاً بك في صقر الحماية! استخدم الأزرار أدناه أو أرسل رابطاً للفحص.")

# 5. تشغيل البوت
if __name__ == '__main__':
    Thread(target=run_server).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    # القائمة
    commands = [BotCommand("start", "بدء البوت"), BotCommand("help", "المساعدة")]
    application.bot.set_my_commands(commands)
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_link))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    application.run_polling()
