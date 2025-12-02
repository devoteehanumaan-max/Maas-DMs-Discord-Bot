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
    
    # ========== BASIC COMMANDS ==========
    
    @commands.command(name="dmhelp")
    async def dm_help(self, ctx):
        """Show all commands"""
        embed = discord.Embed(
            title="🤖 MASS DM BOT - COMMANDS",
            description="Send messages to all server members",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📝 SETUP",
            value="`!setmsg [message]` - Set message to send\n`!preview` - Preview message",
            inline=False
        )
        
        embed.add_field(
            name="⚡ SENDING",
            value="`!startdm` - Start sending DMs\n`!stopdm` - Stop sending\n`!dmstatus` - Check status",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ SETTINGS",
            value="`!mode [fast/slow]` - Change speed\n`!testdm` - Test DM to yourself",
            inline=False
        )
        
        embed.set_footer(text="Made with ❤️")
        await ctx.send(embed=embed)
    
    @commands.command(name="setmsg")
    @commands.has_permissions(administrator=True)
    async def set_message(self, ctx, *, message: str):
        """Set the DM message"""
        self.message = message
        
        embed = discord.Embed(
            title="✅ MESSAGE SET",
            description=f"Message saved successfully!",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📝 PREVIEW",
            value=message[:500] + ("..." if len(message) > 500 else ""),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="preview")
    @commands.has_permissions(administrator=True)
    async def preview(self, ctx):
        """Preview the current message"""
        if not self.message:
            await ctx.send("❌ No message set! Use `!setmsg` first.")
            return
        
        embed = discord.Embed(
            title="📋 MESSAGE PREVIEW",
            description=self.message[:2000],
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(text=f"Length: {len(self.message)} characters")
        await ctx.send(embed=embed)
    
    # ========== DM SENDING ==========
    
    @commands.command(name="startdm")
    @commands.has_permissions(administrator=True)
    async def start_dm(self, ctx):
        """Start sending DMs to all members"""
        if self.is_sending:
            await ctx.send("❌ Already sending DMs! Use `!stopdm` to stop.")
            return
        
        if not self.message:
            await ctx.send("❌ No message set! Use `!setmsg` first.")
            return
        
        # Get all non-bot members
        members = [m for m in ctx.guild.members if not m.bot]
        
        if not members:
            await ctx.send("❌ No members found to DM!")
            return
        
        # Confirmation
        embed = discord.Embed(
            title="⚠️ CONFIRM MASS DM",
            description=f"This will send DM to **{len(members)}** members",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📊 ESTIMATED TIME",
            value=f"• Fast mode: `{len(members) * 0.5:.0f} seconds`\n• Slow mode: `{len(members) * 2:.0f} seconds`",
            inline=False
        )
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        
        # Wait for confirmation
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌']
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '✅':
                await msg.delete()
                await self._start_sending(ctx, members)
            else:
                await msg.delete()
                await ctx.send("❌ Cancelled.")
                
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.send("❌ Timeout. Cancelled.")
    
    async def _start_sending(self, ctx, members):
        """Actual sending function"""
        self.is_sending = True
        self.sent = 0
        self.failed = 0
        self.total = len(members)
        
        # Send initial progress message
        progress_msg = await ctx.send("🔄 **Starting Mass DM...**")
        
        start_time = time.time()
        
        # Send DMs
        for i, member in enumerate(members):
            if not self.is_sending:
                break
            
            try:
                # Send DM
                await member.send(self.message)
                self.sent += 1
                
            except discord.Forbidden:
                # DMs closed
                self.failed += 1
            except Exception as e:
                # Other errors
                self.failed += 1
                print(f"Error sending to {member.name}: {e}")
            
            # Update progress every 10 members
            if i % 10 == 0 or i == len(members) - 1:
                elapsed = time.time() - start_time
                progress = (i + 1) / len(members) * 100
                
                # Create progress embed
                embed = discord.Embed(
                    title="📤 SENDING DMs",
                    color=0x5865F2,
                    timestamp=datetime.utcnow()
                )
                
                # Progress bar
                filled = int(progress / 5)
                bar = "█" * filled + "░" * (20 - filled)
                
                embed.add_field(
                    name="📊 PROGRESS",
                    value=f"```\n{bar}\n{i+1}/{len(members)} | {progress:.1f}%\n```",
                    inline=False
                )
                
                embed.add_field(
                    name="📈 STATS",
                    value=f"• ✅ Sent: `{self.sent}`\n• ❌ Failed: `{self.failed}`",
                    inline=True
                )
                
                # Calculate speed
                if elapsed > 0:
                    speed = self.sent / elapsed
                    embed.add_field(
                        name="⚡ SPEED",
                        value=f"• `{speed:.2f}` DMs/sec",
                        inline=True
                    )
                
                try:
                    await progress_msg.edit(embed=embed)
                except:
                    pass
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)
        
        # Send completion message
        if self.is_sending:
            elapsed = time.time() - start_time
            
            embed = discord.Embed(
                title="✅ MASS DM COMPLETE",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            success_rate = (self.sent / len(members)) * 100
            
            embed.add_field(
                name="📊 RESULTS",
                value=f"```\nTotal: {len(members)}\n✅ Success: {self.sent}\n❌ Failed: {self.failed}\n🎯 Rate: {success_rate:.1f}%\n⏱️ Time: {elapsed:.1f}s\n```",
                inline=False
            )
            
            await progress_msg.edit(embed=embed)
        
        self.is_sending = False
    
    @commands.command(name="stopdm")
    @commands.has_permissions(administrator=True)
    async def stop_dm(self, ctx):
        """Stop sending DMs"""
        if not self.is_sending:
            await ctx.send("❌ No DM process running!")
            return
        
        self.is_sending = False
        
        embed = discord.Embed(
            title="⏹️ DM STOPPED",
            description="Stopped sending DMs",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📊 PARTIAL RESULTS",
            value=f"• ✅ Sent: `{self.sent}`\n• ❌ Failed: `{self.failed}`",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="dmstatus")
    async def dm_status(self, ctx):
        """Check DM status"""
        embed = discord.Embed(
            title="📊 DM STATUS",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        if self.is_sending:
            embed.description = "🔄 **SENDING DMs IN PROGRESS**"
            
            progress = (self.sent + self.failed) / self.total * 100 if self.total > 0 else 0
            
            embed.add_field(
                name="📈 PROGRESS",
                value=f"```\n{self.sent + self.failed}/{self.total}\n{progress:.1f}%\n```",
                inline=False
            )
            
            embed.add_field(
                name="📊 STATS",
                value=f"• ✅ Sent: `{self.sent}`\n• ❌ Failed: `{self.failed}`",
                inline=True
            )
        else:
            embed.description = "✅ **READY TO SEND**"
            
            if self.message:
                embed.add_field(
                    name="📝 CURRENT MESSAGE",
                    value=f"```\n{self.message[:100]}...\n```",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ NO MESSAGE SET",
                    value="Use `!setmsg` to set a message",
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    # ========== TEST COMMAND ==========
    
    @commands.command(name="testdm")
    @commands.has_permissions(administrator=True)
    async def test_dm(self, ctx):
        """Test DM to yourself"""
        try:
            await ctx.author.send("✅ Test DM from bot! If you received this, the bot can send DMs.")
            await ctx.send("✅ Test DM sent! Check your DMs.")
        except Exception as e:
            await ctx.send(f"❌ Failed to send test DM: {str(e)}")

async def setup(bot):
    await bot.add_cog(MassDM(bot))
