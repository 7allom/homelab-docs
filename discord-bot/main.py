"""
Discord Bot Master Script
Features: Gemini AI integration, dynamic voice channels, persistent voice jail,
music playback, and moderation tools.
"""

import asyncio
import json
import os
import random

import discord
import nacl
import yt_dlp
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables (.env file)
load_dotenv()


# ==========================================
# 1. GLOBAL CONFIGURATION & INITIALIZATION
# ==========================================

# --- Channel & Role IDs ---
WELCOME_CHANNEL_ID = 123456789012345678
HUB_VOICE_CHANNEL_ID = 123456789012345678
JAIL_VOICE_CHANNEL_ID = 123456789012345678
STUDY_ROLE_ID = 123456789012345678

# --- File Paths ---
JAIL_FILE = "/app/data/jail_data.json"

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
temp_voice_channels = []  # Tracks dynamically created voice channels

# --- Gemini AI Setup ---
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

roast_system_prompt = (
    "Your prompt"
)

ask_system_prompt = (
    "Your prompt"
)

welcome_system_prompt = (
    "Your prompt"
)

goodbye_system_prompt = (
    "Your prompt"
)

# --- Music/YouTube-DLP Setup ---
ytdl_format_options = {
    "format": "bestaudio/best",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}

ffmpeg_options = {
    "options": "-vn",
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================


async def safe_ai_request(prompt: str, system_prompt: str, retries: int = 3):
    """
    Attempts to call the Gemini API, retrying automatically on 503 overloaded errors
    using exponential backoff to prevent command timeouts.
    """
    for attempt in range(retries):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            # If it's a 503 (Overloaded) or 429 (Rate Limit), wait and try again
            if "503" in error_msg or "429" in error_msg:
                if attempt < retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s...
                    print(
                        f"API Overloaded (503). Retrying in {wait_time}s... (Attempt {attempt + 1}/{retries})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
            # If it's a different error, or we ran out of retries, throw the error
            print(f"Fatal AI Error: {error_msg}")
            raise e


def load_jail():
    """Reads the persistent jail data from the local JSON file."""
    if os.path.exists(JAIL_FILE):
        with open(JAIL_FILE, "r") as f:
            return json.load(f)
    return []


def save_jail():
    """Writes the current list of jailed IDs to the local JSON file."""
    with open(JAIL_FILE, "w") as f:
        json.dump(jailed_users, f)


# Load the prisoners into memory immediately when the script executes
jailed_users = load_jail()


# ==========================================
# 3. UI COMPONENTS (VIEWS)
# ==========================================


class SquadView(discord.ui.View):
    """Interactive button view for the /squad command to track who is joining a game."""

    def __init__(self, host: discord.Member, game: str):
        super().__init__(timeout=7200)  # Buttons expire after 2 hours to save memory
        self.host = host
        self.game = game
        self.players = [host.mention]  # The host is automatically the first player

    def generate_embed(self):
        """Builds the dynamic embed showing the current roster."""
        player_list = "\n".join(f"🎮 {player}" for player in self.players)
        embed = discord.Embed(
            title=f"Looking for squad: {self.game}",
            description=f"{self.host.mention} is rallying the troops.\n\n**Current Roster ({len(self.players)}):**\n{player_list}",
            color=discord.Color.brand_red(),
        )
        return embed

    @discord.ui.button(
        label="Join Squad", style=discord.ButtonStyle.success, emoji="✅"
    )
    async def join_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.mention not in self.players:
            self.players.append(interaction.user.mention)
            await interaction.response.edit_message(
                embed=self.generate_embed(), view=self
            )
        else:
            await interaction.response.send_message(
                "You're already in the squad, calm down.", ephemeral=True
            )

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.secondary, emoji="❌")
    async def leave_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # If the host leaves, disband the entire squad and disable buttons
        if interaction.user.mention == self.host.mention:
            for child in self.children:
                child.disabled = True
            embed = discord.Embed(
                title=f"❌ Squad Canceled: {self.game}",
                description=f"{self.host.mention} has disbanded the squad lobby.",
                color=discord.Color.dark_gray(),
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return

        # If a regular player leaves, remove them from the roster
        if interaction.user.mention in self.players:
            self.players.remove(interaction.user.mention)
            await interaction.response.edit_message(
                embed=self.generate_embed(), view=self
            )
        else:
            await interaction.response.send_message(
                "You aren't even in the squad.", ephemeral=True
            )


# ==========================================
# 4. BOT EVENTS
# ==========================================


@bot.event
async def on_ready():
    """Triggered when the bot successfully connects to Discord."""
    print("==============================")
    print(f"Bot is online! Logged in as: {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print("==============================")


@bot.event
async def on_member_join(member):
    """Triggered when a new user joins the server. Sends an AI-generated welcome."""
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        try:
            prompt = (
                f"Write a welcome message for our newest member: {member.display_name}."
            )
            welcome_text = await safe_ai_request(prompt, welcome_system_prompt)
        except Exception as e:
            print(f"Welcome AI Error: {e}")
            welcome_text = (
                "Welcome to the server! Grab a seat and make yourself comfortable."
            )

        description_with_ping = f"{member.mention}\n\n{welcome_text}"
        embed = discord.Embed(
            title="A new challenger approaches!",
            description=description_with_ping,
            color=discord.Color.brand_green(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)


@bot.event
async def on_member_remove(member):
    """Triggered when a user leaves the server. Sends an AI-generated roast."""
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        try:
            prompt = f"Write a sarcastic goodbye message for the user who just left: {member.display_name}."
            goodbye_text = await safe_ai_request(prompt, goodbye_system_prompt)
        except Exception as e:
            print(f"Goodbye AI Error: {e}")
            deadpool_goodbyes = [
                f"Good riddance! **{member.display_name}** finally left.",
                f"And **{member.display_name}** is gone. "
            ]
            goodbye_text = random.choice(deadpool_goodbyes)

        embed = discord.Embed(
            title="Someone left...",
            description=goodbye_text,
            color=discord.Color.dark_grey(),
        )
        await channel.send(embed=embed)


@bot.event
async def on_voice_state_update(member, before, after):
    """Handles logic for Voice Jail enforcement and Dynamic Voice Channel creation/deletion."""

    # --- 1. The Jail Mechanism ---
    # Enforce jail: if they move to any VC and are on the list, drag them to the actual Jail VC.
    if member.id in jailed_users and after.channel is not None:
        if after.channel.id != JAIL_VOICE_CHANNEL_ID:
            jail_channel = member.guild.get_channel(JAIL_VOICE_CHANNEL_ID)
            if jail_channel:
                await member.move_to(jail_channel)
                return  # Stop execution to prevent dynamic channel creation

    # --- 2. Dynamic Voice Channel Creation ---
    # If a user joins the designated "Hub" channel, create a new private VC for them.
    if after.channel and after.channel.id == HUB_VOICE_CHANNEL_ID:
        category = after.channel.category
        new_channel = await member.guild.create_voice_channel(
            name=f"{member.display_name}'s VC", category=category
        )
        await member.move_to(new_channel)
        temp_voice_channels.append(new_channel.id)

    # --- 3. Dynamic Voice Channel Deletion ---
    # Clean up empty temporary voice channels.
    if before.channel and before.channel.id in temp_voice_channels:
        if len(before.channel.members) == 0:
            await before.channel.delete()
            temp_voice_channels.remove(before.channel.id)


# ==========================================
# 5. SLASH COMMANDS
# ==========================================

# --- Utility & Fun Commands ---


@bot.tree.command(name="squad", description="Rally the boys for a game.")
@app_commands.describe(game="What game are we playing?")
@app_commands.choices(
    game=[
        app_commands.Choice(name="Deadlock", value="Deadlock"),
        app_commands.Choice(name="Overwatch 2", value="Overwatch 2"),
        app_commands.Choice(name="Elden Ring", value="Elden Ring (Co-op)"),
        app_commands.Choice(name="Something Else", value="a mystery game"),
    ]
)
async def squad(interaction: discord.Interaction, game: app_commands.Choice[str]):
    view = SquadView(host=interaction.user, game=game.value)
    embed = view.generate_embed()
    await interaction.response.send_message(
        content=f"Time to play **{game.value}**!", embed=embed, view=view
    )


@bot.tree.command(name="play", description="Forces me to play music for you.")
@app_commands.describe(search="A YouTube link or search term")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer(thinking=True)

    if not interaction.user.voice:
        await interaction.followup.send(
            "Get in a voice channel first, you absolute donut."
        )
        return

    channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

    try:
        # Manage voice connection
        if voice_client is None or not voice_client.is_connected():
            voice_client = await channel.connect(timeout=10.0)
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

        loop = asyncio.get_event_loop()

        # Format search term if it's not a direct URL
        if not search.startswith(("http://", "https://")):
            search = f"ytsearch1:{search}"

        # Extract audio info
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(search, download=False)
        )
        if "entries" in data:
            data = data["entries"][0]

        url = data["url"]
        title = data.get("title", "Some noise")

        if voice_client.is_playing():
            voice_client.stop()

        # Play the audio stream
        voice_client.play(discord.FFmpegPCMAudio(url, **ffmpeg_options))
        await interaction.followup.send(f"Now playing: **{title}**")

    except Exception as e:
        print(f"Music Error: {e}")
        await interaction.followup.send("I couldn't play that. Blame YouTube.")


# --- AI Commands ---


@bot.tree.command(
    name="roast", description="He will verbally destroy someone using AI."
)
@app_commands.describe(
    target="The poor bastard you want to roast",
    topic="Optional: What should I roast them about? (e.g., terrible aim)",
)
async def roast(
    interaction: discord.Interaction, target: discord.Member, topic: str = None
):
    if target == bot.user:
        await interaction.response.send_message(
            "Nice try. I'm the one with the admin keys, moron."
        )
        return

    await interaction.response.defer()

    try:
        if topic:
            roast_prompt = f"Roast this Discord user: {target.display_name}. Focus the roast specifically on this topic: {topic}. Make it ruthless, short (1 to 2 sentences max), and keep your sarcastic persona."
        else:
            roast_prompt = f"Roast this Discord user: {target.display_name}. Make it ruthless, short (1 to 2 sentences max), and keep your sarcastic persona."

        roast_text = await safe_ai_request(roast_prompt, roast_system_prompt)
        await interaction.followup.send(f"{target.mention} {roast_text}")

    except Exception:
        await interaction.followup.send(
            f"I tried to roast {target.mention}, but my AI brain broke. Consider yourself lucky."
        )


@bot.tree.command(name="ask", description="Ask a stupid question.")
@app_commands.describe(question="What do you want to know?")
@app_commands.checks.cooldown(1, 7, key=lambda i: i.user.id)
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()

    try:
        text = await safe_ai_request(question, ask_system_prompt)

        # Smart Chunking for Discord's 2000 character limit
        if len(text) <= 2000:
            await interaction.followup.send(text)
        else:
            while len(text) > 0:
                if len(text) <= 2000:
                    await interaction.followup.send(text)
                    break

                # Find safe splitting points (paragraphs, lines, spaces)
                split_at = text.rfind("\n\n", 0, 2000)
                if split_at == -1:
                    split_at = text.rfind("\n", 0, 2000)
                if split_at == -1:
                    split_at = text.rfind(" ", 0, 2000)
                if split_at == -1:
                    split_at = 2000

                chunk = text[:split_at]
                await interaction.followup.send(chunk)
                text = text[split_at:].lstrip()

    except Exception as e:
        print(f"API Error: {e}")
        await interaction.followup.send("My brain broke. Try again later.")


# --- Moderation & Admin Commands ---


@bot.tree.command(name="jail", description="Lock a user in the voice jail.")
@app_commands.describe(target="The troublemaker to lock away")
@app_commands.checks.has_permissions(administrator=True)
async def jail(interaction: discord.Interaction, target: discord.Member):
    if target.id == interaction.user.id:
        await interaction.response.send_message(
            "You can't jail yourself, genius.", ephemeral=True
        )
        return

    if target.id not in jailed_users:
        jailed_users.append(target.id)
        save_jail()
        await interaction.response.send_message(
            f"🚨 {target.mention} has been sentenced to voice jail!"
        )

        # Snap-teleport them to jail immediately if they are already in a VC
        if target.voice and target.voice.channel:
            jail_channel = interaction.guild.get_channel(JAIL_VOICE_CHANNEL_ID)
            if jail_channel:
                await target.move_to(jail_channel)
    else:
        await interaction.response.send_message(
            f"{target.display_name} is already in jail.", ephemeral=True
        )


@bot.tree.command(name="unjail", description="Release a user from voice jail.")
@app_commands.describe(target="The citizen to pardon")
@app_commands.checks.has_permissions(administrator=True)
async def unjail(interaction: discord.Interaction, target: discord.Member):
    if target.id in jailed_users:
        jailed_users.remove(target.id)
        save_jail()
        await interaction.response.send_message(
            f"🔓 {target.mention} has been released from voice jail. Act natural."
        )
    else:
        await interaction.response.send_message(
            f"{target.display_name} isn't even in jail.", ephemeral=True
        )


@bot.tree.command(
    name="flashbang", description="Temporarily displace a friend's reality with audio."
)
@app_commands.describe(target="The victim to disorient")
@app_commands.checks.has_role("PUT ROLE NAME HERE")
async def flashbang(interaction: discord.Interaction, target: discord.Member):
    YOUR_DISCORD_ID = 123456789012345678

    # Immunity check
    if target.id == YOUR_DISCORD_ID or target == bot.user:
        await interaction.response.send_message(
            "You dare use my own spells against me? Target is immune.", ephemeral=True
        )
        return

    if not target.voice or not target.voice.channel:
        await interaction.response.send_message(
            "They need to be in a voice channel to get flashbanged.", ephemeral=True
        )
        return

    original_channel = target.voice.channel
    temp_channel = interaction.guild.get_channel(JAIL_VOICE_CHANNEL_ID)

    if not temp_channel or original_channel == temp_channel:
        await interaction.response.send_message(
            "Flashbang failed. Environment unstable.", ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        # Prepare the room and bot connection
        voice_client = interaction.guild.voice_client
        if voice_client:
            await voice_client.disconnect()

        vc = await temp_channel.connect()

        # Execute the flashbang sequence
        await target.move_to(temp_channel)
        await interaction.followup.send(
            f"💣 THROWING AUDIO FLASHBANG AT {target.mention}!"
        )

        if os.path.exists("flashbang.mp3"):
            vc.play(discord.FFmpegPCMAudio("flashbang.mp3"))

        await asyncio.sleep(3)

        # Cleanup and return victim to original channel
        if target.voice and target.voice.channel == temp_channel:
            await target.move_to(original_channel)

        await vc.disconnect()

    except discord.Forbidden:
        await interaction.followup.send(
            "I don't have permission to move them. Their armor is too thick."
        )
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
    except Exception as e:
        print(f"Flashbang Error: {e}")
        await interaction.followup.send("The flashbang was a dud. (Internal Error)")
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()


@bot.tree.command(
    name="gostudy",
    description="Force someone to go study. Mutes text and bans from VC.",
)
@app_commands.describe(target="The student who needs to focus")
@app_commands.checks.has_permissions(administrator=True)
async def gostudy(interaction: discord.Interaction, target: discord.Member):
    if target == bot.user:
        await interaction.response.send_message(
            "I am an AI. I already know everything.", ephemeral=True
        )
        return

    study_role = interaction.guild.get_role(STUDY_ROLE_ID)
    if not study_role:
        await interaction.response.send_message(
            "Study role not found! Check the STUDY_ROLE_ID in the code.", ephemeral=True
        )
        return

    if study_role in target.roles:
        await interaction.response.send_message(
            f"{target.display_name} is already locked in study mode!", ephemeral=True
        )
        return

    try:
        await target.add_roles(study_role)
        await interaction.response.send_message(
            f"📚 {target.mention} has been banished to the study zone. No typing, no talking."
        )

        # Force disconnect if they are in a voice channel
        if target.voice and target.voice.channel:
            await target.move_to(None)

    except discord.Forbidden:
        await interaction.response.send_message(
            "I don't have permission to assign that role. Make sure my bot role is higher than the Study role in server settings!",
            ephemeral=True,
        )


@bot.tree.command(name="endstudy", description="Allow a user to return to society.")
@app_commands.describe(target="The student to release")
@app_commands.checks.has_permissions(administrator=True)
async def endstudy(interaction: discord.Interaction, target: discord.Member):
    study_role = interaction.guild.get_role(STUDY_ROLE_ID)

    if study_role in target.roles:
        await target.remove_roles(study_role)
        await interaction.response.send_message(
            f"🎮 {target.mention} is done studying. Welcome back to the grid."
        )
    else:
        await interaction.response.send_message(
            f"{target.display_name} isn't even in study mode.", ephemeral=True
        )


# ==========================================
# 6. ERROR HANDLING & EXECUTION
# ==========================================


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    """Global error handler for slash commands (e.g., cooldowns, missing permissions)."""
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Slow down! Wait {round(error.retry_after, 1)} seconds.", ephemeral=True
        )
    elif isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(
            "You don't have the security clearance to use that weapon.", ephemeral=True
        )
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "Admin privileges required. Back off.", ephemeral=True
        )
    else:
        print(f"An error occurred: {error}")


# Start the bot
bot.run(os.getenv("BOT_TOKEN"))
