import os
import requests
import base64
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MODE = 1

# تحويل الرابط لصيغة VirusTotal المعتمدة (Base64)
def get_url_id(url):
    return base64.urlsafe_b64encode(url.encode()).decode().strip("=")

async def start(update, context):
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🔍 فحص رابط (عميق)", callback_data='mode_link'), 
                 InlineKeyboardButton("📁 فحص ملف (سريع)", callback_data='mode_file')]]
    await update.message.reply_text("🦅 صقر الحماية في وضع الفحص العميق، اختر:", reply_markup=InlineKeyboardMarkup(keyboard))
    return MODE

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data['mode'] = 'link' if query.data == 'mode_link' else 'file'
    await query.edit_message_text(f"✅ تم تفعيل الفحص لـ {context.user_data['mode']}. أرسل الملف أو الرابط الآن:")
    return MODE

async def content_handler(update, context):
    mode = context.user_data.get('mode')
    headers = {"x-apikey": VT_API_KEY}
    
    await update.message.reply_text("⏳ جاري الفحص في البيئة الآمنة (Sandbox)... انتظر لحظة.")

    try:
        if mode == 'link':
            url = update.message.text
            # إرسال للـ Sandbox في VT
            resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url})
            analysis_id = resp.json()['data']['id']
            # جلب تقرير مفصل
            res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
            stats = res.json()['data']['attributes']['stats']
            msg = f"🛡️ تقرير الفحص العميق:\n🔴 ضار: {stats['malicious']}\n🟡 مشبوه: {stats['suspicious']}\n🟢 آمن: {stats['harmless']}"
            await update.message.reply_text(msg)

        elif mode == 'file':
            file = await update.message.document.get_file()
            file_path = await file.download_to_drive()
            with open(file_path, "rb") as f:
                # رفع الملف لبيئة الفحص الآمنة
                files = {"file": f}
                resp = requests.post("https://www.virustotal.com/api/v3/files", headers=headers, files=files)
                file_id = resp.json()['data']['id']
                # جلب النتيجة (فحص سريع)
                res = requests.get(f"https://www.virustotal.com/api/v3/files/{file_id}", headers=headers)
                stats = res.json()['data']['attributes']['last_analysis_stats']
                msg = f"📂 نتيجة فحص الملف:\n🔴 ضار: {stats['malicious']}\n🟢 آمن: {stats['harmless']}"
                await update.message.reply_text(msg)
            os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"❌ تعذر الفحص: {str(e)}")
    
    context.user_data.clear()
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.run_polling()
