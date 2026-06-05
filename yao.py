import os, requests, threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# 1. السيرفر الوهمي (الخداع)
PORT = int(os.environ.get('PORT', 10000))
app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية شغال 🦅"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT)).start()

# إعدادات البوت
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')

# الحالات
SELECTING_ACTION = 1

async def start(update, context):
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية، اختر نوع الفحص:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_ACTION

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    mode = query.data.split('_')[1]
    context.user_data['mode'] = mode
    
    if mode == 'link':
        await query.edit_message_text("✅ اخترت [فحص رابط]. أرسل الرابط الآن:")
    else:
        await query.edit_message_text("✅ اخترت [فحص ملف]. أرسل الملف الآن:")
    return SELECTING_ACTION

async def handle_link(update, context):
    if context.user_data.get('mode') != 'link':
        await update.message.reply_text("⚠️ أنت اخترت فحص ملف، يرجى إرسال ملف وليس رابط.")
        return SELECTING_ACTION
    
    url = update.message.text
    await update.message.reply_text(f"🌐 جاري فحص الرابط في بيئة آمنة: {url}")
    # هنا تحط منطق الفحص حقك
    context.user_data.clear()
    return ConversationHandler.END

async def handle_file(update, context):
    if context.user_data.get('mode') != 'file':
        await update.message.reply_text("⚠️ أنت اخترت فحص رابط، يرجى إرسال رابط وليس ملف.")
        return SELECTING_ACTION
    
    await update.message.reply_text("📁 جاري فحص الملف في بيئة آمنة...")
    # هنا تحط منطق الفحص حقك
    context.user_data.clear()
    return ConversationHandler.END

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(button_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link),
                MessageHandler(filters.Document.ALL, handle_file)
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app_bot.add_handler(conv)
    app_bot.run_polling()
