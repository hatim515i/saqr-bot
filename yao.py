import os, requests, threading, time
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# سيرفر البوت
PORT = int(os.environ.get('PORT', 10000))
TOKEN = os.environ.get('BOT_TOKEN')
VT_API_KEY = os.environ.get('VT_API_KEY')
MODE = 1

# 1. فحص المحتوى (التحليل الصدقي)
def deep_scan_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        score = 0
        # لو الموقع يطلب بيانات حساسة (باسورد، إيميل)
        if soup.find('input', {'type': 'password'}): score += 50
        if soup.find('input', {'type': 'email'}): score += 20
        # لو فيه روابط وهمية أو تلاعب
        if not soup.find('title'): score += 20
        
        if score >= 50: return "⚠️ **تحذير: الفحص العميق يشير إلى احتمال وجود صفحة تصيد (Phishing)!**"
        return "✅ **الفحص العميق: المحتوى يبدو طبيعياً.**"
    except:
        return "❌ **تعذر الدخول للموقع للفحص العميق (قد يكون محجوباً أو معطلاً).**"

async def handle_link(update, context):
    url = update.message.text
    msg = await update.message.reply_text("🔍 جاري البدء بالفحص الشامل...")
    
    # الفحص الأول: VirusTotal
    await msg.edit_text("⏳ جاري الفحص الأولي (VirusTotal)...")
    headers = {"x-apikey": VT_API_KEY}
    resp = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url})
    analysis_id = resp.json()['data']['id']
    time.sleep(5)
    res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
    stats = res.json()['data']['attributes']['stats']
    
    # الفحص الثاني: التحليل الصدقي
    await msg.edit_text("🔍 جاري الفحص العميق للمحتوى...")
    deep_result = deep_scan_page(url)
    
    # النتيجة النهائية
    final_report = (f"🛡️ **تقرير الصقر الشامل:**\n\n"
                    f"🟢 الفحص الأولي (VT): {stats['malicious']} ضار / {stats['harmless']} آمن\n"
                    f"🔎 {deep_result}\n\n"
                    f"النتيجة: {'❌ الرابط مشبوه!' if (stats['malicious'] > 0 or '⚠️' in deep_result) else '✅ الرابط سليم.'}")
    
    await msg.edit_text(final_report)
    return ConversationHandler.END

# بقية كود الـ Handlers كما هي...
