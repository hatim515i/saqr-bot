import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

TOKEN = os.environ.get('BOT_TOKEN')

# حالات البوت
SELECTING_MODE = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_MODE

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'mode_link':
        context.user_data['mode'] = 'link'
        await query.edit_message_text("✅ تم اختيار: فحص رابط. أرسل الرابط الآن:")
    elif query.data == 'mode_file':
        context.user_data['mode'] = 'file'
        await query.edit_message_text("✅ تم اختيار: فحص ملف. أرسل الملف الآن:")
    return SELECTING_MODE

async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    
    if mode == 'link' and update.message.text:
        await update.message.reply_text("🌐 جاري فحص الرابط...")
    elif mode == 'file' and update.message.document:
        await update.message.reply_text("📁 جاري فحص الملف...")
    else:
        await update.message.reply_text("⚠️ خطأ: تأكد أنك أرسلت النوع الصحيح (رابط أو ملف) حسب اختيارك.")

async def post_init(application):
    await application.bot.delete_my_commands()
    await application.bot.set_my_commands([BotCommand("start", "بدء البوت"), BotCommand("help", "المساعدة")])

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={SELECTING_MODE: [CallbackQueryHandler(button_click), MessageHandler(filters.ALL, handle_content)]},
        fallbacks=[]
    )
    
    app_bot.add_handler(conv_handler)
    app_bot.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text("هذا البوت للفحص.")))
    
    app_bot.run_polling()
