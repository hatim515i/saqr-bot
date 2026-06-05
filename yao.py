import logging
import os
import requests
import time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# 1. الإعدادات
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
user_last_request = {}

logging.basicConfig(level=logging.INFO)

# 2. السيرفر (Keep Alive)
app = Flask(__name__)
@app.route('/')
def home():
    return "صقر الحماية يعمل بكفاءة 🦅"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 3. نظام الحماية (Rate Limiter)
async def is_rate_limited(update: Update):
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    current_time = time.time()
    last_time = user_last_request.get(user_id, 0)
    
    if current_time - last_time < 5:
        remaining = int(5 - (current_time - last_time))
        msg = "⏳ مهلاً! انتظر " + str(remaining) + " ثوانٍ قبل الطلب التالي."
        if update.message: await update.message.reply_text(msg)
        else: await update.callback_query.answer(msg, show_alert=True)
        return True
    
    user_last_request[user_id] = current_time
    return False

# 4. الأوامر والقائمة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 فحص رابط", callback_data='check_link')],
        [InlineKeyboardButton("📁 فحص ملف", callback_data='check_file')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🦅 أهلاً بك في صقر الحماية!\nاختر نوع الفحص المطلوب:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'check_link':
        await query.edit_message_text("🔗 أرسل الرابط الذي تود فحصه الآن...")
        context.user_data['waiting_for'] = 'link'
    elif query.data == 'check_file':
        await query.edit_message_text("📁 أرسل الملف الذي تود فحصه...")
        context.user_data['waiting_for'] = 'file'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_rate_limited(update): return
    
    waiting_for = context.user_data.get('waiting_for')
    
    if waiting_for == 'link' and update.message.text:
        await update.message.reply_text("🔍 جاري فحص الرابط...")
        # هنا يوضع منطق VirusTotal
        await update.message.reply_text("✅ الرابط سليم (تجريبي).")
        context.user_data['waiting_for'] = None
    elif waiting_for == 'file' and update.message.document:
        await update.message.reply_text("📁 جاري فحص الملف...")
        context.user_data['waiting_for'] = None
    else:
        await update.message.reply_text("⚠️ يرجى استخدام القائمة لاختيار نوع الفحص أولاً.")

# 5. تشغيل البوت
if __name__ == '__main__':
    Thread(target=run_server).start()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.bot.set_my_commands([BotCommand("start", "بدء البوت")])
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, handle_message))
    
    application.run_polling()
