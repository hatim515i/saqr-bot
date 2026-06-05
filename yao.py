import os, requests, threading, time
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# إعداد السيرفر ليعمل 24/7 على رندر
PORT = int(os.environ.get('PORT', 10000))
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MODE = 1

# دالة الفحص العميق (التحليل الصدقي)
def deep_scan_page(url):
    try:
        # محاكاة متصفح بسيط
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # تحليل وجود خانات حساسة (تصيد)
        score = 0
        if soup.find('input', {'type': 'password'}): score += 50
        if soup.find('input', {'type': 'email'}): score += 20
        if not soup.find('title'): score += 20
        
        if score >= 50: return "⚠️ تحذير: الموقع يحتوي على خانات إدخال بيانات حساسة (احتمال تصيد عالي)!"
        return "✅ التحليل العميق: المحتوى يبدو طبيعياً ولا توجد روابط تلاعب ظاهرة."
    except Exception:
        return "❌ تعذر الدخول للموقع للفحص العميق (قد يكون الموقع محجوباً أو غير متاح)."

async def start(update, context):
    await update.message.reply_text("🦅 أهلاً بك يا حاتم! أرسل الرابط الذي تود فحص "صقرياً" الآن:")
    return MODE

async def handle_link(update, context):
    url = update.message.text
    msg = await update.message.reply_text("🔍 جاري البدء بالفحص الشامل للرابط...")
    
    try:
        # 1. الفحص الأولي (VirusTotal)
        await msg.edit_text("⏳ الفحص الأول: جارٍ فحص السمعة العالمية (VirusTotal)...")
        headers = {"x-apikey": VT_API_KEY}
        resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url})
        analysis_id = resp.json()['data']['id']
        time.sleep(5) # انتظار اكتمال الفحص
        res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
        stats = res.json()['data']['attributes']['stats']
        
        # 2. الفحص العميق (الصدقي)
        await msg.edit_text("🔎 الفحص الثاني: جارٍ التحليل العميق لمحتوى الصفحة...")
        deep_result = deep_scan_page(url)
        
        # النتيجة النهائية
        final_report = (f"🛡️ **تقرير صقر الحماية:**\n\n"
                        f"🌐 الفحص الأولي (VT): {stats['malicious']} ضار / {stats['harmless']} آمن\n"
                        f"📊 {deep_result}\n\n"
                        f"النتيجة النهائية: {'❌ الرابط مشبوه!' if (stats['malicious'] > 0 or '⚠️' in deep_result) else '✅ الرابط سليم حتى الآن.'}")
        
        await msg.edit_text(final_report)
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء الفحص: {str(e)}")
    
    return ConversationHandler.END

if __name__ == '__main__':
    app_bot = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={MODE: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link)]},
        fallbacks=[CommandHandler('start', start)]
    )
    app_bot.add_handler(conv)
    # تشغيل السيرفر في الخلفية
    threading.Thread(target=lambda: os.system("python3 -m http.server " + str(PORT)), daemon=True).start()
    app_bot.run_polling()
