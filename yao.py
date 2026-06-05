import os, requests, threading
from flask import Flask
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# 1. السيرفر الوهمي (الخداع) - يظل شغال 24 ساعة
PORT = int(os.environ.get('PORT', 10000))
app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية شغال 🦅"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT)).start()

# 2. إعدادات البوت
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MODE = 1

async def start(update, context):
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MODE

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = 'link' if query.data == 'mode_link' else 'file'
    await query.edit_message_text(f"✅ تم اختيار: فحص {context.user_data['mode']}. أرسل الآن:")
    return MODE

async def handle_content(update, context):
    mode = context.user_data.get('mode')
    if not mode:
        await update.message.reply_text("⚠️ يرجى الضغط على /start أولاً.")
        return ConversationHandler.END

    status_msg = await update.message.reply_text("⏳ جاري الفحص...")
    headers = {"x-apikey": VT_API_KEY}

    try:
        if mode == 'link' and update.message.text:
            resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": update.message.text})
            analysis_id = resp.json()['data']['id']
            res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
            stats = res.json()['data']['attributes']['stats']
            msg = f"🛡️ نتيجة الرابط:\n🔴 ضار: {stats['malicious']}\n🟢 آمن: {stats['harmless']}"
            
        elif mode == 'file' and update.message.document:
            file = await update.message.document.get_file()
            file_path = "temp_file"
            await file.download_to_drive(file_path)
            with open(file_path, "rb") as f:
                resp = requests.post("https://www.virustotal.com/api/v3/files", headers=headers, files={"file": f})
                file_id = resp.json()['data']['id']
                res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{file_id}", headers=headers)
                stats = res.json()['data']['attributes']['stats']
                msg = f"🛡️ نتيجة الملف:\n🔴 ضار: {stats['malicious']}\n🟢 آمن: {stats['harmless']}"
            os.remove(file_path)
        else:
            msg = "⚠️ أرسل نوع الملف أو الرابط الصحيح."

        await status_msg.edit_text(msg)
    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ: {str(e)}")
    
    return ConversationHandler.END

if __name__ == '__main__':
    # بناء التطبيق بدون Defaults المسببة للمشاكل
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={MODE: [CallbackQueryHandler(button_handler), MessageHandler(filters.ALL, handle_content)]},
        fallbacks=[CommandHandler('start', start)]
    )
    
    app_bot.add_handler(conv)
    app_bot.run_polling()
