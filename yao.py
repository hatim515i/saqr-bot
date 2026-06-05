import os, requests, threading, time
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# سيرفر الخداع (رندر)
PORT = int(os.environ.get('PORT', 10000))
app = Flask(__name__)
@app.route('/')
def home(): return "صقر الحماية في الخدمة 🦅"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()

TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MODE = 1

# قائمة التصيد (Blacklist) - أي كلمة من هذه الكلمات تعني تصيد فوراً
PHISHING_KEYWORDS = ['login', 'bank', 'free-money', 'verify', 'account', 'secure-update', 'rewards', 'prize', 'iclod', 'apple-secure', 'scam']

def check_blacklist(url):
    for word in PHISHING_KEYWORDS:
        if word in url.lower(): return True
    return False

async def start(update, context):
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية في خدمتك. اختر نوع الفحص:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MODE

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = 'link' if query.data == 'mode_link' else 'file'
    await query.edit_message_text(f"✅ تم اختيار: فحص {context.user_data['mode']}. أرسل الآن:")
    return MODE

async def handle_content(update, context):
    mode = context.user_data.get('mode')
    status_msg = await update.message.reply_text("⏳ جاري الفحص في بيئة آمنة (Sandbox)...")
    headers = {"x-apikey": VT_API_KEY}

    try:
        if mode == 'link' and update.message.text:
            url = update.message.text
            
            # 1. فحص البلاك ليست (فوري)
            if check_blacklist(url):
                await status_msg.edit_text("🚨 **تحذير شديد!**\nالرابط مشبوه ومصنف ضمن أدوات التصيد.")
                return ConversationHandler.END

            # 2. فحص VirusTotal
            resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url})
            analysis_id = resp.json()['data']['id']
            
            # انتظر قليلاً لضمان اكتمال التحليل
            time.sleep(5) 
            
            res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
            stats = res.json()['data']['attributes']['stats']
            
            # التقرير الذكي (بدل الأصفار)
            msg = f"🛡️ **نتيجة الفحص (بيئة آمنة):**\n\n🔴 ضار: {stats['malicious']}\n🟡 مشبوه: {stats['suspicious']}\n🟢 آمن: {stats['harmless']}\n\n"
            
            if stats['malicious'] > 0:
                msg += "❌ **الرابط غير آمن!**"
            elif stats['suspicious'] > 0:
                msg += "⚠️ **الرابط مشبوه، لا تفتحه.**"
            else:
                msg += "✅ **الرابط آمن.**"
                
            await status_msg.edit_text(msg)

        elif mode == 'file' and update.message.document:
            file = await update.message.document.get_file()
            file_path = "temp_file"
            await file.download_to_drive(file_path)
            with open(file_path, "rb") as f:
                resp = requests.post("https://www.virustotal.com/api/v3/files", headers=headers, files={"file": f})
                file_id = resp.json()['data']['id']
                time.sleep(5)
                res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{file_id}", headers=headers)
                stats = res.json()['data']['attributes']['stats']
                await status_msg.edit_text(f"🛡️ نتيجة فحص الملف في بيئة آمنة:\n🔴 ضار: {stats['malicious']}\n🟢 آمن: {stats['harmless']}")
            os.remove(file_path)
            
    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ تقني: {str(e)}")
    
    context.user_data.clear()
    return ConversationHandler.END

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={MODE: [CallbackQueryHandler(button_handler), MessageHandler(filters.ALL, handle_content)]},
        fallbacks=[CommandHandler('start', start)]
    )
    app_bot.add_handler(conv)
    app_bot.run_polling()
