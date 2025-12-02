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
        try:
            # Load the massdm cog
            await self.load_extension("cogs.massdm")
            print("✅ Loaded Mass DM cog")
        except Exception as e:
            print(f"❌ Failed to load cog: {e}")
            print("Creating cogs directory...")
            
            # Create cogs directory if not exists
            if not os.path.exists('cogs'):
                os.makedirs('cogs')
                print("📁 Created cogs directory")
            
            # Create basic massdm.py if missing
            with open('cogs/massdm.py', 'w') as f:
                basic_cog = '''import discord
from discord.ext import commands

class MassDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def test(self, ctx):
        await ctx.send("✅ Bot is working!")

async def setup(bot):
    await bot.add_cog(MassDM(bot))'''
                f.write(basic_cog)
                print("📝 Created basic cogs/massdm.py")
            
            # Try loading again
            try:
                await self.load_extension("cogs.massdm")
                print("✅ Loaded basic cog")
            except Exception as e2:
                print(f"❌ Still failed: {e2}")

        # Sync commands
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} commands")
        except Exception as e:
            print(f"⚠️ Command sync error: {e}")

        # Start background tasks
        self.status_task.start()

    async def on_ready(self):
        print(f"🚀 {self.user} is ONLINE!")
        print(f"📊 Connected to {len(self.guilds)} servers")
        print(f"🔧 Prefix: !")
        print(f"💻 Commands: !setup, !setdm, !startdm, etc.")
        
        # Check token validity
        if not TOKEN:
            print("❌ ERROR: No Discord token found!")
        else:
            print("✅ Token: Found")
            
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

    @status_task.before_loop
    async def before_status_task(self):
        await self.wait_until_ready()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 STARTING MASS DM BOT")
    print("=" * 50)
    
    # Check for required files
    required_files = ['cogs/massdm.py', 'requirements.txt', 'Procfile']
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} - Found")
        else:
            print(f"⚠️ {file} - Missing")
    
    # Check token
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN environment variable not set!")
        print("💡 On Render: Add environment variable")
        print("💡 Locally: Create .env file with DISCORD_TOKEN=your_token")
    else:
        print("✅ Discord token: Loaded")
    
    print("-" * 50)
    
    # Create bot and run
    bot = MassDMBot()
    
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("❌ ERROR: Invalid Discord token!")
        print("💡 Check your token in Discord Developer Portal")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
