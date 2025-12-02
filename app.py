import discord
from discord.ext import commands
import os
from datetime import datetime

# Flask for Render
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Mass DM Bot is Online"

TOKEN = os.getenv("DISCORD_TOKEN")

class MassDMBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        # Load DM cog
        try:
            await self.load_extension("cogs.dm")
            print("✅ Loaded DM cog")
        except Exception as e:
            print(f"❌ Failed to load cog: {e}")
        
        # Sync commands
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} commands")
        except:
            pass
    
    async def on_ready(self):
        print(f"🚀 {self.user} is ONLINE!")
        print(f"📊 Connected to {len(self.guilds)} servers")
        print(f"🔧 Prefix: !")
        
        # Set status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="!dmhelp"
            )
        )

if __name__ == "__main__":
    # Check token
    if not TOKEN:
        print("❌ ERROR: No Discord token found!")
        print("💡 Set DISCORD_TOKEN environment variable")
        exit(1)
    
    bot = MassDMBot()
    bot.run(TOKEN)
