import os
import json
from pathlib import Path

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# ========= ENV & INTENTS =========
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True          # untuk prefix cmd (opsional)
intents.members = True                  # wajib untuk add/remove role

bot = commands.Bot(command_prefix="!", intents=intents)

# ========= CONFIG STORAGE =========
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

DEFAULT_CONFIG = {
    "guilds": {}
}

def _default_guild_cfg():
    return {
        "autorole": {"enabled": True, "role_id": None},
        "verify": {"enabled": False, "channel_id": None, "message_id": None, "role_id": None, "emoji": "✅"}
    }

def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"guilds": {}}

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

config = load_config()

def gcfg(guild_id: int):
    gid = str(guild_id)
    if gid not in config["guilds"]:
        config["guilds"][gid] = _default_guild_cfg()
        save_config(config)
    # backfill keys
    for k, v in _default_guild_cfg().items():
        if k not in config["guilds"][gid]:
            config["guilds"][gid][k] = v
            save_config(config)
    return config["guilds"][gid]

# ========= UTIL =========
def require_admin():
    async def predicate(inter: discord.Interaction):
        perms = inter.user.guild_permissions
        if perms.administrator or perms.manage_guild:
            return True
        raise app_commands.AppCommandError("Butuh permission Administrator atau Manage Server.")
    return app_commands.check(predicate)

def bot_can_manage(role: discord.Role) -> bool:
    me = role.guild.me
    return me and me.guild_permissions.manage_roles and (me.top_role > role)

# ========= EVENTS =========
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash commands synced: {len(synced)}")
    except Exception as e:
        print("❌ Slash sync error:", e)

@bot.event
async def on_member_join(member: discord.Member):
    if member.bot:
        return
    cfg = gcfg(member.guild.id)
    ar = cfg["autorole"]
    if not ar.get("enabled", True) or not ar.get("role_id"):
        return
    role = member.guild.get_role(int(ar["role_id"]))
    if not role or not bot_can_manage(role):
        print("⚠️ Autorole: role tidak valid / bot tak bisa manage role tsb.")
        return
    try:
        await member.add_roles(role, reason="Autorole on join")
    except Exception as e:
        print("❌ Autorole gagal:", e)

# raw events untuk verifikasi (emoji)
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.guild_id is None:
        return
    cfg = gcfg(payload.guild_id)
    v = cfg["verify"]
    if not v.get("enabled"):
        return
    if payload.message_id != v.get("message_id"):
        return
    target_emoji = v.get("emoji", "✅")
    if payload.emoji.name != target_emoji:
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return
    role = guild.get_role(int(v["role_id"])) if v.get("role_id") else None
    if not role or not bot_can_manage(role):
        return

    try:
        await member.add_roles(role, reason="Verification react")
    except Exception as e:
        print("❌ Verify add role gagal:", e)

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.guild_id is None:
        return
    cfg = gcfg(payload.guild_id)
    v = cfg["verify"]
    if not v.get("enabled"):
        return
    if payload.message_id != v.get("message_id"):
        return
    target_emoji = v.get("emoji", "✅")
    if payload.emoji.name != target_emoji:
        return

    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return
    role = guild.get_role(int(v["role_id"])) if v.get("role_id") else None
    if not role or not bot_can_manage(role):
        return

    try:
        await member.remove_roles(role, reason="Verification unreact")
    except Exception as e:
        print("❌ Verify remove role gagal:", e)

# ========= SLASH CMDS =========
@bot.tree.command(name="setup_verify", description="Buat pesan verifikasi emoji dan set role yang diberikan.")
@require_admin()
@discord.app_commands.describe(
    channel="Channel tempat pesan verifikasi",
    role="Role yang diberikan setelah react",
    message="Isi pesan (opsional)",
    emoji="Emoji verifikasi (default: ✅)"
)
async def setup_verify(
    inter: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role,
    message: str = "Verifikasi diri kamu dengan react ✅ untuk mendapatkan akses.",
    emoji: str = "✅",
):
    if not bot_can_manage(role):
        await inter.response.send_message(
            "❌ Bot tidak bisa manage role itu. Pastikan bot punya **Manage Roles** dan **role bot** berada **di atas** role target.",
            ephemeral=True
        )
        return
    try:
        msg = await channel.send(message + f"\\n\\nKlik react **{emoji}** di bawah ini.")
        await msg.add_reaction(emoji)
    except Exception as e:
        await inter.response.send_message(f"❌ Gagal membuat pesan verifikasi: {e}", ephemeral=True)
        return

    cfg = gcfg(inter.guild_id)
    cfg["verify"] = {
        "enabled": True,
        "channel_id": channel.id,
        "message_id": msg.id,
        "role_id": role.id,
        "emoji": emoji,
    }
    save_config(config)

    note = ""
    if role >= inter.guild.me.top_role:
        note = "\\n⚠️ **Catatan**: Geser **role bot** ke atas role target di Server Settings → Roles."

    await inter.response.send_message(
        f"✅ Verifikasi diset!\\nChannel: {channel.mention}\\nRole: **{role.name}**\\nEmoji: {emoji}\\nMessage ID: `{msg.id}`{note}",
        ephemeral=True
    )

@bot.tree.command(name="verify_status", description="Lihat status & konfigurasi verifikasi.")
async def verify_status(inter: discord.Interaction):
    v = gcfg(inter.guild_id)["verify"]
    if not v.get("enabled"):
        await inter.response.send_message("ℹ️ Verifikasi: **OFF**", ephemeral=True)
        return
    ch = inter.guild.get_channel(v["channel_id"]) if v.get("channel_id") else None
    role = inter.guild.get_role(v["role_id"]) if v.get("role_id") else None
    emoji = v.get("emoji", "✅")
    await inter.response.send_message(
        f"ℹ️ Verifikasi: **ON**\\nChannel: {ch.mention if ch else '(missing)'}\\nRole: {role.mention if role else '(missing)'}\\nEmoji: {emoji}\\nMessage ID: `{v.get('message_id')}`",
        ephemeral=True
    )

@bot.tree.command(name="verify_on", description="Nyalakan verifikasi emoji.")
@require_admin()
async def verify_on(inter: discord.Interaction):
    g = gcfg(inter.guild_id)
    g["verify"]["enabled"] = True
    save_config(config)
    await inter.response.send_message("✅ Verifikasi: **ON**", ephemeral=True)

@bot.tree.command(name="verify_off", description="Matikan verifikasi emoji.")
@require_admin()
async def verify_off(inter: discord.Interaction):
    g = gcfg(inter.guild_id)
    g["verify"]["enabled"] = False
    save_config(config)
    await inter.response.send_message("🛑 Verifikasi: **OFF**", ephemeral=True)

@bot.tree.command(name="reset_verify", description="Hapus konfigurasi verifikasi.")
@require_admin()
async def reset_verify(inter: discord.Interaction):
    g = gcfg(inter.guild_id)
    g["verify"] = {"enabled": False, "channel_id": None, "message_id": None, "role_id": None, "emoji": "✅"}
    save_config(config)
    await inter.response.send_message("♻️ Konfigurasi verifikasi **di-reset**.", ephemeral=True)

@bot.tree.command(name="set_autorole", description="Set role autorole saat member join (opsional).")
@require_admin()
async def set_autorole(inter: discord.Interaction, role: discord.Role):
    if not bot_can_manage(role):
        await inter.response.send_message(
            "❌ Bot tidak bisa manage role itu. Cek permission & posisi role.", ephemeral=True
        )
        return
    g = gcfg(inter.guild_id)
    g["autorole"]["role_id"] = role.id
    save_config(config)
    warn = ""
    if role >= inter.guild.me.top_role:
        warn = "\\n⚠️ Geser role bot ke atas role target."
    await inter.response.send_message(f"✅ Autorole diset ke **{role.name}**.{warn}", ephemeral=True)

@bot.tree.command(name="autorole_on", description="Nyalakan autorole (opsional).")
@require_admin()
async def autorole_on(inter: discord.Interaction):
    g = gcfg(inter.guild_id)
    g["autorole"]["enabled"] = True
    save_config(config)
    await inter.response.send_message("✅ Autorole: **ON**", ephemeral=True)

@bot.tree.command(name="autorole_off", description="Matikan autorole (opsional).")
@require_admin()
async def autorole_off(inter: discord.Interaction):
    g = gcfg(inter.guild_id)
    g["autorole"]["enabled"] = False
    save_config(config)
    await inter.response.send_message("🛑 Autorole: **OFF**", ephemeral=True)

@bot.tree.command(name="autorole_status", description="Cek status autorole.")
async def autorole_status(inter: discord.Interaction):
    g = gcfg(inter.guild_id)["autorole"]
    role = inter.guild.get_role(g["role_id"]) if g.get("role_id") else None
    status = "ON" if g.get("enabled", True) else "OFF"
    await inter.response.send_message(
        f"ℹ️ Autorole: **{status}**\\nRole: {role.mention if role else '(belum diset)'}",
        ephemeral=True
    )

# basic ping
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN tidak ditemukan. Isi di file .env.")
    bot.run(TOKEN)
