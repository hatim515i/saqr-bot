import os
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# التوكن
TOKEN = os.environ.get('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦅 صقر الحماية جاهز.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هذا البوت مخصص للفحص.")

async def post_init(application):
    # مسح الأوامر القديمة وتعيين الجديدة
    await application.bot.delete_my_commands()
    await application.bot.set_my_commands([
        BotCommand("start", "بدء البوت"),
        BotCommand("help", "المساعدة")
    ])

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    
    app_bot.run_polling()
