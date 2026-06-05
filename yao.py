import logging, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# الإعدادات
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 5946250464  # رقم الآيدي الخاص بك

# سجل الأحداث (في الذاكرة فقط)
activity_log = []

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # تسجيل الدخول فقط في السجل
    activity_log.append(f"👤 دخول: {user.full_name} (ID: {user.id})")
    
    keyboard = [
        [InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link')],
        [InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]
    ]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # حماية السجل: لا يظهر إلا للمدير
    if update.effective_user.id != ADMIN_ID:
        return
    
    logs_text = "\n".join(activity_log[-20:]) if activity_log else "لا توجد نشاطات مسجلة."
    await update.message.reply_text(f"📜 سجل النشاطات (آخر 20 عملية):\n\n{logs_text}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = query.data
    await query.edit_message_text("🛡️ تم اختيار الفحص. أرسل الملف أو الرابط الآن.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mode = context.user_data.get('mode')
    
    if not mode:
        return # لا يفعل شيء إذا لم يتم اختيار خدمة

    if mode == 'mode_file' and update.message.document:
        activity_log.append(f"📁 ملف: {update.message.document.file_name} بواسطة {user.first_name}")
        await update.message.reply_text("✅ تم تسجيل عملية فحص الملف.")
        context.user_data['mode'] = None
        
    elif mode == 'mode_link' and update.message.text:
        url = update.message.text
        activity_log.append(f"🔗 رابط: {url[:20]}... بواسطة {user.first_name}")
        await update.message.reply_text("✅ تم تسجيل عملية فحص الرابط.")
        context.user_data['mode'] = None

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    # إضافة الأوامر
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("logs", admin_logs))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("🦅 صقر الحماية يعمل الآن...")
    app_bot.run_polling()
