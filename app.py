import discord
from discord.ext import commands
import os
from datetime import datetime
import threading

# Flask for Render
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Mass DM Bot is Online ✅"

def run_flask():
    """Run Flask in background"""
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

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
            print("⚠️ No slash commands to sync")
    
    async def on_ready(self):
        print(f"🚀 {self.user} is ONLINE!")
        print(f"📊 Connected to {len(self.guilds)} servers")
        print(f"🔧 Prefix: !")
        
        # Start Flask server for Render
        if os.environ.get('RENDER'):
            print("🌐 Starting Flask server for Render...")
            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()
            print("✅ Flask server started")
        
        # Set status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="!dmhelp"
            )
        )
    
    async def on_message(self, message):
        """Process commands when message is sent"""
        # Don't respond to bots
        if message.author.bot:
            return
        
        # Process commands
        await self.process_commands(message)

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 STARTING MASS DM BOT")
    print("=" * 50)
    
    # Check token
    if not TOKEN:
        print("❌ ERROR: No Discord token found!")
        print("💡 Set DISCORD_TOKEN environment variable")
        exit(1)
    
    print("✅ Token found")
    print("🔄 Starting bot...")
    
    bot = MassDMBot()
    
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("❌ ERROR: Invalid Discord token!")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
