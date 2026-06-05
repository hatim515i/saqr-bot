import logging
import os
import time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# 1. الإعدادات
TOKEN = os.environ.get('BOT_TOKEN')
user_last_request = {}

logging.basicConfig(level=logging.INFO)

# 2. السيرفر (Keep Alive)
app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية يعمل بكفاءة 🦅"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 3. نظام الحماية (Rate Limiter)
async def is_rate_limited(update: Update):
    user_id = update.effective_user.id
    current_time = time.time()
    last_time = user_last_request.get(user_id, 0)
    if current_time - last_time < 5:
        remaining = int(5 - (current_time - last_time))
        msg = f"⏳ مهلاً! انتظر {remaining} ثوانٍ قبل الطلب التالي."
        if update.message: await update.message.reply_text(msg)
        else: await update.callback_query.answer(msg, show_alert=True)
        return True
    user_last_request[user_id] = current_time
    return False

# 4. الأوامر والمنيو
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # الأزرار اللي بتطلع تحت الرسالة
    keyboard = [
        [InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link')],
        [InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🦅 أهلاً بك في صقر الحماية!\nاختر نوع العملية التي تود القيام بها:", 
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'mode_link':
        context.user_data['mode'] = 'link'
        await query.edit_message_text("🔗 ممتاز، أرسل الرابط الآن وسأقوم بفحصه.")
    elif query.data == 'mode_file':
        context.user_data['mode'] = 'file'
        await query.edit_message_text("📁 ممتاز، أرسل الملف الآن وسأقوم بفحصه.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_rate_limited(update): return
    
    mode = context.user_data.get('mode')
    
    if not mode:
        await update.message.reply_text("⚠️ يرجى الضغط على /start واختيار نوع الفحص أولاً.")
        return

    if mode == 'link' and update.message.text:
        await update.message.reply_text(f"🔍 جاري فحص الرابط: {update.message.text}...")
        # هنا سيتم ربط الفحص بـ VirusTotal لاحقاً
    elif mode == 'file' and update.message.document:
        await update.message.reply_text("📁 جاري فحص الملف...")
    else:
        await update.message.reply_text("⚠️ أنت في وضع " + mode + "، يرجى إرسال النوع الصحيح.")

# 5. تشغيل البوت
if __name__ == '__main__':
    Thread(target=run_server).start()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    # تعريف المنيو الجانبي
    app_bot.bot.set_my_commands([BotCommand("start", "بدء التشغيل")])
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, handle_message))
    
    app_bot.run_polling()
