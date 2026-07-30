import os
import asyncio
import threading

import discord
from discord.ext import commands
from flask import Flask


# =========================
# Flask - فتح منفذ لـ Render
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "MLD Broadcast Bot is Online!"


def run_web():
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False
    )


# =========================
# إعداد بوت Discord
# =========================

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# عند تشغيل البوت
# =========================

@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول كـ {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ تم تسجيل {len(synced)} أمر سلاش")

    except Exception as error:
        print(f"❌ فشل تسجيل أمر السلاش: {error}")


# =========================
# إرسال رسالة خاصة
# =========================

async def send_dm(member, message, semaphore):

    async with semaphore:

        try:
            await member.send(message)

            # تأخير بسيط
            await asyncio.sleep(0.2)

            return True

        except discord.Forbidden:
            return False

        except discord.HTTPException as error:
            print(
                f"❌ فشل الإرسال إلى "
                f"{member.id}: {error}"
            )

            return False

        except Exception as error:
            print(
                f"❌ خطأ مع "
                f"{member.id}: {error}"
            )

            return False


# =========================
# أمر /broadcast
# =========================

@bot.tree.command(
    name="broadcast",
    description="إرسال رسالة خاصة لأعضاء السيرفر"
)
@discord.app_commands.describe(
    message="اكتب الرسالة التي تريد إرسالها"
)
@discord.app_commands.checks.has_permissions(
    administrator=True
)
async def broadcast(
    interaction: discord.Interaction,
    message: str
):

    if interaction.guild is None:

        await interaction.response.send_message(
            "❌ استخدم الأمر داخل السيرفر فقط.",
            ephemeral=True
        )

        return

    guild = interaction.guild

    members = [
        member
        for member in guild.members
        if not member.bot
    ]

    await interaction.response.send_message(
        f"📢 بدأ إرسال الرسالة إلى "
        f"**{len(members)}** عضو..."
    )

    # 10 رسائل متزامنة
    semaphore = asyncio.Semaphore(10)

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

    await interaction.edit_original_response(
        content=(
            "✅ اكتمل الإرسال!\n"
            f"📨 تم الإرسال: **{success}**\n"
            f"❌ فشل الإرسال: **{failed}**"
        )
    )


# =========================
# أخطاء أمر السلاش
# =========================

@broadcast.error
async def broadcast_error(
    interaction: discord.Interaction,
    error
):

    if isinstance(
        error,
        discord.app_commands.MissingPermissions
    ):

        text = "❌ هذا الأمر للأدمن فقط."

    else:

        print(
            f"❌ Broadcast Error: "
            f"{repr(error)}"
        )

        text = "❌ حدث خطأ أثناء تنفيذ الأمر."

    if interaction.response.is_done():

        await interaction.followup.send(
            text,
            ephemeral=True
        )

    else:

        await interaction.response.send_message(
            text,
            ephemeral=True
        )


# =========================
# تشغيل Flask أولًا
# =========================

web_thread = threading.Thread(
    target=run_web,
    daemon=True
)

web_thread.start()


# =========================
# تشغيل البوت
# =========================

token = os.getenv("DISCORD_TOKEN")

if not token:

    raise RuntimeError(
        "❌ لم يتم العثور على DISCORD_TOKEN"
    )

bot.run(token)
