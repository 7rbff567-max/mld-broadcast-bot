import os
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كـ {bot.user}")


@bot.command()
@commands.has_permissions(administrator=True)
async def broadcast(ctx, *, message: str):

    if ctx.guild is None:
        return await ctx.send("❌ هذا الأمر يعمل داخل السيرفر فقط.")

    guild = ctx.guild
    success = 0
    failed = 0

    await ctx.send(
        f"📢 جاري إرسال الرسالة إلى أعضاء السيرفر...\n"
        f"عدد الأعضاء: **{len(guild.members)}**"
    )

    for member in guild.members:

        if member.bot:
            continue

        try:
            await member.send(message)
            success += 1

        except discord.Forbidden:
            failed += 1

        except discord.HTTPException:
            failed += 1

        await asyncio.sleep(1.5)

    await ctx.send(
        f"✅ اكتمل الإرسال!\n"
        f"تم الإرسال: **{success}**\n"
        f"فشل الإرسال: **{failed}**"
    )


@broadcast.error
async def broadcast_error(ctx, error):

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ هذا الأمر للأدمن فقط.")

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "❌ الاستخدام الصحيح:\n"
            "`!broadcast اكتب رسالتك هنا`"
        )

    else:
        print(error)
        await ctx.send("❌ حدث خطأ أثناء تنفيذ الأمر.")


bot.run(os.getenv("DISCORD_TOKEN"))
