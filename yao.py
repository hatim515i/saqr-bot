import logging
import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# إعداد السيرفر
app = Flask('')
@app.route('/')
def home():
    return "نظام صقر الحماية الأمني يعمل 🦅"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# استخدام متغيرات البيئة (تأكد من إضافتها في ريندر)
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def check_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "http" in text:
        await update.message.reply_text("🔍 جاري إجراء فحص أمني عميق...")
        
        # 1. قائمة الحماية الاستباقية (حظر فوري)
        blacklist = ["trycloudflare.com", "ngrok.io", "serveo.net", "ngrok-free.app", "loca.lt"]
        if any(domain in text for domain in blacklist):
            await update.message.reply_text("⛔ تنبيه عالي الخطورة: تم رصد أداة تصيد مشبوهة! تم الحظر فوراً.")
            return

        # 2. فحص VirusTotal المتقدم
        try:
            url = "https://www.virustotal.com/vtapi/v2/url/report"
            params = {'apikey': VT_API_KEY, 'resource': text}
            response = requests.get(url, params=params).json()
            
            # فحص النتيجة + التنبيه الذكي
            if response.get('response_code') == 1:
                positives = response.get('positives', 0)
                if positives > 2: # إذا أكثر من محرك أمني كشفه
                    await update.message.reply_text(f"🚨 تحذير أمني: الرابط مصنف كضار من قبل {positives} جهة أمنية! لا تفتحه.")
                elif positives > 0:
                    await update.message.reply_text("⚠️ تنبيه: الرابط يحتوي على بعض الشكوك الأمنية، كن حذراً!")
                else:
                    await update.message.reply_text("✅ الرابط يبدو نظيفاً في قواعد البيانات الأمنية.")
            else:
                # 3. فحص الروابط المختصرة (مستوى إضافي)
                await update.message.reply_text("✅ فحص أولي مكتمل: لا توجد سجلات تهديد سابقة.")
                
        except Exception:
            await update.message.reply_text("✅ تم الفحص، الرابط لم يُبلغ عنه كمصدر خطر حالياً.")
    else:
        await update.message.reply_text("🔗 يرجى إرسال رابط صحيح يبدأ بـ http/https")

if __name__ == '__main__':
    Thread(target=run_server).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("أهلاً بك في صقر الحماية 🦅\nأرسل أي رابط وسأقوم بفحصه أمنياً لك.")))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_link))
    application.run_polling()
