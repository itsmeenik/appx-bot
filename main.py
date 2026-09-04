import os
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from config import Config
from flask import Flask
from threading import Thread

web_app = Flask(name)
@web_app.route('/')
def home():
    return "Bot is Active"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

app = Client("appx_advance_uploader", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)
user_data = {}

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        "👋 Hello Bhai! Main hoon aapka Advance Appx Extploader Bot.\n\n"
        "Mujhe kisi bhi class/batch ki .txt file send karein, main usko poora index aur quality ke sath upload karunga!"
    )

@app.on_message(filters.document)
async def doc_handler(client, message):
    if message.document.file_name.endswith(".txt"):
        msg = await message.reply_text("📥 File download ho rahi hai...")
        file_path = await message.download()
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        os.remove(file_path)
        parsed_links = []
        for line in lines:
            if " : " in line and "http" in line:
                parts = line.split(" : ")
                parsed_links.append({"title": parts[0].strip(), "url": parts[1].strip()})
        if not parsed_links:
            await msg.edit_text("❌ Is file me Title : Link ka sahi format nahi mila.")
            return
        chat_id = message.chat.id
        user_data[chat_id] = {"links": parsed_links, "msg_id": msg.id}
        await msg.edit_text(f"📊 Total {len(parsed_links)} videos mili hain.\n\n👉 Bhai, kis Index number se uploading shuru karni hai? (Sirf number bhejein, jaise 1 ya 96):")
    else:
        await message.reply_text("⚠️ Kripya sirf .txt file send karein.")

@app.on_message(filters.text & ~filters.command(["start"]))
async def text_handler(client, message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return
    state = user_data[chat_id]
    if "start_index" not in state:
        try:
            start_idx = int(message.text.strip())
            if start_idx < 1 or start_idx > len(state["links"]):
                await message.reply_text(f"❌ Sahi number dalein (1 se {len(state['links'])} ke beech):")
                return
            state["start_index"] = start_idx
            keyboard = ReplyKeyboardMarkup([["480p", "720p"]], resize_keyboard=True, one_time_keyboard=True)
            await message.reply_text("🎬 Ab Video Quality select karein jisme upload karna hai:", reply_markup=keyboard)
        except ValueError:
            await message.reply_text("🔢 Kripya sirf ek valid number dalein:")
    elif "quality" not in state:
        quality = message.text.strip()
        if quality not in ["480p", "720p"]:
            await message.reply_text("❌ Kripya button me se '480p' ya '720p' select karein:")
            return
        state["quality"] = quality
        start_num = state["start_index"]
        links_to_process = state["links"][start_num - 1:]
        total_links = len(state["links"])
        status_msg = await message.reply_text("⚡ Uploading Shuru Ho Rahi Hai...", reply_markup=ReplyKeyboardRemove())
        asyncio.create_task(process_uploads(client, message, links_to_process, start_num, total_links, quality, status_msg))

async def process_uploads(client, message, links, start_num, total_links, quality, status_msg):
    # Pure function ko single line statements me likha hai taaki space error ka koi chance na rahe
    current_index = start_num
    async with aiohttp.ClientSession() as session:
        for item in links:
            title = item["title"]
            raw_url = item["url"]
            final_url = f"{raw_url.split('quality=')[0]}quality={quality.replace('p','')}" if "quality=" in raw_url else f"{raw_url}&res={quality}"
            await status_msg.edit_text(f"⚙️ Live Process (Link {current_index}/{total_links})\n📁 File: {title}\n🎯 Task: Preparing Video Download...\n🎬 Selected Quality: {quality}")
            try:
                await message.reply_video(video=final_url, caption=f"Index: {current_index}\nTitle: {title}\nQuality: {quality}\n\n⚡ _Powered by Chotu_ 🤝")
                await asyncio.sleep(2)
            except Exception as e:
                await message.reply_text(f"❌ Error on Index {current_index}:\n{str(e)}")
            current_index += 1
    await status_msg.edit_text("✅ Aapke batch ki sabhi requested files live upload ho chuki hain!")
    user_data.pop(message.chat.id, None)

if __name__ == "__main__":
    Thread(target=run_web).start()
    app.run()
