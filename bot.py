import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول كـ {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"تمت مزامنة {len(synced)} أمر")
    except Exception as e:
        print(e)

async def send_dm(member, message, semaphore):
    async with semaphore:
        for attempt in range(3):  # 3 محاولات لو صار rate limit
            try:
                await member.send(message)
                return True
            except discord.Forbidden:
                return False  # العضو مغلق الخاص أو حاظر البوت
            except discord.HTTPException as e:
                if e.status == 429:
                    retry_after = getattr(e, "retry_after", 2)
                    await asyncio.sleep(retry_after)
                    continue
                return False
        return False

@bot.tree.command(name="broadcast", description="إرسال رسالة خاصة لكل أعضاء السيرفر")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(message="نص الرسالة اللي بترسل لكل الأعضاء")
async def broadcast(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)

    guild = interaction.guild
    members = [m for m in guild.members if not m.bot]

    await interaction.followup.send(f"جاري إرسال الرسالة لـ {len(members)} عضو...")

    semaphore = asyncio.Semaphore(10)  # 10 رسائل متزامنة
    tasks = [send_dm(m, message, semaphore) for m in members]
    results = await asyncio.gather(*tasks)

    success = results.count(True)
    failed = results.count(False)

    await interaction.followup.send(f"✅ تم الإرسال: {success} | ❌ فشل: {failed}")

@broadcast.error
async def broadcast_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ هذا الأمر يتطلب صلاحية أدمن.", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
