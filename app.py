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
    return "🤖 Mass DM Bot - Online"

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
        self.admin_panel_channels = {}  # {server_id: channel_id}
        self.load_data()
        
    def load_data(self):
        """Load saved data"""
        try:
            with open('dm_bot_data.json', 'r') as f:
                data = json.load(f)
                self.admin_panel_channels = data.get('admin_channels', {})
        except:
            self.admin_panel_channels = {}
            
    def save_data(self):
        """Save data to file"""
        data = {
            'admin_channels': self.admin_panel_channels
        }
        with open('dm_bot_data.json', 'w') as f:
            json.dump(data, f, indent=4)

    async def setup_hook(self):
        await self.load_extension("cogs.massdm")
        print("✅ Loaded Mass DM cog")
        await self.tree.sync()
        self.status_task.start()

    async def on_ready(self):
        print(f"🚀 {self.user} is ONLINE!")
        print(f"📊 Connected to {len(self.guilds)} servers")
        
    @tasks.loop(minutes=5)
    async def status_task(self):
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers"
            )
        )

if __name__ == "__main__":
    bot = MassDMBot()
    bot.run(TOKEN)
