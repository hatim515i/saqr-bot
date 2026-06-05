import logging, os, requests, time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 5946250464
last_users = {} # {id: name}
last_messages = [] # [(name, text)]

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in last_users:
        last_users[user.id] = user.full_name
        try: await context.bot.send_message(chat_id=ADMIN_ID, text=f"🦅 دخول جديد: {user.full_name} (ID: {user.id})")
        except: pass
    
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

# لوحة التحكم الخاصة بك
async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    keyboard = [[InlineKeyboardButton("👥 قائمة الزوار", callback_data='log_users'),
                 InlineKeyboardButton("💬 سجل الرسائل", callback_data='log_msgs')]]
    await update.message.reply_text("🛠️ لوحة تحكم الصقر، ماذا تريد أن ترى؟", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data == 'log_users':
        text = "👥 قائمة من دخلوا البوت:\n" + "\n".join([f"- {name}" for name in last_users.values()])
        await query.edit_message_text(text)
    elif data == 'log_msgs':
        text = "💬 آخر الرسائل:\n" + "\n".join([f"- {name}: {msg}" for name, msg in last_messages[-10:]])
        await query.edit_message_text(text)
    else:
        context.user_data['mode'] = data
        await query.edit_message_text("🛡️ تم التهيئة، أرسل المطلوب للتحليل.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    if text: last_messages.append((user.full_name, text))
    
    # ... (باقي منطق الفحص حقك هنا) ...

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("logs", admin_logs))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_bot.run_polling()
