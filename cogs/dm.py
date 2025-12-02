import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import time

class MassDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_sending = False
        self.message = ""
        self.sent = 0
        self.failed = 0
        self.total = 0
    
    @commands.command(name="help")
    async def help_command(self, ctx):
        """Show help"""
        await ctx.send("**🤖 MASS DM BOT**\nCommands: `!setmsg`, `!preview`, `!startdm`, `!stopdm`, `!status`, `!test`")
    
    @commands.command(name="test")
    async def test(self, ctx):
        """Test if bot responds"""
        await ctx.send("✅ Bot is working!")
    
    @commands.command(name="setmsg")
    @commands.has_permissions(administrator=True)
    async def set_message(self, ctx, *, message: str):
        """Set the DM message"""
        self.message = message
        await ctx.send(f"✅ Message set! Preview: `{message[:50]}...`")
    
    @commands.command(name="preview")
    @commands.has_permissions(administrator=True)
    async def preview(self, ctx):
        """Preview message"""
        if not self.message:
            await ctx.send("❌ No message set!")
            return
        await ctx.send(f"**📝 Preview:**\n{self.message}")
    
    @commands.command(name="startdm")
    @commands.has_permissions(administrator=True)
    async def start_dm(self, ctx):
        """Start sending DMs"""
        if self.is_sending:
            await ctx.send("❌ Already sending!")
            return
        
        if not self.message:
            await ctx.send("❌ Set message first with `!setmsg`")
            return
        
        # Get members
        members = [m for m in ctx.guild.members if not m.bot]
        
        if len(members) == 0:
            await ctx.send("❌ No members found!")
            return
        
        # Confirmation
        msg = await ctx.send(f"Send DM to **{len(members)}** members? React ✅ to confirm, ❌ to cancel.")
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌']
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '✅':
                await msg.delete()
                await ctx.send(f"🔄 Starting DM to {len(members)} members...")
                await self._send_dms(ctx, members)
            else:
                await msg.delete()
                await ctx.send("❌ Cancelled.")
                
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.send("❌ Timeout.")
    
    async def _send_dms(self, ctx, members):
        """Send DMs"""
        self.is_sending = True
        self.sent = 0
        self.failed = 0
        
        progress_msg = await ctx.send(f"📤 **Progress:** 0/{len(members)}")
        
        for i, member in enumerate(members):
            if not self.is_sending:
                break
            
            try:
                await member.send(self.message)
                self.sent += 1
                print(f"✅ Sent to {member.name}")
            except:
                self.failed += 1
                print(f"❌ Failed for {member.name}")
            
            # Update progress
            if i % 5 == 0:
                await progress_msg.edit(content=f"📤 **Progress:** {i+1}/{len(members)} (✅{self.sent} ❌{self.failed})")
            
            # Delay
            await asyncio.sleep(1)
        
        # Final message
        if self.is_sending:
            await progress_msg.edit(content=f"✅ **Complete!** Sent: {self.sent}, Failed: {self.failed}")
        
        self.is_sending = False
    
    @commands.command(name="stopdm")
    @commands.has_permissions(administrator=True)
    async def stop_dm(self, ctx):
        """Stop sending"""
        if not self.is_sending:
            await ctx.send("❌ Not sending!")
            return
        
        self.is_sending = False
        await ctx.send(f"⏹️ Stopped! Sent: {self.sent}, Failed: {self.failed}")
    
    @commands.command(name="status")
    async def status(self, ctx):
        """Check status"""
        if self.is_sending:
            await ctx.send(f"🔄 Sending... {self.sent+self.failed}/{self.total}")
        else:
            if self.message:
                await ctx.send(f"✅ Ready! Message set: `{self.message[:30]}...`")
            else:
                await ctx.send("✅ Ready! No message set.")

async def setup(bot):
    await bot.add_cog(MassDM(bot))
