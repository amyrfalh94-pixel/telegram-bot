import re
import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.types import Channel, User

api_id = int(os.getenv("38389791"))
api_hash = os.getenv("0ec316cde3c866ac5365d8daae315461")
bot_token = os.getenv("8654595028:AAGrU4ySn3uEenKi7TcpUcjb_cujzBYIMHc")

bot = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

db = {}

def get_chat(chat_id):
    if chat_id not in db:
        db[chat_id] = {
            "owner": None,
            "warns": {},
            "settings": {
                "links": True,
                "usernames": True,
                "channels": True,
                "groups": True,
                "bots": True
            }
        }
    return db[chat_id]

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond(
        "👋 أهلاً بك في بوت الحماية",
        buttons=[
            [Button.inline("⚙️ لوحة التحكم", b"panel")]
        ]
    )

@bot.on(events.CallbackQuery)
async def panel(event):
    chat = get_chat(event.chat_id)

    if event.data == b"panel":
        await event.edit(
            "⚙️ لوحة التحكم:",
            buttons=[
                [Button.inline("🔗 الروابط", b"links")],
                [Button.inline("@ المعرفات", b"usernames")],
                [Button.inline("📊 الإنذارات", b"warns")]
            ]
        )

    elif event.data == b"links":
        chat["settings"]["links"] = not chat["settings"]["links"]
        await event.answer("تم التبديل")

    elif event.data == b"usernames":
        chat["settings"]["usernames"] = not chat["settings"]["usernames"]
        await event.answer("تم التبديل")

link_pattern = re.compile(r"(https?://|t\.me/)")

@bot.on(events.NewMessage)
async def filter_links(event):
    if not event.is_group:
        return

    chat = get_chat(event.chat_id)

    if chat["settings"]["links"]:
        if link_pattern.search(event.raw_text or ""):
            await event.delete()
            await warn_user(event)

username_pattern = re.compile(r"@(\w+)")

@bot.on(events.NewMessage)
async def filter_usernames(event):
    if not event.is_group:
        return

    chat = get_chat(event.chat_id)

    if not chat["settings"]["usernames"]:
        return

    text = event.raw_text or ""
    matches = username_pattern.findall(text)

    for username in matches:
        try:
            entity = await bot.get_entity(username)

            if isinstance(entity, User):
                continue

            if isinstance(entity, Channel):
                if entity.broadcast and chat["settings"]["channels"]:
                    await event.delete()
                    await warn_user(event)
                    return

                if entity.megagroup and chat["settings"]["groups"]:
                    await event.delete()
                    await warn_user(event)
                    return

            if getattr(entity, "bot", False) and chat["settings"]["bots"]:
                await event.delete()
                await warn_user(event)
                return

        except:
            pass

async def warn_user(event):
    chat = get_chat(event.chat_id)
    user_id = event.sender_id

    if user_id not in chat["warns"]:
        chat["warns"][user_id] = 0

    chat["warns"][user_id] += 1
    warns = chat["warns"][user_id]

    await event.respond(f"⚠️ تحذير {warns}/3")

    if warns >= 3:
        await bot.edit_permissions(event.chat_id, user_id, send_messages=False)
        await event.respond("🚫 تم تقييد المستخدم بسبب كثرة المخالفات")

@bot.on(events.NewMessage(pattern="/setowner"))
async def set_owner(event):
    chat = get_chat(event.chat_id)
    chat["owner"] = event.sender_id
    await event.respond("✅ تم تعيينك مالك")

print("Bot is running...")
bot.run_until_disconnected()
