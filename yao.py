import logging, os, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 5946250464

# سجل أحداث (في الذاكرة فقط)
activity_log = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # استثناء نفسك من التسجيل في الـ Logs
    if user.id != ADMIN_ID:
        activity_log.append(f"{time.strftime('%H:%M:%S')} - دخول: {user.full_name}")
    
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    # عرض آخر 15 سجل
    logs_text = "\n".join(activity_log[-15:]) if activity_log else "لا توجد نشاطات مسجلة."
    await update.message.reply_text(f"📜 سجل الأحداث (بدونك):\n\n{logs_text}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['mode'] = query.data
    await query.edit_message_text("🛡️ النظام جاهز، أرسل الملف أو الرابط.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # استثناء نفسك من تسجيل الرسائل أيضاً
    if user.id != ADMIN_ID:
        activity_log.append(f"{time.strftime('%H:%M:%S')} - نشاط: {user.first_name}")
    
    # ... (باقي منطق الفحص) ...
    context.user_data['mode'] = None

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("logs", admin_logs))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_message))
    app_bot.run_polling()
