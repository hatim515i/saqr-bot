import logging, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# التوكن يسحب من متغيرات البيئة في رندر
TOKEN = os.environ.get('BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # كود الترحيب فقط (تم حذف كود التنبيه بالدخول)
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

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    # مسح أي أوامر قديمة عالقة من سيرفرات تليجرام
    app_bot.bot.delete_my_commands()
    
    # تعيين القائمة النظيفة للجميع (start و help فقط)
    app_bot.bot.set_my_commands([("start", "بدء البوت"), ("help", "المساعدة")])
    
    # إضافة الأوامر
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    
    app_bot.run_polling()
