import os, requests, time, threading
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# إعدادات النظام
PORT = int(os.environ.get('PORT', 10000))
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 ميجابايت فقط لمنع تعليق السيرفر

# 1. فك الروابط وتتبعها
def get_final_url(url):
    try:
        res = requests.head(url, allow_redirects=True, timeout=5)
        return res.url
    except: return url

# 2. فحص المحتوى (ميداني)
def deep_scan_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        # فحص خانات حساسة
        if soup.find('input', {'type': 'password'}): return True
        return False
    except: return False

# 3. فحص عالمي (VirusTotal) - خلف الكواليس
def vt_check(url_or_file_id, is_file=False):
    try:
        headers = {"x-apikey": VT_API_KEY}
        if not is_file:
            resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url_or_file_id})
        else:
            resp = requests.post("https://www.virustotal.com/api/v3/files", headers=headers, files={"file": url_or_file_id})
        
        analysis_id = resp.json()['data']['id']
        time.sleep(5)
        res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
        stats = res.json()['data']['attributes']['stats']
        return stats['malicious'] > 0
    except: return False

# معالج الرسائل الموحد
async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("🦅 جاري فحص صقر الحماية الشامل...")

    # فحص الروابط
    if update.message.text:
        url = get_final_url(update.message.text)
        is_bad = vt_check(url) or deep_scan_url(url)
        report = f"🛡️ **تقرير صقر الحماية**\n\n🔗 {url}\n\nالنتيجة: {'❌ خطر! تم كشف تهديد.' if is_bad else '✅ آمن.'}"
    
    # فحص الملفات
    elif update.message.document:
        doc = update.message.document
        if doc.file_size > MAX_FILE_SIZE:
            report = "❌ الملف كبير جداً! صقر الحماية لا يفحص ملفات أكبر من 10MB حمايةً للسيرفر."
        else:
            file = await doc.get_file()
            file_bytes = await file.download_as_bytearray()
            is_bad = vt_check(file_bytes, is_file=True)
            report = f"🛡️ **تقرير صقر الحماية**\n\nملف: {doc.file_name}\n\nالنتيجة: {'❌ خطر! الملف مشبوه.' if is_bad else '✅ آمن.'}"
    
    await status_msg.edit_text(report)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("🦅 أرسل رابط أو ملف وسأقوم بفحصه..")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND) | filters.Document.ALL, handle_everything))
    
    threading.Thread(target=lambda: os.system(f"python3 -m http.server {PORT}"), daemon=True).start()
    app.run_polling()
