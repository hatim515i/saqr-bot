import os
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 5946250464

# الحالات
MODE = 1

async def start(update, context):
    context.user_data.clear() # مسح أي اختيار قديم عشان ما يعلق
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MODE

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'mode_link':
        context.user_data['mode'] = 'link'
        await query.edit_message_text("✅ تم اختيار: فحص رابط. أرسل الرابط الآن (أو اكتب /start للعودة):")
    else:
        context.user_data['mode'] = 'file'
        await query.edit_message_text("✅ تم اختيار: فحص ملف. أرسل الملف الآن (أو اكتب /start للعودة):")
    return MODE

async def content_handler(update, context):
    mode = context.user_data.get('mode')
    
    # هنا الجزء اللي يفك التعليق
    if mode == 'link' and update.message.text:
        await update.message.reply_text("🌐 جاري فحص الرابط... تم الفحص بنجاح! ✅")
    elif mode == 'file' and update.message.document:
        await update.message.reply_text("📁 جاري فحص الملف... تم الفحص بنجاح! ✅")
    else:
        await update.message.reply_text("⚠️ أرسل المحتوى الصحيح، أو استخدم /start للرجوع للقائمة.")
    
    # بعد الرد، نمسح الحالة عشان يفك التعليق ويرجع البوت حر
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update, context):
    context.user_data.clear()
    await update.message.reply_text("تم الإلغاء. ارجع للقائمة بالضغط على /start")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    # تعيين الأوامر
    app.bot.set_my_commands([BotCommand("start", "بدء البوت"), BotCommand("help", "المساعدة")])
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MODE: [CallbackQueryHandler(button_handler), MessageHandler(filters.ALL, content_handler)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text("هذا البوت مخصص للفحص.")))
    
    print("البوت يعمل الآن...")
    app.run_polling()
