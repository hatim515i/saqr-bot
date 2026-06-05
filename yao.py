import logging, os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 5946250464

# تخزين المستخدمين: {id: {"name": name, "username": username}}
users_db = {}
# تخزين الرسائل: [{"user_id": id, "text": text}]
messages_db = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # تسجيل المستخدم بدون إرسال تنبيه
    users_db[user.id] = {"name": user.full_name, "username": user.username}
    
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية جاهز، اختر الخدمة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    keyboard = [[InlineKeyboardButton("👥 الزوار", callback_data='log_users'),
                 InlineKeyboardButton("💬 الرسائل", callback_data='log_msgs')]]
    await update.message.reply_text("🛠️ لوحة تحكم الصقر:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == 'log_users':
        # إنشاء أزرار لكل مستخدم عشان تضغط عليهم وتفتح محادثتهم
        keyboard = []
        for uid, info in users_db.items():
            # الزر يحمل اسم المستخدم، وعند الضغط عليه يظهر معرفه
            keyboard.append([InlineKeyboardButton(f"👤 {info['name']}", callback_data=f"chat_{uid}")])
        await query.edit_message_text("👥 اضغط على اسم المستخدم للتواصل معه:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith("chat_"):
        uid = query.data.split("_")[1]
        await query.edit_message_text(f"🔗 يمكنك التواصل مع المستخدم عبر الرابط:\nhttps://t.me/{users_db[int(uid)]['username'] if users_db[int(uid)]['username'] else 'user_id_' + uid}")
    
    elif query.data == 'log_msgs':
        text = "💬 آخر 10 رسائل:\n" + "\n".join([f"- {users_db[m['user_id']]['name']}: {m['text']}" for m in messages_db[-10:]])
        await query.edit_message_text(text)
    else:
        context.user_data['mode'] = query.data
        await query.edit_message_text("🛡️ أرسل الملف أو الرابط.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    if text and not text.startswith('/'):
        messages_db.append({"user_id": user.id, "text": text})
    
    # ... (باقي منطق الفحص) ...
    context.user_data['mode'] = None

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("logs", admin_logs))
    app_bot.add_handler(CallbackQueryHandler(handle_callback))
    app_bot.add_handler(MessageHandler(filters.ALL, handle_message))
    app_bot.run_polling()
