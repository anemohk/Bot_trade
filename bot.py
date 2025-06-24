# bot.py
import os
import telegram
import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import yfinance as yf

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')

bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
app = Flask(__name__)
scheduler = BackgroundScheduler()

def init_db():
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            expiry_minutes INTEGER NOT NULL,
            entry_time TIMESTAMP NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

async def send_telegram_message(message):
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=message,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error sending message: {e}")

def get_current_price(symbol):
    try:
        ticker = yf.Ticker(f"{symbol}=X")
        data = ticker.history(period='1d', interval='1m')
        return data['Close'].iloc[-1] if not data.empty else None
    except Exception as e:
        print(f"Could not fetch price for {symbol}: {e}")
        return None

def check_trade_outcome(trade_id):
    with app.app_context():
        conn = sqlite3.connect('trades.db')
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, direction, entry_price FROM trades WHERE id = ?", (trade_id,))
        trade = cursor.fetchone()
        if not trade: return

        symbol, direction, entry_price = trade
        current_price = get_current_price(symbol)
        if current_price is None: return

        result = "LOSS" if (direction == "CALL" and current_price <= entry_price) or \
                           (direction == "PUT" and current_price >= entry_price) else "WIN"

        cursor.execute("UPDATE trades SET status = ? WHERE id = ?", (result, trade_id))
        conn.commit()

        outcome_symbol = "✅" if result == "WIN" else "❌"
        outcome_message = f"""
      
