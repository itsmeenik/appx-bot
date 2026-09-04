import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.custom import Button
from config import Config
from flask import Flask

# Flask setup for Render uptime (Fixed 'name' to 'name' here)
web_app = Flask(___name__)

@web_app.route('/')
def home():
    return "Bot is Active and Live!"

def run_web():
    from werkzeug.serving import make_server
    port = int(os.environ.get("PORT", 8080))
    srv = make_server('0.0.0.0', port, web_app)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, srv.serve_forever)

# Initialize Telethon Bot Client
bot = TelegramClient('appx_session', Config.API_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
user_data = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    await event.reply(
        "👋 Hello Bhai! Main hoon aapka Advance Appx Extploader Bot.\n\n"
        "Mujhe .txt file send karein, main usko poora index aur quality ke sath upload harunga!"
    )

@bot.on(events.NewMessage(incoming=True))
async def message_handler(event):
    chat_id = event.chat_id
    
    # Handle File/Document Upload
    if event.message.document and event.message.file.ext == '.txt':
        msg = await event.reply("📥 File download ho rahi hai...")
        file_path = await event.download_media()
        
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        os.remove(file_path)
        
        parsed_links = []
        for line in lines:
            if " : " in line and "http" in line:
                parts = line.split(" : ")
                parsed_links.append({"title": parts[0].strip(), "url": parts[1].strip()})
                
        if not parsed_links:
            await msg.edit("❌ Is file me Title : Link ka sahi format nahi mila.")
            return
            
        user_data[chat_id] = {"links": parsed_links, "msg_id": msg.id}
        await msg.edit(f"📊 Total {len(parsed_links)} videos mili hain.\n\n👉 Bhai, kis Index number se uploading shuru karni hai? (Sirf number bhejein, jaise 1):")
        return

    # Handle Text Input (Index and Quality)
    if chat_id in user_data and event.text and not event.text.startswith('/'):
        state = user_data[chat_id]
        
        if "start_index" not in state:
            try:
                start_idx = int(event.text.strip())
                if start_idx < 1 or start_idx > len(state["links"]):
                    await event.reply(f"❌ Sahi number dalein (1 se {len(state['links'])}):")
                    return
                state["start_index"] = start_idx
                
                # Show Quality selection inline buttons
                buttons = [
                    [Button.inline("480p", b"480p"), Button.inline("720p", b"720p")]
                ]
                await event.reply("🎬 Ab Video Quality select karein:", buttons=buttons)
            except ValueError:
                await event.reply("🔢 Kripya valid number dalein:")

# Handle Quality Button Click
@bot.on(events.CallbackQuery)
async def callback_handler(event):
    chat_id = event.chat_id
    if chat_id not in user_data:
        return
        
    state = user_data[chat_id]
    quality = event.data.decode('utf-8')
    state["quality"] = quality
    
    await event.answer(f"{quality} Selected", alert=False)
    status_msg = await event.respond("⚡ Uploading Shuru Ho Rahi Hai...")
    
    start_num = state["start_index"]
    links = state["links"][start_num - 1:]
    total_links = len(state["links"])
    
    current_index = start_num
    for item in links:
        title = item["title"]
        raw_url = item["url"]
        
        if "quality=" in raw_url:
            base_parts = raw_url.split("quality=")
            final_url = f"{base_parts[0]}quality={quality.replace('p','')}"
            else:
            final_url = f"{raw_url}&res={quality}"
        
        try:
            await status_msg.edit(f"⚙️ Live Process ({current_index}/{total_links})\n📁 File: {title}\n🎬 Quality: {quality}")
            await bot.send_file(chat_id, final_url, caption=f"Index: {current_index}\nTitle: {title}\nQuality: {quality}\n\n⚡ _Powered by Nik_ 🤝")
            await asyncio.sleep(3)
        except Exception as e:
            await event.respond(f"❌ Error on Index {current_index}:\n{str(e)}")
        current_index += 1
        
    await status_msg.edit("✅ Aapke batch ki sabhi requested files live upload ho chuki hain!")
    user_data.pop(chat_id, None)

if __name__ == "__main__":
    run_web()
    print("Bot is Starting...")
    bot.run_until_disconnected()
