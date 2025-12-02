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
        self.delay_safe = 1.5  # Safe mode delay
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
            self.delay_ultrafast = 0.1  # 10 DMs per second
            
            embed = discord.Embed(
                title="⚡ ULTRA FAST MODE ACTIVATED",
                description="**Warning:** This mode may trigger rate limits!",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="⚡ SPEED SETTINGS",
                value="• Delay: `0.1 seconds`\n• Speed: `10 DMs/second`\n• Risk Level: **HIGH**",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        elif mode.lower() in ["safe", "slow", "normal", "🛡️"]:
            self.dm_mode = "safe"
            self.delay_safe = 1.5
            
            embed = discord.Embed(
                title="🛡️ SAFE MODE ACTIVATED",
                description="**Rate Limit Safe Mode**",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="⚙️ SAFE SETTINGS",
                value="• Delay: `1.5 seconds`\n• Speed: `0.67 DMs/second`\n• Risk Level: **LOW**",
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
        
        members = [m for m in ctx.guild.members if not m.bot]
        time_estimate = self.calculate_time(len(members))
        
        embed = discord.Embed(
            title="✅ MESSAGE SET",
            description=f"**Mode:** `{self.dm_mode.upper()}`\n\n**Preview:**\n{message[:300]}...",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="⏱️ TIME ESTIMATE",
            value=f"• Members: `{len(members)}`\n• Est. Time: `{time_estimate}`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    def calculate_time(self, member_count):
        """Calculate estimated time based on mode"""
        if self.dm_mode == "ultrafast":
            total_time = member_count * self.delay_ultrafast
            if total_time < 60:
                return f"{total_time:.1f} seconds ⚡"
            else:
                minutes = total_time / 60
                return f"{minutes:.1f} minutes"
        else:
            total_time = member_count * self.delay_safe
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
        
        # Confirmation
        confirm_embed = discord.Embed(
            title=f"⚠️ {self.dm_mode.upper()} MASS DM - CONFIRM",
            description=f"**{ctx.guild.name}** - {len(members)} members",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        
        time_est = self.calculate_time(len(members))
        
        if self.dm_mode == "ultrafast":
            confirm_embed.add_field(
                name="⚡ ULTRA FAST MODE",
                value=f"• Delay: `{self.delay_ultrafast}s`\n• Est. Time: `{time_est}`\n• Risk: **HIGH**",
                inline=False
            )
        else:
            confirm_embed.add_field(
                name="🛡️ SAFE MODE",
                value=f"• Delay: `{self.delay_safe}s`\n• Est. Time: `{time_est}`\n• Risk: **LOW**",
                inline=False
            )
        
        msg = await ctx.send(embed=confirm_embed)
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

    async def start_dm_process(self, ctx, members):
        """Start DM process"""
        self.is_dming = True
        self.sent_count = 0
        self.failed_count = 0
        self.total_members = len(members)
        
        progress_msg = await ctx.send(f"🔄 **Starting {self.dm_mode.upper()} Mass DM...**")
        
        # Start DM task
        task = asyncio.create_task(self.send_dms_to_members(ctx, members, progress_msg))
        self.dm_tasks[ctx.guild.id] = task
        
        try:
            await task
        except asyncio.CancelledError:
            await progress_msg.edit(content=f"⏹️ **{self.dm_mode.upper()} Mass DM Stopped!**")
        except Exception as e:
            await progress_msg.edit(content=f"❌ **Error:** {str(e)}")
        finally:
            self.is_dming = False

    async def send_dms_to_members(self, ctx, members, progress_msg):
        """Send DMs to all members - SIMPLE & WORKING VERSION"""
        total = len(members)
        start_time = time.time()
        
        for i, member in enumerate(members):
            if not self.is_dming:
                break
            
            try:
                # Try to send DM
                if self.embed_mode and isinstance(self.current_message, dict):
                    embed = discord.Embed.from_dict(self.current_message)
                    await member.send(embed=embed)
                else:
                    await member.send(self.current_message)
                self.sent_count += 1
                print(f"✅ Sent to {member.name} ({i+1}/{total})")
                
            except discord.Forbidden:
                # DMs closed
                self.failed_count += 1
                print(f"❌ {member.name} - DMs closed")
            except Exception as e:
                # Other errors
                self.failed_count += 1
                print(f"❌ {member.name} - Error: {str(e)}")
            
            # Update progress every 10 members
            if i % 10 == 0 or i == total - 1:
                elapsed = time.time() - start_time
                progress_percent = ((i + 1) / total) * 100
                
                # Create progress embed
                embed = discord.Embed(
                    title=f"📤 {self.dm_mode.upper()} MASS DM - IN PROGRESS",
                    color=0xff0000 if self.dm_mode == "ultrafast" else 0x00ff00,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="📊 PROGRESS",
                    value=f"```\n{i+1}/{total}\n{progress_percent:.1f}%\n```",
                    inline=True
                )
                
                embed.add_field(
                    name="📈 STATS",
                    value=f"• ✅ Sent: `{self.sent_count}`\n• ❌ Failed: `{self.failed_count}`\n• 🎯 Rate: `{(self.sent_count/(i+1)*100):.1f}%`",
                    inline=True
                )
                
                # Calculate speed and ETA
                if elapsed > 0:
                    speed = self.sent_count / elapsed
                    remaining = total - (i + 1)
                    if speed > 0:
                        eta = remaining / speed
                        embed.add_field(
                            name="⏱️ TIMING",
                            value=f"• Speed: `{speed:.2f}/sec`\n• Elapsed: `{elapsed:.0f}s`\n• ETA: `{eta:.0f}s`",
                            inline=False
                        )
                
                try:
                    await progress_msg.edit(embed=embed)
                except:
                    pass
            
            # Apply delay based on mode
            if self.dm_mode == "ultrafast":
                await asyncio.sleep(self.delay_ultrafast)
            else:
                await asyncio.sleep(self.delay_safe)
        
        # Send completion message
        if self.is_dming:
            await self.send_completion_message(ctx, progress_msg, members, start_time)

    async def send_completion_message(self, ctx, progress_msg, members, start_time):
        """Send completion message"""
        elapsed = time.time() - start_time
        total = len(members)
        
        embed = discord.Embed(
            title=f"✅ {self.dm_mode.upper()} MASS DM COMPLETE",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        success_rate = (self.sent_count / total * 100) if total > 0 else 0
        
        embed.add_field(
            name="📊 FINAL STATISTICS",
            value=f"```\nTotal Members: {total}\n✅ Successful: {self.sent_count}\n❌ Failed: {self.failed_count}\n🎯 Success Rate: {success_rate:.1f}%\n⏱️ Time Taken: {elapsed:.1f} seconds\n```",
            inline=False
        )
        
        if elapsed > 0:
            speed = self.sent_count / elapsed
            embed.add_field(
                name="⚡ PERFORMANCE",
                value=f"• Avg. Speed: `{speed:.2f} DMs/sec`\n• Mode: `{self.dm_mode.upper()}`",
                inline=False
            )
        
        embed.add_field(
            name="📝 MESSAGE SENT",
            value=f"```\n{str(self.current_message)[:150]}...\n```",
            inline=False
        )
        
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
        
        embed = discord.Embed(
            title=f"⏹️ {self.dm_mode.upper()} MASS DM STOPPED",
            description="DM sending process has been stopped.",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📊 PARTIAL STATS",
            value=f"• ✅ Sent: `{self.sent_count}`\n• ❌ Failed: `{self.failed_count}`\n• 📊 Progress: `{(self.sent_count/self.total_members*100):.1f}%`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='preview')
    @commands.has_permissions(administrator=True)
    async def preview_message(self, ctx):
        """Preview the current message"""
        if not self.current_message:
            await ctx.send("❌ No message set! Use `!setdm` first.")
            return
            
        if self.embed_mode:
            try:
                if isinstance(self.current_message, dict):
                    embed = discord.Embed.from_dict(self.current_message)
                    await ctx.send("**📋 PREVIEW:**", embed=embed)
                else:
                    await ctx.send("❌ Invalid embed data!")
            except:
                await ctx.send("❌ Error displaying embed!")
        else:
            embed = discord.Embed(
                title="📋 MESSAGE PREVIEW",
                description=self.current_message[:2000],
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Length: {len(self.current_message)} characters | Mode: {self.dm_mode}")
            await ctx.send(embed=embed)

    @commands.command(name='dmstatus')
    @commands.has_permissions(administrator=True)
    async def dm_status(self, ctx):
        """Check DM sending status"""
        members = [m for m in ctx.guild.members if not m.bot]
        
        embed = discord.Embed(
            title="📊 DM STATUS",
            color=0x5865F2 if not self.is_dming else 0xff9900,
            timestamp=datetime.utcnow()
        )
        
        if self.is_dming:
            embed.description = f"🔄 **{self.dm_mode.upper()} MASS DM IN PROGRESS**"
            
            progress = (self.sent_count / self.total_members * 100) if self.total_members > 0 else 0
            
            embed.add_field(
                name="📈 PROGRESS",
                value=f"```\n{self.sent_count}/{self.total_members}\n{progress:.1f}%\n```",
                inline=False
            )
            
            embed.add_field(
                name="⚙️ MODE",
                value=f"• Current: `{self.dm_mode.upper()}`\n• Delay: `{self.delay_ultrafast if self.dm_mode == 'ultrafast' else self.delay_safe}s`",
                inline=True
            )
        else:
            embed.description = "✅ **READY FOR MASS DM**"
            
            if self.current_message:
                msg_type = "Embed" if self.embed_mode else "Text"
                time_est = self.calculate_time(len(members))
                
                embed.add_field(
                    name="📝 CURRENT SETUP",
                    value=f"• Mode: `{self.dm_mode.upper()}`\n• Type: `{msg_type}`\n• Length: `{len(str(self.current_message))} chars`\n• Est. Time: `{time_est}`",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ NO MESSAGE SET",
                    value="Use `!setdm` to set a message first",
                    inline=False
                )
        
        await ctx.send(embed=embed)

    @commands.command(name='dmhelp')
    async def dm_help(self, ctx):
        """Show help menu"""
        embed = discord.Embed(
            title="🤖 MASS DM BOT HELP",
            description="**Commands and Usage Guide**",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🚀 BASIC COMMANDS",
            value=(
                "`!setup` - Setup admin panel\n"
                "`!mode [ultrafast/safe]` - Change speed mode\n"
                "`!setdm [message]` - Set DM message\n"
                "`!preview` - Preview message\n"
                "`!startdm` - Start sending DMs\n"
                "`!stopdm` - Stop sending\n"
                "`!dmstatus` - Check status"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ ULTRA FAST MODE",
            value="• Delay: 0.1 seconds\n• Speed: 10 DMs/second\n• Risk: High (rate limits possible)\n• Use for emergency",
            inline=False
        )
        
        embed.add_field(
            name="🛡️ SAFE MODE",
            value="• Delay: 1.5 seconds\n• Speed: 0.67 DMs/second\n• Risk: Low (rate limit safe)\n• Recommended for normal use",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MassDM(bot))
