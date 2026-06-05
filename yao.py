import logging, time, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# التوكن يسحب من متغيرات البيئة في رندر
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 5946250464

# سجل النشاط في الذاكرة
activity_log = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_entry = f"{time.strftime('%H:%M:%S')} - دخول: {user.full_name}"
    activity_log.append(log_entry)
    
    if user.id != ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID, 
                text=f"👤 دخول جديد: {user.full_name}", 
                parse_mode='Markdown'
            )
        except:
            pass
    
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    
    await update.message.reply_text(
        "🦅 صقر الحماية جاهز، اختر الخدمة:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هذا البوت مخصص لفحص الروابط والملفات أمنياً.")

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    logs_text = "\n".join(activity_log[-20:]) if activity_log else "لا توجد سجلات."
    await update.message.reply_text(f"📜 سجل الأحداث:\n\n{logs_text}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🛡️ أرسل الملف أو الرابط للفحص.")

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    # الخطوة الحاسمة: مسح القائمة من تليجرام وإعادة تعيينها بدون logs
    app_bot.bot.delete_my_commands()
    app_bot.bot.set_my_commands([("start", "بدء البوت"), ("help", "المساعدة")])
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("help", help_command))
    app_bot.add_handler(CommandHandler("logs", admin_logs))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.run_polling()
