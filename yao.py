import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

TOKEN = os.environ.get('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هذا البوت مخصص لفحص الروابط والملفات أمنياً.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🛡️ أرسل الملف أو الرابط للفحص.")

async def post_init(application):
    # هذه الدالة تتنفذ مرة واحدة عند تشغيل البوت لتنظيف القائمة
    await application.bot.delete_my_commands()
    await application.bot.set_my_commands([("start", "بدء البوت"), ("help", "المساعدة")])

if __name__ == '__main__':
    # نستخدم post_init عشان نضمن إن الأوامر تتنفذ بشكل صحيح
    app_bot = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    
    app_bot.run_polling()
