from keep_alive import keep_alive
keep_alive()
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from keep_alive import keep_alive

# ===== KEEP BOT ALIVE =====
keep_alive()

# ===== LOAD TOKEN =====
load_dotenv()
TOKEN = os.getenv("TOKEN")

# ===== INTENTS =====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== CONFIG =====
WELCOME_CHANNEL_ID = 1430852024098095236  # your welcome channel ID
AUTO_ROLE_ID = 1431930680530571264       # your auto role ID
WELCOME_GIF = "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExeHhucXlsNHd2YWlmdTZ0Nno3bXR6Njg4NHU0dmsydDJweGJyZTd1NSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/RGadjcbJ0y9Ihf79qQ/giphy.gif"

RULES_TEXT = """
📜 **UUltimateLY Server Rules**

💖 Be respectful to everyone  
🚫 No toxicity, racism, or NSFW  
📁 Post scripts in correct channels  
🎁 No fake giveaways or scams  
⚙️ Listen to staff  
🌈 Chill, have fun, and enjoy UUltimateLY  

⚡ Breaking rules = warnings or bans
"""

# ===== READY =====
@bot.event
async def on_ready():
    print(f"🟢 UUltimateLY Welcomer Bot ready as {bot.user}")

# ===== MEMBER JOIN =====
@bot.event
async def on_member_join(member):
    guild = member.guild
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    member_count = guild.member_count

    embed = discord.Embed(
        title="✨ Welcome to UUltimateLY ✨",
        description=(
            f"🔥 **{member.mention} just joined the squad!**\n\n"
            f"🎮 You are **Member #{member_count}**\n"
            f"📜 Check the rules & enjoy your stay\n"
            f"💜 Anime • Roblox • Scripts • Vibes"
        ),
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    embed.set_image(url=WELCOME_GIF)
    embed.set_footer(text="UUltimateLY • Powering the next gen 💻")

    if channel:
        await channel.send(embed=embed)

    # Auto role
    if AUTO_ROLE_ID:
        role = guild.get_role(AUTO_ROLE_ID)
        if role:
            await member.add_roles(role)

    # DM rules
    try:
        dm_embed = discord.Embed(
            title="📜 Welcome to UUltimateLY!",
            description=RULES_TEXT,
            color=discord.Color.blurple()
        )
        await member.send(embed=dm_embed)
    except:
        pass  # DMs closed

# ===== TEST COMMAND =====
@bot.command()
async def testwelcome(ctx):
    member = ctx.author
    guild = ctx.guild
    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    embed = discord.Embed(
        title="✨ Welcome to UUltimateLY ✨",
        description=(
            f"🔥 **{member.mention} just joined the squad!**\n\n"
            f"🎮 You are **Member #{guild.member_count}**\n"
            f"📜 Check the rules & enjoy your stay\n"
            f"💜 Anime • Roblox • Scripts • Vibes"
        ),
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    embed.set_image(url=WELCOME_GIF)
    embed.set_footer(text="UUltimateLY • Powering the next gen 💻")

    await channel.send(embed=embed)
    await ctx.send("✅ Test welcome sent!")

# ===== RUN =====
bot.run(TOKEN)
