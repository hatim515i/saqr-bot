import os
import requests
import threading
from flask import Flask
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# التوكنات
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
PORT = int(os.environ.get('PORT', 8080))

# 1. حركة الخداع (عشان رندر يظن إنه ويب)
app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "البوت شغال 🦅"
def run_flask():
    app_web.run(host='0.0.0.0', port=PORT)

# حالات المحادثة
MODE = 1

async def start(update, context):
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية، اختر نوع الفحص:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MODE

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = 'link' if query.data == 'mode_link' else 'file'
    await query.edit_message_text(f"✅ اخترت {context.user_data['mode']}. أرسل الملف أو الرابط الآن:")
    return MODE

async def content_handler(update, context):
    mode = context.user_data.get('mode')
    headers = {"x-apikey": VT_API_KEY}
    status_msg = await update.message.reply_text("⏳ جاري التحليل في البيئة الآمنة...")

    try:
        if mode == 'link':
            url = update.message.text
            resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url})
            analysis_id = resp.json()['data']['id']
            res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
            stats = res.json()['data']['attributes']['stats']
            msg = f"🛡️ نتيجة فحص الرابط:\n🔴 ضار: {stats['malicious']}\n🟡 مشبوه: {stats['suspicious']}"
            
        elif mode == 'file':
            file = await update.message.document.get_file()
            file_path = "temp_file"
            await file.download_to_drive(file_path)
            with open(file_path, "rb") as f:
                resp = requests.post("https://www.virustotal.com/api/v3/files", headers=headers, files={"file": f})
                file_id = resp.json()['data']['id']
                res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{file_id}", headers=headers)
                stats = res.json()['data']['attributes']['stats']
                msg = f"🛡️ نتيجة فحص الملف:\n🔴 ضار: {stats['malicious']}\n🟢 مشبوه: {stats['suspicious']}"
            os.remove(file_path)
            
        await status_msg.edit_text(msg)
    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ: {str(e)}")
    
    return ConversationHandler.END

if __name__ == '__main__':
    threading.Thread(target=run_flask).start() # تشغيل الخداع
    
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.bot.set_my_commands([BotCommand("start", "بدء")])
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={MODE: [CallbackQueryHandler(button_handler), MessageHandler(filters.ALL, content_handler)]},
        fallbacks=[CommandHandler('start', start)]
    )
    
    app_bot.add_handler(conv)
    app_bot.run_polling()
