import os, requests, time, threading
from bs4 import BeautifulSoup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

# إعدادات النظام
PORT = int(os.environ.get('PORT', 10000))
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')

# 1. فك الروابط المختصرة
def get_final_url(url):
    try:
        res = requests.head(url, allow_redirects=True, timeout=5)
        return res.url
    except: return url

# 2. الفحص الميداني (تحليل المحتوى)
def deep_scan(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # كشف المخاطر
        score = 0
        if soup.find('input', {'type': 'password'}): score += 50
        if soup.find('input', {'type': 'email'}): score += 20
        if score >= 50: return True # مشبوه
        return False
    except: return False

# 3. الفحص العالمي (خلف الكواليس)
def vt_check(url):
    try:
        headers = {"x-apikey": VT_API_KEY}
        resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url})
        analysis_id = resp.json()['data']['id']
        time.sleep(5)
        res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
        stats = res.json()['data']['attributes']['stats']
        return stats['malicious'] > 0
    except: return False

# النظام الموحد (قلب الصقر)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_url = update.message.text
    if not raw_url.startswith("http"): return
    
    status_msg = await update.message.reply_text("🦅 جاري تشغيل فحص الصقر الشامل...")
    
    # تنفيذ الفحوصات
    url = get_final_url(raw_url)
    is_bad_vt = vt_check(url)
    is_bad_deep = deep_scan(url)
    
    is_malicious = is_bad_vt or is_bad_deep
    
    report = (f"🛡️ **تقرير فحص الصقر الشامل**\n\n"
              f"🔗 النطاق: {url.split('//')[-1].split('/')[0]}\n\n"
              f"🔎 النتيجة النهائية:\n"
              f"{'❌ خطر: تم رصد نشاط مريب!' if is_malicious else '✅ آمن: لم يتم رصد أي مخاطر.'}\n\n"
              f"🦅 صقر الحماية - تقرير موثق.")
    
    await status_msg.edit_text(report)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🦅 أرسل الرابط وسأقوم بفحصه..")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    threading.Thread(target=lambda: os.system(f"python3 -m http.server {PORT}"), daemon=True).start()
    app.run_polling()
