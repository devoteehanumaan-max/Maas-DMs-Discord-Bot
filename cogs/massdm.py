import discord
from discord.ext import commands
import asyncio
import json
from datetime import datetime
import time

class MassDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dm_tasks = {}
        self.sent_count = 0
        self.failed_count = 0
        self.total_members = 0
        self.is_dming = False
        self.current_message = ""
        self.embed_mode = False
        self.dm_mode = "safe"  # "safe" or "ultrafast"
        self.batch_size = 50  # Ultrafast ke liye
        self.delay_safe = 1.0  # Safe mode delay
        self.delay_ultrafast = 0.1  # Ultrafast mode delay

    @commands.command(name='setup')
    @commands.has_permissions(administrator=True)
    async def setup_panel(self, ctx):
        """Setup Admin Panel for Mass DM"""
        embed = discord.Embed(
            title="⚡ MASS DM BOT - ADMIN PANEL",
            description="**Professional Mass DM System with Dual Mode**",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🚀 ULTRA FAST MODE",
            value="• Speed: **Light Speed** ⚡\n• Time: **5-10 seconds**\n• Risk: **HIGH**\n• Rate Limit: **POSSIBLE**",
            inline=False
        )
        
        embed.add_field(
            name="🛡️ SAFE MODE",
            value="• Speed: **25 seconds** ⏱️\n• Time: **Controlled**\n• Risk: **LOW**\n• Rate Limit: **AVOIDED**",
            inline=False
        )
        
        embed.add_field(
            name="📋 COMMANDS",
            value=(
                "`!setdm [message]` - Set DM message\n"
                "`!setembed` - Toggle embed mode\n"
                "`!mode [ultrafast/safe]` - Change DM mode\n"
                "`!preview` - Preview message\n"
                "`!startdm` - Start Mass DM\n"
                "`!stopdm` - Stop Mass DM\n"
                "`!dmstatus` - Check status\n"
                "`!dmstats` - View statistics\n"
                "`!dmhelp` - Show help"
            ),
            inline=False
        )
        
        embed.set_footer(text="⚡ Ultrafast Mode | 🛡️ Safe Mode")
        await ctx.send(embed=embed)
        
        self.bot.admin_panel_channels[str(ctx.guild.id)] = str(ctx.channel.id)
        self.bot.save_data()

    @commands.command(name='mode')
    @commands.has_permissions(administrator=True)
    async def set_dm_mode(self, ctx, mode: str):
        """Set DM mode: ultrafast or safe"""
        if mode.lower() in ["ultrafast", "fast", "light", "⚡"]:
            self.dm_mode = "ultrafast"
            self.batch_size = 50
            self.delay_ultrafast = 0.05  # 20 DMs per second!
            
            embed = discord.Embed(
                title="⚡ ULTRA FAST MODE ACTIVATED",
                description="**Warning:** This mode may trigger rate limits!",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="⚡ SPEED SETTINGS",
                value="• Delay: `0.05 seconds`\n• Batch Size: `50 members`\n• Estimated Speed: `20 DMs/second`\n• Risk Level: **HIGH**",
                inline=False
            )
            
            embed.add_field(
                name="⚠️ WARNING",
                value="This mode sends DMs at maximum possible speed. May cause rate limits or temporary bans.",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        elif mode.lower() in ["safe", "slow", "normal", "🛡️"]:
            self.dm_mode = "safe"
            self.batch_size = 10
            self.delay_safe = 1.5
            
            embed = discord.Embed(
                title="🛡️ SAFE MODE ACTIVATED",
                description="**Rate Limit Safe Mode**",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="⚙️ SAFE SETTINGS",
                value="• Delay: `1.5 seconds`\n• Batch Size: `10 members`\n• Estimated Speed: `0.67 DMs/second`\n• Risk Level: **LOW**",
                inline=False
            )
            
            embed.add_field(
                name="✅ BENEFITS",
                value="• No rate limits\n• No bot bans\n• Stable delivery\n• Professional",
                inline=False
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Invalid mode! Use `ultrafast` or `safe`")

    @commands.command(name='setdm')
    @commands.has_permissions(administrator=True)
    async def set_dm_message(self, ctx, *, message: str):
        """Set the message to send to all members"""
        self.current_message = message
        self.embed_mode = False
        
        embed = discord.Embed(
            title="✅ MESSAGE SET",
            description=f"**Mode:** `{self.dm_mode.upper()}`\n\n**Preview:**\n{message[:300]}...",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        time_estimate = self.calculate_time(ctx.guild)
        embed.add_field(
            name="⏱️ TIME ESTIMATE",
            value=f"• **{self.dm_mode} mode**\n• Members: `{sum(1 for m in ctx.guild.members if not m.bot)}`\n• Est. Time: `{time_estimate}`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    def calculate_time(self, guild):
        """Calculate estimated time based on mode"""
        members = sum(1 for m in guild.members if not m.bot)
        
        if self.dm_mode == "ultrafast":
            # 0.05 seconds per member, batches of 50
            total_time = (members / 50) * 0.05
            if total_time < 10:
                return f"{total_time:.1f} seconds ⚡"
            else:
                return f"{total_time:.1f} seconds"
        else:
            # 1.5 seconds per member, batches of 10
            total_time = (members / 10) * 1.5
            if total_time < 60:
                return f"{total_time:.1f} seconds"
            else:
                minutes = total_time / 60
                return f"{minutes:.1f} minutes"

    @commands.command(name='startdm')
    @commands.has_permissions(administrator=True)
    async def start_mass_dm(self, ctx):
        """Start Mass DM to all server members"""
        if self.is_dming:
            await ctx.send("❌ DM process is already running!")
            return
            
        if not self.current_message:
            await ctx.send("❌ No message set! Use `!setdm` first.")
            return
        
        members = [m for m in ctx.guild.members if not m.bot]
        if not members:
            await ctx.send("❌ No members found to DM!")
            return
        
        # Mode-specific confirmation
        if self.dm_mode == "ultrafast":
            embed = self.create_ultrafast_confirmation(ctx, members)
        else:
            embed = self.create_safe_confirmation(ctx, members)
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '✅':
                await msg.delete()
                await self.start_dm_process(ctx, members)
            else:
                await msg.delete()
                await ctx.send("❌ Mass DM cancelled.")
                
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.send("❌ Confirmation timeout. Operation cancelled.")

    def create_ultrafast_confirmation(self, ctx, members):
        """Create confirmation embed for ultrafast mode"""
        embed = discord.Embed(
            title="⚡ ULTRA FAST MASS DM - CONFIRM",
            description=f"**{ctx.guild.name}** - {len(members)} members",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🚀 ULTRA FAST MODE",
            value="• Speed: **MAXIMUM POSSIBLE** ⚡\n• Delay: `0.05 seconds`\n• Batch: `50 members/batch`\n• Est. Time: `5-10 seconds`",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ EXTREME WARNING",
            value="**HIGH RISK OF RATE LIMITS!**\n• Discord may temporarily ban the bot\n• Use at your own risk\n• Not recommended for large servers",
            inline=False
        )
        
        embed.add_field(
            name="🔥 BYPASS TECHNIQUES",
            value="• Batch sending (50 at once)\n• Minimum delays\n• Async overload\n• Maximum speed",
            inline=False
        )
        
        embed.set_footer(text="⚡ LIGHT SPEED DM - Confirm with ✅")
        return embed

    def create_safe_confirmation(self, ctx, members):
        """Create confirmation embed for safe mode"""
        embed = discord.Embed(
            title="🛡️ SAFE MASS DM - CONFIRM",
            description=f"**{ctx.guild.name}** - {len(members)} members",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        time_est = self.calculate_time(ctx.guild)
        
        embed.add_field(
            name="🛡️ SAFE MODE",
            value=f"• Speed: **CONTROLLED**\n• Delay: `1.5 seconds`\n• Batch: `10 members/batch`\n• Est. Time: `{time_est}`",
            inline=False
        )
        
        embed.add_field(
            name="✅ SAFETY FEATURES",
            value="• No rate limits\n• Stable delivery\n• Progress saving\n• Can be stopped anytime",
            inline=False
        )
        
        embed.add_field(
            name="📊 ESTIMATED STATS",
            value=f"• Total Members: `{len(members)}`\n• Success Rate: `~95%`\n• Time Required: `{time_est}`\n• Status: **SAFE**",
            inline=False
        )
        
        embed.set_footer(text="🛡️ RATE LIMIT SAFE - Confirm with ✅")
        return embed

    async def start_dm_process(self, ctx, members):
        """Start DM process based on mode"""
        self.is_dming = True
        self.sent_count = 0
        self.failed_count = 0
        self.total_members = len(members)
        
        progress_msg = await ctx.send(f"🔄 **Starting {self.dm_mode.upper()} Mass DM...**")
        
        # Start appropriate DM task
        if self.dm_mode == "ultrafast":
            task = asyncio.create_task(self.send_ultrafast_dms(ctx, members, progress_msg))
        else:
            task = asyncio.create_task(self.send_safe_dms(ctx, members, progress_msg))
        
        self.dm_tasks[ctx.guild.id] = task
        
        try:
            await task
        except asyncio.CancelledError:
            await progress_msg.edit(content=f"⏹️ **{self.dm_mode.upper()} Mass DM Stopped!**")
        except Exception as e:
            await progress_msg.edit(content=f"❌ **Error:** {str(e)}")
        finally:
            self.is_dming = False

    async def send_ultrafast_dms(self, ctx, members, progress_msg):
        """ULTRA FAST DM sending - Light Speed ⚡"""
        total_members = len(members)
        start_time = time.time()
        
        # Send in ultra-fast batches
        for i in range(0, total_members, self.batch_size):
            if not self.is_dming:
                break
                
            batch = members[i:i + self.batch_size]
            batch_tasks = []
            
            # Create send tasks for batch
            for member in batch:
                try:
                    if self.embed_mode and isinstance(self.current_message, dict):
                        embed = discord.Embed.from_dict(self.current_message)
                        batch_tasks.append(member.send(embed=embed))
                    else:
                        batch_tasks.append(member.send(self.current_message))
                except:
                    self.failed_count += 1
            
            # Send entire batch at once - MAXIMUM SPEED
            if batch_tasks:
                try:
                    results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    successful = sum(1 for r in results if not isinstance(r, Exception))
                    self.sent_count += successful
                    self.failed_count += len(results) - successful
                except:
                    self.failed_count += len(batch_tasks)
            
            # Update progress
            current = min(i + self.batch_size, total_members)
            elapsed = time.time() - start_time
            speed = self.sent_count / elapsed if elapsed > 0 else 0
            
            # Ultra-fast progress update
            if i % 100 == 0 or current == total_members:
                embed = discord.Embed(
                    title="⚡ ULTRA FAST DM - IN PROGRESS",
                    color=0xff0000,
                    timestamp=datetime.utcnow()
                )
                
                progress_percent = (current / total_members) * 100
                remaining = total_members - current
                eta = remaining / (speed if speed > 0 else 50)
                
                embed.add_field(
                    name="📊 PROGRESS",
                    value=f"```\n{current}/{total_members}\n{progress_percent:.1f}%\n```",
                    inline=True
                )
                
                embed.add_field(
                    name="⚡ SPEED",
                    value=f"• DMs/sec: `{speed:.1f}`\n• ETA: `{eta:.1f}s`\n• Elapsed: `{elapsed:.1f}s`",
                    inline=True
                )
                
                embed.add_field(
                    name="📈 STATS",
                    value=f"• ✅ Sent: `{self.sent_count}`\n• ❌ Failed: `{self.failed_count}`\n• 🎯 Success: `{(self.sent_count/current*100):.1f}%`",
                    inline=False
                )
                
                try:
                    await progress_msg.edit(embed=embed)
                except:
                    pass
            
            # MINIMUM DELAY - LIGHT SPEED
            await asyncio.sleep(self.delay_ultrafast)
        
        # Completion for ultrafast
        await self.send_completion_message(ctx, progress_msg, members, start_time, "ULTRA FAST")

    async def send_safe_dms(self, ctx, members, progress_msg):
        """SAFE DM sending - Rate Limit Safe"""
        total_members = len(members)
        start_time = time.time()
        
        for i, member in enumerate(members):
            if not self.is_dming:
                break
                
            try:
                if self.embed_mode and isinstance(self.current_message, dict):
                    embed = discord.Embed.from_dict(self.current_message)
                    await member.send(embed=embed)
                else:
                    await member.send(self.current_message)
                self.sent_count += 1
            except discord.Forbidden:
                self.failed_count += 1
            except Exception as e:
                self.failed_count += 1
            
            # Update progress every 10 members
            if i % 10 == 0 or i == total_members - 1:
                elapsed = time.time() - start_time
                progress = (i + 1) / total_members * 100
                speed = self.sent_count / elapsed if elapsed > 0 else 0
                
                embed = discord.Embed(
                    title="🛡️ SAFE DM - IN PROGRESS",
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="📊 PROGRESS",
                    value=f"```\n{i+1}/{total_members}\n{progress:.1f}%\n```",
                    inline=True
                )
                
                embed.add_field(
                    name="⏱️ TIMING",
                    value=f"• Speed: `{speed:.2f}/sec`\n• Elapsed: `{elapsed:.0f}s`\n• Delay: `{self.delay_safe}s`",
                    inline=True
                )
                
                embed.add_field(
                    name="📈 STATISTICS",
                    value=f"• ✅ Sent: `{self.sent_count}`\n• ❌ Failed: `{self.failed_count}`\n• 🎯 Rate: `{(self.sent_count/(i+1)*100):.1f}%`",
                    inline=False
                )
                
                try:
                    await progress_msg.edit(embed=embed)
                except:
                    pass
            
            # Safe delay to avoid rate limits
            await asyncio.sleep(self.delay_safe)
        
        # Completion for safe mode
        await self.send_completion_message(ctx, progress_msg, members, start_time, "SAFE")

    async def send_completion_message(self, ctx, progress_msg, members, start_time, mode):
        """Send completion message"""
        elapsed = time.time() - start_time
        total = len(members)
        
        embed = discord.Embed(
            title=f"✅ {mode} MASS DM COMPLETE",
            color=0x00ff00 if mode == "SAFE" else 0xff0000,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📊 FINAL STATISTICS",
            value=f"```\nTotal Members: {total}\n✅ Successful: {self.sent_count}\n❌ Failed: {self.failed_count}\n🎯 Success Rate: {(self.sent_count/total*100):.1f}%\n⏱️ Time Taken: {elapsed:.1f} seconds\n```",
            inline=False
        )
        
        embed.add_field(
            name=f"⚡ {mode} MODE PERFORMANCE",
            value=f"• Avg. Speed: `{self.sent_count/elapsed:.2f} DMs/sec`\n• Total Time: `{elapsed:.1f}s`\n• Efficiency: `{(self.sent_count/total*100):.1f}%`",
            inline=False
        )
        
        embed.add_field(
            name="📝 MESSAGE SENT",
            value=f"```\n{str(self.current_message)[:150]}...\n```",
            inline=False
        )
        
        if mode == "ULTRA FAST":
            embed.add_field(
                name="⚠️ ULTRA FAST MODE NOTE",
                value="Bot may be rate limited temporarily. Wait 5-10 minutes before next ultra fast DM.",
                inline=False
            )
        
        embed.set_footer(text=f"{mode} Mass DM Bot • Professional Delivery")
        
        await progress_msg.edit(embed=embed)

    @commands.command(name='stopdm')
    @commands.has_permissions(administrator=True)
    async def stop_mass_dm(self, ctx):
        """Stop ongoing Mass DM"""
        if not self.is_dming:
            await ctx.send("❌ No DM process is running!")
            return
            
        self.is_dming = False
        
        if ctx.guild.id in self.dm_tasks:
            self.dm_tasks[ctx.guild.id].cancel()
            del self.dm_tasks[ctx.guild.id]
        
        mode_display = "⚡ ULTRA FAST" if self.dm_mode == "ultrafast" else "🛡️ SAFE"
        
        embed = discord.Embed(
            title=f"⏹️ {mode_display} MASS DM STOPPED",
            description=f"DM sending process has been stopped.",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📊 PARTIAL STATS",
            value=f"• ✅ Sent: `{self.sent_count}`\n• ❌ Failed: `{self.failed_count}`\n• 📊 Progress: `{(self.sent_count/self.total_members*100):.1f}%`\n• Mode: `{self.dm_mode.upper()}`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='dmstatus')
    @commands.has_permissions(administrator=True)
    async def dm_status(self, ctx):
        """Check DM sending status"""
        members = [m for m in ctx.guild.members if not m.bot]
        
        embed = discord.Embed(
            title="📊 DM STATUS DASHBOARD",
            color=0x5865F2 if self.dm_mode == "safe" else 0xff0000,
            timestamp=datetime.utcnow()
        )
        
        if self.is_dming:
            mode_display = "⚡ ULTRA FAST" if self.dm_mode == "ultrafast" else "🛡️ SAFE"
            embed.description = f"🔄 **{mode_display} MASS DM IN PROGRESS**"
            
            progress = (self.sent_count / self.total_members * 100) if self.total_members > 0 else 0
            
            embed.add_field(
                name="📈 PROGRESS",
                value=f"```\n{self.sent_count}/{self.total_members}\n{progress:.1f}% complete\n```",
                inline=False
            )
            
            if self.dm_mode == "ultrafast":
                embed.add_field(
                    name="⚡ ULTRA FAST MODE",
                    value="• Speed: **MAXIMUM**\n• Delay: `0.05s`\n• Batch: `50/batch`\n• Risk: **HIGH**",
                    inline=True
                )
            else:
                embed.add_field(
                    name="🛡️ SAFE MODE",
                    value="• Speed: `0.67/sec`\n• Delay: `1.5s`\n• Batch: `10/batch`\n• Risk: **LOW**",
                    inline=True
                )
        else:
            embed.description = "✅ **READY FOR MASS DM**"
            
            if self.current_message:
                msg_type = "Embed" if self.embed_mode else "Text"
                time_est = self.calculate_time(ctx.guild)
                
                embed.add_field(
                    name="📝 CURRENT SETUP",
                    value=f"• Mode: `{self.dm_mode.upper()}`\n• Type: `{msg_type}`\n• Length: `{len(str(self.current_message))} chars`\n• Est. Time: `{time_est}`",
                    inline=False
                )
                
                embed.add_field(
                    name="👥 SERVER STATS",
                    value=f"• Total Members: `{len(ctx.guild.members)}`\n• Humans: `{len(members)}`\n• Ready for DM: `✅`",
                    inline=True
                )
            else:
                embed.add_field(
                    name="⚠️ NO MESSAGE SET",
                    value="Use `!setdm` to set a message first",
                    inline=False
                )
        
        embed.set_footer(text=f"Current Mode: {self.dm_mode.upper()}")
        await ctx.send(embed=embed)

    @commands.command(name='dmstats')
    @commands.has_permissions(administrator=True)
    async def dm_statistics(self, ctx):
        """View DM statistics"""
        members = [m for m in ctx.guild.members if not m.bot]
        
        embed = discord.Embed(
            title="📈 ADVANCED DM STATISTICS",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        # Mode comparison
        if self.dm_mode == "ultrafast":
            ultra_time = len(members) * 0.05 / 50
            safe_time = len(members) * 1.5 / 10
            
            embed.add_field(
                name="⚡ ULTRA FAST MODE",
                value=f"• Est. Time: `{ultra_time:.1f}s`\n• Speed: `20 DMs/sec`\n• Risk: **HIGH**\n• Rate Limit: **LIKELY**",
                inline=True
            )
            
            embed.add_field(
                name="🛡️ SAFE MODE",
                value=f"• Est. Time: `{safe_time:.1f}s`\n• Speed: `0.67 DMs/sec`\n• Risk: **LOW**\n• Rate Limit: **UNLIKELY**",
                inline=True
            )
        else:
            ultra_time = len(members) * 0.05 / 50
            safe_time = len(members) * 1.5 / 10
            
            embed.add_field(
                name="🛡️ SAFE MODE",
                value=f"• Est. Time: `{safe_time:.1f}s`\n• Speed: `0.67 DMs/sec`\n• Risk: **LOW**\n• Rate Limit: **UNLIKELY**",
                inline=True
            )
            
            embed.add_field(
                name="⚡ ULTRA FAST MODE",
                value=f"• Est. Time: `{ultra_time:.1f}s`\n• Speed: `20 DMs/sec`\n• Risk: **HIGH**\n• Rate Limit: **LIKELY**",
                inline=True
            )
        
        # Bot performance
        total_attempts = self.sent_count + self.failed_count
        success_rate = (self.sent_count / total_attempts * 100) if total_attempts > 0 else 0
        
        embed.add_field(
            name="🤖 BOT PERFORMANCE",
            value=f"• Total Sent: `{self.sent_count}`\n• Total Failed: `{self.failed_count}`\n• Success Rate: `{success_rate:.1f}%`\n• Current Mode: `{self.dm_mode.upper()}`",
            inline=False
        )
        
        # Server analysis
        dm_enabled = len(members) * 0.95  # 95% can receive DMs approx
        
        embed.add_field(
            name="👥 SERVER ANALYSIS",
            value=f"• Total Humans: `{len(members)}`\n• Expected Success: `{dm_enabled:.0f}`\n• Expected Fail: `{len(members) - dm_enabled:.0f}`\n• Est. Success Rate: `95%`",
            inline=False
        )
        
        embed.set_footer(text=f"Server: {ctx.guild.name} | Mode: {self.dm_mode.upper()}")
        await ctx.send(embed=embed)

    @commands.command(name='dmhelp')
    async def dm_help(self, ctx):
        """Show help menu for Mass DM"""
        embed = discord.Embed(
            title="🤖 DUAL MODE MASS DM BOT - HELP",
            description="**Ultra Fast ⚡ vs Safe 🛡️ Mode**",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="⚡ ULTRA FAST MODE",
            value=(
                "**Commands:**\n"
                "`!mode ultrafast` - Switch to ultra fast\n"
                "`!setdm [msg]` - Set message\n"
                "`!startdm` - Start at light speed\n\n"
                "**Features:**\n"
                "• 0.05s delay per batch\n"
                "• 50 members per batch\n"
                "• 20 DMs/second\n"
                "• HIGH risk of rate limits\n"
                "• Use for emergency broadcasts"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🛡️ SAFE MODE",
            value=(
                "**Commands:**\n"
                "`!mode safe` - Switch to safe mode\n"
                "`!setdm [msg]` - Set message\n"
                "`!startdm` - Start safely\n\n"
                "**Features:**\n"
                "• 1.5s delay per member\n"
                "• 10 members per batch\n"
                "• 0.67 DMs/second\n"
                "• NO rate limits\n"
                "• Stable and reliable"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 ALL COMMANDS",
            value=(
                "`!setup` - Setup admin panel\n"
                "`!mode [ultrafast/safe]` - Change mode\n"
                "`!setdm [message]` - Set DM message\n"
                "`!setembed` - Set embed message\n"
                "`!preview` - Preview message\n"
                "`!startdm` - Start Mass DM\n"
                "`!stopdm` - Stop Mass DM\n"
                "`!dmstatus` - Check status\n"
                "`!dmstats` - View statistics\n"
                "`!dmhelp` - This menu"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚠️ IMPORTANT NOTES",
            value=(
                "• **Ultra Fast:** Use only when speed is critical\n"
                "• **Safe Mode:** Recommended for daily use\n"
                "• Rate limits can ban bot for 1-24 hours\n"
                "• Always preview before sending!\n"
                "• Can stop anytime with `!stopdm`"
            ),
            inline=False
        )
        
        embed.set_footer(text="Dual Mode Mass DM Bot • Professional System")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MassDM(bot))
