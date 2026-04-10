import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# 🔑 Récupération des variables d’environnement (Render)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🤖 Initialisation OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ▶️ Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut 👋 je suis ton bot IA. Pose-moi une question !")

# 💬 Réponse automatique avec OpenAI
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant utile."},
                {"role": "user", "content": user_message}
            ]
        )

        reply = response.choices[0].message.content
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text("Erreur ⚠️ : " + str(e))

# 🚀 Lancement du bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot lancé ✅")
app.run_polling()