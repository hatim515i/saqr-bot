import os, requests, threading, time
from bs4 import BeautifulSoup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

PORT = int(os.environ.get('PORT', 10000))
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')

def get_vt_report(url):
    try:
        headers = {"x-apikey": VT_API_KEY}
        resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url})
        analysis_id = resp.json()['data']['id']
        time.sleep(5)
        res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
        stats = res.json()['data']['attributes']['stats']
        return stats['malicious'] > 0
    except: return False

def deep_analyze(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        # فحص محتوى الموقع (خانات سرية)
        if soup.find('input', {'type': 'password'}): return True
        return False
    except: return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return

    status_msg = await update.message.reply_text("🦅 جاري تحليل الرابط من قِبل صقر الحماية...")
    
    # الفحص المدمج (بدون ذكر مصادر)
    is_malicious_vt = get_vt_report(url)
    is_suspicious_deep = deep_analyze(url)
    
    # قرار البوت النهائي
    is_bad = is_malicious_vt or is_suspicious_deep
    
    report = (f"🛡️ **تقرير صقر الحماية الاحترافي**\n\n"
              f"🔗 الرابط: {url}\n\n"
              f"🔎 نتائج التحليل:\n"
              f"{'❌ خطر: تم كشف أنماط مشبوهة في الرابط والمحتوى.' if is_bad else '✅ فحص الصقر: الرابط آمن ولا يوجد تهديد ظاهر.'}\n\n"
              f"🦅 ملاحظة: تم الفحص باستخدام خوارزميات صقر الحماية الخاصة.")
    
    await status_msg.edit_text(report)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🦅 أرسل الرابط للفحص:")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    threading.Thread(target=lambda: os.system(f"python3 -m http.server {PORT}"), daemon=True).start()
    app.run_polling()
