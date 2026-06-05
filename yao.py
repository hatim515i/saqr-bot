import logging, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = "حط التوكن حقك هنا"
ADMIN_ID = 5946250464

# سجل الأحداث (في الذاكرة فقط)
activity_log = []
# قائمة عشان نتأكد أننا سجلنا المستخدم مرة واحدة فقط
tracked_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # تسجيل الدخول في السجل فقط (بدون إرسال رسالة لك في الخاص)
    if user.id not in tracked_users:
        activity_log.append(f"{time.strftime('%H:%M:%S')} - دخول: {user.full_name}")
        tracked_users.add(user.id)
    
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # لا يمكن لأحد غيرك رؤية السجل
    if update.effective_user.id != ADMIN_ID: return
    
    logs_text = "\n".join(activity_log[-15:]) if activity_log else "لا توجد نشاطات مسجلة."
    await update.message.reply_text(f"📜 سجل الأحداث:\n\n{logs_text}")

# باقي الأوامر (handle_callback, handle_message) تبقى كما هي...

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("logs", admin_logs))
    # ... إضافة باقي الهاندلرات
    app_bot.run_polling()
