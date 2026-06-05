import logging, os, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# التوكن يسحب من متغيرات البيئة في رندر
TOKEN = os.environ.get('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    
    await update.message.reply_text(
        "🦅 صقر الحماية جاهز، اختر الخدمة:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هذا البوت مخصص لفحص الروابط والملفات أمنياً.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🛡️ أرسل الملف أو الرابط للفحص.")

async def setup_commands(app):
    # مسح الأوامر القديمة وتعيين الجديدة فقط (بدون logs)
    await app.bot.delete_my_commands()
    await app.bot.set_my_commands([("start", "بدء البوت"), ("help", "المساعدة")])

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    # تنفيذ إعداد الأوامر قبل تشغيل البوت
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_commands(app_bot))
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    
    app_bot.run_polling()
