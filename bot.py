import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# --- CONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# --- CAS ---
cases = {
    "Design": [
        {"title": "Flyer lancement produit", "format": "image"},
        {"title": "Post Instagram événement", "format": "image"}
    ],
    "Productivité": [
        {"title": "Trello board projet équipe", "format": "screenshot"},
        {"title": "Page Notion planning", "format": "screenshot"}
    ],
    "Réseau": [
        {"title": "Réseau Cisco Packet Tracer", "format": "screenshot"},
        {"title": "Architecture réseau entreprise", "format": "image"}
    ]
}

user_state = {}

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = "\n".join([f"- {d}" for d in cases.keys()])
    await update.message.reply_text(f"Choisis un domaine :\n{menu}")

# --- CHOIX ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if text in cases:
        user_state[user_id] = {"domaine": text}
        case_list = "\n".join([f"{i+1}. {c['title']}" for i, c in enumerate(cases[text])])
        await update.message.reply_text(f"Choisis un cas :\n{case_list}")
        return

    if user_id in user_state and "cas_index" not in user_state[user_id]:
        try:
            idx = int(text) - 1
            domaine = user_state[user_id]["domaine"]
            selected = cases[domaine][idx]

            user_state[user_id]["cas_index"] = idx
            user_state[user_id]["format"] = selected["format"]

            await update.message.reply_text(
                f"Cas : {selected['title']}\n"
                f"Format attendu : {selected['format']}\n"
                "Envoie ton image maintenant."
            )
        except:
            await update.message.reply_text("Choix invalide.")
        return

# --- ANALYSE IMAGE ---
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_state or "cas_index" not in user_state[user_id]:
        await update.message.reply_text("Choisis d'abord un cas.")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = f"{user_id}.jpg"
    await file.download_to_drive(file_path)

    await update.message.reply_text("Analyse en cours...")

    domaine = user_state[user_id]["domaine"]
    cas = cases[domaine][user_state[user_id]["cas_index"]]["title"]

    prompt = f"""
Analyse cette image pour le cas : {cas}

Donne :
1. Score /50 basé sur :
- Hiérarchie visuelle
- Lisibilité
- Couleurs / contraste
- Cohérence
- Impact

2. Erreurs critiques

3. Conseils d'amélioration concrets
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"file://{file_path}"}}
                ]}
            ]
        )

        result = response.choices[0].message.content
        await update.message.reply_text(result)

    except Exception as e:
        await update.message.reply_text(f"Erreur : {e}")

# --- APP ---
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_image))

app.run_polling()