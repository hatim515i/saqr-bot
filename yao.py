import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# الإعدادات
TOKEN = "هنا_ضع_التوكن_الخاص_بك"
ADMIN_ID = 5946250464

# سجل أحداث نظيف (في الذاكرة فقط)
activity_log = []

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # تسجيل الدخول في السجل فقط بدون إرسال أي تنبيه لك
    if user.id != ADMIN_ID:
        activity_log.append(f"👤 {user.full_name}")
    
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    
    # رسالة البداية فقط
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # لا يظهر السجل إلا لك أنت
    if update.effective_user.id != ADMIN_ID: return
    
    logs = "\n".join(activity_log[-15:]) if activity_log else "لا يوجد زوار."
    await update.message.reply_text(f"📜 سجل الزوار:\n{logs}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = query.data
    await query.edit_message_text("🛡️ أرسل الملف أو الرابط الآن.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # لا يفعل البوت شيئاً تلقائياً، فقط يستلم الفحص
    mode = context.user_data.get('mode')
    if mode:
        await update.message.reply_text("✅ تم استلام الطلب.")
        context.user_data['mode'] = None

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("logs", admin_logs))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_message))
    app_bot.run_polling()
