import discord
from discord.ext import commands
import asyncio
import json
from datetime import datetime

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

    @commands.command(name='setup')
    @commands.has_permissions(administrator=True)
    async def setup_panel(self, ctx):
        """Setup Admin Panel for Mass DM"""
        embed = discord.Embed(
            title="⚙️ MASS DM BOT - ADMIN PANEL",
            description="**Setup successful!** This channel is now your Mass DM control panel.",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📋 AVAILABLE COMMANDS",
            value=(
                "`!setdm [message]` - Set DM message\n"
                "`!setembed` - Toggle embed mode\n"
                "`!preview` - Preview current message\n"
                "`!startdm` - Start Mass DM\n"
                "`!stopdm` - Stop Mass DM\n"
                "`!dmstatus` - Check DM status\n"
                "`!dmstats` - View statistics\n"
                "`!dmhelp` - Show help menu"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ QUICK START",
            value=(
                "1. Use `!setdm your message` to set message\n"
                "2. Use `!setembed` for embed mode\n"
                "3. Use `!preview` to check message\n"
                "4. Use `!startdm` to begin sending"
            ),
            inline=False
        )
        
        embed.set_footer(text="Mass DM Bot • Professional Messaging System")
        await ctx.send(embed=embed)
        
        # Save this channel as admin panel
        self.bot.admin_panel_channels[str(ctx.guild.id)] = str(ctx.channel.id)
        self.bot.save_data()

    @commands.command(name='setdm')
    @commands.has_permissions(administrator=True)
    async def set_dm_message(self, ctx, *, message: str):
        """Set the message to send to all members"""
        self.current_message = message
        self.embed_mode = False
        
        embed = discord.Embed(
            title="✅ MESSAGE SET",
            description=f"Message saved successfully!\n\n**Preview:**\n{message[:500]}...",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📊 STATS", value=f"• Characters: `{len(message)}`\n• Mode: `Normal Text`", inline=False)
        embed.set_footer(text="Use !preview to see full message")
        await ctx.send(embed=embed)

    @commands.command(name='setembed')
    @commands.has_permissions(administrator=True)
    async def set_embed_message(self, ctx, *, json_data: str = None):
        """Set embed message using JSON or interactive mode"""
        if json_data:
            try:
                data = json.loads(json_data)
                self.current_message = data
                self.embed_mode = True
                await ctx.send("✅ Embed message set from JSON!")
            except:
                await ctx.send("❌ Invalid JSON format!")
        else:
            # Interactive embed builder
            embed = discord.Embed(
                title="🎨 EMBED BUILDER",
                description="React with emojis to build your embed:",
                color=0x5865F2
            )
            
            embed.add_field(
                name="📝 OPTIONS",
                value=(
                    "🇹 - Set Title\n"
                    "🇩 - Set Description\n"
                    "🇨 - Set Color\n"
                    "🇫 - Add Field\n"
                    "🇮 - Set Image URL\n"
                    "🇹🇭 - Set Thumbnail\n"
                    "🇫🇴 - Set Footer\n"
                    "✅ - Finish & Save"
                ),
                inline=False
            )
            
            msg = await ctx.send(embed=embed)
            
            # Add reactions
            reactions = ['🇹', '🇩', '🇨', '🇫', '🇮', '🇹🇭', '🇫🇴', '✅']
            for reaction in reactions:
                await msg.add_reaction(reaction)
            
            # Store message for later
            self.embed_builder_msg = msg
            self.embed_data = {
                'title': '',
                'description': '',
                'color': 0x5865F2,
                'fields': [],
                'image': '',
                'thumbnail': '',
                'footer': ''
            }

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
                description=self.current_message[:4000],
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Length: {len(self.current_message)} characters")
            await ctx.send(embed=embed)

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
            
        # Confirmation
        confirm_embed = discord.Embed(
            title="⚠️ CONFIRM MASS DM",
            description=f"This will send DM to **ALL** members of **{ctx.guild.name}**",
            color=0xff9900,
            timestamp=datetime.utcnow()
        )
        
        member_count = sum(1 for m in ctx.guild.members if not m.bot)
        confirm_embed.add_field(
            name="📊 STATISTICS",
            value=f"• Total Members: `{member_count}`\n• Bots Excluded: `✅`\n• Estimated Time: `{member_count*2} seconds`",
            inline=False
        )
        
        confirm_embed.add_field(
            name="🚨 WARNING",
            value="This action cannot be undone! Make sure you have the right to DM all members.",
            inline=False
        )
        
        confirm_embed.set_footer(text="React with ✅ to confirm or ❌ to cancel")
        
        msg = await ctx.send(embed=confirm_embed)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '✅':
                await msg.delete()
                await self.start_dm_process(ctx)
            else:
                await msg.delete()
                await ctx.send("❌ Mass DM cancelled.")
                
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.send("❌ Confirmation timeout. Operation cancelled.")

    async def start_dm_process(self, ctx):
        """Actual DM sending process"""
        self.is_dming = True
        self.sent_count = 0
        self.failed_count = 0
        
        # Get all non-bot members
        members = [m for m in ctx.guild.members if not m.bot]
        self.total_members = len(members)
        
        if self.total_members == 0:
            await ctx.send("❌ No members found to DM!")
            self.is_dming = False
            return
        
        # Progress embed
        progress_msg = await ctx.send("🔄 **Starting Mass DM...**")
        
        # Start DM task
        task = asyncio.create_task(self.send_dms(ctx, members, progress_msg))
        self.dm_tasks[ctx.guild.id] = task
        
        try:
            await task
        except asyncio.CancelledError:
            await progress_msg.edit(content="⏹️ **Mass DM Stopped!**")
        except Exception as e:
            await progress_msg.edit(content=f"❌ **Error:** {str(e)}")
        finally:
            self.is_dming = False

    async def send_dms(self, ctx, members, progress_msg):
        """Send DMs to all members"""
        for i, member in enumerate(members):
            if not self.is_dming:
                break
                
            try:
                if self.embed_mode:
                    # Send embed
                    if isinstance(self.current_message, dict):
                        embed = discord.Embed.from_dict(self.current_message)
                        await member.send(embed=embed)
                    else:
                        await member.send(self.current_message)
                else:
                    # Send normal message
                    await member.send(self.current_message)
                    
                self.sent_count += 1
                
                # Update progress every 10 members
                if i % 10 == 0 or i == len(members) - 1:
                    progress = (i + 1) / len(members) * 100
                    
                    embed = discord.Embed(
                        title="📤 MASS DM IN PROGRESS",
                        color=0x5865F2,
                        timestamp=datetime.utcnow()
                    )
                    
                    embed.add_field(
                        name="📊 PROGRESS",
                        value=f"```\n{self.sent_count}/{len(members)} members\n{progress:.1f}% complete\n```",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="⚡ STATS",
                        value=f"• ✅ Sent: `{self.sent_count}`\n• ❌ Failed: `{self.failed_count}`\n• ⏱️ Remaining: `{len(members) - i - 1}`",
                        inline=True
                    )
                    
                    embed.set_footer(text=f"Current: {member.name}")
                    
                    try:
                        await progress_msg.edit(embed=embed)
                    except:
                        pass
                    
                # Rate limiting
                await asyncio.sleep(1.5)
                
            except discord.Forbidden:
                self.failed_count += 1
                continue
            except Exception as e:
                self.failed_count += 1
                continue
        
        # Completion message
        if self.is_dming:
            complete_embed = discord.Embed(
                title="✅ MASS DM COMPLETE",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            complete_embed.add_field(
                name="📊 FINAL STATISTICS",
                value=f"```\nTotal Members: {len(members)}\n✅ Successful: {self.sent_count}\n❌ Failed: {self.failed_count}\n🎯 Success Rate: {(self.sent_count/len(members)*100):.1f}%\n```",
                inline=False
            )
            
            complete_embed.add_field(
                name="📝 MESSAGE SENT",
                value=f"```\n{self.current_message[:200]}...\n```" if len(str(self.current_message)) > 200 else f"```\n{self.current_message}\n```",
                inline=False
            )
            
            complete_embed.set_footer(text="Mass DM Bot • Professional Delivery")
            
            await progress_msg.edit(embed=complete_embed)
            self.is_dming = False

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
            title="⏹️ MASS DM STOPPED",
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

    @commands.command(name='dmstatus')
    @commands.has_permissions(administrator=True)
    async def dm_status(self, ctx):
        """Check DM sending status"""
        embed = discord.Embed(
            title="📊 DM STATUS",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        if self.is_dming:
            embed.description = "🔄 **Mass DM in Progress**"
            embed.color = 0xff9900
            
            progress = (self.sent_count / self.total_members * 100) if self.total_members > 0 else 0
            
            embed.add_field(
                name="📈 PROGRESS",
                value=f"```\n{self.sent_count}/{self.total_members}\n{progress:.1f}% complete\n```",
                inline=False
            )
            
            embed.add_field(
                name="⚡ SPEED",
                value=f"• Rate: `1.5s per member`\n• ETA: `{(self.total_members - self.sent_count) * 1.5:.0f} seconds`",
                inline=True
            )
        else:
            embed.description = "✅ **No DM process running**"
            embed.color = 0x00ff00
            
            if self.current_message:
                msg_type = "Embed" if self.embed_mode else "Text"
                embed.add_field(
                    name="📝 READY MESSAGE",
                    value=f"• Type: `{msg_type}`\n• Length: `{len(str(self.current_message))} chars`",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ NO MESSAGE SET",
                    value="Use `!setdm` to set a message",
                    inline=False
                )
        
        embed.set_footer(text="Use !startdm to begin sending")
        await ctx.send(embed=embed)

    @commands.command(name='dmstats')
    @commands.has_permissions(administrator=True)
    async def dm_statistics(self, ctx):
        """View DM statistics"""
        members = [m for m in ctx.guild.members if not m.bot]
        dm_enabled = sum(1 for m in members if not m.is_on_mobile())  # Approximate
        
        embed = discord.Embed(
            title="📈 DM STATISTICS",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="👥 SERVER MEMBERS",
            value=f"• Total: `{len(ctx.guild.members)}`\n• Humans: `{len(members)}`\n• Bots: `{len(ctx.guild.members) - len(members)}`",
            inline=True
        )
        
        embed.add_field(
            name="📊 DM ANALYSIS",
            value=f"• Can Receive DMs: `{dm_enabled}`\n• DM Blocked: `{len(members) - dm_enabled}`\n• Success Rate: `{(dm_enabled/len(members)*100):.1f}%`",
            inline=True
        )
        
        embed.add_field(
            name="⚡ BOT STATS",
            value=f"• Total Sent: `{self.sent_count}`\n• Total Failed: `{self.failed_count}`\n• Overall Rate: `{(self.sent_count/(self.sent_count+self.failed_count)*100):.1f}%`" if self.sent_count+self.failed_count > 0 else "No data yet",
            inline=False
        )
        
        embed.set_footer(text=f"Server: {ctx.guild.name}")
        await ctx.send(embed=embed)

    @commands.command(name='dmhelp')
    async def dm_help(self, ctx):
        """Show help menu for Mass DM"""
        embed = discord.Embed(
            title="🤖 MASS DM BOT - HELP MENU",
            description="Complete guide to using the Mass DM Bot",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🚀 QUICK START",
            value=(
                "1. `!setup` - Setup admin panel\n"
                "2. `!setdm [message]` - Set message\n"
                "3. `!preview` - Check message\n"
                "4. `!startdm` - Start sending\n"
                "5. `!stopdm` - Stop sending\n"
                "6. `!dmstatus` - Check progress"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 MESSAGE TYPES",
            value=(
                "**Normal Text:** `!setdm Hello members!`\n"
                "**Embed Mode:** `!setembed` (interactive)\n"
                "**JSON Embed:** `!setembed {\"title\":\"Hello\",\"description\":\"Message\"}`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ ADMIN COMMANDS",
            value=(
                "`!setup` - Setup control panel\n"
                "`!setdm` - Set DM message\n"
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
                "• Rate limit: 1.5 seconds per member\n"
                "• Bots are automatically excluded\n"
                "• Members with DMs closed will be skipped\n"
                "• Progress is saved and can be resumed\n"
                "• Always preview before sending!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔧 TECHNICAL",
            value=(
                "• Requires: `Administrator` permission\n"
                "• Safe: Rate limit optimized\n"
                "• Efficient: Async processing\n"
                "• Reliable: Progress tracking\n"
                "• Professional: Beautiful embeds"
            ),
            inline=False
        )
        
        embed.set_footer(text="Mass DM Bot • Professional Messaging System")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle embed builder reactions"""
        if user.bot:
            return
            
        if hasattr(self, 'embed_builder_msg') and reaction.message.id == self.embed_builder_msg.id:
            await self.handle_embed_builder(reaction, user)

    async def handle_embed_builder(self, reaction, user):
        """Process embed builder reactions"""
        channel = reaction.message.channel
        
        if str(reaction.emoji) == '🇹':
            # Set title
            await channel.send("📝 **Enter title:**")
            
            def check(m):
                return m.author == user and m.channel == channel
                
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                self.embed_data['title'] = msg.content
                await channel.send(f"✅ Title set: `{msg.content}`")
            except asyncio.TimeoutError:
                await channel.send("❌ Timeout!")
                
        elif str(reaction.emoji) == '✅':
            # Save embed
            self.current_message = self.embed_data
            self.embed_mode = True
            await channel.send("✅ Embed saved! Use `!preview` to see it.")
            
            # Cleanup
            del self.embed_builder_msg
            del self.embed_data

async def setup(bot):
    await bot.add_cog(MassDM(bot))
