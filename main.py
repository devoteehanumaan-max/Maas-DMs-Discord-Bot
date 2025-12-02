import discord
from discord.ext import commands, tasks
import os
import asyncio
import json
from datetime import datetime
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Mass DM Bot - Online ✅"

TOKEN = os.getenv("DISCORD_TOKEN")

class MassDMBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.start_time = datetime.now()
        self.admin_panel_channels = {}
        self.load_data()
        
    def load_data(self):
        try:
            with open('dm_bot_data.json', 'r') as f:
                data = json.load(f)
                self.admin_panel_channels = data.get('admin_channels', {})
        except:
            self.admin_panel_channels = {}
            
    def save_data(self):
        data = {'admin_channels': self.admin_panel_channels}
        with open('dm_bot_data.json', 'w') as f:
            json.dump(data, f, indent=4)

    async def setup_hook(self):
        # Create cogs folder if not exists
        if not os.path.exists('cogs'):
            os.makedirs('cogs')
            
        try:
            await self.load_extension("cogs.massdm")
            print("✅ Loaded Mass DM cog")
        except Exception as e:
            print(f"❌ Failed to load cog: {e}")
            # Try to create cog file if missing
            self.create_cog_file()

        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} commands")
        except Exception as e:
            print(f"⚠️ Command sync error: {e}")

        self.status_task.start()

    def create_cog_file(self):
        """Create massdm.py if missing"""
        cog_content = '''import discord
from discord.ext import commands

class MassDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def test(self, ctx):
        await ctx.send("✅ Bot is working!")

async def setup(bot):
    await bot.add_cog(MassDM(bot))'''
    
        with open('cogs/massdm.py', 'w') as f:
            f.write(cog_content)
        print("📁 Created cogs/massdm.py")

    async def on_ready(self):
        print(f"🚀 {self.user} is ONLINE!")
        print(f"📊 Connected to {len(self.guilds)} servers")
        print(f"🔧 Prefix: !")
        print(f"💻 Ready to send Mass DMs!")
        
    @tasks.loop(minutes=5)
    async def status_task(self):
        try:
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"!dmhelp | {len(self.guilds)} servers"
                )
            )
        except:
            pass

if __name__ == "__main__":
    print("🚀 Starting Mass DM Bot...")
    print(f"📁 Current directory: {os.getcwd()}")
    
    # Check for token
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables!")
        print("💡 Create .env file with: DISCORD_TOKEN=your_token_here")
        exit(1)
    
    bot = MassDMBot()
    
    # Run with error handling
    try:
        bot.run(TOKEN)
