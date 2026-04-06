import anthropic
import base64
import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

user_requests = {}
FREE_LIMIT = 5

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 MASK AI Trading Bot\n\n"
        "✅ Chart screenshot পাঠান\n"
        "⚡ ৫ সেকেন্ডে analysis পাবেন!"
    )

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in user_requests:
        user_requests[user_id] = FREE_LIMIT
    if user_requests[user_id] <= 0:
        await update.message.reply_text("❌ আপনার free limit শেষ।")
        return
    await update.message.reply_text("🔍 Analyzing chart...")
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = requests.get(file.file_path).content
    img_base64 = base64.b64encode(img_bytes).decode()
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": img_base64
                    }
                },
                {
                    "type": "text",
                    "text": """Analyze this binary options trading chart and respond in this exact format:

SIGNAL: [CALL or PUT]
STRENGTH: [50-95%]
TREND: [Uptrend/Downtrend/Sideways]
SUPPORT: [price level]
RESISTANCE: [price level]
LOGIC: [2-3 sentences explanation]
MARTINGALE: [+1 If Needed or No]"""
                }
            ]
        }]
    )
    result = response.content[0].text
    direction = "GO FOR BUY ⬆️" if "CALL" in result.upper() else "GO FOR SELL ⬇️"
    signal_emoji = "🟢" if "CALL" in result.upper() else "🔴"
    user_requests[user_id] -= 1
    remaining = user_requests[user_id]
    msg = f"""{signal_emoji} MASK AI BOT REPORT

{result}

📊 {direction}
✅ Remaining: {remaining}
⚡ Powered by Mask AI Bot"""
    await update.message.reply_text(msg)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analyze))
    app.run_polling()
