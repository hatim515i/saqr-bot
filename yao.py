import os
import logging
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# التوكن
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 5946250464  # تأكد أن هذا هو رقم الأيدي الخاص بك

# ذاكرة لتخزين السجلات
activity_log = []

# إضافة سجل جديد
def add_log(user, action):
    import time
    activity_log.append(f"{time.strftime('%H:%M:%S')} - {user.full_name}: {action}")

# حالات المحادثة
MODE = 1

async def start(update, context):
    user = update.effective_user
    add_log(user, "ضغط /start")
    
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MODE

async def button_handler(update, context):
    query = update.callback_query
    user = update.effective_user
    await query.answer()
    
    if query.data == 'mode_link':
        context.user_data['mode'] = 'link'
        add_log(user, "اختار فحص رابط")
        await query.edit_message_text("✅ تم اختيار: فحص رابط. أرسل الرابط:")
    else:
        context.user_data['mode'] = 'file'
        add_log(user, "اختار فحص ملف")
        await query.edit_message_text("✅ تم اختيار: فحص ملف. أرسل الملف:")
    return MODE

async def show_logs(update, context):
    # هذا الأمر خاص بك أنت فقط
    if update.effective_user.id == ADMIN_ID:
        logs_text = "\n".join(activity_log[-20:]) if activity_log else "لا توجد سجلات."
        await update.message.reply_text(f"📜 سجل الأحداث (آخر 20):\n\n{logs_text}")
    else:
        await update.message.reply_text("⛔ عذراً، هذا الأمر للأدمن فقط.")

async def content_handler(update, context):
    user = update.effective_user
    mode = context.user_data.get('mode')
    
    if mode == 'link' and update.message.text:
        add_log(user, "أرسل رابط للفحص")
        await update.message.reply_text("🌐 جاري فحص الرابط...")
    elif mode == 'file' and update.message.document:
        add_log(user, "أرسل ملف للفحص")
        await update.message.reply_text("📁 جاري فحص الملف...")
    else:
        await update.message.reply_text("⚠️ أرسل المحتوى الصحيح (رابط أو ملف).")

async def post_init(application):
    # القائمة لا تحتوي على logs لكي لا تظهر للناس
    await application.bot.set_my_commands([
        BotCommand("start", "بدء البوت"),
        BotCommand("help", "المساعدة")
    ])

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={MODE: [CallbackQueryHandler(button_handler), MessageHandler(filters.ALL, content_handler)]},
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("logs", show_logs)) # مخفي من المنيو بس شغال لك
    app.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text("هذا البوت مخصص للفحص الأمني.")))
    
    print("البوت يعمل الآن...")
    app.run_polling()
