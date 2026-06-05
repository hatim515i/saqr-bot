import logging, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import os

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 5946250464

activity_log = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # تسجيل الدخول في السجل
    activity_log.append(f"{time.strftime('%H:%M:%S')} - دخول: {user.full_name}")
    
    # تنبيه لك أنت فقط كمدير
    if user.id != ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID, 
                text=f"👤 دخول جديد:\nالاسم: {user.full_name}\nID: `{user.id}`", 
                parse_mode='Markdown'
            )
        except:
            pass
    
    # رسالة الترحيب للكل (بدون إظهار الـ ID)
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text(
        "🦅 صقر الحماية جاهز، اختر الخدمة:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    logs_text = "\n".join(activity_log[-15:]) if activity_log else "لا توجد نشاطات."
    await update.message.reply_text(f"📜 سجل الأحداث:\n\n{logs_text}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🛡️ أرسل الملف أو الرابط للفحص.")

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("logs", admin_logs))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.run_polling()
