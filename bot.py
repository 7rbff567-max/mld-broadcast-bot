import os
import asyncio
import discord
from discord.ext import commands

# إعداد الصلاحيات
intents = discord.Intents.default()
intents.members = True

# إعداد البوت
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# عند تشغيل البوت
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم تسجيل الدخول كـ {bot.user}")
        print(f"✅ تم تسجيل {len(synced)} أمر سلاش")
    except Exception as error:
        print(f"❌ فشل تسجيل أوامر السلاش: {error}")


# إرسال رسالة خاصة لعضو واحد
async def send_dm(member, message, semaphore):
    async with semaphore:
        try:
            await member.send(message)

            # تأخير بسيط بين الإرسالات
            await asyncio.sleep(0.2)

            return True

        except discord.Forbidden:
            # العضو قافل الخاص أو يمنع رسائل السيرفر
            return False

        except discord.HTTPException as error:
            print(
                f"❌ فشل الإرسال إلى "
                f"{member.id}: {error}"
            )
            return False

        except Exception as error:
            print(
                f"❌ خطأ غير متوقع مع "
                f"{member.id}: {error}"
            )
            return False


# أمر السلاش
@bot.tree.command(
    name="broadcast",
    description="إرسال رسالة خاصة لجميع أعضاء السيرفر"
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

    # يمنع استخدام الأمر في الخاص
    if interaction.guild is None:
        return await interaction.response.send_message(
            "❌ استخدم الأمر داخل السيرفر فقط.",
            ephemeral=True
        )

    guild = interaction.guild

    # أخذ الأعضاء واستبعاد البوتات
    members = [
        member
        for member in guild.members
        if not member.bot
    ]

    # الرد مباشرة حتى لا تنتهي مهلة Discord
    await interaction.response.send_message(
        f"📢 بدأ إرسال الرسالة إلى "
        f"**{len(members)}** عضو..."
    )

    # 10 عمليات إرسال في نفس الوقت
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

    # حساب النتائج
    success = sum(
        result is True
        for result in results
    )

    failed = len(results) - success

    # تعديل رسالة البداية وإظهار النتيجة
    await interaction.edit_original_response(
        content=(
            "✅ اكتمل الإرسال!\n"
            f"📨 تم الإرسال: **{success}**\n"
            f"❌ فشل الإرسال: **{failed}**"
        )
    )


# إذا حاول شخص غير أدمن استخدام الأمر
@broadcast.error
async def broadcast_error(
    interaction: discord.Interaction,
    error
):

    if isinstance(
        error,
        discord.app_commands.MissingPermissions
    ):
        message = "❌ هذا الأمر للأدمن فقط."

    else:
        print(
            f"❌ Broadcast Error: "
            f"{repr(error)}"
        )

        message = "❌ حدث خطأ أثناء تنفيذ الأمر."

    # إرسال الخطأ بطريقة مناسبة
    if interaction.response.is_done():
        await interaction.followup.send(
            message,
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            message,
            ephemeral=True
        )


# تشغيل البوت باستخدام متغير Render
bot.run(
    os.getenv("DISCORD_TOKEN")
)
