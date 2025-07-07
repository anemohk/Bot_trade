# bot.py
import os # <-- إضافة مكتبة جديدة
from flask import Flask, request, jsonify
import requests
import threading
import time
from datetime import datetime, timedelta

# --- إعدادات ---
# سيتم الآن قراءة هذه المتغيرات من إعدادات Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- متغيرات لتخزين الإحصائيات ---
stats = {
    "wins": 0,
    "losses": 0,
    "last_reset": datetime.now()
}

app = Flask(__name__)

# --- بقية الكود تبقى كما هي تماماً ---
# (انسخ والصق كل الدوال من الرد السابق هنا: send_telegram_message, process_trade, etc.)

# --- دالة لإرسال الرسائل إلى تليجرام ---
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

# --- دالة لمعالجة كل صفقة في خيط منفصل ---
def process_trade(signal_data):
    pair = signal_data.get("pair")
    action = signal_data.get("action")
    trade_time = datetime.now()
    
    entry_message = (
        f"🚨 **إشارة جديدة** 🚨\n\n"
        f"📈 **الزوج:** `{pair}`\n"
        f"🔹 **الاتجاه:** `{action}`\n"
        f"⏳ **مدة الصفقة:** 5 دقائق\n"
        f"⏰ **التوقيت:** `{trade_time.strftime('%Y-%m-%d %H:%M:%S')}`"
    )
    send_telegram_message(entry_message)
    
    time.sleep(300)
    
    send_telegram_message(
        f"🔔 **انتهت مدة الصفقة** 🔔\n\n"
        f"الزوج: `{pair}` | الاتجاه: `{action}`\n\n"
        f"**الرجاء تأكيد النتيجة يدويًا لتحديث الإحصائيات!**"
    )

def check_and_reset_stats():
    global stats
    if datetime.now() - stats["last_reset"] > timedelta(hours=24):
        win_percentage = 0
        if (stats['wins'] + stats['losses']) > 0:
            win_percentage = (stats['wins'] / (stats['wins'] + stats['losses'])) * 100
            
        summary_message = (
            f"📊 **ملخص الـ 24 ساعة الماضية** 📊\n\n"
            f"✅ **الربح:** {stats['wins']}\n"
            f"❌ **الخسارة:** {stats['losses']}\n"
            f"🎯 **نسبة النجاح:** {win_percentage:.2f}%\n\n"
            f"تم إعادة تعيين العداد. بالتوفيق في اليوم الجديد!"
        )
        send_telegram_message(summary_message)
        stats = {"wins": 0, "losses": 0, "last_reset": datetime.now()}
        
@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return jsonify({"status": "error", "message": "Bot credentials are not set"}), 500
    check_and_reset_stats()
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
    print(f"Webhook received: {data}")
    trade_thread = threading.Thread(target=process_trade, args=(data,))
    trade_thread.start()
    return jsonify({"status": "success"}), 200

@app.route('/stats', methods=['GET'])
def get_stats():
    win_percentage = 0
    total_trades = stats['wins'] + stats['losses']
    if total_trades > 0:
        win_percentage = (stats['wins'] / total_trades) * 100
    stats_message = (
        f"📊 **الإحصائيات الحالية** 📊\n\n"
        f"✅ **الربح:** {stats['wins']}\n"
        f"❌ **الخسارة:** {stats['losses']}\n"
        f"📈 **إجمالي الصفقات:** {total_trades}\n"
        f"🎯 **نسبة النجاح:** {win_percentage:.2f}%"
    )
    send_telegram_message(stats_message)
    return jsonify(stats), 200
    
@app.route('/update_stats', methods=['GET'])
def update_stats():
    result = request.args.get('result')
    if result == 'win':
        stats['wins'] += 1
        send_telegram_message(f"✅ تم تسجيل صفقة رابحة. الإحصائيات المحدثة: {stats['wins']} ربح / {stats['losses']} خسارة.")
    elif result == 'loss':
        stats['losses'] += 1
        send_telegram_message(f"❌ تم تسجيل صفقة خاسرة. الإحصائيات المحدثة: {stats['wins']} ربح / {stats['losses']} خسارة.")
    else:
        return "Invalid result parameter. Use ?result=win or ?result=loss", 400
    return "Stats updated!", 200

@app.route('/')
def index():
    return "Bot is alive!", 200

# لا تحتاج قسم if __name__ == '__main__': لأن Render يستخدم Gunicorn
