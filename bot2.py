# ============================
# Night Neighbors System Bot
# ============================

import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import json
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ============================
# Data Setup
# ============================

if not os.path.exists("userdata.json"):
    with open("userdata.json", "w") as f:
        json.dump({}, f)

with open("userdata.json", "r") as f:
    user_data = json.load(f)

def save_user_data():
    with open("userdata.json", "w") as f:
        json.dump(user_data, f, indent=4)

# ============================
# Role Progression Map
# ============================

role_progression = {
    "Phantom": ["Phantom", "Phantom 2", "Phantom 3", "Undead", "The Ghost"],
    "Whisperer": ["Whisperer", "Whisperer 2", "Whisperer 3", "Echowalker", "The Vampire"],
    "Lurker": ["Lurker", "Lurker 2", "Lurker 3", "Shadowstalker", "Absolute Ninja"],
    "Dreamwalker": ["Dreamwalker", "Dreamwalker 2", "Dreamwalker 3", "Lucid Seeker", "The Nightmare"],
    "Angel": ["Angel", "Angel 2", "Angel 3", "Celestia", "The Heaven"]
}

# ============================
# Persistent Verify View
# ============================

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Verify | *Verifikasi*", style=discord.ButtonStyle.success, custom_id="verify_button")
    async def verify_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Adventurer")
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✅ Kamu telah diverifikasi!\n*You have been verified!*", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    print(f"{bot.user} is ready.")

# ============================
# Verification Command
# ============================

@bot.command()
async def verify(ctx):
    embed = discord.Embed(
        title="📜 Verify Yourself",
        description="Klik tombol di bawah untuk mendapatkan akses penuh ke server.\n\n*Click the button below to verify yourself.*",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=VerifyView())

# ============================
# Reaction Role System (Persistent)
# ============================

reaction_roles = {
    "💀": "Phantom",
    "🧛🏻‍♀️": "Whisperer",
    "🦉": "Lurker",
    "🦇": "Dreamwalker",
    "🪽": "Angel"
}

@bot.command()
async def roles(ctx):
    embed = discord.Embed(
        title="🎭 Choose Your Path",
        description=(
            "Pilih peran malam yang paling mencerminkan dirimu.\n"
            "*Choose the night identity that best reflects your soul.*\n\n"
            "Kamu hanya bisa memilih satu. Jika kamu memilih lebih dari satu, peran sebelumnya akan digantikan.\n"
            "*One choice. One path. If you select more than one, the previous role will be replaced.*\n\n"
            "💀 **Phantom**\n"
            "Hening, misterius, dan berjalan di antara bayangan.\n"
            "*Silent and unseen, they drift through shadows.*\n\n"
            "🧛 **Whisperer**\n"
            "Pembisik malam, membawa kisah dan rahasia tersembunyi.\n"
            "*Bearers of secrets and stories, they speak when the night listens.*\n\n"
            "🦉 **Lurker**\n"
            "Pengamat dalam diam, selalu hadir meski tak bersuara.\n"
            "*Watchful and calm, their eyes pierce through silence.*\n\n"
            "🦇 **Dreamwalker**\n"
            "Penjelajah dimensi mimpi, hidup antara ilusi dan realita.\n"
            "*Wanderers of dreamscapes, floating between illusion and truth.*\n\n"
            "🪽 **Angel**\n"
            "Cahaya lembut di tengah gelapnya malam, pelindung dan penyembuh.\n"
            "*Gentle lights in the dark. They protect and quietly heal.*\n\n"
            "*React with the emoji below to claim your role. The night awaits.*"
        ),
        color=discord.Color.dark_purple()
    )
    embed.set_footer(text="⚠️ You can only have ONE main role. You cannot choose another role, when you have chosen a role, please choose wisely.")
    message = await ctx.send(embed=embed)
    for emoji in reaction_roles:
        await message.add_reaction(emoji)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member is None or payload.member.bot:
        return

    guild = bot.get_guild(payload.guild_id)
    role_name = reaction_roles.get(str(payload.emoji))
    if not role_name:
        return

    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        return

    member = payload.member

    # Remove existing role from same category
    existing_roles = [r for r in member.roles if r.name in sum(role_progression.values(), [])]
    for r in existing_roles:
        await member.remove_roles(r)

    await member.add_roles(role)
    try:
        await member.send(f"✅ Kamu telah memilih peran: **{role.name}**\n*You have chosen the role: **{role.name}***")
    except:
        pass

# ============================
# Leveling System
# ============================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id not in user_data:
        user_data[user_id] = {"xp": 0, "level": 0}

    user_data[user_id]["xp"] += 5
    xp = user_data[user_id]["xp"]
    level = user_data[user_id]["level"]
    new_level = xp // 50

    if new_level > level:
        user_data[user_id]["level"] = new_level
        await handle_level_up(message.author, new_level, message.guild)

    save_user_data()
    await bot.process_commands(message)

async def handle_level_up(member, level, guild):
    user_roles = [role.name for role in member.roles if role.name.split()[0] in role_progression]
    if not user_roles:
        return

    main_role_key = user_roles[0].split()[0]
    progression = role_progression[main_role_key]
    stage = level // 15

    if stage >= len(progression):
        return

    new_role_name = progression[stage]
    old_roles = [discord.utils.get(guild.roles, name=name) for name in progression]

    new_role = discord.utils.get(guild.roles, name=new_role_name)
    if new_role is None:
        new_role = await guild.create_role(name=new_role_name)

    await member.add_roles(new_role)
    for role in old_roles:
        if role and role in member.roles and role != new_role:
            await member.remove_roles(role)

    try:
        channel = bot.get_channel(1402310010259771593)
        if channel:
            messages = {
                "Phantom": f"*You fade deeper into the unseen...*\n🎉 Selamat {member.mention}, kamu telah menjadi **{new_role.name}** di Level {level}!\n*The silence embraces you.*",
                "Whisperer": f"*Your whispers now echo through darker halls...*\n🎉 Selamat {member.mention}, kamu telah naik ke **{new_role.name}** di Level {level}!\n*The night listens more closely now.*",
                "Lurker": f"*The shadows welcome your gaze...*\n🎉 {member.mention}, kamu kini adalah **{new_role.name}**, Level {level}!\n*Your presence becomes harder to notice, yet impossible to ignore.*",
                "Dreamwalker": f"*Reality bends further around you...*\n🎉 Selamat {member.mention}, kamu kini memasuki Level {level} sebagai **{new_role.name}**!\n*Drift deeper between dreams and nightmares.*",
                "Angel": f"*Your light shines brighter in the dark...*\n😇 {member.mention}, kamu telah naik ke **{new_role.name}** di Level {level}!\n*Even silence feels safer around you.*"
            }
            await channel.send(messages.get(main_role_key, "🎉 Selamat!"))
            await member.send(messages.get(main_role_key, "🎉 Selamat!"))
    except Exception as e:
        print(f"Error sending level-up message: {e}")

# ============================
# Leaderboard Command
# ============================

@bot.command()
async def rank(ctx):
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['xp'], reverse=True)[:10]
    embed = discord.Embed(title="🏆 Top 10 Leaderboard", color=discord.Color.purple())

    for index, (user_id, data) in enumerate(sorted_users, start=1):
        user = await bot.fetch_user(int(user_id))
        embed.add_field(
            name=f"#{index} - {user.name}",
            value=f"Level: {data['level']} | XP: {data['xp']}",
            inline=False
        )

    embed.set_footer(text="Keep chatting to climb the ranks! 💬")
    await ctx.send(embed=embed)

    channel = bot.get_channel(1402310010259771593)
    if channel:
        await channel.send(embed=embed)

# ============================
# Check XP Command
# ============================

@bot.command()
async def xp(ctx):
    user_id = str(ctx.author.id)
    data = user_data.get(user_id, {"xp": 0, "level": 0})
    embed = discord.Embed(
        title=f"📊 XP & Level for {ctx.author.name}",
        description=f"Level: {data['level']}\nXP: {data['xp']}",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

# ============================
# Bot Run
# ============================

bot.run('THE_TOKEN')
