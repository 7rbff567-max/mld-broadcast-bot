import os
import asyncio
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كـ {bot.user}")


async def send_dm(member, message, semaphore):
    async with semaphore:
        try:
            await member.send(message)

            # تأخير بسيط بين عمليات الإرسال
            await asyncio.sleep(0.5)

            return True

        except discord.Forbidden:
            return False

        except discord.HTTPException as error:
            print(
                f"فشل الإرسال إلى "
                f"{member.id}: {error}"
            )
            return False

        except Exception as error:
            print(
                f"خطأ غير متوقع مع "
                f"{member.id}: {error}"
            )
            return False


@bot.command()
@commands.has_permissions(administrator=True)
async def broadcast(ctx, *, message: str):

    # يمنع استخدام الأمر في الخاص
    if ctx.guild is None:
        return await ctx.send(
            "❌ استخدم الأمر داخل السيرفر."
        )

    guild = ctx.guild

    members = [
        member
        for member in guild.members
        if not member.bot
    ]

    await ctx.send(
        f"📢 جاري إرسال الرسالة إلى "
        f"**{len(members)}** عضو..."
    )

    # عدد عمليات الإرسال المتزامنة
    semaphore = asyncio.Semaphore(3)

    tasks = [
        send_dm(
            member,
            message,
            semaphore
        )
        for member in members
    ]

    results = await asyncio.gather(
        *tasks,
        return_exceptions=True
    )

    success = sum(
        result is True
        for result in results
    )

    failed = len(results) - success

    await ctx.send(
        f"✅ اكتمل الإرسال!\n"
        f"تم الإرسال: **{success}**\n"
        f"فشل الإرسال: **{failed}**"
    )


@broadcast.error
async def broadcast_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):
        await ctx.send(
            "❌ هذا الأمر للأدمن فقط."
        )

    elif isinstance(
        error,
        commands.MissingRequiredArgument
    ):
        await ctx.send(
            "❌ الاستخدام الصحيح:\n"
            "`!broadcast رسالتك`"
        )

    else:
        print(
            f"❌ Broadcast Error: "
            f"{repr(error)}"
        )

        await ctx.send(
            "❌ حدث خطأ أثناء تنفيذ الأمر."
        )


bot.run(
    os.getenv("DISCORD_TOKEN")
)
